"""Ryan Waller v2 — Remotion render driver.

Session #34 FIX-6: Merges visual_spec.json + subtitles_remotion.json into Remotion
props, syncs public/ryan-waller/ with latest assets (Kling mp4 clips, new
narration.mp3, new subtitles, Korean welsh corgi), then invokes
`npx remotion render` to produce output/ryan-waller/final_v2.mp4.

Usage:
  python scripts/experiments/render_ryan_waller_v2.py
"""
from __future__ import annotations

import json
import shutil
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
VISUAL_SPEC = EPISODE_DIR / "visual_spec.json"
SUBTITLES = EPISODE_DIR / "subtitles_remotion.json"
SUBTITLES_SRT = EPISODE_DIR / "subtitles_remotion.srt"
NARRATION = EPISODE_DIR / "narration.mp3"

REMOTION_DIR = Path("remotion")
PUBLIC_DIR = REMOTION_DIR / "public" / EPISODE_ID
PROPS_PATH = EPISODE_DIR / "remotion_props_v2.json"
FINAL_RAW = EPISODE_DIR / "final_v2_raw.mp4"   # before SRT mux
FINAL_OUT = EPISODE_DIR / "final_v2.mp4"        # after SRT mux (parity target)


def _safe_copy(src: Path, dst: Path) -> str:
    """Copy src→dst. If dst is read-only and already identical (by size), skip.
    If dst is read-only but differs, clear attrib then copy.
    """
    import os as _os
    import stat as _stat
    if dst.exists():
        same_size = src.stat().st_size == dst.stat().st_size
        writable = _os.access(dst, _os.W_OK)
        if same_size and not writable:
            return "skip-readonly-identical"
        if not writable:
            # Clear read-only attr on dst so we can overwrite (explicit freshness)
            try:
                _os.chmod(dst, _stat.S_IWRITE | _stat.S_IREAD)
            except Exception:
                pass
    shutil.copy2(src, dst)
    return "copied"


def sync_public_assets() -> None:
    """Copy latest episode assets into remotion/public/<episode>/."""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, int]] = []

    # Narration + subtitles (top-level episode files)
    for src in (NARRATION, SUBTITLES):
        dst = PUBLIC_DIR / src.name
        action = _safe_copy(src, dst)
        results.append((dst.name, action, dst.stat().st_size))

    # Sources (intro + characters + 6 b-roll mp4 + 6 b-roll png anchors)
    for src in SOURCES_DIR.iterdir():
        if src.is_file():
            dst = PUBLIC_DIR / src.name
            action = _safe_copy(src, dst)
            results.append((dst.name, action, dst.stat().st_size))

    copied_n = sum(1 for _, a, _ in results if a == "copied")
    skipped_n = sum(1 for _, a, _ in results if a.startswith("skip"))
    print(f"[SYNC] {copied_n} copied + {skipped_n} skipped → {PUBLIC_DIR}")
    for name, action, size in results:
        mark = "✓" if action == "copied" else "•"
        if size > 1024 * 100:
            print(f"  {mark} {name} ({size/1024/1024:.2f} MB) [{action}]")
        else:
            print(f"  {mark} {name} ({size/1024:.1f} KB) [{action}]")


def build_props() -> dict:
    """Merge visual_spec + subtitles into Remotion props."""
    spec = json.loads(VISUAL_SPEC.read_text(encoding="utf-8"))
    subs = json.loads(SUBTITLES.read_text(encoding="utf-8"))

    # Convert subtitles cues → wordSubCueSchema (startMs, endMs, words, highlightIndex)
    sub_cues = []
    for cue in subs.get("cues", []):
        text = cue["text"]
        # Split sentence into words (space-separated) — Korean TTS fallback level
        words = text.split()
        sub_cues.append({
            "startMs": round(cue["start_s"] * 1000),
            "endMs": round(cue["end_s"] * 1000),
            "words": words,
            "highlightIndex": 0,  # no word-level highlight at sentence fallback
        })

    props = dict(spec)
    props["subtitles"] = sub_cues
    # Remotion pipeline expects `titleLine1` already; keep everything else.

    # Add channelName fallback if missing
    props.setdefault("channelName", "사건기록부")

    return props


def render() -> float:
    print(f"[RENDER] Syncing public assets...")
    sync_public_assets()

    print(f"[RENDER] Building props...")
    props = build_props()
    PROPS_PATH.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[RENDER] props: {PROPS_PATH}")
    print(f"  audioSrc        : {props.get('audioSrc')}")
    print(f"  durationInFrames: {props.get('durationInFrames')}")
    print(f"  clip count      : {len(props.get('clips', []))}")
    print(f"  clip types      : {[c.get('type') for c in props.get('clips', [])]}")
    print(f"  subtitle cues   : {len(props.get('subtitles', []))}")

    # entry is relative to cwd=REMOTION_DIR (mirror remotion_renderer.py L733-738)
    entry = "src/index.ts"
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
        # v2 parity fix: lift video bitrate ≥5 Mbps (v1 was 4.74 Mbps — FAIL)
        "--video-bitrate=6000K",
    ]
    print(f"[RENDER] cmd: {' '.join(cmd)}")
    print(f"[RENDER] cwd: {REMOTION_DIR.absolute()}")

    t0 = time.time()
    result = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR.absolute()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        shell=sys.platform == "win32",
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print("[RENDER] STDOUT tail:")
        print((result.stdout or "")[-2000:])
        print("[RENDER] STDERR tail:")
        print((result.stderr or "")[-2000:])
        raise RuntimeError(f"Remotion render failed (exit {result.returncode})")

    print(f"[RENDER] ✅ raw {FINAL_RAW} ({elapsed:.1f}s)")
    if FINAL_RAW.exists():
        size_mb = FINAL_RAW.stat().st_size / 1024 / 1024
        print(f"         size: {size_mb:.2f} MB")

    # Post-process: mux SRT as embedded subtitle track to satisfy verifier SC.
    # Remotion burn-in is visual only — verify_baseline_parity requires
    # subtitle_streams >= 1, so we add an mov_text track alongside.
    print(f"[MUX] Embedding SRT subtitle track via ffmpeg...")
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
    mux_result = subprocess.run(
        mux_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if mux_result.returncode != 0:
        print("[MUX] STDERR tail:")
        print((mux_result.stderr or "")[-1500:])
        raise RuntimeError(f"ffmpeg mux failed (exit {mux_result.returncode})")
    if FINAL_OUT.exists():
        size_mb = FINAL_OUT.stat().st_size / 1024 / 1024
        print(f"[MUX] ✅ {FINAL_OUT} ({size_mb:.2f} MB, SRT embedded)")
    return elapsed


if __name__ == "__main__":
    render()
