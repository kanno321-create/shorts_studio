"""TTS generation script with 4-tier fallback (Typecast -> Fish Audio -> ElevenLabs -> EdgeTTS).

Reads script.json, applies pronunciation conversion, generates Korean TTS audio.
Implements 4-tier fallback: tries Typecast first (Tier 0), then Fish Audio S1 (Tier 1),
then ElevenLabs (Tier 2), then EdgeTTS (Tier 3).

Exit codes:
    0 = success
    1 = input error (missing file, invalid JSON)
    2 = TTS generation error (all providers failed)

Outputs:
    - narration.mp3 at the specified output path
    - JSON result to stdout with keys: provider, output_path, duration_seconds, character_count
"""
import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
import ormsgpack
from dotenv import load_dotenv

# Load .env from project root (feedback_env_keys_sacred.md: load_dotenv(override=True) 필수)
# Silent provider fallback masked missing TYPECAST_API_KEY in session 41 — this fix is critical
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env", override=True)

from typecast import Typecast
from typecast.models import TTSRequest, Output, PresetPrompt

# ---------------------------------------------------------------------------
# VOICEVOX Nemo — 일본어 전용 TTS Provider (Tier 0 for ja)
# ---------------------------------------------------------------------------

VOICEVOX_DEFAULT_ENDPOINT = "http://localhost:50121"

# VOICEVOX 감정 파라미터 매핑 (Typecast처럼 프리셋 없으므로 파라미터 조합으로 표현)
VOICEVOX_EMOTION_MAP: dict[str, dict[str, float]] = {
    "normal":   {"speed": 1.0,  "pitch": 0.0,   "intonation": 1.0, "volume": 1.0},
    "tonedown": {"speed": 0.92, "pitch": -0.02, "intonation": 0.8, "volume": 0.9},
    "sad":      {"speed": 0.85, "pitch": -0.05, "intonation": 0.6, "volume": 0.8},
    "whisper":  {"speed": 0.80, "pitch": -0.03, "intonation": 0.5, "volume": 0.6},
    "toneup":   {"speed": 1.05, "pitch": 0.03,  "intonation": 1.2, "volume": 1.1},
    "angry":    {"speed": 1.08, "pitch": 0.05,  "intonation": 1.4, "volume": 1.2},
    "happy":    {"speed": 1.05, "pitch": 0.04,  "intonation": 1.3, "volume": 1.1},
}

# Module-level voice cache: voice_name -> voice_id (prevents redundant API calls)
_typecast_voice_cache: dict[str, str] = {}

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))
from pronunciation import load_pronunciation_table, apply_pronunciation


class TTSProviderError(Exception):
    """Raised when any TTS provider returns a retriable/fatal error."""
    def __init__(self, provider: str, status_code: int = None, message: str = ""):
        self.provider = provider
        self.status_code = status_code
        self.message = message
        super().__init__(f"{provider} error (HTTP {status_code}): {message}")


# Backward compatibility alias (per D-02)
ElevenLabsCreditError = TTSProviderError


def extract_narration(script_path: str) -> tuple[str, int]:
    """Extract concatenated narration text from script.json.

    Reads all sections and joins their narration fields with newline separators.
    Returns (full_text, total_character_count).
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    narration_parts = []
    for section in script["sections"]:
        narration_parts.append(section["narration"])

    full_text = "\n".join(narration_parts)
    return full_text, len(full_text.replace("\n", ""))


def extract_sections_with_emotions(script_path: str) -> list[dict]:
    """Extract sections with per-section emotion metadata from script.json.

    Returns list of dicts:
      [{narration, type, emotion, emotion_intensity, style_tag, scene}]
    Falls back to emotion_map from voice preset if section has no emotion field.
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    sections = []
    for section in script.get("sections", []):
        sections.append({
            "narration": section.get("narration", ""),
            "type": section.get("type", "body"),
            "scene": section.get("scene"),
            "emotion": section.get("emotion"),
            "emotion_intensity": section.get("emotion_intensity"),
            "style_tag": section.get("style_tag"),
        })
    return sections


