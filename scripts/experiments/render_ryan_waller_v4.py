"""Ryan Waller v4 Step 9 — Remotion render + SRT mux.

INVARIANT Rule 1: reads script_v4.json first.
v4 fork of render_ryan_waller_v3_2.py. Key diff:
- inputs: narration_v4.mp3 / subtitles_remotion_v4.json / visual_spec_v4.json
- public sync: copy sources/shot_final/ subtree (22 shot_final mp4s)
- outputs: final_v4_raw.mp4 + final_v4.mp4 (with SRT mux)
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

EPISODE_ID = "ryan-waller"
EPISODE_DIR = Path("output/ryan-waller")
SOURCES_DIR = EPISODE_DIR / "sources"
SHOT_FINAL_DIR = SOURCES_DIR / "shot_final"
SCRIPT_V4 = EPISODE_DIR / "script_v4.json"
VISUAL_SPEC = EPISODE_DIR / "visual_spec_v4.json"
SUBTITLES = EPISODE_DIR / "subtitles_remotion_v4.json"
SUBTITLES_SRT = EPISODE_DIR / "subtitles_remotion_v4.srt"
NARRATION = EPISODE_DIR / "narration_v4.mp3"

REMOTION_DIR = Path("remotion")
PUBLIC_EP = REMOTION_DIR / "public" / EPISODE_ID
PUBLIC_SHOT_FINAL = PUBLIC_EP / "sources" / "shot_final"
PROPS_PATH = EPISODE_DIR / "remotion_props_v4.json"
FINAL_RAW = EPISODE_DIR / "final_v4_raw.mp4"
FINAL_OUT = EPISODE_DIR / "final_v4.mp4"


def _safe_copy(src: Path, dst: Path) -> str:
    if dst.exists():
        same_size = src.stat().st_size == dst.stat().st_size
        writable = os.access(dst, os.W_OK)
        if same_size and not writable:
            return "skip-readonly-identical"
        if not writable:
            try:
                os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass
    shutil.copy2(src, dst)
    return "copied"


def sync_public_assets() -> None:
    PUBLIC_EP.mkdir(parents=True, exist_ok=True)
    PUBLIC_SHOT_FINAL.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str, int]] = []

    # narration + subtitles
    for src, alias in [(NARRATION, "narration_v4.mp3"),
                       (SUBTITLES, "subtitles_remotion_v4.json")]:
        dst = PUBLIC_EP / alias
        action = _safe_copy(src, dst)
        results.append((alias, action, dst.stat().st_size))

    # top-level sources (intro/outro/character/broll etc.)
    for src in SOURCES_DIR.iterdir():
        if src.is_file():
            dst = PUBLIC_EP / src.name
            action = _safe_copy(src, dst)
            results.append((src.name, action, dst.stat().st_size))

    # shot_final/ subtree (22 shot final mp4s) — required by visual_spec_v4 clip src
    for src in SHOT_FINAL_DIR.iterdir():
        if src.is_file():
            dst = PUBLIC_SHOT_FINAL / src.name
            action = _safe_copy(src, dst)
            results.append((f"sources/shot_final/{src.name}", action, dst.stat().st_size))

    copied = sum(1 for _, a, _ in results if a == "copied")
    skipped = sum(1 for _, a, _ in results if a.startswith("skip"))
    print(f"[SYNC-v4] {copied} copied + {skipped} skipped → {PUBLIC_EP}")
    # only show large items
    for name, action, size in results:
        if size > 1024 * 500:
            print(f"  {name} ({size/1024/1024:.2f} MB) [{action}]")


def build_props() -> dict:
    spec = json.loads(VISUAL_SPEC.read_text(encoding="utf-8"))
    subs = json.loads(SUBTITLES.read_text(encoding="utf-8"))

    sub_cues = []
    for cue in subs.get("cues", []):
        words = cue.get("words") or cue["text"].split()
        sub_cues.append({
            "startMs": round(cue["start_s"] * 1000),
            "endMs": round(cue["end_s"] * 1000),
            "words": words,
            "highlightIndex": 0,
        })

    props = dict(spec)
    props["subtitles"] = sub_cues
    props.setdefault("channelName", "사건기록부")
    return props


def render() -> float:
    print("[Agent Render v4] reads script_v4.json (INVARIANT Rule 1)")
    _ = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))  # evidence read

    print("[RENDER-v4] sync public/ ...")
    sync_public_assets()

    print("[RENDER-v4] build props ...")
    props = build_props()
    PROPS_PATH.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[RENDER-v4] props: {PROPS_PATH}")
    print(f"  audioSrc          : {props.get('audioSrc')}")
    print(f"  durationInFrames  : {props.get('durationInFrames')} "
          f"({props.get('durationInFrames', 0)/30:.2f}s @ 30fps)")
    print(f"  clip count        : {len(props.get('clips', []))}")
    print(f"  subtitle cues     : {len(props.get('subtitles', []))}")

    cmd = [
        "npx", "remotion", "render", "src/index.ts", "ShortsVideo",
        FINAL_RAW.absolute().as_posix(),
        f"--props={PROPS_PATH.absolute().as_posix()}",
        "--codec=h264", "--fps=30", "--width=1080", "--height=1920",
        "--video-bitrate=6000K",
    ]
    print(f"[RENDER-v4] cwd={REMOTION_DIR.absolute()}")
    print(f"[RENDER-v4] cmd={' '.join(cmd)}")

    t0 = time.time()
    result = subprocess.run(
        cmd, cwd=str(REMOTION_DIR.absolute()),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=1500, shell=sys.platform == "win32",
    )
    elapsed = time.time() - t0
    if result.returncode != 0:
        print("[RENDER-v4] STDOUT tail:\n" + (result.stdout or "")[-2500:])
        print("[RENDER-v4] STDERR tail:\n" + (result.stderr or "")[-2500:])
        raise RuntimeError(f"Remotion render failed (exit {result.returncode})")
    print(f"[RENDER-v4] OK raw {FINAL_RAW} ({elapsed:.1f}s)")
    if FINAL_RAW.exists():
        print(f"  size: {FINAL_RAW.stat().st_size / 1024 / 1024:.2f} MB")

    # SRT mux
    print("[MUX-v4] mov_text subtitle mux ...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", str(FINAL_RAW.absolute()),
        "-i", str(SUBTITLES_SRT.absolute()),
        "-c:v", "copy", "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=kor",
        "-disposition:s:0", "default",
        str(FINAL_OUT.absolute()),
    ]
    mr = subprocess.run(mux_cmd, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=180)
    if mr.returncode != 0:
        print("[MUX-v4] STDERR tail:\n" + (mr.stderr or "")[-1500:])
        raise RuntimeError(f"ffmpeg mux failed (exit {mr.returncode})")
    if FINAL_OUT.exists():
        print(f"[MUX-v4] OK {FINAL_OUT} "
              f"({FINAL_OUT.stat().st_size / 1024 / 1024:.2f} MB, SRT embedded)")
    return elapsed


if __name__ == "__main__":
    render()
