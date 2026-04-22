"""Multi-speaker TTS orchestrator -- routes to Typecast per-section or ElevenLabs dialogue.

Per D-01: Hybrid TTS engine.
- narration_style "single": standard single-voice (existing tts_generate.py flow)
- narration_style "multi": Typecast per-section with different voice per speaker_id
- narration_style "dialogue": ElevenLabs Text to Dialogue API for conversational flow

Per D-02: Voice pool loaded from voice-presets.json voice_pools section.
Per D-03: Channel-specific voice pools (humor/politics/trend).
Per D-04: speaker_id field in script.json sections. Missing = default narrator.

Session 74 iter6 (2026-04-17) — incidents comma-pause:
Voice pool entries may carry passthrough Typecast fields:
  auto_punctuation_pause, pause_mark_seconds, pause_comma_seconds,
  volume, emotion_intensity, audio_tempo, model.
These are forwarded into tc_config so tts_generate._inject_punctuation_breaks
activates for Morgan + Guri (incidents channel).

Additionally: concat step honours per-section silence_after_ms from script.json
instead of a fixed 0.15s gap. Also supports per-section emotion from script.json.
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Sibling-module imports -- audio-pipeline is a hyphenated directory, not a Python
# package, so we add the parent dir to sys.path and import directly.
# This matches the established pattern in test_dialogue_generate.py.
sys.path.insert(0, str(Path(__file__).parent))
import tts_generate  # noqa: E402
import dialogue_generate  # noqa: E402

VOICE_PRESETS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "voice-presets.json"

# Keys that, if present in a voice_pool entry, are forwarded as-is into tc_config
# for generate_typecast(). Centralised so new pause-related fields propagate.
_TC_PASSTHROUGH_KEYS = (
    "auto_punctuation_pause",
    "pause_mark_seconds",
    "pause_comma_seconds",
    "volume",
    "emotion_intensity",
)


def load_voice_pool(channel: str, *, presets_path: str = None) -> dict:
    """Load voice pool for a channel from voice-presets.json.

    Args:
        channel: Channel name (humor, politics, trend).
        presets_path: Override path to voice-presets.json.

    Returns:
        Dict mapping role -> voice config dict.
        Empty dict if channel not found in voice_pools.
    """
    if presets_path is None:
        presets_path = str(VOICE_PRESETS_PATH)
    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f)
    return presets.get("voice_pools", {}).get(channel, {})


def route_tts_engine(narration_style: str, channel: str) -> str:
    """Determine which TTS engine to use based on narration style and channel.

    Args:
        narration_style: "single", "multi", or "dialogue".
        channel: Channel name.

    Returns:
        Engine identifier: "typecast" | "typecast_multi" | "elevenlabs_dialogue".
    """
    if narration_style == "dialogue":
        return "elevenlabs_dialogue"
    elif narration_style == "multi":
        return "typecast_multi"
    return "typecast"


def resolve_voice_for_section(
    section: dict, channel: str, voice_pool: dict
) -> dict:
    """Resolve voice config for a script section based on speaker_id.

    Args:
        section: Script section dict (may have speaker_id field).
        channel: Channel name.
        voice_pool: Channel voice pool from load_voice_pool().

    Returns:
        Voice config dict with at minimum voice_name or voice_id key.
        Falls back to first role in pool (narrator/anchor) if speaker_id missing.
    """
    speaker_id = section.get("speaker_id")
    if speaker_id and speaker_id in voice_pool:
        return voice_pool[speaker_id]
    # Default: first role in pool (usually "narrator" or "anchor")
    default_roles = ["narrator", "anchor"]
    for role in default_roles:
        if role in voice_pool:
            return voice_pool[role]
    # Absolute fallback: return first entry
    if voice_pool:
        return next(iter(voice_pool.values()))
    return {"voice_name": "박창수", "provider": "typecast", "emotion_default": "normal"}


def _concat_with_per_section_silence(
    section_files: list,
    silence_durations_s: list,
    output_path: str,
) -> None:
    """Concatenate section MP3 files with per-section silence gaps.

    silence_durations_s[i] is the gap AFTER section_files[i]. The last entry is
    ignored (no silence after the final chunk). Duration <= 0 means no gap.

    Re-encodes to a consistent codec because the section files may have slightly
    different sample formats after Typecast chunking; `-c copy` is unsafe here.
    """
    if len(section_files) != len(silence_durations_s):
        raise ValueError(
            f"section_files ({len(section_files)}) and silence_durations_s "
            f"({len(silence_durations_s)}) length mismatch"
        )

    output_dir = str(Path(output_path).parent)
    concat_list_path = os.path.join(output_dir, "_multi_concat_list.txt")
    generated_silences: list = []

    # Pre-generate unique silence files (dedupe on ms to avoid N files for same duration)
    silence_cache: dict = {}
    for i, dur_s in enumerate(silence_durations_s[:-1]):  # last one ignored
        if dur_s <= 0:
            continue
        key_ms = int(round(dur_s * 1000))
        if key_ms in silence_cache:
            continue
        silence_path = os.path.join(output_dir, f"_multi_silence_{key_ms}ms.mp3")
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "anullsrc=r=44100:cl=stereo", "-t", f"{dur_s:.3f}",
                "-c:a", "libmp3lame", "-q:a", "2", silence_path,
            ],
            check=True, capture_output=True,
        )
        silence_cache[key_ms] = silence_path
        generated_silences.append(silence_path)

    # Build concat list
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for i, section_file in enumerate(section_files):
            safe_path = os.path.abspath(section_file).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
            if i < len(section_files) - 1:
                dur_s = silence_durations_s[i]
                if dur_s > 0:
                    key_ms = int(round(dur_s * 1000))
                    silence_path = silence_cache[key_ms]
                    safe_silence = os.path.abspath(silence_path).replace("\\", "/")
                    f.write(f"file '{safe_silence}'\n")

    # Concat — re-encode for safety (different MP3 frame rates from chunked TTS).
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c:a", "libmp3lame", "-q:a", "2",
            output_path,
        ],
        check=True, capture_output=True,
    )

    # Cleanup
    for p in generated_silences + [concat_list_path]:
        if os.path.exists(p):
            os.remove(p)


def _get_section_duration_s(path: str) -> float:
    """Probe an MP3 file's duration in seconds via ffprobe."""
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", path,
        ],
        check=True, capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def generate_multi_speaker(
    script_data: dict,
    output_path: str,
    channel: str,
    *,
    narration_style: str = None,
    presets_path: str = None,
    timing_output: str = None,
    _tts_generate=None,
    _dialogue_generate=None,
) -> dict:
    """Orchestrate multi-speaker TTS generation.

    Args:
        script_data: Parsed script.json dict with sections array.
        output_path: Path to write final concatenated narration.mp3.
        channel: Channel name (humor, politics, trend).
        narration_style: Override narration style. If None, reads from
            script_data["narration_style"] or defaults to "single".
        presets_path: Override voice-presets.json path.
        timing_output: If provided, write section_timing.json to this path
            with per-section start/duration/silence metadata.
        _tts_generate: Injectable tts_generate module (for testing).
        _dialogue_generate: Injectable dialogue_generate module (for testing).

    Returns:
        Dict with engine, output_path, speaker_count, section_count keys.

    Raises:
        ValueError: If dialogue style but < 2 unique speaker_ids.
    """
    tts_mod = _tts_generate or tts_generate
    dlg_mod = _dialogue_generate or dialogue_generate

    if narration_style is None:
        narration_style = script_data.get("narration_style", "single")

    engine = route_tts_engine(narration_style, channel)
    voice_pool = load_voice_pool(channel, presets_path=presets_path)
    sections = script_data.get("sections", [])

    if engine == "elevenlabs_dialogue":
        # Validate: need >= 2 unique speaker_ids for dialogue
        unique_speakers = set()
        for sec in sections:
            sid = sec.get("speaker_id", "narrator")
            unique_speakers.add(sid)
        if len(unique_speakers) < 2:
            raise ValueError(
                f"Dialogue narration requires >= 2 unique speaker_ids, "
                f"got {len(unique_speakers)}: {unique_speakers}"
            )

        # Build dialogue inputs for ElevenLabs
        dialogue_sections = []
        for sec in sections:
            speaker = sec.get("speaker_id", "narrator")
            dialogue_sections.append({
                "speaker": speaker,
                "text": sec.get("narration", ""),
            })

        result = dlg_mod.generate_dialogue(
            dialogue_sections, output_path
        )
        return {
            "engine": "elevenlabs_dialogue",
            "output_path": output_path,
            "speaker_count": result.speaker_count,
            "section_count": len(sections),
        }

    elif engine == "typecast_multi":
        # Generate per-section with different Typecast voices, then concat
        section_files = []
        output_dir = str(Path(output_path).parent)
        unique_speakers = set()
        silence_durations_s: list = []

        for i, sec in enumerate(sections):
            voice_config = resolve_voice_for_section(sec, channel, voice_pool)
            section_path = os.path.join(output_dir, f"_multi_section_{i:03d}.mp3")
            text = sec.get("narration", "")
            # Section-level emotion from script.json overrides voice default.
            emotion = sec.get("emotion") or voice_config.get("emotion_default", "normal")

            # Build typecast config from voice pool entry, forwarding pause
            # fields so tts_generate._inject_punctuation_breaks activates.
            tc_config = {
                "voice_name": voice_config.get("voice_name", "박창수"),
                "model": voice_config.get("model", "ssfm-v30"),
                "language": "kor",
                "audio_format": "mp3",
                "audio_tempo": voice_config.get("audio_tempo", 1.0),
                "volume": voice_config.get("volume", 100),
                "default_emotion": emotion,
                "emotion_intensity": voice_config.get("emotion_intensity", 1.0),
                "emotion_map": {},
            }
            for k in _TC_PASSTHROUGH_KEYS:
                if k in voice_config and k not in tc_config:
                    tc_config[k] = voice_config[k]

            tts_mod.generate_typecast(
                text, tc_config, section_path, emotion=emotion
            )
            section_files.append(section_path)
            unique_speakers.add(sec.get("speaker_id", "narrator"))

            # Per-section silence gap (ms → s). Default 150ms if missing.
            # Voice pool may set silence_after_scale (e.g. 0.5) to shorten gaps
            # without editing every script.json. Applied multiplicatively.
            silence_ms = sec.get("silence_after_ms", 150)
            silence_scale = float(voice_config.get("silence_after_scale", 1.0))
            silence_durations_s.append(float(silence_ms) * silence_scale / 1000.0)

        # Concatenate all section files with per-section gaps
        _concat_with_per_section_silence(
            section_files, silence_durations_s, output_path
        )

        # Optional timing output — measure each section after TTS, accumulate.
        if timing_output:
            timings = []
            cursor = 0.0
            for i, (sec, sec_path) in enumerate(zip(sections, section_files)):
                dur = _get_section_duration_s(sec_path)
                timings.append({
                    "index": i,
                    "id": sec.get("id", f"section_{i}"),
                    "speaker_id": sec.get("speaker_id", "narrator"),
                    "emotion": sec.get("emotion") or "normal",
                    "start_s": round(cursor, 3),
                    "duration_s": round(dur, 3),
                    "silence_after_s": round(silence_durations_s[i], 3),
                    "text_len": len(sec.get("narration", "")),
                })
                cursor += dur + silence_durations_s[i]
            # The last silence is excluded from total (nothing follows),
            # so cursor overshoots by the final gap — subtract it.
            if silence_durations_s:
                cursor -= silence_durations_s[-1]
            total_duration = _get_section_duration_s(output_path)
            timing_doc = {
                "total_duration_s": round(total_duration, 3),
                "computed_end_s": round(cursor, 3),
                "section_count": len(sections),
                "sections": timings,
            }
            Path(timing_output).write_text(
                json.dumps(timing_doc, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # Cleanup temp section files
        for f in section_files:
            if os.path.exists(f):
                os.remove(f)

        return {
            "engine": "typecast_multi",
            "output_path": output_path,
            "speaker_count": len(unique_speakers),
            "section_count": len(sections),
        }

    else:
        # single: delegate to existing tts_generate flow (no change)
        return {
            "engine": "typecast",
            "output_path": output_path,
            "speaker_count": 1,
            "section_count": len(sections),
            "note": "single speaker -- use existing tts_generate.py directly",
        }


def _main():
    """CLI entry: read script.json, produce narration.mp3 + section_timing.json."""
    parser = argparse.ArgumentParser(description="Multi-speaker TTS orchestrator")
    parser.add_argument("--script", required=True, help="script.json path")
    parser.add_argument("--output", required=True, help="narration.mp3 output path")
    parser.add_argument("--channel", required=True, help="channel name for voice pool")
    parser.add_argument(
        "--timing",
        default=None,
        help="Optional section_timing.json output path (defaults to <output_dir>/section_timing.json)",
    )
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}", file=sys.stderr)
        sys.exit(2)

    script_data = json.loads(script_path.read_text(encoding="utf-8"))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    timing_out = args.timing or str(out_path.parent / "section_timing.json")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    result = generate_multi_speaker(
        script_data,
        str(out_path),
        args.channel,
        timing_output=timing_out,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
