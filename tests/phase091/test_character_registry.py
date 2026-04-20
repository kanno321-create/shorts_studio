"""RED stub for REQ-091-03 — Wave 1 CharacterRegistry + CharacterEntry target.

Frozen contract:
    CharacterEntry (pydantic BaseModel, extra=forbid): name, ref_path, description, tags
    CharacterRegistry: load() / get() / get_reference_path() / list_all()
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_registry_importable() -> None:
    """REQ-091-03: CharacterRegistry + CharacterEntry are importable."""
    from scripts.orchestrator.character_registry import (  # noqa: F401
        CharacterEntry,
        CharacterRegistry,
    )


def test_load_missing_raises(tmp_registry_path: Path) -> None:
    """REQ-091-03: missing registry.json raises FileNotFoundError with Korean message."""
    from scripts.orchestrator.character_registry import CharacterRegistry

    with pytest.raises(FileNotFoundError, match="레지스트리"):
        CharacterRegistry(tmp_registry_path).load()


def test_character_entry_schema_drift_rejected() -> None:
    """REQ-091-03: pydantic extra='forbid' — unknown fields raise ValidationError."""
    from pydantic import ValidationError

    from scripts.orchestrator.character_registry import CharacterEntry

    with pytest.raises(ValidationError):
        CharacterEntry(name="x", ref_path="y.png", unknown_field="bad")  # type: ignore[call-arg]


def test_get_reference_path_resolves_relative(
    tmp_registry_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-091-03: relative ref_path resolves against registry.json parent dir."""
    from scripts.orchestrator.character_registry import CharacterRegistry

    sample = tmp_registry_path.parent / "sample.png"
    sample.write_bytes(fixture_png_bytes)
    tmp_registry_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "characters": [
                    {"name": "sample", "ref_path": "sample.png", "description": "", "tags": []}
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = CharacterRegistry(tmp_registry_path).load()
    assert reg.get_reference_path("sample").exists()


def test_list_all_returns_names(
    tmp_registry_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-091-03: list_all returns set of all character names."""
    from scripts.orchestrator.character_registry import CharacterRegistry

    for name in ("a", "b"):
        (tmp_registry_path.parent / f"{name}.png").write_bytes(fixture_png_bytes)
    tmp_registry_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "characters": [
                    {"name": "a", "ref_path": "a.png", "description": "", "tags": []},
                    {"name": "b", "ref_path": "b.png", "description": "", "tags": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = CharacterRegistry(tmp_registry_path).load()
    assert set(reg.list_all()) == {"a", "b"}
