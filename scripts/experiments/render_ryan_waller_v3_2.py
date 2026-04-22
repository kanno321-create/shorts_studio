"""Ryan Waller v3 Remotion render — syncs public/ + builds props + renders + mux SRT.

Session #34 v3 render driver. Mirrors v2 render_ryan_waller_v2.py structure
but with v3 inputs (narration_v3.mp3, subtitles_remotion_v3.json,
visual_spec_v3.json). Keeps v2 parity fixes: 6 Mbps video bitrate + mov_text
subtitle mux.

Usage:
  python scripts/experiments/render_ryan_waller_v3.py
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
VISUAL_SPEC = EPISODE_DIR / "visual_spec_v3_2.json"
SUBTITLES = EPISODE_DIR / "subtitles_remotion_v3_2.json"
SUBTITLES_SRT = EPISODE_DIR / "subtitles_remotion_v3_2.srt"
NARRATION = EPISODE_DIR / "narration_v3_2.mp3"  # v3.2 with Morgan+Guri emotion prompts

REMOTION_DIR = Path("remotion")
PUBLIC_DIR = REMOTION_DIR / "public" / EPISODE_ID
PROPS_PATH = EPISODE_DIR / "remotion_props_v3_2.json"
FINAL_RAW = EPISODE_DIR / "final_v3_2_raw.mp4"
FINAL_OUT = EPISODE_DIR / "final_v3_2.mp4"


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
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, int]] = []

    # Copy narration_v3 + subtitles_v3 with canonical names (narration.mp3 / subtitles_remotion.json
    # so existing Remotion composition code paths still resolve — then also write _v3 suffixed
    # for clarity)
    for src, alias_name in [
        (NARRATION, "narration_v3_2.mp3"),
        (SUBTITLES, "subtitles_remotion_v3_2.json"),
    ]:
        dst = PUBLIC_DIR / alias_name
        action = _safe_copy(src, dst)
        results.append((dst.name, action, dst.stat().st_size))

    # Copy all files in sources/ (including subdirs that contain real footage — but only from
    # top-level since visual_spec refs top-level filenames)
    for src in SOURCES_DIR.iterdir():
        if src.is_file():
            dst = PUBLIC_DIR / src.name
            action = _safe_copy(src, dst)
            results.append((dst.name, action, dst.stat().st_size))

    copied_n = sum(1 for _, a, _ in results if a == "copied")
    skipped_n = sum(1 for _, a, _ in results if a.startswith("skip"))
    print(f"[SYNC-v3] {copied_n} copied + {skipped_n} skipped → {PUBLIC_DIR}")
    for name, action, size in results:
        mark = "✓" if action == "copied" else "•"
        if size > 1024 * 100:
            print(f"  {mark} {name} ({size/1024/1024:.2f} MB) [{action}]")
        else:
            print(f"  {mark} {name} ({size/1024:.1f} KB) [{action}]")


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
    print(f"[RENDER-v3] Syncing public assets...")
    sync_public_assets()

    print(f"[RENDER-v3] Building props...")
    props = build_props()
    PROPS_PATH.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[RENDER-v3] props: {PROPS_PATH}")
    print(f"  audioSrc        : {props.get('audioSrc')}")
    print(f"  durationInFrames: {props.get('durationInFrames')} "
          f"(= {props.get('durationInFrames', 0) / 30:.2f}s @ 30fps)")
    print(f"  clip count      : {len(props.get('clips', []))}")
    print(f"  clip types      : {[c.get('type') for c in props.get('clips', [])]}")
    print(f"  subtitle cues   : {len(props.get('subtitles', []))}")

    entry = "src/index.ts"  # relative to cwd=REMOTION_DIR
    cmd = [
        "npx", "remotion", "render",
        entry,
        "ShortsVideo",
        FINAL_RAW.absolute().as_posix(),
        f"--props={PROPS_PATH.absolute().as_posix()}",
        "--codec=h264",
        "--fps=30",
        "--width=1080",
        "--height=1920",
        "--video-bitrate=6000K",
    ]
    print(f"[RENDER-v3] cmd: {' '.join(cmd)}")
    print(f"[RENDER-v3] cwd: {REMOTION_DIR.absolute()}")

    t0 = time.time()
    result = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR.absolute()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1200,
        shell=sys.platform == "win32",
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print("[RENDER-v3] STDOUT tail:")
        print((result.stdout or "")[-2000:])
        print("[RENDER-v3] STDERR tail:")
        print((result.stderr or "")[-2000:])
        raise RuntimeError(f"Remotion render failed (exit {result.returncode})")

    print(f"[RENDER-v3] ✅ raw {FINAL_RAW} ({elapsed:.1f}s)")
    if FINAL_RAW.exists():
        print(f"         size: {FINAL_RAW.stat().st_size / 1024 / 1024:.2f} MB")

    # SRT mux
    print(f"[MUX-v3] Embedding SRT subtitle via ffmpeg...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", str(FINAL_RAW.absolute()),
        "-i", str(SUBTITLES_SRT.absolute()),
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=kor",
        "-disposition:s:0", "default",
        str(FINAL_OUT.absolute()),
    ]
    mux_result = subprocess.run(mux_cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=120)
    if mux_result.returncode != 0:
        print("[MUX-v3] STDERR tail:")
        print((mux_result.stderr or "")[-1500:])
        raise RuntimeError(f"ffmpeg mux failed (exit {mux_result.returncode})")
    if FINAL_OUT.exists():
        print(f"[MUX-v3] ✅ {FINAL_OUT} "
              f"({FINAL_OUT.stat().st_size / 1024 / 1024:.2f} MB, SRT embedded)")
    return elapsed


if __name__ == "__main__":
    render()
