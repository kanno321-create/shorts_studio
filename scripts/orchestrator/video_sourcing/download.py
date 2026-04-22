"""Download candidate (video or image) to local path.

- YouTube → yt-dlp subprocess, 720p mp4 (avoids copyright-disputed 1080p sometimes blocked)
- Direct URL (Wikimedia / others) → requests streaming
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import requests

REQ_TIMEOUT = 60


def _download_youtube(candidate: dict[str, Any], out_dir: Path, basename: str) -> Path:
    """Use yt-dlp to grab the MP4. Returns local path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / f"{basename}.%(ext)s")
    url = candidate["url"]
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--quiet",
        # 720p max mp4 — fair-use safer, lower disk
        "-f", "mp4[height<=720]/best[height<=720]/mp4/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=180)
    if result.returncode != 0:
        stderr_tail = (result.stderr or "")[-500:]
        raise RuntimeError(f"yt-dlp failed ({result.returncode}): {stderr_tail}")
    # yt-dlp may have ext like .mp4; glob find
    for path in out_dir.glob(f"{basename}.*"):
        if path.is_file():
            return path
    raise RuntimeError(f"yt-dlp reported success but no output file at {out_dir}/{basename}.*")


def _download_direct(candidate: dict[str, Any], out_dir: Path, basename: str) -> Path:
    """Download a direct URL (e.g., Wikimedia) via requests streaming."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = candidate["url"]
    mime = candidate.get("mime", "") or ""
    # crude ext inference
    if mime.startswith("video/"):
        ext = ".mp4" if "mp4" in mime else ".webm"
    elif mime.startswith("image/"):
        ext = ".png" if "png" in mime else (".jpg" if "jpeg" in mime or "jpg" in mime else ".bin")
    else:
        # fallback: url tail
        tail = url.rsplit(".", 1)[-1].lower()
        ext = f".{tail}" if tail in ("mp4", "webm", "png", "jpg", "jpeg", "gif", "svg") else ".bin"
    out_path = out_dir / f"{basename}{ext}"
    with requests.get(url, stream=True, timeout=REQ_TIMEOUT,
                      headers={"User-Agent": "naberal-shorts-v3/0.1"}) as resp:
        resp.raise_for_status()
        with out_path.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
    return out_path


def download_candidate(candidate: dict[str, Any], out_dir: Path, basename: str) -> Path:
    """Dispatch by source — returns local path of downloaded file."""
    src = candidate.get("source", "").lower()
    if src == "youtube":
        return _download_youtube(candidate, out_dir, basename)
    return _download_direct(candidate, out_dir, basename)
