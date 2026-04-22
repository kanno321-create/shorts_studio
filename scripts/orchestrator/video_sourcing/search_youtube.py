"""YouTube Data API v3 search — returns candidate dicts for ranking.

Uses googleapiclient if available, else falls back to yt-dlp search CLI.
No retry / rate-limit / cache — prototype single-shot use.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any


def _search_via_googleapiclient(query: str, max_results: int) -> list[dict[str, Any]]:
    """Preferred path — Google official SDK (batched fields)."""
    from googleapiclient.discovery import build  # lazy

    api_key = os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("YOUTUBE_API_KEY / GOOGLE_API_KEY not set (check .env)")

    yt = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    resp = (
        yt.search()
        .list(
            q=query,
            part="snippet",
            type="video",
            videoDuration="short",  # ≤ 4 min — matches shorts scene range
            maxResults=max_results,
            safeSearch="none",  # incidents channel (adult-ish crime)
        )
        .execute()
    )

    out: list[dict[str, Any]] = []
    for item in resp.get("items", []):
        vid = item["id"]["videoId"]
        sn = item["snippet"]
        out.append({
            "source": "youtube",
            "id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "title": sn.get("title", ""),
            "description": sn.get("description", ""),
            "channel": sn.get("channelTitle", ""),
            "published_at": sn.get("publishedAt", ""),
            "thumbnail": sn.get("thumbnails", {}).get("high", {}).get("url", ""),
            "license_flag": "fair-use-educational",  # YouTube default — ind. verify
            "raw_snippet": sn,
        })
    return out


def _search_via_ytdlp(query: str, max_results: int) -> list[dict[str, Any]]:
    """Fallback when googleapiclient missing — use yt-dlp ytsearch CLI."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-warnings",
        "--flat-playlist",
        "--default-search", "ytsearch",
        f"ytsearch{max_results}:{query}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60)
    if result.returncode != 0:
        # Graceful empty — caller will fall back to Wikimedia/Kling
        return []

    out: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        vid = rec.get("id") or ""
        out.append({
            "source": "youtube",
            "id": vid,
            "url": rec.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "title": rec.get("title", ""),
            "description": rec.get("description", "") or "",
            "channel": rec.get("channel", ""),
            "published_at": rec.get("upload_date", ""),
            "thumbnail": "",
            "license_flag": "fair-use-educational",
            "raw_snippet": rec,
        })
    return out


def search_youtube(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search YouTube for short videos matching ``query``.

    Tries googleapiclient first (uses API key — faster, structured).
    Falls back to yt-dlp CLI search if SDK unavailable.
    Returns list of candidate dicts.
    """
    try:
        return _search_via_googleapiclient(query, max_results)
    except ImportError:
        # SDK not installed — use yt-dlp fallback
        return _search_via_ytdlp(query, max_results)
    except Exception as exc:  # noqa: BLE001
        # API quota / transient — log & fall back gracefully
        print(f"[yt-search] googleapiclient error ({exc!r}); falling back to yt-dlp")
        try:
            return _search_via_ytdlp(query, max_results)
        except Exception:  # noqa: BLE001
            return []
