"""Subtitle generation from audio using faster-whisper.

⚠️ SHORTS PIPELINE DEPRECATED — see word_subtitle.py
========================================================
이 스크립트는 **SRT만** 생성하기 때문에 Remotion이 실제로 읽는
`subtitles_remotion.json`을 갱신하지 못한다. 그 결과 TTS가 재생성되면
`.srt`는 바뀌는데 final.mp4에 박히는 자막은 옛 JSON 그대로 남아
싱크가 영구적으로 어긋난다 (세션 37 기타큐슈 Part 1 사고).

**Shorts(9:16) 파이프라인에서는 `scripts/audio-pipeline/word_subtitle.py`를 사용하라.**
`word_subtitle.py`는 실행 한 번에 `.srt` + `.ass` + `subtitles_remotion.json`을
모두 생성하므로 Remotion이 읽는 진실 원본이 항상 최신 상태로 유지된다.

**Shorts 모드 호출은 런타임에 명시적으로 실패한다** (main() 참조).
`--pipeline video --chapter-dir ...` legacy 16:9 long-form 경로만
계속 지원된다. 이 분기는 create-video 스킬 전용이며 쇼츠 제작에는
절대 사용하지 마라.
========================================================

Reads narration.mp3 (or chapter_NN.mp3 files in video mode) and generates
frame-accurate SRT subtitles using faster-whisper segment-level timestamps.
This script takes AUDIO ONLY as input -- it never reads script text for
timing (SUBT-02).

Korean word-level timestamps are unreliable (Pitfall 3), so only
segment-level timestamps are used (word_timestamps=False).

Exit codes:
    0 = success
    1 = input error (missing file, invalid args, or shorts-mode guard triggered)
    2 = transcription error (model load or transcribe failure)

Outputs:
    - subtitles.srt at the specified output path (video pipeline only)
    - JSON result to stdout: {output_path, segment_count, language_detected, style, duration_seconds}
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp HH:MM:SS,mmm.

    Uses comma separator as required by the SRT specification.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def _parse_srt_timestamp(ts: str) -> float:
    """Parse SRT timestamp 'HH:MM:SS,mmm' to seconds float."""
    parts = ts.replace(",", ".").split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def parse_srt(srt_path: str) -> list[dict]:
    """Parse SRT file into list of {index, start, end, text} dicts.

    Timestamps parsed as float seconds.
    """
    segments = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return segments
    blocks = content.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        index = int(lines[0])
        times = lines[1].split(" --> ")
        start = _parse_srt_timestamp(times[0].strip())
        end = _parse_srt_timestamp(times[1].strip())
        text = "\n".join(lines[2:])
        segments.append({"index": index, "start": start, "end": end, "text": text})
    return segments


def merge_chapter_srts(chapter_srts: list[str], chapter_offsets: list[float], output_path: str):
    """Merge multiple chapter SRT files with time offsets into one combined SRT.

    Args:
        chapter_srts: List of paths to chapter SRT files
        chapter_offsets: List of time offsets (seconds) for each chapter
        output_path: Path to write merged SRT
    """
    merged_lines = []
    global_index = 1
    for srt_path, offset in zip(chapter_srts, chapter_offsets):
        if not os.path.exists(srt_path):
            continue
        segments = parse_srt(srt_path)
        for seg in segments:
            merged_lines.append(str(global_index))
            start_ts = format_srt_timestamp(seg["start"] + offset)
            end_ts = format_srt_timestamp(seg["end"] + offset)
            merged_lines.append(f"{start_ts} --> {end_ts}")
            merged_lines.append(seg["text"])
            merged_lines.append("")
            global_index += 1
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_lines))


def segments_to_srt(segments) -> tuple[str, int]:
    """Convert faster-whisper segments to SRT string.

    Returns (srt_content, segment_count).
    Uses segment-level timestamps only (not word-level).
    Each segment maps to one subtitle line (D-06: 1 line at a time).
    """
    srt_lines = []
    count = 0
    for i, segment in enumerate(segments, start=1):
        start = format_srt_timestamp(segment.start)
        end = format_srt_timestamp(segment.end)
        text = segment.text.strip()
        if not text:
            continue
        srt_lines.append(str(i))
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")
        count = i
    return "\n".join(srt_lines), count


# ---------------------------------------------------------------------------
# ASS karaoke subtitle generation (Phase 26 — VFEX-12)
# ---------------------------------------------------------------------------

# Channel-specific karaoke colors in ASS BGR format (from channel SKILL.md files)
KARAOKE_COLORS = {
    "humor": {"highlight": "&H0047C9FF&", "default": "&H00FFFFFF&", "outline": "&H002E1A1A&"},
    "politics": {"highlight": "&H00D9904A&", "default": "&H00FFFFFF&", "outline": "&H002A1B0D&"},
    "trend": {"highlight": "&H00FFD200&", "default": "&H00FFFFFF&", "outline": "&H002E1A1A&"},
}


def format_ass_timestamp(seconds: float) -> str:
    """Format seconds as ASS timestamp H:MM:SS.cc (centiseconds).

    ASS format uses single-digit hour, colon separator, and centiseconds (1/100th second).
    Example: 65.32 -> "0:01:05.32"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole_secs = int(secs)
    centiseconds = int(round((secs - whole_secs) * 100))
    return f"{hours}:{minutes:02d}:{whole_secs:02d}.{centiseconds:02d}"


