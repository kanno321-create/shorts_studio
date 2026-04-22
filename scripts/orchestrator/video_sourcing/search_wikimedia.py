"""Wikimedia Commons search — PD / CC-BY only, returns image+video candidates.

commons.wikimedia.org REST (no API key required).
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
TIMEOUT = 20

# License keywords that commons file-info returns in extmetadata
ALLOWED_LICENSE_SUBSTR = (
    "public domain", "cc0", "cc-by", "cc by-sa", "cc-by-sa",
    "pd-us", "pd-old", "no restrictions",
)


def _infer_license_flag(extmeta: dict[str, Any]) -> str:
    """Map commons extmetadata → license_flag enum."""
    license_name = (extmeta.get("LicenseShortName", {}) or {}).get("value", "").lower()
    if not license_name:
        license_name = (extmeta.get("License", {}) or {}).get("value", "").lower()
    if "public domain" in license_name or "pd-" in license_name or license_name == "cc0":
        return "public-domain"
    if license_name.startswith("cc-by") or license_name.startswith("cc by"):
        return "cc-by"
    if any(s in license_name for s in ALLOWED_LICENSE_SUBSTR):
        return "public-domain"
    return "unknown"


def search_wikimedia(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search Wikimedia Commons for files (images+videos) matching ``query``.

    Returns only files with public-domain / CC-BY license (unknown filtered out).
    """
    # Step 1: search file titles
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,  # File: namespace
        "srlimit": max_results,
        "format": "json",
    }
    try:
        r = requests.get(COMMONS_API, params=search_params, timeout=TIMEOUT,
                         headers={"User-Agent": "naberal-shorts-v3/0.1"})
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[commons-search] error {exc!r}")
        return []

    hits = r.json().get("query", {}).get("search", [])
    if not hits:
        return []

    titles = "|".join(h["title"] for h in hits)

    # Step 2: batch-fetch imageinfo + extmetadata for license
    info_params = {
        "action": "query",
        "titles": titles,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size",
        "iiextmetadatafilter": "License|LicenseShortName|Credit",
        "format": "json",
    }
    try:
        r2 = requests.get(COMMONS_API, params=info_params, timeout=TIMEOUT,
                          headers={"User-Agent": "naberal-shorts-v3/0.1"})
        r2.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[commons-info] error {exc!r}")
        return []

    pages = r2.json().get("query", {}).get("pages", {})
    out: list[dict[str, Any]] = []
    for _pid, page in pages.items():
        title = page.get("title", "")
        ii = (page.get("imageinfo") or [{}])[0]
        extmeta = ii.get("extmetadata", {}) or {}
        license_flag = _infer_license_flag(extmeta)
        if license_flag == "unknown":
            continue  # drop restrictive
        url = ii.get("url", "")
        mime = ii.get("mime", "")
        if not url:
            continue
        out.append({
            "source": "wikimedia",
            "id": title,
            "url": url,
            "title": title,
            "description": (extmeta.get("Credit", {}) or {}).get("value", "") or "",
            "mime": mime,
            "size": ii.get("size", 0),
            "license_flag": license_flag,
            "raw_snippet": {"extmetadata": extmeta},
        })
    return out
