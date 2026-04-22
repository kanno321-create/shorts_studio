"""Ryan Waller v4 — Replace reveal_s01 Kling output with clean text-overlay clip.

INVARIANT Rule 1: reads script_v4.json first.
Context: Inspector 2nd pass found reveal_s01 (Carver father-son reveal) fell
back to interrogation anchor. Story-critical reveal moment — must clearly show
"리치 카버" + "래리 카버" names. Replace Kling output with ffmpeg-generated
black background + bilingual name plates + fade in/out.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
SHOT_FINAL = Path("output/ryan-waller/sources/shot_final")
SHOT_ID = "reveal_s01_carver_father_son"
FONT = "C\\:/Windows/Fonts/malgunbd.ttf"


def main() -> int:
    print("[Replace reveal_s01] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    target_shot = None
    for sec in script["sections"]:
        for s in sec["shots"]:
            if s["shot_id"] == SHOT_ID:
                target_shot = s
    if not target_shot:
        raise ValueError(f"shot {SHOT_ID} not found")
    duration = target_shot["duration_hint_s"]
    print(f"  target duration: {duration}s")
    print(f"  script text:     {target_shot['text']}")

    with tempfile.TemporaryDirectory(prefix="reveal_s01_") as tmp:
        tdir = Path(tmp)
        t1 = tdir / "t1.txt"; t1.write_text("리치 카버", encoding="utf-8")
        t2 = tdir / "t2.txt"; t2.write_text("래리 카버", encoding="utf-8")
        t3 = tdir / "t3.txt"; t3.write_text("전 룸메이트 · 아버지", encoding="utf-8")
        t4 = tdir / "t4.txt"; t4.write_text("진범", encoding="utf-8")

        # escape Windows drive colon for drawtext filter parser: C:/... → C\:/...
        def esc(p: Path) -> str:
            return p.as_posix().replace(":", r"\:")

        p1, p2, p3, p4 = esc(t1), esc(t2), esc(t3), esc(t4)

        vf = (
            f"drawtext=fontfile='{FONT}':textfile='{p4}':"
            f"fontsize=80:fontcolor=#FF2200:"
            f"x=(w-text_w)/2:y=500,"
            f"drawtext=fontfile='{FONT}':textfile='{p1}':"
            f"fontsize=140:fontcolor=#F5F5F5:"
            f"x=(w-text_w)/2:y=820,"
            f"drawtext=fontfile='{FONT}':textfile='{p2}':"
            f"fontsize=140:fontcolor=#F5F5F5:"
            f"x=(w-text_w)/2:y=1020,"
            f"drawtext=fontfile='{FONT}':textfile='{p3}':"
            f"fontsize=55:fontcolor=#999999:"
            f"x=(w-text_w)/2:y=1280,"
            f"fade=t=in:st=0:d=0.4,"
            f"fade=t=out:st={duration-0.35:.3f}:d=0.35"
        )

        dst = SHOT_FINAL / f"{SHOT_ID}_final.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c=#0a0a0a:size=1080x1920:duration={duration}:rate=30",
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an",
            "-r", "30",
            str(dst),
        ]
        print(f"  cmd: ffmpeg drawtext → {dst}")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stderr[-2000:])
            raise RuntimeError("ffmpeg drawtext failed")
        size_mb = dst.stat().st_size / 1024 / 1024
        # probe duration
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(dst)],
            capture_output=True, text=True, check=True,
        )
        actual = float(p.stdout.strip())
        print(f"  DONE {dst.name} size={size_mb:.2f}MB duration={actual:.3f}s (target {duration}s)")
    print("OK reveal_s01 replaced with clean text-overlay clip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
