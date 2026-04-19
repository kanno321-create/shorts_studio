"""Plan 06-06 Task 2 — prefix.json <-> ContinuityPrefix drift detection.

Pitfall 5 (RESEARCH §Pitfall 5): ``wiki/continuity_bible/prefix.json`` and
``ContinuityPrefix`` pydantic v2 model must stay byte-level synchronised.
Drift between the two is a silent-render bug — Shotstack adapter loads the
JSON at render time so a rogue key survives until an actual render attempt.

These tests assert:
    1. prefix.json exists at the canonical path
    2. Its contents parse through ``ContinuityPrefix.model_validate``
    3. UTF-8 Korean literal is preserved (no \\uXXXX escaping)
    4. Every HEX color in prefix.json is documented in channel_identity.md
    5. ``model_validate_json`` path works (the path Plan 07 uses)
    6. Adding a rogue field to a COPY trips ``extra='forbid'`` (drift guard)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api.models import ContinuityPrefix


def test_prefix_json_file_exists(repo_root: Path):
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    assert p.exists(), f"Plan 06 must maintain {p}"


def test_prefix_json_loads_through_model(repo_root: Path):
    """Pitfall 5: prefix.json out of sync with schema = render failure. Guard at CI."""
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    m = ContinuityPrefix.model_validate(data)
    assert m.visual_style in ("photorealistic", "cinematic", "documentary")
    assert m.bgm_mood in ("ambient", "tension", "uplift")
    assert 3 <= len(m.color_palette) <= 5


def test_prefix_json_is_valid_utf8_korean(repo_root: Path):
    """D-16 Korean senior descriptor literal must be human-readable (not \\uXXXX)."""
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    raw = p.read_text(encoding="utf-8")
    assert "한국 시니어" in raw, (
        "D-16 Korean senior descriptor literal missing (or \\uXXXX escaped)"
    )


def test_prefix_json_has_exact_seven_keys(repo_root: Path):
    """Plan 06 contract — prefix.json exposes EXACTLY the 7 D-20 fields.

    Any extra keys would fail ContinuityPrefix.model_validate (extra=forbid)
    at parse time. This asserts the set equality up-front for a clearer
    failure mode when drift is introduced.
    """
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    expected = {
        "color_palette",
        "warmth",
        "focal_length_mm",
        "aperture_f",
        "visual_style",
        "audience_profile",
        "bgm_mood",
    }
    assert set(data.keys()) == expected, (
        f"prefix.json keys diverge from D-20 schema: "
        f"unexpected={set(data.keys()) - expected}, missing={expected - set(data.keys())}"
    )


def test_prefix_json_values_match_channel_identity(repo_root: Path):
    """prefix.json HEX palette must be documented in channel_identity.md (D-10)."""
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    identity_text = (
        repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    ).read_text(encoding="utf-8")
    # Every HEX color in prefix.json must appear in channel_identity.md
    for hex_color in data["color_palette"]:
        assert hex_color in identity_text, (
            f"{hex_color} missing from channel_identity.md"
        )


def test_prefix_json_via_model_validate_json(repo_root: Path):
    """Pydantic JSON parse path (Plan 07 uses this via ContinuityPrefix.model_validate_json)."""
    p = repo_root / "wiki" / "continuity_bible" / "prefix.json"
    raw = p.read_text(encoding="utf-8")
    m = ContinuityPrefix.model_validate_json(raw)
    # Spot-check a couple of key fields to prove full round-trip
    assert m.focal_length_mm == 35
    assert m.warmth == 0.2
    assert m.visual_style == "cinematic"


def test_prefix_json_drift_detection(tmp_path: Path):
    """If a developer adds a rogue field, ContinuityPrefix (extra=forbid) blocks load."""
    bad = tmp_path / "bad_prefix.json"
    bad.write_text(
        json.dumps(
            {
                "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
                "warmth": 0.2,
                "focal_length_mm": 35,
                "aperture_f": 2.8,
                "visual_style": "cinematic",
                "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
                "bgm_mood": "ambient",
                "rogue_field": "breaks adapter",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate_json(bad.read_text(encoding="utf-8"))
