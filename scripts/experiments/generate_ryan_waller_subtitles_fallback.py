"""Sentence-level subtitle fallback — generate ASS/JSON/SRT from narration_timing.json.

word_subtitle.py (faster-whisper port) produced empty files despite reporting
success. This fallback uses the Typecast-reported AudioSegment timings to
generate sentence-level subtitles. Not word-level, but production-acceptable
for first Phase 16 smoke. Word-level refinement deferred.

Output:
- output/ryan-waller/subtitles_remotion.json (Remotion TS import)
- output/ryan-waller/subtitles_remotion.ass (Aegisub v4+ burn-in)
- output/ryan-waller/subtitles_remotion.srt (SubRip backup)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

TIMING = Path("output/ryan-waller/narration_timing.json")
OUT_JSON = Path("output/ryan-waller/subtitles_remotion.json")
OUT_ASS = Path("output/ryan-waller/subtitles_remotion.ass")
OUT_SRT = Path("output/ryan-waller/subtitles_remotion.srt")


def format_srt_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_ass_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def main() -> int:
    if not TIMING.exists():
        raise FileNotFoundError(f"Timing manifest missing: {TIMING}")
    manifest = json.loads(TIMING.read_text(encoding="utf-8"))
    sentences = manifest["sentences"]
    total_duration = manifest["total_duration_s"]

    # JSON cues (Remotion TS)
    cues = []
    for s in sentences:
        cues.append({
            "start_s": s["start_s"],
            "end_s": s["end_s"],
            "text": s["text"],
            "speaker": s["speaker"],
            "section": s["section"],
            "emotion": s["emotion"],
        })
    OUT_JSON.write_text(
        json.dumps({
            "cues": cues,
            "total_duration_s": total_duration,
            "source": "typecast_timing_fallback",
            "level": "sentence",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ASS (Aegisub v4+, Remotion burn-in)
    ass_lines = [
        "[Script Info]",
        "Title: Ryan Waller (incidents)",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,NanumSquare ExtraBold,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,520,1",
        "Style: Assistant,NanumSquare ExtraBold,54,&H00FFE600,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,520,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for s in sentences:
        # Use Assistant style (yellow) for Watson, Default (white) for Detective
        style = "Assistant" if s["speaker"] == "assistant" else "Default"
        start = format_ass_timecode(s["start_s"])
        end = format_ass_timecode(s["end_s"])
        # Escape ASS control characters
        text = s["text"].replace("\n", "\\N")
        ass_lines.append(
            f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}"
        )
    OUT_ASS.write_text("\n".join(ass_lines) + "\n", encoding="utf-8")

    # SRT (SubRip backup)
    srt_lines = []
    for i, s in enumerate(sentences, 1):
        srt_lines.append(str(i))
        srt_lines.append(
            f"{format_srt_timecode(s['start_s'])} --> {format_srt_timecode(s['end_s'])}"
        )
        srt_lines.append(s["text"])
        srt_lines.append("")
    OUT_SRT.write_text("\n".join(srt_lines), encoding="utf-8")

    print(f"✅ Subtitle fallback complete (sentence-level)")
    print(f"  JSON  : {OUT_JSON} ({len(cues)} cues)")
    print(f"  ASS   : {OUT_ASS} ({len(sentences)} Dialogue events, 2 styles)")
    print(f"  SRT   : {OUT_SRT}")
    print(f"  Total duration: {total_duration:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
