"""Phase 6 Plan 04 — library.json channel-bible append helper tests (WIKI-03 D-8).

Validates `scripts.notebooklm.library.add_channel_bible_entry`:
- Appends naberal-shorts-channel-bible without modifying shorts-production-pipeline-bible
- Idempotency (1st=create, Nth=update updated_at only; preserves created_at/use_count/last_used)
- active_notebook_id never mutated
- Korean description survives UTF-8 round-trip (ensure_ascii=False)
- Schema shape matches D-8 + RESEARCH §Area 2 (12 keys, topics len=5, use_count=0, last_used=null)
- Error surface (missing file -> FileNotFoundError; malformed -> KeyError)
- Fixture tests/phase06/fixtures/library_json_delta.json aligns with CHANNEL_BIBLE_TEMPLATE
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.notebooklm.library import (
    CHANNEL_BIBLE_ID,
    CHANNEL_BIBLE_TEMPLATE,
    add_channel_bible_entry,
    load_library,
)


def _seed_library(path: Path) -> None:
    """Write a minimal library.json with only the existing pipeline-bible notebook."""
    data = {
        "notebooks": {
            "shorts-production-pipeline-bible": {
                "id": "shorts-production-pipeline-bible",
                "url": "https://notebooklm.google.com/notebook/existing-uuid",
                "name": "Shorts Production Pipeline Bible",
                "description": "production pipeline",
                "topics": ["shorts", "production"],
                "content_types": [],
                "use_cases": [],
                "tags": [],
                "created_at": "2026-04-07T00:00:00+00:00",
                "updated_at": "2026-04-07T00:00:00+00:00",
                "use_count": 10,
                "last_used": "2026-04-15T10:00:00+00:00",
            },
        },
        "active_notebook_id": "shorts-production-pipeline-bible",
        "updated_at": "2026-04-07T00:00:00+00:00",
    }
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def test_add_to_library_with_only_existing_notebook(tmp_path: Path):
    """1st call creates channel-bible entry; existing notebook untouched byte-identical."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    before_existing = load_library(lib)["notebooks"]["shorts-production-pipeline-bible"]

    result = add_channel_bible_entry(lib, timestamp="2026-04-19T12:00:00+00:00")

    assert "shorts-production-pipeline-bible" in result["notebooks"]
    assert CHANNEL_BIBLE_ID in result["notebooks"]
    # Existing entry unchanged (dict equality -> every field preserved)
    after_existing = result["notebooks"]["shorts-production-pipeline-bible"]
    assert after_existing == before_existing
    # New entry has the placeholder URL
    assert result["notebooks"][CHANNEL_BIBLE_ID]["url"] == "TBD-url-await-user"
    assert result["notebooks"][CHANNEL_BIBLE_ID]["created_at"] == "2026-04-19T12:00:00+00:00"
    assert result["notebooks"][CHANNEL_BIBLE_ID]["updated_at"] == "2026-04-19T12:00:00+00:00"


def test_idempotent_same_url_preserves_created_at(tmp_path: Path):
    """2nd call with identical url: updated_at refreshed; created_at preserved."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    add_channel_bible_entry(lib, timestamp="2026-04-19T12:00:00+00:00")
    updated = add_channel_bible_entry(lib, timestamp="2026-04-19T13:00:00+00:00")
    entry = updated["notebooks"][CHANNEL_BIBLE_ID]
    assert entry["created_at"] == "2026-04-19T12:00:00+00:00"
    assert entry["updated_at"] == "2026-04-19T13:00:00+00:00"


def test_different_url_updates_url_preserves_created_at(tmp_path: Path):
    """Calling with a new URL updates url + updated_at but preserves created_at."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    add_channel_bible_entry(
        lib, url="TBD-url-await-user", timestamp="2026-04-19T12:00:00+00:00"
    )
    updated = add_channel_bible_entry(
        lib,
        url="https://notebooklm.google.com/notebook/real-uuid-xxxx",
        timestamp="2026-04-19T14:00:00+00:00",
    )
    entry = updated["notebooks"][CHANNEL_BIBLE_ID]
    assert entry["url"] == "https://notebooklm.google.com/notebook/real-uuid-xxxx"
    assert entry["created_at"] == "2026-04-19T12:00:00+00:00"
    assert entry["updated_at"] == "2026-04-19T14:00:00+00:00"


