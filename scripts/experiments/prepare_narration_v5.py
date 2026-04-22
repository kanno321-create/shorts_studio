"""Ryan Waller v5 — Narration preparation: reuse v4 TTS + prepend 1s silence for intro bookend.

INVARIANT Rule 1: reads script_v5.json first.
v5 audio-video alignment fix:
- intro_signature = 1s hold (30 frames) instead of v4's 3.3s (eliminates dead-air)
- narration audio prepended with 1s silence → plays during intro, narration begins at 1s
- outro_signature = 1s hold → 1s silent outro (natural fade)
- all shot timings in narration_timing_v5.json shifted +1s
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

V4_BACKUP = Path("output/.v4_backup_ryan-waller")
EP_V5 = Path("output/ryan-waller")
SCRIPT_V5 = EP_V5 / "script_v5.json"
NARRATION_V4 = V4_BACKUP / "narration_v4.mp3"
TIMING_V4 = V4_BACKUP / "narration_timing_v4.json"
NARRATION_V5 = EP_V5 / "narration_v5.mp3"
TIMING_V5 = EP_V5 / "narration_timing_v5.json"
INTRO_SEC = 1.0  # v5: 1s intro bookend


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def main() -> int:
    print("[Narration v5] reads script_v5.json (INVARIANT Rule 1)")
    _ = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))

    if not NARRATION_V4.exists():
        raise FileNotFoundError(f"v4 narration not found: {NARRATION_V4}")
    if not TIMING_V4.exists():
        raise FileNotFoundError(f"v4 timing not found: {TIMING_V4}")

    # 1) prepend 1s silence via ffmpeg adelay
    print(f"[Narration v5] prepending {INTRO_SEC}s silence to narration ...")
    delay_ms = int(INTRO_SEC * 1000)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(NARRATION_V4),
        "-af", f"adelay={delay_ms}|{delay_ms}",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        str(NARRATION_V5),
    ], check=True, capture_output=True)
    d_v5 = probe_duration(NARRATION_V5)
    d_v4 = probe_duration(NARRATION_V4)
    print(f"[Narration v5] v4 duration={d_v4:.2f}s → v5 duration={d_v5:.2f}s (intro offset={INTRO_SEC}s)")

    # 2) shift timing +1s
    timing_v4 = json.loads(TIMING_V4.read_text(encoding="utf-8"))
    shifted_sections = []
    for sec in timing_v4["sections"]:
        shifted_sections.append({
            **sec,
            "start_s": round(sec["start_s"] + INTRO_SEC, 3),
            "end_s": round(sec["end_s"] + INTRO_SEC, 3),
        })
    shifted_shots = []
    for shot in timing_v4["shots"]:
        shifted_shots.append({
            **shot,
            "start_s": round(shot["start_s"] + INTRO_SEC, 3),
            "end_s": round(shot["end_s"] + INTRO_SEC, 3),
        })
    timing_v5 = {
        "schema_version": "v5-shot-level-timing-with-intro-offset",
        "narration_mp3_path": str(NARRATION_V5),
        "total_duration_s": d_v5,
        "section_count": len(shifted_sections),
        "shot_count": len(shifted_shots),
        "intro_offset_s": INTRO_SEC,
        "v4_source_narration": str(NARRATION_V4),
        "sections": shifted_sections,
        "shots": shifted_shots,
    }
    TIMING_V5.write_text(json.dumps(timing_v5, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Narration v5] timing_v5 written: {TIMING_V5}")
    print(f"  all {len(shifted_shots)} shots shifted +{INTRO_SEC}s")
    print(f"  first shot start: {shifted_shots[0]['start_s']}s (was 0.0s in v4)")
    print(f"  last shot end   : {shifted_shots[-1]['end_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