def extract_chapters(script_path: str) -> list[dict]:
    """Extract chapter narrations from a video-mode script.json.

    Returns list of dicts: [{chapter_index: int, narration: str, type: str, title: str|None}]
    Ordered: intro (chapter=0), chapters (1..N), conclusion (chapter=-1).
    Returns empty list if script is not video pipeline.
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    if script.get("pipeline_type") != "video":
        return []
    chapters = []
    for section in script.get("sections", []):
        chapters.append({
            "chapter_index": section.get("chapter", 0),
            "narration": section.get("narration", ""),
            "type": section.get("type", "chapter"),
            "title": section.get("title"),
        })
    # Sort: intro (0) first, chapters (1..N) middle, conclusion (-1) last
    chapters.sort(key=lambda c: (c["chapter_index"] == -1, c["chapter_index"]))
    return chapters


def concat_with_silence(chapter_files: list[str], output_path: str, gap_seconds: float = 0.3):
    """Concatenate chapter MP3 files with silence gaps using FFmpeg concat demuxer.

    1. Generate silence.mp3 using FFmpeg anullsrc
    2. Build concat list file interleaving chapter files and silence
    3. Run FFmpeg concat demuxer (-f concat -safe 0 -c copy)
    """
    output_dir = str(Path(output_path).parent)
    silence_path = os.path.join(output_dir, "silence_gap.mp3")

    # Generate silence gap
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=44100:cl=stereo", "-t", str(gap_seconds),
        "-c:a", "libmp3lame", "-q:a", "2", silence_path
    ], check=True, capture_output=True)

    # Build concat list
    concat_list_path = os.path.join(output_dir, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for i, chapter_file in enumerate(chapter_files):
            safe_path = os.path.abspath(chapter_file).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
            if i < len(chapter_files) - 1:  # No silence after last chapter
                safe_silence = os.path.abspath(silence_path).replace("\\", "/")
                f.write(f"file '{safe_silence}'\n")

    # Concat without re-encoding
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", output_path
    ], check=True, capture_output=True)

    # Cleanup temp files
    for temp_file in [silence_path, concat_list_path]:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def chunk_text_for_typecast(text: str, max_chars: int = 2000) -> list[str]:
    """Split text into chunks at sentence boundaries, each <= max_chars.

    Korean sentence boundaries: 다. / 요. / ! / ? / 니다. / 세요.
    Falls back to newline split, then hard split at max_chars.

    Returns list of non-empty text chunks.
    """
    if len(text) <= max_chars:
        return [text]

    # Split into sentences using sentence-ending punctuation (. ! ?)
    # Use findall to capture sentences including their terminator
    sentences = re.findall(r'[^.!?]*[.!?]+\s*|[^.!?]+$', text)
    # Filter out empty strings
    sentences = [s for s in sentences if s.strip()]

    # If regex produced no sentences, fall back to simple newline split
    if not sentences:
        sentences = [s for s in text.split('\n') if s.strip()]
    if not sentences:
        sentences = [text]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding this sentence would exceed limit
        if current_chunk and len(current_chunk) + len(sentence) > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = ""

        # If a single sentence exceeds max_chars, split at last newline/space
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Hard split at space boundaries
            while len(sentence) > max_chars:
                split_pos = sentence.rfind(" ", 0, max_chars)
                if split_pos == -1:
                    split_pos = sentence.rfind("\n", 0, max_chars)
                if split_pos == -1:
                    split_pos = max_chars
                chunks.append(sentence[:split_pos].strip())
                sentence = sentence[split_pos:].strip()
            if sentence:
                current_chunk = sentence
        else:
            current_chunk += sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Final filter: no empty chunks
    return [c for c in chunks if c.strip()]


def _inject_punctuation_breaks(
    text: str,
    mark_pause: float = 0.35,
    comma_pause: float = 0.2,
) -> str:
    """Inject <break /> tags after sentence-ending marks and commas.

    Typecast's Morgan voice (incidents channel) under-emphasises punctuation
    pauses, leaving sentences glued together. This pre-pass guarantees a
    minimum pause after every terminal mark and comma. The result is then
    consumed by `_convert_breaks_to_silence()` which turns `<break/>` tags
    into silence markers during post-processing — so the pause shows up in
    the final narration.mp3 without any scripter involvement.

    Rules:
        * Only injects when the punctuation is followed by whitespace. That
          condition alone already protects decimals like "3.14" because the
          dot inside a decimal is followed by a digit, not whitespace, so
          the regex never matches it. A naive `(?<!\d)` digit guard was
          tried first but it also blocked legitimate sentence-final endings
          such as "2025년 1월. 그 이후…", so we rely on the whitespace rule
          exclusively.
        * Idempotent — after one pass the punctuation is immediately
          followed by `<break ... />` (no whitespace in between), so a
          second pass cannot match and re-inject.

    Args:
        text: Raw narration text.
        mark_pause: Seconds of silence after .!?。！？ (default 0.35).
        comma_pause: Seconds of silence after ,、，(default 0.2).

    Returns:
        Text with `<break time="Xs"/>` tags injected after punctuation.

    Example:
        >>> _inject_punctuation_breaks("겁니다. 오늘의 기록, 기타큐슈")
        '겁니다.<break time="0.35s"/> 오늘의 기록,<break time="0.2s"/> 기타큐슈'
    """
    # Sentence-ending punctuation followed by whitespace. No digit guard:
    # the trailing-whitespace requirement is enough to skip decimals.
    text = re.sub(
        r'([.!?。！？])(\s+)',
        lambda m: f'{m.group(1)}<break time="{mark_pause}s"/>{m.group(2)}',
        text,
    )
    # Comma pause — same whitespace requirement.
    text = re.sub(
        r'([,，、])(\s+)',
        lambda m: f'{m.group(1)}<break time="{comma_pause}s"/>{m.group(2)}',
        text,
    )
    return text


def _convert_breaks_to_silence(text: str, output_dir: str) -> tuple[str, list[tuple[int, float]]]:
    """Convert <break /> tags and "..." to silence markers for post-processing.

    Replaces <break time="1.0s"/> or "..." with a placeholder marker.
    Returns (cleaned_text, list of (char_position, silence_seconds)).

    For "..." patterns: 0.5s silence.
    For <break time="Xs"/>: X seconds silence.
    For <break />: 1.0s silence (default).
    """
    silence_markers: list[tuple[int, float]] = []
    marker = "\u200B"  # Zero-width space as placeholder

    # Process <break time="Xs"/> tags first
    def _replace_break(m):
        time_str = m.group(1) if m.group(1) else "1.0"
        seconds = float(time_str.rstrip("s"))
        silence_markers.append((m.start(), min(seconds, 3.0)))
        return marker
    text = re.sub(r'<break\s*(?:time=["\']?(\d+\.?\d*s?)["\']?)?\s*/?\s*>', _replace_break, text)

    # Process "..." → 0.5s silence (only standalone, not inside words)
    def _replace_ellipsis(m):
        silence_markers.append((m.start(), 0.5))
        return marker
    text = re.sub(r'(?<=[가-힣a-zA-Z])\.\.\.\s*', _replace_ellipsis, text)

    # Clean up markers for TTS (Typecast ignores zero-width spaces)
    return text, silence_markers


def generate_typecast(text: str, voice_config: dict, output_path: str,
                      emotion: str = "normal", emotion_intensity: float = 1.0,
                      previous_text: str = None, next_text: str = None,
                      style_tag: str = None) -> dict:
    """Generate TTS via Typecast with 2000-char chunking and emotion pipeline.

    Args:
        text: Korean narration text (may exceed 2000 chars).
        voice_config: Dict with voice_name, model, language, audio_format,
                      audio_tempo, volume keys from voice-presets.json typecast block.
        output_path: Path to write final MP3 file.
        emotion: Emotion preset name (normal/happy/sad/angry/whisper/toneup/tonedown).
        emotion_intensity: Emotion strength 0.0-2.0 (default 1.0).
        previous_text: Previous sentence context for smart inflection (optional).
        next_text: Next sentence context for smart inflection (optional).
        style_tag: SSFM 3.0 natural language style prompt (e.g. "(속삭이듯)", "(담담하게)").
                   Only effective with ssfm-v30+ models. Ignored on ssfm-v21.

    Returns:
        Dict with provider, output_path keys.

    Raises:
        TTSProviderError: On API errors (401, 402, 429, 500).
        ValueError: If TYPECAST_API_KEY env var is not set.
    """
    api_key = os.environ.get("TYPECAST_API_KEY")
    if not api_key:
        raise ValueError("TYPECAST_API_KEY environment variable not set")

    # Remove "아따" prefix per user feedback (Changsu Settings)
    text = re.sub(r'^아따[,\s]*', '', text)

    # Optional automatic punctuation pause injection. Voice presets that set
    # "auto_punctuation_pause": true (e.g. Morgan on the incidents channel)
    # get extra <break /> tags injected after marks/commas before the break
    # converter runs. This compensates for Typecast voices that under-emphasise
    # punctuation pauses and glue sentences together.
    if voice_config.get("auto_punctuation_pause", False):
        mark_pause = float(voice_config.get("pause_mark_seconds", 0.35))
        comma_pause = float(voice_config.get("pause_comma_seconds", 0.2))
        text = _inject_punctuation_breaks(
            text,
            mark_pause=mark_pause,
            comma_pause=comma_pause,
        )

    # Process <break /> tags and "..." → silence markers + zero-width
    # space placeholders. The placeholders survive into ``text`` so the
    # silence-split pass below can locate them and split the text into
    # sub-segments separated by silent gaps.
    output_dir = str(Path(output_path).parent)
    text, silence_markers = _convert_breaks_to_silence(text, output_dir)

    # Determine if SSFM 3.0+ is available for style_tag support
    model = voice_config.get("model", "ssfm-v21")
    use_style_prompt = (style_tag and "v3" in model)

    client = Typecast(api_key=api_key)

    # Resolve voice_name to voice_id (cached)
    voice_name = voice_config["voice_name"]
    if voice_name not in _typecast_voice_cache:
        voices = client.voices_v2()
        voice_map = {v.voice_name: v.voice_id for v in voices}
        if voice_name not in voice_map:
            raise TTSProviderError(
                provider="typecast",
                message=f"Voice '{voice_name}' not found in Typecast catalog",
            )
        _typecast_voice_cache[voice_name] = voice_map[voice_name]

    voice_id = _typecast_voice_cache[voice_name]

    # ------------------------------------------------------------------
    # SILENCE-SPLIT PATH (FAIL-PROD-* root fix, session 40)
    # ------------------------------------------------------------------
    # If the text contains injected silence markers (zero-width space at
    # the position of every original <break/> tag or "..." pattern), we
    # split the text on those markers, generate one Typecast call per
    # sub-segment, and concatenate the resulting audio with explicit
    # AudioSegment silences in between.
    #
    # Why this exists: previously the silence_markers list was computed
    # but **never used**. Typecast does not honour zero-width spaces or
    # SSML <break/> tags, so the audio length was unaffected by pause
    # injection — Morgan + tempo 0.88 + supposed pauses still produced
    # ~76 s for a 533-char script that should have been ~135 s.
    ZWSP = "\u200b"
    if ZWSP in text and silence_markers:
        # Sub-segment path. Each segment becomes its own TTS call so we
        # can stitch silence in between with millisecond precision.
        segments = text.split(ZWSP)
        # silence_markers preserves insertion order, so the i-th gap
        # corresponds to silence_markers[i][1] seconds.
        silence_durations = [dur for _, dur in silence_markers]
        # When the text starts/ends with a marker we may end up with
        # an empty leading or trailing segment; filter and re-align.
        if len(segments) != len(silence_durations) + 1:
            # Defensive: drop the silence path and fall back to single-pass
            # so we never crash. The fallback warning makes the bug visible.
            print(
                f"[WARN] silence-split mismatch: {len(segments)} segments vs "
                f"{len(silence_durations)} gaps; falling back to single pass",
                file=sys.stderr,
            )
        else:
            from pydub import AudioSegment

            result_audio: AudioSegment | None = None
            sub_chunk_files: list[str] = []
            try:
                for i, segment in enumerate(segments):
                    seg = segment.strip()
                    if seg:
                        # Each segment can itself be longer than the 2000-char
                        # Typecast limit, so we still have to chunk it.
                        sub_chunks = chunk_text_for_typecast(seg, 2000)
                        for j, sub in enumerate(sub_chunks):
                            sub_styled = f"{style_tag} {sub}" if use_style_prompt else sub
                            sub_prompt = PresetPrompt(
                                emotion_type="preset",
                                emotion_preset=emotion,
                                emotion_intensity=emotion_intensity,
                            )
                            try:
                                response = client.text_to_speech(TTSRequest(
                                    text=sub_styled,
                                    model=model,
                                    voice_id=voice_id,
                                    language=voice_config.get("language", "kor"),
                                    prompt=sub_prompt,
                                    output=Output(
                                        volume=voice_config.get("volume", 100),
                                        audio_tempo=voice_config.get("audio_tempo", 1.1),
                                        audio_format=voice_config.get("audio_format", "mp3"),
                                    ),
                                ))
                            except Exception as e:
                                status_code = getattr(e, "status_code", None)
                                if status_code is None and hasattr(e, "response"):
                                    status_code = getattr(e.response, "status_code", None)
                                raise TTSProviderError(
                                    provider="typecast",
                                    status_code=status_code,
                                    message=str(e),
                                )
                            sub_path = os.path.join(
                                output_dir,
                                f"_typecast_seg_{i:03d}_{j:03d}.mp3",
                            )
                            with open(sub_path, "wb") as fh:
                                fh.write(response.audio_data)
                            sub_chunk_files.append(sub_path)
                            seg_audio = AudioSegment.from_mp3(sub_path)
                            result_audio = seg_audio if result_audio is None else result_audio + seg_audio

                    # Append silence after this segment, except for the
                    # final position (no silence after the last segment).
                    if i < len(silence_durations):
                        gap_ms = int(round(silence_durations[i] * 1000))
                        silence_seg = AudioSegment.silent(duration=gap_ms)
                        result_audio = silence_seg if result_audio is None else result_audio + silence_seg

                if result_audio is None:
                    # Defensive: empty narration → empty file (won't happen
                    # in practice because validation upstream rejects empty
                    # script.json).
                    open(output_path, "wb").close()
                else:
                    result_audio.export(output_path, format="mp3")

                try:
                    from ui.components.api_usage_tracker import record_api_call
                    record_api_call("typecast", "tts_synthesize", cost_usd=0.10)
                except Exception:
                    pass
                return {"provider": "typecast", "output_path": output_path}
            finally:
                for sf in sub_chunk_files:
                    if os.path.exists(sf):
                        os.remove(sf)

    # ------------------------------------------------------------------
    # SINGLE-PASS PATH (no silence markers — original behaviour)
    # ------------------------------------------------------------------
    # Chunk text for 2000-char limit
    chunks = chunk_text_for_typecast(text, 2000)

    # Generate audio for each chunk
    chunk_files = []
    output_dir = str(Path(output_path).parent)

    try:
        for i, chunk in enumerate(chunks):
            # Build context for natural cross-sentence inflection
            chunk_prev = previous_text
            chunk_next = next_text
            if len(chunks) > 1:
                if i > 0:
                    chunk_prev = chunks[i - 1][-100:]
                if i < len(chunks) - 1:
                    chunk_next = chunks[i + 1][:100]

            try:
                # Build prompt: SSFM 3.0 style_tag or preset emotion
                if use_style_prompt:
                    # SSFM 3.0: natural language style prompt
                    tts_prompt = PresetPrompt(
                        emotion_type="preset",
                        emotion_preset=emotion,
                        emotion_intensity=emotion_intensity,
                    )
                    # Prepend style_tag to text for SSFM 3.0 natural language understanding
                    styled_chunk = f"{style_tag} {chunk}" if style_tag else chunk
                else:
                    tts_prompt = PresetPrompt(
                        emotion_type="preset",
                        emotion_preset=emotion,
                        emotion_intensity=emotion_intensity,
                    )
                    styled_chunk = chunk

                response = client.text_to_speech(TTSRequest(
                    text=styled_chunk,
                    model=model,
                    voice_id=voice_id,
                    language=voice_config.get("language", "kor"),
                    prompt=tts_prompt,
                    output=Output(
                        volume=voice_config.get("volume", 100),
                        audio_tempo=voice_config.get("audio_tempo", 1.1),
                        audio_format=voice_config.get("audio_format", "mp3"),
                    ),
                ))
            except Exception as e:
                # Wrap API errors in TTSProviderError
                status_code = getattr(e, 'status_code', None)
                if status_code is None and hasattr(e, 'response'):
                    status_code = getattr(e.response, 'status_code', None)
                raise TTSProviderError(
                    provider="typecast",
                    status_code=status_code,
                    message=str(e),
                )

            if len(chunks) == 1:
                # Single chunk: write directly to output
                with open(output_path, "wb") as f:
                    f.write(response.audio_data)
            else:
                # Multi-chunk: write to temp file
                chunk_path = os.path.join(output_dir, f"_typecast_chunk_{i:03d}.mp3")
                with open(chunk_path, "wb") as f:
                    f.write(response.audio_data)
                chunk_files.append(chunk_path)

        # Concatenate multi-chunk output (no gap -- Typecast handles pacing)
        if len(chunks) > 1:
            concat_with_silence(chunk_files, output_path, gap_seconds=0.0)

    finally:
        # Clean up temp chunk files
        for chunk_file in chunk_files:
            if os.path.exists(chunk_file):
                os.remove(chunk_file)

    try:
        from ui.components.api_usage_tracker import record_api_call
        record_api_call('typecast', 'tts_synthesize', cost_usd=0.10)
    except Exception:
        pass
    return {"provider": "typecast", "output_path": output_path}


def generate_fish_audio(text: str, voice_config: dict, output_path: str,
                        emotion: str = None) -> dict:
    """Generate TTS via Fish Audio S1.

    Args:
        text: Pronunciation-converted narration text.
        voice_config: Dict with reference_id, format, mp3_bitrate, speed keys.
        output_path: Path to write MP3 file.
        emotion: Optional emotion tag (e.g., "excited", "serious").
            Prepended as (emotion) at text start per Fish Audio docs.

    Returns:
        Dict with provider, output_path keys.

    Raises:
        TTSProviderError: On HTTP 401, 402, 429, 500, 503 errors.
    """
    api_key = os.environ.get("FISH_AUDIO_API_KEY")
    if not api_key:
        raise ValueError("FISH_AUDIO_API_KEY environment variable not set")

    # Prepend emotion tag if specified (per D-05 research result)
    if emotion:
        text = f"({emotion}) {text}"

    request_data = {
        "text": text,
        "reference_id": voice_config["reference_id"],
        "format": voice_config.get("format", "mp3"),
        "mp3_bitrate": voice_config.get("mp3_bitrate", 128),
    }
    if "speed" in voice_config:
        request_data["speed"] = voice_config["speed"]

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            "https://api.fish.audio/v1/tts",
            content=ormsgpack.packb(request_data),
            headers={
                "authorization": f"Bearer {api_key}",
                "content-type": "application/msgpack",
                "model": "s1",
            },
        )

    if response.status_code >= 400:
        raise TTSProviderError(
            provider="fish-audio",
            status_code=response.status_code,
            message=response.text,
        )

    with open(output_path, "wb") as f:
        f.write(response.content)

    return {"provider": "fish-audio", "output_path": output_path}


def generate_elevenlabs(text: str, voice_config: dict, output_path: str,
                        voice_settings: dict = None, previous_request_ids: list = None) -> dict:
    """Generate TTS via ElevenLabs Flash v2.5.

    Args:
        text: Pronunciation-converted narration text.
        voice_config: Dict with voice_id, model_id, language_code, output_format.
        output_path: Path to write MP3 file.
        voice_settings: Optional dict with stability, similarity_boost, style params.
        previous_request_ids: Optional list of previous request IDs for prosody
            continuity across chapters (max 3 per ElevenLabs API).

    Returns:
        Dict with provider, output_path, and optionally request_id keys.

    Raises:
        ElevenLabsCreditError: On HTTP 401/402/429 with credit/quota-related error codes.
        Exception: On other API errors.
    """
    import os
    from elevenlabs.client import ElevenLabs
    from elevenlabs.core import ApiError

    api_key = os.environ.get("ELEVEN_API_KEY")
    if not api_key:
        raise ValueError("ELEVEN_API_KEY environment variable not set")

    client = ElevenLabs(api_key=api_key)

    try:
        kwargs = {
            "text": text,
            "voice_id": voice_config["voice_id"],
            "model_id": voice_config["model_id"],           # "eleven_flash_v2_5"
            "language_code": voice_config["language_code"],   # "ko" (VOIC-05)
            "output_format": voice_config["output_format"],   # "mp3_44100_128"
        }
        if voice_settings:
            kwargs["voice_settings"] = voice_settings
        if previous_request_ids:
            kwargs["previous_request_ids"] = previous_request_ids
        audio_iterator = client.text_to_speech.convert(**kwargs)

        request_id = None
        with open(output_path, "wb") as f:
            for chunk in audio_iterator:
                if isinstance(chunk, bytes):
                    f.write(chunk)

        # Try to capture request_id from the response headers if available
        if hasattr(audio_iterator, 'request_id'):
            request_id = audio_iterator.request_id

        result = {"provider": "elevenlabs", "output_path": output_path}
        if request_id:
            result["request_id"] = request_id
        return result

    except ApiError as e:
        status = getattr(e, 'status_code', None)
        body = str(getattr(e, 'body', ''))
        # D-09: Error-based switching. Catch 401, 402, and 429 for credit/quota issues.
        # 401 = auth failure (bad/expired key), 402 = payment required (no credits),
        # 429 = rate limit or quota exceeded (per D-09: "429 등").
        # All three trigger permanent EdgeTTS fallback for this run.
        # Also check body for "insufficient_credits" or "quota_exceeded" strings.
        if status in (401, 402, 429) or "insufficient_credits" in body or "quota_exceeded" in body:
            raise TTSProviderError(
                provider="elevenlabs",
                status_code=status,
                message=body,
            )
        raise


def generate_voicevox(
    text: str,
    voice_config: dict,
    output_path: str,
    emotion: str = "normal",
) -> dict:
    """Generate TTS via VOICEVOX Nemo (일본어 전용, 무료 로컬 REST API).

    2단계 API 호출:
    1. POST /audio_query — 텍스트 → 음성 쿼리 생성
    2. POST /synthesis — 음성 쿼리 → WAV → MP3 변환

    Args:
        text: 일본어 나레이션 텍스트.
        voice_config: Dict with endpoint, tempo, engine keys from channels.yaml.
        output_path: 출력 MP3 파일 경로.
        emotion: 감정 키 (normal/tonedown/sad/whisper/toneup/angry/happy).

    Returns:
        Dict with provider, output_path, duration_seconds, character_count keys.

    Raises:
        TTSProviderError: VOICEVOX API 오류 시.
    """
    endpoint = voice_config.get("endpoint", VOICEVOX_DEFAULT_ENDPOINT)
    # speaker_id: VOICEVOX Nemo 보이스 ID — 0이 기본 (테스트 후 변경)
    speaker_id = voice_config.get("speaker_id", 0)
    base_tempo = voice_config.get("tempo", 1.0)

    # 감정 파라미터 조회
    emo_params = VOICEVOX_EMOTION_MAP.get(emotion, VOICEVOX_EMOTION_MAP["normal"])

    with httpx.Client(timeout=60.0) as client:
        # Step 1: audio_query
        try:
            query_resp = client.post(
                f"{endpoint}/audio_query",
                params={"text": text, "speaker": speaker_id},
            )
            query_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TTSProviderError(
                provider="voicevox",
                status_code=e.response.status_code,
                message=f"audio_query failed: {e.response.text}",
            )
        except httpx.ConnectError:
            raise TTSProviderError(
                provider="voicevox",
                message=f"VOICEVOX server not reachable at {endpoint}",
            )

        audio_query = query_resp.json()

        # 파라미터 조정 (감정 + 기본 tempo 적용)
        audio_query["speedScale"] = emo_params["speed"] * base_tempo
        audio_query["pitchScale"] = emo_params["pitch"]
        audio_query["intonationScale"] = emo_params["intonation"]
        audio_query["volumeScale"] = emo_params["volume"]

        # Step 2: synthesis
        try:
            synth_resp = client.post(
                f"{endpoint}/synthesis",
                params={"speaker": speaker_id},
                json=audio_query,
            )
            synth_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TTSProviderError(
                provider="voicevox",
                status_code=e.response.status_code,
                message=f"synthesis failed: {e.response.text}",
            )

    # WAV 저장 → MP3 변환
    wav_path = output_path.replace(".mp3", ".wav")
    Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
    Path(wav_path).write_bytes(synth_resp.content)

    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-codec:a", "libmp3lame", "-b:a", "192k",
            output_path,
        ], check=True, capture_output=True)
    finally:
        # WAV 임시파일 삭제
        if os.path.exists(wav_path):
            os.remove(wav_path)

    # 오디오 길이 계산
    try:
        duration = get_audio_duration(output_path)
    except Exception:
        duration = None

    return {
        "provider": "voicevox",
        "output_path": output_path,
        "duration_seconds": round(duration, 2) if duration else None,
        "character_count": len(text),
        "speaker_id": speaker_id,
        "emotion": emotion,
    }


def generate_edge_tts(text: str, voice: str, output_path: str) -> dict:
    """Generate TTS via EdgeTTS (free Microsoft Neural TTS).

    Args:
        text: Pronunciation-converted narration text.
        voice: EdgeTTS voice identifier (e.g., "ko-KR-InJoonNeural").
        output_path: Path to write MP3 file.

    Returns:
        Dict with provider, output_path keys.
    """
    import edge_tts

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    asyncio.run(_generate())
    return {"provider": "edge-tts", "output_path": output_path}


def get_audio_duration(file_path: str) -> float:
    """Get duration of MP3 file in seconds using pydub."""
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(file_path)
    return len(audio) / 1000.0


def main():
    parser = argparse.ArgumentParser(description="Generate Korean TTS from script.json")
    parser.add_argument("--input", required=True, help="Path to script.json")
    parser.add_argument("--output", required=True, help="Path to write narration.mp3")
    parser.add_argument("--voice-preset", default="narrator-male-01",
                        help="Voice preset name from voice-presets.json")
    parser.add_argument("--config-dir", default="config",
                        help="Path to config/ directory")
    parser.add_argument("--provider", default="auto",
                        choices=["auto", "typecast", "fish-audio", "elevenlabs", "edge-tts", "voicevox"],
                        help="TTS provider. 'auto' tries Typecast first (Tier 0), "
                             "then Fish Audio, ElevenLabs, EdgeTTS. "
                             "For Japanese: VOICEVOX (Tier 0) → ElevenLabs → EdgeTTS (default: auto)")
    parser.add_argument("--language", default="ko",
                        choices=["ko", "ja"],
                        help="Language for TTS (default: ko). 'ja' routes to VOICEVOX.")
    parser.add_argument("--channel", default=None,
                        help="Channel name from channels.yaml. Overrides TTS provider priority "
                             "based on channel voice config (e.g., documentary/object_nag use ElevenLabs primary)")
    parser.add_argument("--typecast-emotion", default=None,
                        help="Typecast emotion preset (normal/happy/sad/angry/whisper/toneup/tonedown)")
    parser.add_argument("--section-type", default=None,
                        help="Script section type for emotion mapping (hook/body/climax/conclusion)")
    parser.add_argument("--voice-id", default=None,
                        help="ElevenLabs voice_id (inline override, bypasses preset lookup)")
    parser.add_argument("--fish-reference-id", default=None,
                        help="Fish Audio reference_id (inline override, bypasses preset lookup)")
    parser.add_argument("--fish-emotion", default=None,
                        help="Fish Audio emotion tag (e.g., excited, serious, relaxed)")
    parser.add_argument("--stability", type=float, default=None,
                        help="ElevenLabs stability param (0.0-1.0)")
    parser.add_argument("--similarity-boost", type=float, default=None,
                        help="ElevenLabs similarity_boost param (0.0-1.0)")
    parser.add_argument("--style", type=float, default=None,
                        help="ElevenLabs style param (0.0-1.0)")
    parser.add_argument("--edge-voice", default=None,
                        help="EdgeTTS voice name (inline override)")
    parser.add_argument("--pipeline", default="shorts", choices=["shorts", "video"],
                        help="Pipeline type: shorts (default) or video (chapter-based splitting)")
    parser.add_argument("--style-tag", default=None,
                        help="SSFM 3.0 natural language style tag (e.g. '(속삭이듯)', '(담담하게)')")
    parser.add_argument("--section-emotions", action="store_true",
                        help="Generate TTS per-section with individual emotions from script.json")
    args = parser.parse_args()

    # Validate input
    if not Path(args.input).exists():
        print(json.dumps({"error": f"Input file not found: {args.input}"}),
              file=sys.stderr)
        sys.exit(1)

    # Load configs
    config_dir = Path(args.config_dir)

    # Channel-based provider override (per channels.yaml voice.provider)
    channel_provider_override = None
    if args.channel:
        channels_path = config_dir / "channels.yaml"
        if channels_path.exists():
            import yaml
            with open(channels_path, "r", encoding="utf-8") as f:
                channels_data = yaml.safe_load(f)
            ch_config = channels_data.get("channels", {}).get(args.channel, {})
            ch_voice = ch_config.get("voice", {})
            if ch_voice.get("provider"):
                channel_provider_override = ch_voice["provider"]
                # Also override voice_preset if channel specifies one
                if ch_config.get("voice_preset") and args.voice_preset == "narrator-male-01":
                    args.voice_preset = ch_config["voice_preset"]
                # Override language if channel specifies one
                ch_lang = ch_config.get("language", "ko")
                if ch_lang == "en":
                    args.language = "en"

    # Resolve voice config: inline params take priority over preset lookup
    if args.voice_id is not None or args.fish_reference_id is not None:
        # Inline mode: build config from CLI flags (channel-specific flow)
        voice_config = {
            "voice_id": args.voice_id or "",
            "model_id": "eleven_flash_v2_5",
            "language_code": "ko",
            "output_format": "mp3_44100_128",
        }
        voice_settings = {}
        if args.stability is not None:
            voice_settings["stability"] = args.stability
        if args.similarity_boost is not None:
            voice_settings["similarity_boost"] = args.similarity_boost
        if args.style is not None:
            voice_settings["style"] = args.style
        edge_voice = args.edge_voice or "ko-KR-InJoonNeural"
        # Fish Audio inline config
        fish_config = {
            "reference_id": args.fish_reference_id or "",
            "format": "mp3",
            "mp3_bitrate": 128,
            "speed": 1.0,
        }
        # Typecast inline config (minimal defaults)
        typecast_config = {
            "voice_name": "Changsu",
            "model": "ssfm-v21",
            "language": "kor",
            "audio_format": "mp3",
            "audio_tempo": 1.1,
            "volume": 100,
            "default_emotion": "normal",
            "emotion_intensity": 1.0,
            "emotion_map": {}
        }
    else:
        # Preset mode: existing lookup logic (unchanged)
        with open(config_dir / "voice-presets.json", "r", encoding="utf-8") as f:
            presets = json.load(f)

        preset = presets["presets"].get(args.voice_preset)
        if not preset:
            print(json.dumps({"error": f"Voice preset not found: {args.voice_preset}"}),
                  file=sys.stderr)
            sys.exit(1)
        voice_config = preset.get("elevenlabs", {})
        voice_settings = {}
        edge_voice = preset.get("edge_tts", {}).get("voice", "ko-KR-InJoonNeural")
        # Fish Audio preset config (D-06)
        fish_config = preset.get("fish_audio", {})
        # Typecast preset config (from voice-presets.json typecast block)
        typecast_config = preset.get("typecast", {})

    # Resolve Fish Audio emotion tag
    fish_emotion = args.fish_emotion

    # Resolve Typecast emotion from section type or CLI flag
    typecast_emotion = args.typecast_emotion  # CLI override takes priority
    if typecast_emotion is None and args.section_type:
        emotion_map = typecast_config.get("emotion_map", {})
        typecast_emotion = emotion_map.get(args.section_type, "normal")
    if typecast_emotion is None:
        typecast_emotion = typecast_config.get("default_emotion", "normal")

    # Load pronunciation table (D-04: original script.json untouched)
    pronunciation_table = load_pronunciation_table(str(config_dir / "pronunciation-table.json"))

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Determine provider choice
    provider_choice = args.provider

    # === Video pipeline: chapter-based TTS splitting (GEN-04, D-10) ===
    if args.pipeline == "video":
        chapters = extract_chapters(args.input)
        if not chapters:
            print(json.dumps({"error": "No chapters found in script.json for video pipeline"}), file=sys.stderr)
            sys.exit(1)

        chapter_files = []
        chapter_request_ids = []
        output_dir = str(Path(args.output).parent)
        total_chapters = len(chapters)

        for i, chapter in enumerate(chapters):
            chapter_path = os.path.join(output_dir, f"chapter_{i:02d}.mp3")
            text = chapter["narration"]
            text = apply_pronunciation(text, pronunciation_table)  # Apply pronunciation
            chapter_provider = None

            # Resolve per-chapter emotion from section type
            chapter_emotion = typecast_emotion
            if chapter.get("type"):
                chapter_emotion = typecast_config.get("emotion_map", {}).get(
                    chapter["type"], typecast_emotion
                )

            # Tier 0: Typecast (primary for configured channels, per TTS-01/TTS-03)
            if provider_choice in ("auto", "typecast") and chapter_provider is None:
                try:
                    voice_name = typecast_config.get("voice_name", "")
                    if not voice_name:
                        raise ValueError("Typecast voice_name not configured in preset")
                    result = generate_typecast(
                        text,
                        typecast_config,
                        chapter_path,
                        emotion=chapter_emotion,
                        emotion_intensity=typecast_config.get("emotion_intensity", 1.0),
                    )
                    chapter_provider = "typecast"
                    chapter_files.append(chapter_path)
                    continue
                except (TTSProviderError, ValueError) as e:
                    if provider_choice == "typecast":
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                        sys.exit(2)
                    print(f"[FALLBACK] Typecast unavailable ({e}), trying Fish Audio",
                          file=sys.stderr)

            # Tier 1: Fish Audio S1 (per D-01: primary provider)
            if provider_choice in ("auto", "fish-audio") and chapter_provider is None:
                try:
                    ref_id = fish_config.get("reference_id", "")
                    if not ref_id or ref_id.startswith("PENDING"):
                        raise ValueError("Fish Audio reference_id not configured")
                    result = generate_fish_audio(
                        text, fish_config, chapter_path,
                        emotion=fish_emotion,
                    )
                    chapter_provider = "fish-audio"
                    chapter_files.append(chapter_path)
                    continue
                except (TTSProviderError, ValueError) as e:
                    if provider_choice == "fish-audio":
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                        sys.exit(2)
                    print(f"[FALLBACK] Fish Audio unavailable ({e}), trying ElevenLabs",
                          file=sys.stderr)

            # Tier 2: ElevenLabs (existing behavior)
            if provider_choice in ("auto", "elevenlabs") and chapter_provider is None:
                try:
                    vid = voice_config.get("voice_id", "")
                    if not vid or vid.startswith("PLACEHOLDER"):
                        raise TTSProviderError(provider="elevenlabs", message="voice_id not configured")
                    prev_ids = chapter_request_ids[-3:]  # Max 3 per ElevenLabs API
                    result = generate_elevenlabs(
                        text, voice_config, chapter_path,
                        voice_settings=voice_settings if voice_settings else None,
                        previous_request_ids=prev_ids if prev_ids else None,
                    )
                    if result.get("request_id"):
                        chapter_request_ids.append(result["request_id"])
                    chapter_provider = "elevenlabs"
                    chapter_files.append(chapter_path)
                    time.sleep(1.5)  # Rate limit spacing between chapter requests
                    continue
                except (TTSProviderError, ValueError) as e:
                    if provider_choice == "elevenlabs":
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                        sys.exit(2)
                    print(f"[FALLBACK] ElevenLabs unavailable ({e}), switching to EdgeTTS",
                          file=sys.stderr)

            # Tier 3: EdgeTTS (last resort)
            if chapter_provider is None:
                generate_edge_tts(text, edge_voice, chapter_path)
                chapter_provider = "edge-tts"
                chapter_files.append(chapter_path)

        # Concat chapters with silence gaps
        concat_with_silence(chapter_files, args.output, gap_seconds=0.3)

        # Calculate total duration
        total_duration = get_audio_duration(args.output)
        total_chars = sum(len(ch["narration"]) for ch in chapters)

        # Determine actual provider used
        # For video pipeline, use provider_choice if explicit, otherwise detect from fallback state
        if provider_choice in ("typecast", "fish-audio", "elevenlabs", "edge-tts"):
            actual_provider = provider_choice
        else:
            # Auto mode: check what was last used based on chapter_request_ids
            elevenlabs_chapters = len(chapter_request_ids)
            if elevenlabs_chapters == total_chapters:
                actual_provider = "elevenlabs"
            elif elevenlabs_chapters == 0:
                actual_provider = "auto"  # Could be fish-audio or edge-tts
            else:
                actual_provider = "mixed"

        video_result = {
            "provider": actual_provider,
            "output_path": args.output,
            "duration_seconds": round(total_duration, 2),
            "character_count": total_chars,
            "chapters": len(chapters),
            "chapter_files": [os.path.basename(f) for f in chapter_files],
        }
        if fish_emotion and actual_provider in ("fish-audio", "auto"):
            video_result["emotion"] = fish_emotion
        if typecast_emotion and actual_provider == "typecast":
            video_result["emotion"] = typecast_emotion
        print(json.dumps(video_result, ensure_ascii=False))
        sys.exit(0)

    # === Shorts pipeline: 4-tier fallback (Typecast -> Fish Audio -> ElevenLabs -> EdgeTTS) ===

    # === Japanese pipeline: VOICEVOX → ElevenLabs → EdgeTTS ===
    if args.language == "ja" or provider_choice == "voicevox":
        narration_text, char_count = extract_narration(args.input)

        # VOICEVOX 감정: section_type → emotion_map 매핑
        voicevox_emotion = typecast_emotion  # reuse CLI emotion flag
        if voicevox_emotion not in VOICEVOX_EMOTION_MAP:
            voicevox_emotion = "normal"

        # Section-emotions mode for Japanese
        if args.section_emotions:
            sections = extract_sections_with_emotions(args.input)
            if sections:
                section_files = []
                output_dir = str(Path(args.output).parent)
                ja_emotion_map = {
                    "hook": "normal", "body": "tonedown",
                    "climax": "whisper", "cta": "sad",
                }
                total_chars = 0
                for i, sec in enumerate(sections):
                    sec_path = os.path.join(output_dir, f"_voicevox_sec_{i:02d}.mp3")
                    sec_emotion = sec.get("emotion") or ja_emotion_map.get(sec["type"], "normal")
                    total_chars += len(sec["narration"])
                    try:
                        # Build voice config from channels.yaml voice block
                        vvox_config = {
                            "endpoint": typecast_config.get("endpoint", VOICEVOX_DEFAULT_ENDPOINT),
                            "speaker_id": typecast_config.get("speaker_id", 0),
                            "tempo": typecast_config.get("audio_tempo", 1.0),
                        }
                        generate_voicevox(sec["narration"], vvox_config, sec_path, emotion=sec_emotion)
                        section_files.append(sec_path)
                    except (TTSProviderError, ValueError) as e:
                        print(f"[VOICEVOX-SECTION] Section {i} failed ({e}), falling back", file=sys.stderr)
                        for sf in section_files:
                            if os.path.exists(sf):
                                os.remove(sf)
                        section_files = []
                        break

                if section_files:
                    concat_with_silence(section_files, args.output, gap_seconds=0.15)
                    for sf in section_files:
                        if os.path.exists(sf):
                            os.remove(sf)
                    duration = get_audio_duration(args.output)
                    print(json.dumps({
                        "provider": "voicevox", "output_path": args.output,
                        "duration_seconds": round(duration, 2) if duration else None,
                        "character_count": total_chars,
                        "mode": "section_emotions", "language": "ja",
                    }, ensure_ascii=False))
                    sys.exit(0)

        # Single-pass VOICEVOX
        provider_used = None
        start_time = time.time()

        # Tier 0: VOICEVOX
        if provider_used is None and provider_choice in ("auto", "voicevox"):
            try:
                vvox_config = {
                    "endpoint": typecast_config.get("endpoint", VOICEVOX_DEFAULT_ENDPOINT),
                    "speaker_id": typecast_config.get("speaker_id", 0),
                    "tempo": typecast_config.get("audio_tempo", 1.0),
                }
                generate_voicevox(narration_text, vvox_config, args.output, emotion=voicevox_emotion)
                provider_used = "voicevox"
            except (TTSProviderError, ValueError) as e:
                if provider_choice == "voicevox":
                    print(json.dumps({"error": str(e)}), file=sys.stderr)
                    sys.exit(2)
                print(f"[FALLBACK] VOICEVOX unavailable ({e}), trying ElevenLabs", file=sys.stderr)

        # Tier 1: ElevenLabs (일본어)
        if provider_used is None and provider_choice in ("auto", "elevenlabs"):
            try:
                vid = voice_config.get("voice_id", "")
                if not vid or vid.startswith("PLACEHOLDER"):
                    raise TTSProviderError(provider="elevenlabs", message="voice_id not configured")
                generate_elevenlabs(narration_text, voice_config, args.output,
                                     voice_settings=voice_settings if voice_settings else None)
                provider_used = "elevenlabs"
            except (TTSProviderError, ValueError) as e:
                print(f"[FALLBACK] ElevenLabs unavailable ({e}), switching to EdgeTTS", file=sys.stderr)

        # Tier 2: EdgeTTS (일본어 최후 수단)
        if provider_used is None:
            ja_edge_voice = "ja-JP-NanamiNeural"  # Microsoft 일본어 여성 보이스
            generate_edge_tts(narration_text, ja_edge_voice, args.output)
            provider_used = "edge-tts"

        elapsed = time.time() - start_time
        try:
            duration = get_audio_duration(args.output)
        except Exception:
            duration = None

        print(json.dumps({
            "provider": provider_used, "output_path": args.output,
            "duration_seconds": duration, "character_count": char_count,
            "language": "ja", "generation_time_seconds": round(elapsed, 2),
        }, ensure_ascii=False))
        sys.exit(0)

    # --- Section-emotions mode: per-section TTS with individual emotions ---
    if args.section_emotions and args.provider in ("auto", "typecast"):
        sections = extract_sections_with_emotions(args.input)
        if sections:
            section_files = []
            output_dir = str(Path(args.output).parent)
            emotion_map = typecast_config.get("emotion_map", {})
            total_chars = 0

            for i, sec in enumerate(sections):
                sec_path = os.path.join(output_dir, f"_section_{i:02d}.mp3")
                sec_text = apply_pronunciation(sec["narration"], pronunciation_table)
                total_chars += len(sec["narration"])

                # Resolve emotion: section explicit > emotion_map > default
                sec_emotion = sec.get("emotion") or emotion_map.get(sec["type"], typecast_emotion)
                sec_intensity = sec.get("emotion_intensity") or typecast_config.get("emotion_intensity", 1.0)
                sec_style = sec.get("style_tag") or args.style_tag

                try:
                    generate_typecast(
                        sec_text,
                        typecast_config,
                        sec_path,
                        emotion=sec_emotion,
                        emotion_intensity=sec_intensity,
                        style_tag=sec_style,
                    )
                    section_files.append(sec_path)
                except (TTSProviderError, ValueError) as e:
                    print(f"[SECTION-EMOTIONS] Section {i} failed ({e}), falling back to single-pass", file=sys.stderr)
                    # Clean up partial files and fall through to single-pass mode
                    for sf in section_files:
                        if os.path.exists(sf):
                            os.remove(sf)
                    section_files = []
                    break

            if section_files:
                # Concatenate section audio files with small silence gap
                concat_with_silence(section_files, args.output, gap_seconds=0.15)

                # Clean up temp section files
                for sf in section_files:
                    if os.path.exists(sf):
                        os.remove(sf)

                duration = get_audio_duration(args.output)
                section_result = {
                    "provider": "typecast",
                    "output_path": args.output,
                    "duration_seconds": round(duration, 2) if duration else None,
                    "character_count": total_chars,
                    "mode": "section_emotions",
                    "sections_generated": len(sections),
                    "pronunciation_rules_applied": len(pronunciation_table),
                }
                print(json.dumps(section_result, ensure_ascii=False))
                sys.exit(0)

    # --- Single-pass mode (fallback or non-section-emotions) ---

    # Extract narration
    narration_text, char_count = extract_narration(args.input)

    # Apply pronunciation conversion
    converted_text = apply_pronunciation(narration_text, pronunciation_table)

    # Generate TTS with 4-tier fallback logic
    provider_used = None
    start_time = time.time()

    # Tier 0: Typecast (primary for configured channels, per TTS-01/TTS-03)
    if provider_used is None and args.provider in ("auto", "typecast"):
        try:
            voice_name = typecast_config.get("voice_name", "")
            if not voice_name:
                raise ValueError("Typecast voice_name not configured in preset")
            result = generate_typecast(
                converted_text,
                typecast_config,
                args.output,
                emotion=typecast_emotion,
                emotion_intensity=typecast_config.get("emotion_intensity", 1.0),
                style_tag=args.style_tag,
            )
            provider_used = "typecast"
        except (TTSProviderError, ValueError) as e:
            if args.provider == "typecast":
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                sys.exit(2)
            print(f"[FALLBACK] Typecast unavailable ({e}), trying Fish Audio",
                  file=sys.stderr)

    # Tier 1: Fish Audio S1 (per D-01: primary provider)
    if provider_used is None and args.provider in ("auto", "fish-audio"):
        try:
            ref_id = fish_config.get("reference_id", "")
            if not ref_id or ref_id.startswith("PENDING"):
                raise ValueError("Fish Audio reference_id not configured")
            result = generate_fish_audio(
                converted_text, fish_config, args.output,
                emotion=fish_emotion,
            )
            provider_used = "fish-audio"
        except (TTSProviderError, ValueError) as e:
            if args.provider == "fish-audio":
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                sys.exit(2)
            print(f"[FALLBACK] Fish Audio unavailable ({e}), trying ElevenLabs",
                  file=sys.stderr)

    # Tier 2: ElevenLabs (existing behavior)
    if provider_used is None and args.provider in ("auto", "elevenlabs"):
        try:
            vid = voice_config.get("voice_id", "")
            if not vid or vid.startswith("PLACEHOLDER"):
                raise TTSProviderError(provider="elevenlabs", message="voice_id not configured")
            result = generate_elevenlabs(converted_text, voice_config, args.output,
                                         voice_settings=voice_settings if voice_settings else None)
            provider_used = "elevenlabs"
        except (TTSProviderError, ValueError) as e:
            if args.provider == "elevenlabs":
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                sys.exit(2)
            print(f"[FALLBACK] ElevenLabs unavailable ({e}), switching to EdgeTTS",
                  file=sys.stderr)

    # Tier 3: EdgeTTS (last resort)
    if provider_used is None:
        result = generate_edge_tts(converted_text, edge_voice, args.output)
        provider_used = "edge-tts"

    elapsed = time.time() - start_time

    # Get audio duration
    try:
        duration = get_audio_duration(args.output)
    except Exception:
        duration = None

    # Output result as JSON to stdout
    output = {
        "provider": provider_used,
        "output_path": args.output,
        "duration_seconds": duration,
        "character_count": char_count,
        "pronunciation_rules_applied": len(pronunciation_table),
        "generation_time_seconds": round(elapsed, 2),
    }
    if fish_emotion and provider_used == "fish-audio":
        output["emotion"] = fish_emotion
    if typecast_emotion and provider_used == "typecast":
        output["emotion"] = typecast_emotion
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