def test_idempotent_preserves_use_count_and_last_used(tmp_path: Path):
    """2nd call must not reset use_count / last_used (caller-managed state)."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    add_channel_bible_entry(lib, timestamp="2026-04-19T12:00:00+00:00")
    # Simulate downstream consumer bumping use_count + last_used
    data = load_library(lib)
    data["notebooks"][CHANNEL_BIBLE_ID]["use_count"] = 5
    data["notebooks"][CHANNEL_BIBLE_ID]["last_used"] = "2026-04-19T12:30:00+00:00"
    lib.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # Second add_channel_bible_entry call must preserve the bumped values
    updated = add_channel_bible_entry(lib, timestamp="2026-04-19T13:00:00+00:00")
    entry = updated["notebooks"][CHANNEL_BIBLE_ID]
    assert entry["use_count"] == 5
    assert entry["last_used"] == "2026-04-19T12:30:00+00:00"


def test_active_notebook_id_not_changed(tmp_path: Path):
    """add_channel_bible_entry must never hijack the default notebook pointer."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    before_active = load_library(lib)["active_notebook_id"]
    result = add_channel_bible_entry(lib)
    assert result["active_notebook_id"] == before_active == "shorts-production-pipeline-bible"


def test_korean_description_preserved_utf8(tmp_path: Path):
    """Korean literals must survive JSON round-trip (ensure_ascii=False)."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    add_channel_bible_entry(lib)
    raw = lib.read_text(encoding="utf-8")
    assert "한국 시니어 타겟팅" in raw
    # Verify the NEW entry's description is not \uXXXX-escaped in the file.
    data = json.loads(raw)
    entry = data["notebooks"][CHANNEL_BIBLE_ID]
    # The entry dict has the literal Korean string
    assert "한국 시니어 타겟팅" in entry["description"]


def test_missing_notebooks_key_raises(tmp_path: Path):
    """Malformed library (no 'notebooks' key) raises KeyError with 'notebooks' in message."""
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps({"updated_at": "2026-04-19"}), encoding="utf-8")
    with pytest.raises(KeyError, match="notebooks"):
        add_channel_bible_entry(lib)


def test_nonexistent_library_path_raises(tmp_path: Path):
    """Missing file raises FileNotFoundError with library.json mentioned."""
    with pytest.raises(FileNotFoundError, match="library.json"):
        add_channel_bible_entry(tmp_path / "does_not_exist.json")


def test_schema_shape_of_new_entry(tmp_path: Path):
    """New entry has exactly the 12 expected keys per D-8 schema."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    result = add_channel_bible_entry(lib)
    entry = result["notebooks"][CHANNEL_BIBLE_ID]
    expected_keys = {
        "id",
        "url",
        "name",
        "description",
        "topics",
        "content_types",
        "use_cases",
        "tags",
        "created_at",
        "updated_at",
        "use_count",
        "last_used",
    }
    assert set(entry.keys()) == expected_keys


def test_topics_list_length_5_matches_d8(tmp_path: Path):
    """D-8 template specifies exactly 5 topics."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    result = add_channel_bible_entry(lib)
    topics = result["notebooks"][CHANNEL_BIBLE_ID]["topics"]
    assert len(topics) == 5
    assert topics == [
        "continuity",
        "channel-identity",
        "korean-seniors",
        "color-palette",
        "camera-lens",
    ]


def test_use_count_starts_zero_last_used_null(tmp_path: Path):
    """Fresh entry has use_count=0 and last_used=None (serialized as JSON null)."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    result = add_channel_bible_entry(lib)
    entry = result["notebooks"][CHANNEL_BIBLE_ID]
    assert entry["use_count"] == 0
    assert entry["last_used"] is None
    # Verify null on disk too
    raw = lib.read_text(encoding="utf-8")
    assert '"last_used": null' in raw


def test_second_call_does_not_duplicate_key(tmp_path: Path):
    """Two calls -> exactly 2 notebooks (existing + channel-bible), not 3."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    add_channel_bible_entry(lib)
    add_channel_bible_entry(lib)
    final = load_library(lib)
    assert len(final["notebooks"]) == 2
    assert set(final["notebooks"].keys()) == {
        "shorts-production-pipeline-bible",
        CHANNEL_BIBLE_ID,
    }


def test_entry_id_matches_constant(tmp_path: Path):
    """New entry's internal id field matches CHANNEL_BIBLE_ID constant."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    result = add_channel_bible_entry(lib)
    assert result["notebooks"][CHANNEL_BIBLE_ID]["id"] == CHANNEL_BIBLE_ID
    assert CHANNEL_BIBLE_ID == "naberal-shorts-channel-bible"


def test_fixture_delta_matches_template(library_json_delta: dict):
    """Fixture library_json_delta.json must align structurally with CHANNEL_BIBLE_TEMPLATE."""
    entry = library_json_delta[CHANNEL_BIBLE_ID]
    # All template keys present in fixture
    for key in CHANNEL_BIBLE_TEMPLATE:
        assert key in entry, f"fixture missing template key: {key}"


def test_library_updated_at_refreshed(tmp_path: Path):
    """Top-level library['updated_at'] is refreshed to the timestamp."""
    lib = tmp_path / "library.json"
    _seed_library(lib)
    result = add_channel_bible_entry(lib, timestamp="2026-04-19T15:00:00+00:00")
    assert result["updated_at"] == "2026-04-19T15:00:00+00:00"
