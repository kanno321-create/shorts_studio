"""Ryan Waller v5 — Reconcile shot_final/*.mp4 durations with reconciled script_v5.

INVARIANT Rule 1: reads script_v5.json first.
After script_v5 duration_hint_s was refreshed from timing_v5, shot_final files
(previously trimmed to old/drifted durations) need re-trim. Also: section-last
shots need duration_hint_s + silence_after_ms so video extends to cover silence
without Remotion freezing on the last frame.

Per-mode sources:
- real_footage: trim Full Interrogation at shot.doc_source_timestamp_s
- kling_t2i_i2v: already replaced by Pexels fallback — Ken Burns from pexels_v5/<sid>_pexels.jpg
- overlay_text: re-run ffmpeg drawtext with new duration
"""
from __future__ import annotations
import builtins as _b
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V5 = Path("output/ryan-waller/script_v5.json")
SHOT_FINAL = Path("output/ryan-waller/sources/shot_final")
PEXELS_DIR = Path("output/ryan-waller/sources/pexels_v5")
FULL_INTERROGATION = Path("output/ryan-waller/sources/real/raw_documentaries/ZI8G0KOOtqk_Ryan Waller Full Interrogation.mp4")
FONT_WIN = "C\\:/Windows/Fonts/malgunbd.ttf"


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def trim_real(src: Path, dst: Path, start: float, dur: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
        "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
               "setsar=1,setpts=PTS-STARTPTS",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ], check=True, capture_output=True)


def ken_burns(src: Path, dst: Path, duration: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    frames = max(30, round(duration * 30))
    vf = (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"zoompan=z='min(1+0.0005*on,1.12)':d={frames}:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
        "fade=t=in:st=0:d=0.2"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{duration:.3f}",
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-an",
        str(dst),
    ], check=True, capture_output=True)


def overlay_clip(shot: dict, dst: Path, duration: float) -> None:
    cfg = shot["overlay_config"]
    bg = cfg.get("bg_color", "#0a0a0a")
    lines = cfg["lines"]
    with tempfile.TemporaryDirectory(prefix=f"ov_{shot['shot_id'][:10]}_") as tmp:
        tdir = Path(tmp)
        filters = []
        for i, ln in enumerate(lines):
            p = tdir / f"t{i}.txt"
            p.write_text(ln["text"], encoding="utf-8")
            esc = p.as_posix().replace(":", r"\:")
            y_ratio = ln.get("y_ratio", 0.5)
            filters.append(
                f"drawtext=fontfile='{FONT_WIN}':textfile='{esc}':"
                f"fontsize={ln['fontsize']}:fontcolor={ln['color']}:"
                f"x=(w-text_w)/2:y=h*{y_ratio}-text_h/2"
            )
        vf = ",".join(filters) + f",fade=t=in:st=0:d=0.3,fade=t=out:st={max(0,duration-0.3):.3f}:d=0.3"
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={bg}:size=1080x1920:duration={duration}:rate=30",
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-an",
            str(dst),
        ], check=True, capture_output=True)


def main() -> int:
    _p("[Reconcile shot_final v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))

    # section-last map
    section_last = {}
    silence_by_section = {}
    for sec in script["sections"]:
        section_last[sec["shots"][-1]["shot_id"]] = sec["section_id"]
        silence_by_section[sec["section_id"]] = int(sec.get("silence_after_ms", 0)) / 1000.0

    total_reprocessed = 0
    for sec in script["sections"]:
        for shot in sec["shots"]:
            sid = shot["shot_id"]
            mode = shot.get("visual_mode")
            base_dur = shot["duration_hint_s"]
            extra = silence_by_section[sec["section_id"]] if sid in section_last else 0
            target = round(base_dur + extra, 3)
            dst = SHOT_FINAL / f"{sid}_final.mp4"
            current = probe_duration(dst) if dst.exists() else 0
            if abs(current - target) < 0.05:
                continue  # already accurate
            _p(f"  [{sid:<45s} mode={mode}] current={current:.3f}s target={target:.3f}s")
            if mode == "real_footage":
                ts = float(shot.get("doc_source_timestamp_s", 0))
                trim_real(FULL_INTERROGATION, dst, ts, target)
            elif mode == "kling_t2i_i2v":
                anchor = PEXELS_DIR / f"{sid}_pexels.jpg"
                if not anchor.exists():
                    raise FileNotFoundError(f"Pexels anchor missing: {anchor}")
                ken_burns(anchor, dst, target)
            elif mode == "overlay_text":
                overlay_clip(shot, dst, target)
            else:
                raise ValueError(f"unknown mode: {mode}")
            actual = probe_duration(dst)
            _p(f"    OK re-trim {sid:<45s} actual={actual:.3f}s (target {target:.3f}s)")
            total_reprocessed += 1
    _p(f"[Reconcile shot_final v5] {total_reprocessed} shots re-trimmed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
