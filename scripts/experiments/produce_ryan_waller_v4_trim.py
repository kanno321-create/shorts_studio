"""Ryan Waller v4 Step 3a — Case A+B trim-only producer (sync, fast).

INVARIANT Rule 1: reads script_v4.json first.
Case A (6 shots): raw_doc_clips_v2/* → trim to shot.duration_hint_s
Case B (6 shots): existing broll_0X_*_v3.mp4 → trim to shot.duration_hint_s, 1:1 배정 (shot-level 중복 방지)
intro reuse (1): hook_s06 → intro_signature.mp4 copy

Output: output/ryan-waller/sources/shot_final/<shot_id>_final.mp4 x 13
"""
from __future__ import annotations
import builtins as _b
import json
import os
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
SOURCES = Path("output/ryan-waller/sources")
SHOT_FINAL = SOURCES / "shot_final"
RAW_DOC_V2 = SOURCES / "real/raw_doc_clips_v2"

# Case A: shot_id → raw_doc_clips_v2 filename
CASE_A_MAP = {
    "hook_s03_ryan_blood_sitting":          "hook_ryan_chair.mp4",
    "watson_q1_s01_doubt":                  "body_dalton_confront.mp4",
    "body_scene_s03_ryan_forehead_eye":     "hook_ryan_closeup.mp4",
    "body_dalton_s02_drug_pretend_confession": "body_scene_interrog.mp4",
    "body_6hours_s02_ryan_pupil_unresponsive": "body_6hours_fatigue.mp4",
    "reveal_s03_bullet_in_skull_alive":     "reveal_final_moments.mp4",
}
# Case B: shot_id → existing broll_0X_*_v3.mp4 (shot-level 1:1 배정)
CASE_B_MAP = {
    "hook_s01_date_christmas_eve":          "broll_02_christmas_night_v3.mp4",
    "body_dalton_s01_detective_suspect":    "broll_01_interrogation_v3.mp4",
    "body_6hours_s01_clock_six_hours":      "broll_03_clock_v3.mp4",
    "body_6hours_s03_real_killer_fleeing_phoenix": "broll_04_fleeing_v3.mp4",
    "aftermath_det_s01_brain_eye_loss":     "broll_05_hospital_v3.mp4",
    "aftermath_det_s02_lawsuit_dismissed_cta": "broll_06_court_dismissed_v3.mp4",
}
# intro signature reuse (hook_s06)
INTRO_REUSE = {"hook_s06_truth_reveal_title": "intro_signature.mp4"}


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def trim_clip(src: Path, dst: Path, target_dur: float) -> None:
    """Trim src to exactly target_dur seconds, scale/pad to 1080x1920, no audio."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    # ss=0 start. if src shorter than target_dur, loop by re-encoding fps.
    src_dur = probe_duration(src)
    if src_dur >= target_dur:
        start = max(0.0, (src_dur - target_dur) / 2.0) if src_dur > target_dur + 1 else 0.0
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{target_dur:.3f}",
            "-i", str(src),
            "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
                   "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
                   "setsar=1,setpts=PTS-STARTPTS",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            "-an",
            str(dst),
        ], check=True, capture_output=True)
    else:
        # loop source to reach target_dur
        loops = int(target_dur / src_dur) + 1
        subprocess.run([
            "ffmpeg", "-y", "-stream_loop", str(loops), "-i", str(src),
            "-t", f"{target_dur:.3f}",
            "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
                   "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
                   "setsar=1,setpts=PTS-STARTPTS",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            "-an",
            str(dst),
        ], check=True, capture_output=True)


def copy_intro(src: Path, dst: Path, target_dur: float) -> None:
    """Scale intro signature to 1080x1920 (if not already), trim to target_dur."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", f"{target_dur:.3f}",
        "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
               "setsar=1,setpts=PTS-STARTPTS",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an",
        str(dst),
    ], check=True, capture_output=True)


def main() -> int:
    _p("[Agent 2 Producer v4 trim] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    shots_by_id: dict[str, dict] = {}
    for sec in script["sections"]:
        for shot in sec["shots"]:
            shots_by_id[shot["shot_id"]] = shot

    SHOT_FINAL.mkdir(parents=True, exist_ok=True)

    # Case A — raw_doc_clips_v2 재사용
    _p(f"\n[Case A] raw_doc_clips_v2 trim ({len(CASE_A_MAP)} shots)")
    for shot_id, src_name in CASE_A_MAP.items():
        shot = shots_by_id[shot_id]
        src = RAW_DOC_V2 / src_name
        if not src.exists():
            raise FileNotFoundError(f"Case A src missing: {src}")
        dst = SHOT_FINAL / f"{shot_id}_final.mp4"
        dur = shot["duration_hint_s"]
        trim_clip(src, dst, dur)
        actual = probe_duration(dst)
        _p(f"  [A] shot={shot_id:<45s} src={src_name:<32s} target={dur:.3f}s actual={actual:.3f}s")

    # Case B — 기존 Kling v3 mp4 재사용 (shot-level 1:1)
    _p(f"\n[Case B] existing Kling v3 trim 1:1 ({len(CASE_B_MAP)} shots)")
    for shot_id, src_name in CASE_B_MAP.items():
        shot = shots_by_id[shot_id]
        src = SOURCES / src_name
        if not src.exists():
            raise FileNotFoundError(f"Case B src missing: {src}")
        dst = SHOT_FINAL / f"{shot_id}_final.mp4"
        dur = shot["duration_hint_s"]
        trim_clip(src, dst, dur)
        actual = probe_duration(dst)
        _p(f"  [B] shot={shot_id:<45s} src={src_name:<40s} target={dur:.3f}s actual={actual:.3f}s")

    # intro signature reuse (hook_s06)
    _p(f"\n[intro reuse] ({len(INTRO_REUSE)} shot)")
    for shot_id, src_name in INTRO_REUSE.items():
        shot = shots_by_id[shot_id]
        src = SOURCES / src_name
        if not src.exists():
            raise FileNotFoundError(f"intro src missing: {src}")
        dst = SHOT_FINAL / f"{shot_id}_final.mp4"
        dur = shot["duration_hint_s"]
        copy_intro(src, dst, dur)
        actual = probe_duration(dst)
        _p(f"  [I] shot={shot_id:<45s} src={src_name:<32s} target={dur:.3f}s actual={actual:.3f}s")

    _p(f"\nOK trim done: {len(CASE_A_MAP) + len(CASE_B_MAP) + len(INTRO_REUSE)} shots → shot_final/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