def validate_word_timestamps(
    words: list,
    segment_start: float,
    segment_end: float,
) -> list:
    """Post-process word-level timestamps for karaoke subtitle quality.

    Processing steps:
    1. Clamp word timestamps to segment boundaries
    2. Merge words with duration < 100ms into the next word
    3. Enforce minimum 200ms duration per word

    Args:
        words: List of {"word": str, "start": float, "end": float}
        segment_start: Segment start time (seconds)
        segment_end: Segment end time (seconds)

    Returns:
        Validated word list with corrected timestamps.
    """
    if not words:
        return []

    # Step 1: Clamp to segment boundaries
    clamped = []
    for w in words:
        clamped.append({
            "word": w["word"],
            "start": max(w["start"], segment_start),
            "end": min(w["end"], segment_end),
        })

    # Step 2: Merge short words (duration < 100ms) into next word
    merged = []
    i = 0
    while i < len(clamped):
        current = dict(clamped[i])
        duration = current["end"] - current["start"]

        if duration < 0.1 and i + 1 < len(clamped):
            # Merge into next word: concatenate text, keep earlier start
            next_word = clamped[i + 1]
            merged_word = {
                "word": current["word"] + next_word["word"],
                "start": current["start"],
                "end": next_word["end"],
            }
            # Replace next word with merged version
            clamped[i + 1] = merged_word
            i += 1
            continue
        elif duration < 0.1 and merged:
            # Last word is short — merge into previous
            merged[-1]["word"] = merged[-1]["word"] + current["word"]
            merged[-1]["end"] = current["end"]
            i += 1
            continue

        merged.append(current)
        i += 1

    # Step 3: Enforce minimum 200ms duration
    for w in merged:
        duration = w["end"] - w["start"]
        if duration < 0.2:
            w["end"] = min(w["start"] + 0.2, segment_end)

    return merged


