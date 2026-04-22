"""Ryan Waller v5 Remotion render + SRT mux.

INVARIANT Rule 1: reads script_v5.json first.
v5 fork of render_ryan_waller_v4.py. Diffs:
- narration_v5.mp3 (1s silence prefix)
- subtitles_remotion_v5.{json,srt}
- visual_spec_v5.json
- intro/outro 30 frames each (was 99)
"""
from __future__ import annotations
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

EP_ID = "ryan-waller"
EP = Path("output/ryan-waller")
SOURCES = EP / "sources"
SHOT_FINAL = SOURCES / "shot_final"
SCRIPT_V5 = EP / "script_v5.json"
VISUAL_SPEC = EP / "visual_spec_v5.json"
SUBS = EP / "subtitles_remotion_v5.json"
SUBS_SRT = EP / "subtitles_remotion_v5.srt"
NARR = EP / "narration_v5.mp3"

INTRO_SRC = Path("output/.v4_backup_ryan-waller/sources/intro_signature.mp4")
OUTRO_SRC = Path("output/.v4_backup_ryan-waller/sources/outro_signature.mp4")
CHAR_DETECTIVE_SRC = Path("output/.v4_backup_ryan-waller/sources/character_detective.png")
CHAR_ASSISTANT_SRC = Path("output/.v4_backup_ryan-waller/sources/character_assistant.png")

REMOTION = Path("remotion")
PUBLIC_EP = REMOTION / "public" / EP_ID
PUBLIC_SHOT_FINAL = PUBLIC_EP / "sources" / "shot_final"
PROPS = EP / "remotion_props_v5.json"
RAW_OUT = EP / "final_v5_raw.mp4"
FINAL_OUT = EP / "final_v5.mp4"


def _safe_copy(src: Path, dst: Path) -> str:
    if dst.exists():
        if src.stat().st_size == dst.stat().st_size and not os.access(dst, os.W_OK):
            return "skip-ro"
        if not os.access(dst, os.W_OK):
            try: os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
            except Exception: pass
    shutil.copy2(src, dst)
    return "copied"


def restore_bookends() -> None:
    """v5 fresh folder: restore intro/outro/character from v4 backup."""
    for src, dst in [
        (INTRO_SRC, SOURCES / "intro_signature.mp4"),
        (OUTRO_SRC, SOURCES / "outro_signature.mp4"),
        (CHAR_DETECTIVE_SRC, SOURCES / "character_detective.png"),
        (CHAR_ASSISTANT_SRC, SOURCES / "character_assistant.png"),
    ]:
        if src.exists() and not dst.exists():
            # temporarily unset read-only flag on src copy
            shutil.copy2(src, dst)
            if not os.access(dst, os.W_OK):
                try: os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
                except Exception: pass
            print(f"  restored: {dst.name}")


def sync_public() -> None:
    PUBLIC_EP.mkdir(parents=True, exist_ok=True)
    PUBLIC_SHOT_FINAL.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, int]] = []
    for src, alias in [(NARR, "narration_v5.mp3"), (SUBS, "subtitles_remotion_v5.json")]:
        dst = PUBLIC_EP / alias
        results.append((alias, _safe_copy(src, dst), dst.stat().st_size))
    for src in SOURCES.iterdir():
        if src.is_file():
            dst = PUBLIC_EP / src.name
            results.append((src.name, _safe_copy(src, dst), dst.stat().st_size))
    for src in SHOT_FINAL.iterdir():
        if src.is_file():
            dst = PUBLIC_SHOT_FINAL / src.name
            results.append((f"sources/shot_final/{src.name}", _safe_copy(src, dst), dst.stat().st_size))
    copied = sum(1 for _, a, _ in results if a == "copied")
    print(f"[SYNC] {copied} copied → {PUBLIC_EP}")


def build_props() -> dict:
    spec = json.loads(VISUAL_SPEC.read_text(encoding="utf-8"))
    subs = json.loads(SUBS.read_text(encoding="utf-8"))
    cues = []
    for cue in subs.get("cues", []):
        words = cue.get("words") or cue["text"].split()
        cues.append({"startMs": round(cue["start_s"] * 1000),
                     "endMs": round(cue["end_s"] * 1000),
                     "words": words, "highlightIndex": 0})
    props = dict(spec)
    props["subtitles"] = cues
    props.setdefault("channelName", "사건기록부")
    return props


def render() -> float:
    print("[Render v5] reads script_v5.json (INVARIANT Rule 1)")
    _ = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))
    print("[Render v5] restore bookends from v4 backup ...")
    restore_bookends()
    print("[Render v5] sync public/ ...")
    sync_public()
    print("[Render v5] build props ...")
    props = build_props()
    PROPS.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  audioSrc        : {props.get('audioSrc')}")
    print(f"  durationInFrames: {props.get('durationInFrames')} ({props.get('durationInFrames')/30:.2f}s)")
    print(f"  clips           : {len(props.get('clips', []))}")
    print(f"  cues            : {len(props.get('subtitles', []))}")

    cmd = ["npx", "remotion", "render", "src/index.ts", "ShortsVideo",
           RAW_OUT.absolute().as_posix(),
           f"--props={PROPS.absolute().as_posix()}",
           "--codec=h264", "--fps=30", "--width=1080", "--height=1920",
           "--video-bitrate=6000K"]
    print(f"[Render v5] cmd: {' '.join(cmd)}")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(REMOTION.absolute()),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=1500, shell=sys.platform == "win32")
    el = time.time() - t0
    if r.returncode != 0:
        print((r.stdout or "")[-2500:])
        print((r.stderr or "")[-2500:])
        raise RuntimeError(f"render exit {r.returncode}")
    print(f"[Render v5] OK raw {RAW_OUT} ({el:.0f}s, {RAW_OUT.stat().st_size/1024/1024:.2f} MB)")

    print("[MUX v5] mov_text ...")
    r2 = subprocess.run([
        "ffmpeg", "-y", "-i", str(RAW_OUT.absolute()),
        "-i", str(SUBS_SRT.absolute()),
        "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=kor",
        "-disposition:s:0", "default",
        str(FINAL_OUT.absolute()),
    ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if r2.returncode != 0:
        print((r2.stderr or "")[-1500:])
        raise RuntimeError(f"mux exit {r2.returncode}")
    print(f"[MUX v5] OK {FINAL_OUT} ({FINAL_OUT.stat().st_size/1024/1024:.2f} MB)")
    return el


if __name__ == "__main__":
    render()
