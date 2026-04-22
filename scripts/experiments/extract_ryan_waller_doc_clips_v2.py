"""Ryan Waller v3.2 doc clip re-extraction — ZI8G0KOOtqk Full Interrogation 중심.

Session #34 v3.2 (대표님 지시 "여자 유튜버는 뭐하러 몇번씩이나 넣는건데?"):
- uHCUrMZNiLE "Unbelievable Case / Young Love" = true crime YouTuber 호스트 중심
  → 배제 (여자 유튜버 얼굴만 반복 노출)
- 7lluGVAsiDw "78. Infamous Interrogation" = series, 호스트 가능성
  → 배제 (안전 보수)
- **ZI8G0KOOtqk "Ryan Waller Full Interrogation"** = raw 취조실 CCTV 영상
  → 주력 (호스트 없음, Ryan/Dalton/취조실 다양 angle)

Extract from 65-min Full Interrogation at varied timestamps covering early/mid/late
phases. All crops center-pad to 1080×1920 9:16 letterbox.

Output: output/ryan-waller/sources/real/raw_doc_clips_v2/*.mp4
(old raw_doc_clips/ 는 유지하되 v3.2 builder 가 v2 만 참조)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

DOC_DIR = Path("output/ryan-waller/sources/real/raw_documentaries")
OUT_DIR = Path("output/ryan-waller/sources/real/raw_doc_clips_v2")

# PRIMARY only — Full Interrogation raw CCTV (no YouTuber host)
DOC_ID = "ZI8G0KOOtqk"

# (clip_name, start_sec, dur_sec, description)
# Full Interrogation = 3902s (65 min). Sampling varied phases.
EXTRACTS = [
    ("hook_ryan_chair",       30,  4, "Ryan enters interrogation chair (first moments)"),
    ("hook_ryan_closeup",    120,  4, "Ryan face close-up (2 min mark)"),
    ("hook_dalton_arrive",   300,  3, "Dalton / handlers angle (5 min)"),
    ("body_scene_interrog",   90,  5, "scene — Ryan slumped (90s)"),
    ("body_dalton_confront", 600,  6, "Dalton confrontation (10 min)"),
    ("body_6hours_fatigue",  1800, 6, "Ryan showing fatigue (30 min - mid-interrogation)"),
    ("body_6hours_silent",   2400, 5, "Ryan silent / deteriorating (40 min)"),
    ("reveal_final_moments", 3000, 5, "late-stage interrogation (50 min)"),
    ("aftermath_wrap",       3600, 5, "near end of interrogation (60 min)"),
]


def find_doc() -> Path:
    candidates = list(DOC_DIR.glob(f"{DOC_ID}_*.mp4"))
    if not candidates:
        raise FileNotFoundError(f"No doc mp4 starting with {DOC_ID}_")
    return candidates[0]


def extract_clip(src: Path, start: float, dur: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    vf = (
        "scale=1080:-2,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
        "setsar=1"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.2f}",
        "-i", str(src),
        "-t", f"{dur:.2f}",
        "-vf", vf,
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg {out.name} failed: {(r.stderr or '')[-500:]}")


def main() -> int:
    src = find_doc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[EXTRACT-v2] source: {src.name}")
    print(f"[EXTRACT-v2] {len(EXTRACTS)} clips → {OUT_DIR}")
    print()

    for name, start, dur, desc in EXTRACTS:
        out = OUT_DIR / f"{name}.mp4"
        print(f"[EXTRACT-v2] {name} @{start}s +{dur}s — {desc}")
        extract_clip(src, float(start), float(dur), out)
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"  → {out.name} ({size_mb:.2f} MB)")

    print(f"\n✅ {len(EXTRACTS)} clips extracted from Full Interrogation (raw CCTV)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