def generate_ass(
    segments,
    channel: str = "humor",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Generate ASS subtitle file content with karaoke \\k tags.

    Creates an ASS file with:
    - [Script Info] section with PlayRes dimensions
    - [V4+ Styles] with channel-specific karaoke highlight colors
    - [Events] with Dialogue lines containing \\k{centiseconds} per word

    Fallback: If a segment has no word-level timestamps, a single \\k tag
    covers the entire segment text (segment-level highlighting).

    Args:
        segments: List of faster-whisper segment objects with .start, .end, .text, .words
        channel: Channel name for color selection ("humor", "politics", "trend")
        width: Video width for PlayResX
        height: Video height for PlayResY

    Returns:
        Complete ASS file content as string.
    """
    colors = KARAOKE_COLORS.get(channel, KARAOKE_COLORS["humor"])

    # [Script Info]
    lines = [
        "[Script Info]",
        "Title: Karaoke Subtitles",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
    ]

    # [V4+ Styles]
    # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour,
    #         OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut,
    #         ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow,
    #         Alignment, MarginL, MarginR, MarginV, Encoding
    lines.extend([
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,Pretendard,44,"
        f"{colors['default']},{colors['highlight']},"
        f"{colors['outline']},&H80000000&,"
        f"-1,0,0,0,100,100,0,0,1,3,1,2,10,10,40,1",
        "",
    ])

    # [Events]
    lines.extend([
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ])

    for segment in segments:
        start_ts = format_ass_timestamp(segment.start)
        end_ts = format_ass_timestamp(segment.end)
        text = segment.text.strip()
        if not text:
            continue

        # Build karaoke text with \k tags
        words = getattr(segment, "words", None)
        if words and len(words) > 0:
            # Word-level karaoke: one \k per word
            karaoke_parts = []
            for word in words:
                word_text = getattr(word, "word", str(word.get("word", ""))) if isinstance(word, dict) else word.word
                word_start = getattr(word, "start", word.get("start", 0)) if isinstance(word, dict) else word.start
                word_end = getattr(word, "end", word.get("end", 0)) if isinstance(word, dict) else word.end
                duration_cs = max(1, int((word_end - word_start) * 100))
                karaoke_parts.append(f"{{\\k{duration_cs}}}{word_text}")
            karaoke_text = "".join(karaoke_parts)
        else:
            # Segment-level fallback: single \k for whole segment
            duration_cs = max(1, int((segment.end - segment.start) * 100))
            karaoke_text = f"{{\\k{duration_cs}}}{text}"

        lines.append(
            f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{karaoke_text}"
        )

    return "\n".join(lines)


def load_subtitle_style(config_dir: str, style_name: str) -> dict:
    """Load subtitle style configuration from subtitle-styles.json.

    Args:
        config_dir: Path to config/ directory.
        style_name: Name of the style to load (e.g., "shorts-standard").

    Returns:
        Style configuration dict.

    Raises:
        FileNotFoundError: If config file not found.
        KeyError: If style name not found in config.
    """
    config_path = Path(config_dir) / "subtitle-styles.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if style_name not in config["styles"]:
        raise KeyError(f"Style '{style_name}' not found in subtitle-styles.json. "
                       f"Available: {list(config['styles'].keys())}")

    return config["styles"][style_name]


def transcribe_audio(input_path: str, use_word_timestamps: bool = False) -> tuple[list, dict]:
    """Transcribe audio using faster-whisper.

    Tries GPU (CUDA) first, falls back to CPU if unavailable (Pitfall 1:
    CUDA 13 vs CTranslate2 CUDA 12 compatibility issue).
    Fallback covers both model init AND transcribe — cublas errors can
    surface at either stage on Windows.

    Args:
        input_path: Path to narration.mp3.
        use_word_timestamps: If True, enables word-level timestamps for
            karaoke ASS subtitle generation (VFEX-12). Default False
            for segment-level only (Pitfall 3: Korean word-level can be
            unreliable, but needed for karaoke highlighting).

    Returns:
        Tuple of (segments_list, info_dict).
        Segments are materialized into a list to allow reuse.
    """
    from faster_whisper import WhisperModel

    # Try GPU first (init + transcribe), fall back to CPU on any CUDA error
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
        segments, info = model.transcribe(
            input_path,
            language="ko",
            word_timestamps=use_word_timestamps,
        )
        segments_list = list(segments)
        return segments_list, info
    except Exception as e:
        print(f"[WARN] CUDA failed ({e}), falling back to CPU mode (slower)",
              file=sys.stderr)

    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        input_path,
        language="ko",
        word_timestamps=use_word_timestamps,
    )

    # Materialize generator into list for reuse
    segments_list = list(segments)
    return segments_list, info


def transcribe_dubbed_audio(audio_path: str, language: str, output_dir: str = None) -> str:
    """Transcribe dubbed audio and generate target-language SRT subtitles.

    Re-transcribes dubbed audio using the existing faster-whisper pipeline
    to produce SRT subtitles in the target language. faster-whisper auto-detects
    language, no special config needed.

    Args:
        audio_path: Path to the dubbed audio file (e.g., dubbed_en.mp3).
        language: Target language code (e.g., "en", "ja", "es") for filename.
        output_dir: Directory to write the SRT file. If None, uses the same
            directory as the audio file.

    Returns:
        Path to the generated SRT file (e.g., subtitles_en.srt).
    """
    if output_dir is None:
        output_dir = str(Path(audio_path).parent)

    # Reuse existing faster-whisper pipeline
    segments, info = transcribe_audio(audio_path)

    # Convert segments to SRT format
    srt_content, segment_count = segments_to_srt(segments)

    # Write SRT file with language suffix
    srt_filename = f"subtitles_{language}.srt"
    srt_path = str(Path(output_dir) / srt_filename)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    logger.info(
        "Dubbed audio transcribed: %s (%d segments, lang=%s)",
        srt_path, segment_count, language,
    )

    return srt_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate SRT subtitles from narration audio using faster-whisper"
    )
    parser.add_argument("--input", required=True,
                        help="Path to narration.mp3 audio file")
    parser.add_argument("--output", required=True,
                        help="Path to write subtitles.srt")
    parser.add_argument("--style", default="shorts-standard",
                        help="Subtitle style name from subtitle-styles.json (default: shorts-standard)")
    parser.add_argument("--config-dir", default="config",
                        help="Path to config/ directory (default: config)")
    parser.add_argument("--pipeline", default="shorts", choices=["shorts", "video"],
                        help="Pipeline type: shorts (default) or video (chapter-based SRT merge)")
    parser.add_argument("--chapter-dir", default=None,
                        help="Directory containing chapter_NN.mp3 files (video pipeline only)")
    args = parser.parse_args()

    # === Video pipeline: chapter-based SRT with offset merge (GEN-04, D-10) ===
    if args.pipeline == "video":
        if not args.chapter_dir:
            print(json.dumps({"error": "--chapter-dir required for video pipeline"}))
            sys.exit(1)

        # Find chapter MP3 files
        chapter_dir = Path(args.chapter_dir)
        chapter_files = sorted(chapter_dir.glob("chapter_*.mp3"))
        if not chapter_files:
            print(json.dumps({"error": f"No chapter_*.mp3 files found in {args.chapter_dir}"}))
            sys.exit(1)

        # Load subtitle style config
        try:
            style_config = load_subtitle_style(args.config_dir, args.style)
        except (FileNotFoundError, KeyError) as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

        # Generate SRT per chapter
        chapter_srts = []
        chapter_offsets = []
        cumulative_offset = 0.0

        for chapter_file in chapter_files:
            srt_path = chapter_file.with_suffix(".srt")
            # Transcribe this chapter's audio
            segments, info = transcribe_audio(str(chapter_file))
            srt_content, segment_count = segments_to_srt(segments)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            chapter_srts.append(str(srt_path))
            chapter_offsets.append(cumulative_offset)

            # Get actual audio duration for next offset (not script estimate)
            chapter_duration = getattr(info, "duration", 0.0) or 0.0
            cumulative_offset += chapter_duration + 0.3  # 0.3s silence gap

        # Ensure output directory exists
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)

        # Merge all chapter SRTs with offsets
        merge_chapter_srts(chapter_srts, chapter_offsets, args.output)

        result = {
            "status": "success",
            "output_path": args.output,
            "chapters": len(chapter_srts),
            "total_segments": sum(len(parse_srt(s)) for s in chapter_srts if os.path.exists(s)),
            "style": args.style,
            "ffmpeg_force_style": style_config.get("ffmpeg_force_style", ""),
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    # === Shorts pipeline — DEPRECATED HARD GUARD ===
    # Shorts(9:16) 모드는 word_subtitle.py로 강제 이관되었다.
    # 이 분기를 호출하면 Remotion이 읽는 subtitles_remotion.json이 갱신되지 않아
    # final.mp4 자막 싱크가 영구적으로 어긋난다 (세션 37 기타큐슈 Part 1 사고).
    print(json.dumps({
        "error": (
            "subtitle_generate.py 의 shorts 모드는 DEPRECATED 입니다. "
            "쇼츠(9:16) 파이프라인에서는 scripts/audio-pipeline/word_subtitle.py 를 사용하세요. "
            "word_subtitle.py 는 실행 한 번에 .srt + .ass + subtitles_remotion.json 을 모두 생성하여 "
            "Remotion 이 읽는 진실 원본을 항상 최신 상태로 유지합니다."
        ),
        "remediation": (
            "scripts/audio-pipeline/.venv/Scripts/python.exe "
            "scripts/audio-pipeline/word_subtitle.py "
            "--audio <narration.mp3> --output <subtitles.srt> --max-chars 8 --model large-v3"
        ),
        "legacy_video_mode": (
            "16:9 long-form 경로(create-video 스킬)는 --pipeline video --chapter-dir 로 계속 지원됩니다."
        ),
    }), file=sys.stderr)
    sys.exit(1)

    # === UNREACHABLE (legacy shorts code kept below for reference only) ===
    # Validate input file exists
    if not Path(args.input).exists():
        print(json.dumps({"error": f"Input audio file not found: {args.input}"}),
              file=sys.stderr)
        sys.exit(1)

    # Load subtitle style config (SUBT-03)
    try:
        style_config = load_subtitle_style(args.config_dir, args.style)
    except (FileNotFoundError, KeyError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    # Transcribe audio with faster-whisper
    try:
        segments, info = transcribe_audio(args.input)
    except Exception as e:
        print(json.dumps({"error": f"Transcription failed: {e}"}),
              file=sys.stderr)
        sys.exit(2)

    # Generate SRT from segments
    srt_content, segment_count = segments_to_srt(segments)

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Write SRT file
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # Output JSON result to stdout
    result = {
        "output_path": args.output,
        "segment_count": segment_count,
        "language_detected": getattr(info, "language", "ko"),
        "style": args.style,
        "duration_seconds": getattr(info, "duration", None),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
