"""D-9 / D-19: ShotstackAdapter Continuity Prefix injection — unit tests.

Covers:
    * _load_continuity_preset() lazy loader contract
        - returns ContinuityPrefix when prefix.json exists + validates
        - returns None when prefix.json absent (graceful degradation, no raise)
        - raises pydantic.ValidationError on schema drift (extra field)
        - raises pydantic.ValidationError on invalid HEX palette entries
        - DEFAULT_CONTINUITY_PRESET_PATH points at wiki/continuity_bible/prefix.json
        - real wiki/continuity_bible/prefix.json loads through default path

    * ShotstackAdapter._build_timeline_payload injection seam
        - preset loaded → filters_order[0] == "continuity_prefix"
        - preset None → filters_order unchanged
        - caller pre-prepended prefix → no duplication (idempotent)
        - timeline payload contains continuity_preset = preset.model_dump()

The D-17 Phase 5 tail order (color_grade → saturation → film_grain) must
remain contiguous and unchanged after injection — D-19 canonical invariant.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api import shotstack
from scripts.orchestrator.api.models import ContinuityPrefix


VALID_PAYLOAD: dict = {
    "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
    "warmth": 0.2,
    "focal_length_mm": 35,
    "aperture_f": 2.8,
    "visual_style": "cinematic",
    "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
    "bgm_mood": "ambient",
}


def _write_prefix_json(tmp_path: Path, payload: dict | None = None) -> Path:
    p = tmp_path / "prefix.json"
    p.write_text(
        json.dumps(payload or VALID_PAYLOAD, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


def _sample_entries() -> list[dict]:
    return [
        {
            "kind": "clip",
            "start": 0.0,
            "end": 1.0,
            "clip_path": "/tmp/x.mp4",
            "speed": 1.0,
            "audio_path": "/tmp/a.mp3",
        }
    ]


# ---------------------------------------------------------------------------
# _load_continuity_preset — loader contract
# ---------------------------------------------------------------------------


def test_load_preset_returns_none_when_missing(tmp_path: Path) -> None:
    """Missing path → None, no raise (D-19 graceful degradation)."""
    missing = tmp_path / "nope.json"
    assert shotstack._load_continuity_preset(path=missing) is None


def test_load_preset_returns_model_when_valid(tmp_path: Path) -> None:
    """Valid prefix.json → ContinuityPrefix instance with parsed fields."""
    p = _write_prefix_json(tmp_path)
    preset = shotstack._load_continuity_preset(path=p)
    assert isinstance(preset, ContinuityPrefix)
    assert preset.visual_style == "cinematic"
    assert preset.focal_length_mm == 35
    assert preset.bgm_mood == "ambient"


def test_load_preset_raises_on_schema_drift(tmp_path: Path) -> None:
    """extra='forbid' fails fast on rogue JSON keys (Pitfall 5)."""
    bad = dict(VALID_PAYLOAD, rogue_field="surprise")
    p = _write_prefix_json(tmp_path, bad)
    with pytest.raises(ValidationError):
        shotstack._load_continuity_preset(path=p)


def test_load_preset_raises_on_invalid_hex(tmp_path: Path) -> None:
    """HexColor regex blocks malformed palette entries."""
    bad = dict(VALID_PAYLOAD, color_palette=["#NOTHEX", "#C8A660", "#E4E4E4"])
    p = _write_prefix_json(tmp_path, bad)
    with pytest.raises(ValidationError):
        shotstack._load_continuity_preset(path=p)


def test_default_path_points_at_wiki_continuity_bible() -> None:
    """D-9: DEFAULT_CONTINUITY_PRESET_PATH canonical location."""
    assert (
        str(shotstack.DEFAULT_CONTINUITY_PRESET_PATH).replace("\\", "/").endswith(
            "wiki/continuity_bible/prefix.json"
        )
    )


def test_real_prefix_json_loads_via_default(repo_root: Path, monkeypatch) -> None:
    """Plan 06 Task 1 wiki/continuity_bible/prefix.json loads via module default."""
    monkeypatch.chdir(repo_root)
    preset = shotstack._load_continuity_preset()
    assert preset is not None
    assert preset.visual_style in ("photorealistic", "cinematic", "documentary")
    assert preset.bgm_mood in ("ambient", "tension", "uplift")


# ---------------------------------------------------------------------------
# ShotstackAdapter._build_timeline_payload — injection seam
# ---------------------------------------------------------------------------


def test_adapter_injects_prefix_at_position_zero(monkeypatch) -> None:
    """Preset loaded → filters_order[0] == 'continuity_prefix' (D-19)."""
    fake = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: fake
    )
    adapter = shotstack.ShotstackAdapter(api_key="test_key")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    filters = payload["timeline"]["filters"]
    assert filters[0] == "continuity_prefix"
    assert filters == [
        "continuity_prefix",
        "color_grade",
        "saturation",
        "film_grain",
    ]


def test_adapter_no_injection_when_preset_missing(monkeypatch) -> None:
    """preset None → filters_order unchanged (graceful degradation)."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: None
    )
    adapter = shotstack.ShotstackAdapter(api_key="test_key")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    filters = payload["timeline"]["filters"]
    assert "continuity_prefix" not in filters
    assert filters == ["color_grade", "saturation", "film_grain"]


def test_adapter_idempotent_against_caller_prepend(monkeypatch) -> None:
    """Caller already includes continuity_prefix → no duplication."""
    fake = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: fake
    )
    adapter = shotstack.ShotstackAdapter(api_key="test_key")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=[
            "continuity_prefix",
            "color_grade",
            "saturation",
            "film_grain",
        ],
    )
    filters = payload["timeline"]["filters"]
    assert filters.count("continuity_prefix") == 1
    assert filters == [
        "continuity_prefix",
        "color_grade",
        "saturation",
        "film_grain",
    ]


def test_timeline_payload_includes_continuity_preset_dump(monkeypatch) -> None:
    """timeline['continuity_preset'] = preset.model_dump() when preset loaded."""
    fake = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: fake
    )
    adapter = shotstack.ShotstackAdapter(api_key="test_key")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    preset_dump = payload["timeline"].get("continuity_preset")
    assert preset_dump is not None
    assert preset_dump["visual_style"] == "cinematic"
    assert preset_dump["focal_length_mm"] == 35
    assert preset_dump["color_palette"] == ["#1A2E4A", "#C8A660", "#E4E4E4"]


def test_timeline_payload_continuity_preset_none_when_missing(monkeypatch) -> None:
    """preset None → timeline['continuity_preset'] = None (explicit key present)."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: None
    )
    adapter = shotstack.ShotstackAdapter(api_key="test_key")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    assert payload["timeline"]["continuity_preset"] is None
