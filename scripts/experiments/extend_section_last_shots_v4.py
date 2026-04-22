"""Ryan Waller v4 Step 3c — Extend section-last shots by silence_after_ms.

INVARIANT Rule 1: reads script_v4.json first.
v4 alignment fix: section 마지막 shot 의 shot_final mp4 을
  new_duration = shot.duration_hint_s + section.silence_after_ms
로 재 trim/loop (video freeze 방지 + narration silence 구간 자연스러운 시각 hold).

Re-trims Case A/B/C/intro source where needed.
Idempotent: 이미 extended 된 파일은 actual duration 비교 후 skip.
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
KLING_RAW = Path("outputs/kling/ryan-waller-v4")
RAW_DOC_V2 = SOURCES / "real/raw_doc_clips_v2"

# shot_id → source mp4 (재 trim 소스)
SHOT_SOURCE_MAP = {
    # Case A: raw_doc_clips_v2
    "hook_s03_ryan_blood_sitting":            RAW_DOC_V2 / "hook_ryan_chair.mp4",
    "watson_q1_s01_doubt":                    RAW_DOC_V2 / "body_dalton_confront.mp4",
    "body_scene_s03_ryan_forehead_eye":       RAW_DOC_V2 / "hook_ryan_closeup.mp4",
    "body_dalton_s02_drug_pretend_confession": RAW_DOC_V2 / "body_scene_interrog.mp4",
    "body_6hours_s02_ryan_pupil_unresponsive": RAW_DOC_V2 / "body_6hours_fatigue.mp4",
    "reveal_s03_bullet_in_skull_alive":       RAW_DOC_V2 / "reveal_final_moments.mp4",
    # Case B: existing Kling v3 mp4
    "hook_s01_date_christmas_eve":            SOURCES / "broll_02_christmas_night_v3.mp4",
    "body_dalton_s01_detective_suspect":      SOURCES / "broll_01_interrogation_v3.mp4",
    "body_6hours_s01_clock_six_hours":        SOURCES / "broll_03_clock_v3.mp4",
    # regen v4 2nd pass: body_6hours_s03 now uses NEW Kling raw (desert highway aerial)
    "body_6hours_s03_real_killer_fleeing_phoenix": KLING_RAW / "body_6hours_s03_real_killer_fleeing_phoenix_kling_raw.mp4",
    "aftermath_det_s01_brain_eye_loss":       SOURCES / "broll_05_hospital_v3.mp4",
    "aftermath_det_s02_lawsuit_dismissed_cta": SOURCES / "broll_06_court_dismissed_v3.mp4",
    # intro reuse
    "hook_s06_truth_reveal_title":            SOURCES / "intro_signature.mp4",
    # Case C: Kling raw (outputs/kling/ryan-waller-v4/<shot_id>_kling_raw.mp4)
    "hook_s02_phoenix_arizona":               KLING_RAW / "hook_s02_phoenix_arizona_kling_raw.mp4",
    "hook_s04_heather_body":                  KLING_RAW / "hook_s04_heather_body_kling_raw.mp4",
    "hook_s05_interrogation_6hours":          KLING_RAW / "hook_s05_interrogation_6hours_kling_raw.mp4",
    "body_scene_s01_heather_victim":          KLING_RAW / "body_scene_s01_heather_victim_kling_raw.mp4",
    "body_scene_s02_phoenix_shooting":        KLING_RAW / "body_scene_s02_phoenix_shooting_kling_raw.mp4",
    "watson_q2_s01_flee_shock":               KLING_RAW / "watson_q2_s01_flee_shock_kling_raw.mp4",
    "reveal_s01_carver_father_son":           KLING_RAW / "reveal_s01_carver_father_son_kling_raw.mp4",
    "reveal_s02_doorway_ambush":              KLING_RAW / "reveal_s02_doorway_ambush_kling_raw.mp4",
    "aftermath_watson_s01_cta":               KLING_RAW / "aftermath_watson_s01_cta_kling_raw.mp4",
}


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def trim_or_loop(src: Path, dst: Path, target_dur: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_dur = probe_duration(src)
    if src_dur >= target_dur:
        start = max(0.0, (src_dur - target_dur) / 2.0) if src_dur > target_dur + 0.5 else 0.0
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


def main() -> int:
    _p("[Extend v4] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))

    # section-last shot map
    extends: list[tuple[str, float, int]] = []  # (shot_id, new_duration, silence_ms)
    for sec in script["sections"]:
        last_shot = sec["shots"][-1]
        sil_ms = int(sec.get("silence_after_ms", 0))
        if sil_ms <= 0:
            continue  # no extension needed (e.g., aftermath_watson with silence=0)
        new_dur = last_shot["duration_hint_s"] + sil_ms / 1000.0
        extends.append((last_shot["shot_id"], new_dur, sil_ms))

    _p(f"[Extend v4] {len(extends)} section-last shots to extend")
    for sid, new_dur, sil in extends:
        src = SHOT_SOURCE_MAP.get(sid)
        if not src or not src.exists():
            raise FileNotFoundError(f"source for {sid} not found: {src}")
        dst = SHOT_FINAL / f"{sid}_final.mp4"
        current = probe_duration(dst)
        if abs(current - new_dur) < 0.1:
            _p(f"  SKIP {sid:<45s} already={current:.3f}s target={new_dur:.3f}s")
            continue
        trim_or_loop(src, dst, new_dur)
        actual = probe_duration(dst)
        _p(f"  EXTEND {sid:<45s} src={src.name[:30]:<30s} "
           f"base+sil={new_dur:.3f}s actual={actual:.3f}s (sil={sil}ms)")
    _p("OK section-last shots extended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
