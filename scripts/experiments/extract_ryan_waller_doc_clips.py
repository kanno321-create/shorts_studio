"""Extract 9:16 clips from downloaded Ryan Waller YouTube documentaries.

Session #34 v3.1: 3 docs downloaded (~138 min total) → extract key time-window
clips per section.visual_directing, pad to 1080×1920, save as v3.1 assets.

Each clip: ffmpeg -ss <start> -t <dur> -vf "scale=1080:-2,pad=1080:1920..."
-c:v libx264 -an (strip doc audio, our narration.mp3 is the track).

Output: output/ryan-waller/sources/real/raw_doc_clips/<section>_<index>.mp4

Strategy (blind timestamp picks based on documentary genre norms):
- Documentary intro (0-1min): skip
- Case overview + victim context (1-5min): body_scene source
- Wellness check / scene (5-10min): hook shot2 / body_scene source
- Interrogation start (10-18min): body_dalton source
- 6-hour interrogation segment (18-22min): body_6hours source
- Reveal / Carver (22-28min): reveal source
- Aftermath / hospital (28-end): aftermath_detective source
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
OUT_DIR = Path("output/ryan-waller/sources/real/raw_doc_clips")

# Primary doc: uHCUrMZNiLE "Unbelievable Case" (29 min, 1739s) — documentary style
DOC_PRIMARY = "uHCUrMZNiLE"
# Secondary doc: 7lluGVAsiDw "Infamous Interrogation" (43 min) — interrogation focus
DOC_SECONDARY = "7lluGVAsiDw"

# (section_id, doc_prefix, start_sec, dur_sec, visual_descriptor)
# Blind picks — Claude can't watch video; caller will review & rotate as needed.
EXTRACTS = [
    # Hook shot 2 — Ryan at scene / victim context
    ("hook_shot2", DOC_PRIMARY, 90, 4, "case overview ~1:30"),
    # Hook shot 3 — detective context
    ("hook_shot3", DOC_PRIMARY, 150, 4, "Phoenix detective ~2:30"),
    # body_scene — Heather Quan + crime scene
    ("body_scene_doc", DOC_PRIMARY, 240, 8, "Heather Quan + crime scene ~4:00"),
    # body_dalton — interrogation opening
    ("body_dalton_doc", DOC_PRIMARY, 420, 8, "Ryan Waller at interrogation ~7:00"),
    # body_6hours — interrogation progression
    ("body_6hours_doc", DOC_SECONDARY, 420, 8, "interrogation progression ~7min"),
    # watson_q2 filler (replace character — NEVER ASSISTANT PER feedback_assistant_never_appears_visually)
    # → use documentary cutaway
    ("watson_q2_doc", DOC_PRIMARY, 720, 4, "cutaway ~12:00"),
    # reveal — Carver reveal
    ("reveal_doc", DOC_PRIMARY, 1020, 8, "Carver reveal ~17:00"),
    # aftermath_detective — hospital / court
    ("aftermath_doc", DOC_PRIMARY, 1380, 8, "aftermath hospital ~23:00"),
    # Hook shot 1 intro context
    ("hook_shot1", DOC_PRIMARY, 60, 4, "opening ~1:00"),
]


def find_doc_file(prefix: str) -> Path:
    candidates = list(DOC_DIR.glob(f"{prefix}_*.mp4"))
    if not candidates:
        raise FileNotFoundError(f"No documentary mp4 starting with {prefix}_ in {DOC_DIR}")
    return candidates[0]


def extract_clip(src: Path, start: float, dur: float, out: Path) -> None:
    """Extract [start, start+dur] from src, pad to 1080×1920 9:16, strip audio."""
    out.parent.mkdir(parents=True, exist_ok=True)
    # scale width to 1080 (preserve aspect) → 640×360 becomes 1080×608
    # then pad to 1080×1920 with black bars top+bottom
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
        "-an",                      # no audio (our narration is separate)
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[EXTRACT] {len(EXTRACTS)} clips → {OUT_DIR}")
    print(f"[EXTRACT] primary doc = {DOC_PRIMARY}, secondary = {DOC_SECONDARY}")
    print()

    for name, doc, start, dur, desc in EXTRACTS:
        src = find_doc_file(doc)
        out = OUT_DIR / f"{name}.mp4"
        print(f"[EXTRACT] {name}")
        print(f"  src: {src.name}")
        print(f"  @{start}s +{dur}s — {desc}")
        extract_clip(src, float(start), float(dur), out)
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"  → {out.name} ({size_mb:.2f} MB)")
        print()

    print(f"✅ {len(EXTRACTS)} clips extracted")
    for name, _, _, _, _ in EXTRACTS:
        p = OUT_DIR / f"{name}.mp4"
        if p.exists():
            print(f"   · {p.name} ({p.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
