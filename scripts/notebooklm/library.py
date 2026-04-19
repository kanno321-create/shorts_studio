"""library.json append helper for the D-8 naberal-shorts-channel-bible notebook.

Phase 6 Plan 04 (WIKI-03 D-8). Companion to scripts.notebooklm.query (Plan 03):
- query_notebook is the subprocess boundary for RAG queries against a notebook.
- add_channel_bible_entry is the idempotent registration helper that makes
  the new channel-bible notebook addressable via its id.

D-7 compliance: no cross-import of the external skill package. Mutation of
the external library.json happens by path only (subprocess-free, stdlib-only).

Idempotency contract:
- 1st call: creates entry from template with created_at == updated_at == now
- Nth call same url: refreshes updated_at, preserves created_at/use_count/last_used
- Nth call different url: updates url + updated_at, preserves created_at/use_count/last_used
- Never mutates shorts-production-pipeline-bible entry
- Never touches the default-notebook pointer
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "add_channel_bible_entry",
    "load_library",
    "dump_library",
    "CHANNEL_BIBLE_ID",
    "CHANNEL_BIBLE_TEMPLATE",
]


# D-8 notebook identifier (also the dict key under library["notebooks"]).
CHANNEL_BIBLE_ID = "naberal-shorts-channel-bible"


# D-8 template verbatim from 06-CONTEXT.md §Specific Ideas + 06-RESEARCH.md §Area 2.
# created_at / updated_at are set at call time so they remain None in the template.
CHANNEL_BIBLE_TEMPLATE: dict[str, Any] = {
    "id": CHANNEL_BIBLE_ID,
    "url": "TBD-url-await-user",
    "name": "Naberal Shorts Channel Bible",
    # Korean description per D-16. ensure_ascii=False preserves literal glyphs.
    "description": (
        "Continuity Bible prefix 전용. 색상 팔레트 + 카메라 렌즈 + 시각 스타일 + 한국 시니어 타겟팅."
    ),
    "topics": [
        "continuity",
        "channel-identity",
        "korean-seniors",
        "color-palette",
        "camera-lens",
    ],
    "content_types": [],
    "use_cases": [],
    "tags": [],
    "created_at": None,
    "updated_at": None,
    "use_count": 0,
    "last_used": None,
}


def _iso_now() -> str:
    """ISO 8601 UTC timestamp with seconds precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_library(library_path: Path) -> dict:
    """Read and parse library.json (UTF-8).

    Raises FileNotFoundError with the path embedded so callers can surface which
    library.json was missing. JSON parse errors propagate as json.JSONDecodeError.
    """
    library_path = Path(library_path)
    if not library_path.exists():
        raise FileNotFoundError(f"library.json not found: {library_path}")
    return json.loads(library_path.read_text(encoding="utf-8"))


def dump_library(library_path: Path, data: dict) -> None:
    """Write library.json with indent=2 + ensure_ascii=False (UTF-8 Korean-safe).

    Trailing newline matches POSIX text-file convention + the existing
    external skill's library.json file.
    """
    library_path = Path(library_path)
    library_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_channel_bible_entry(
    library_path: Path,
    url: str = "TBD-url-await-user",
    timestamp: str | None = None,
) -> dict:
    """Idempotently append (or refresh) the channel-bible entry in library.json.

    Parameters
    ----------
    library_path : Path
        Path to the external skill's ``data/library.json`` (or any fixture with
        the same schema).
    url : str, default "TBD-url-await-user"
        NotebookLM URL. The placeholder reflects the D-8 deferred-item blocker
        (대표님 must create the notebook in the Google NotebookLM console first).
    timestamp : str | None, default None
        ISO 8601 timestamp. When None, ``datetime.now(UTC).isoformat()`` is used.
        Explicit timestamps exist primarily for deterministic unit tests.

    Returns
    -------
    dict
        The post-update library dict (also persisted to ``library_path``).

    Raises
    ------
    FileNotFoundError
        If ``library_path`` does not exist.
    KeyError
        If the parsed library JSON is missing the top-level ``notebooks`` key.
    """
    library = load_library(library_path)

    if "notebooks" not in library:
        raise KeyError(
            f"malformed library.json (missing 'notebooks' key): {library_path}"
        )

    now = timestamp or _iso_now()
    notebooks: dict[str, Any] = library["notebooks"]
    existing = notebooks.get(CHANNEL_BIBLE_ID)

    if existing is None:
        # First-time registration: build from template, fill timestamps + url.
        entry = {**CHANNEL_BIBLE_TEMPLATE}
        # Shallow copy is safe because every mutable value (lists) we then
        # reassign below or never mutate in place.
        entry["topics"] = list(CHANNEL_BIBLE_TEMPLATE["topics"])
        entry["content_types"] = list(CHANNEL_BIBLE_TEMPLATE["content_types"])
        entry["use_cases"] = list(CHANNEL_BIBLE_TEMPLATE["use_cases"])
        entry["tags"] = list(CHANNEL_BIBLE_TEMPLATE["tags"])
        entry["url"] = url
        entry["created_at"] = now
        entry["updated_at"] = now
        notebooks[CHANNEL_BIBLE_ID] = entry
    else:
        # Idempotent refresh: never clobber caller-managed state (use_count,
        # last_used) or the original created_at. Only url (if changed) and
        # updated_at are mutated. Missing template fields are backfilled for
        # forward-compat with older library.json dumps.
        for key, default in CHANNEL_BIBLE_TEMPLATE.items():
            if key not in existing:
                # Preserve list identity by deep-copying where applicable.
                if isinstance(default, list):
                    existing[key] = list(default)
                else:
                    existing[key] = default
        if existing.get("url") != url:
            existing["url"] = url
        existing["updated_at"] = now
        # created_at, use_count, last_used left untouched.

    # Refresh the top-level updated_at marker. The default-notebook pointer is
    # intentionally NOT referenced here — channel-bible must never become the
    # default (that pointer belongs to shorts-production-pipeline-bible).
    library["updated_at"] = now

    dump_library(library_path, library)
    return library
