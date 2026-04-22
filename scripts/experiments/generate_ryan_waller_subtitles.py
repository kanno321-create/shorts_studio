"""Generate Ryan Waller word-level subtitles via subtitle-producer + faster-whisper.

Uses `scripts.orchestrator.api.subtitle_producer.SubtitleProducer` which wraps
`scripts.orchestrator.subtitle.word_subtitle.py` (1705-line faster-whisper
large-v3 port from Phase 16-03).

Output:
- output/ryan-waller/subtitles_remotion.srt
- output/ryan-waller/subtitles_remotion.ass   (Aegisub v4+, Remotion render path)
- output/ryan-waller/subtitles_remotion.json  (word-level cues, Remotion TS import)

Usage:
  python scripts/experiments/generate_ryan_waller_subtitles.py

Note: faster-whisper large-v3 model ~3GB on first run (HF cache download).
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api.subtitle_producer import SubtitleProducer  # noqa: E402

NARRATION = Path("output/ryan-waller/narration.mp3").resolve()
SCRIPT = Path("output/ryan-waller/script.json").resolve()
OUT_DIR = Path("output/ryan-waller").resolve()


def main() -> int:
    if not NARRATION.exists():
        raise FileNotFoundError(f"narration.mp3 missing: {NARRATION}")
    if not SCRIPT.exists():
        raise FileNotFoundError(f"script.json missing: {SCRIPT}")

    producer = SubtitleProducer()
    print(f"[SUB] narration: {NARRATION}")
    print(f"[SUB] script   : {SCRIPT}")
    print(f"[SUB] output   : {OUT_DIR}")
    print(f"[SUB] model    : faster-whisper large-v3")
    print(f"[SUB] language : ko, max_chars_per_line=8")
    print("[SUB] generating (first run may download ~3GB model)...")

    result = producer.produce(
        narration_mp3=NARRATION,
        script_json=SCRIPT,
        output_dir=OUT_DIR,
        max_chars_per_line=8,
        language="ko",
        model="large-v3",
    )

    print()
    print("✅ Subtitle generation complete:")
    print(f"  SRT   : {result.srt_path}")
    print(f"  ASS   : {result.ass_path}")
    print(f"  JSON  : {result.json_path}")
    print(f"  cues  : {result.cue_count} words")
    print(f"  duration coverage: {result.coverage_pct:.1%}" if hasattr(result, "coverage_pct") else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
