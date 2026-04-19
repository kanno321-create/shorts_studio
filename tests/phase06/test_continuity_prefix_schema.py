"""Plan 06-06 Task 2 — ContinuityPrefix pydantic v2 schema tests.

D-20: Continuity Bible prefix schema enforces D-10 5-component coverage at
parse time. This test module exercises every boundary the model claims
(extra=forbid, HexColor pattern, palette length 3-5, warmth / focal_length
/ aperture ranges, visual_style Literal, bgm_mood Literal, audience_profile
min_length) so schema regressions surface immediately.

Pitfall 5 (RESEARCH §Pitfall 5): prefix.json drift vs pydantic model is a
silent-render bug generator unless both sides fail loudly at parse time.
These tests lock the pydantic side; test_prefix_json_serialization.py locks
the JSON side.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api.models import ContinuityPrefix, HexColor  # noqa: F401


VALID_PAYLOAD = {
    "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
    "warmth": 0.2,
    "focal_length_mm": 35,
    "aperture_f": 2.8,
    "visual_style": "cinematic",
    "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
    "bgm_mood": "ambient",
}


def test_valid_payload_parses():
    m = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    assert m.focal_length_mm == 35
    assert m.visual_style == "cinematic"
    assert m.bgm_mood == "ambient"
    assert len(m.color_palette) == 3
    assert m.warmth == 0.2
    assert m.aperture_f == 2.8


def test_extra_field_forbidden():
    """extra='forbid' surfaces prefix.json drift at parse time (Pitfall 5)."""
    bad = dict(VALID_PAYLOAD, extra_field="should be rejected")
    with pytest.raises(ValidationError, match="extra"):
        ContinuityPrefix.model_validate(bad)


def test_color_palette_min_length():
    bad = dict(VALID_PAYLOAD, color_palette=["#1A2E4A", "#C8A660"])  # len 2
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_color_palette_max_length():
    bad = dict(
        VALID_PAYLOAD,
        color_palette=[
            "#111111",
            "#222222",
            "#333333",
            "#444444",
            "#555555",
            "#666666",  # len 6 > 5
        ],
    )
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_color_palette_invalid_hex():
    bad = dict(VALID_PAYLOAD, color_palette=["#GGGGGG", "#C8A660", "#E4E4E4"])
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_color_palette_hex_no_hash():
    bad = dict(VALID_PAYLOAD, color_palette=["1A2E4A", "#C8A660", "#E4E4E4"])
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_color_palette_hex_too_short():
    """5-digit hex rejected (must be exactly 6)."""
    bad = dict(VALID_PAYLOAD, color_palette=["#1A2E4", "#C8A660", "#E4E4E4"])
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_warmth_lower_bound():
    bad = dict(VALID_PAYLOAD, warmth=-1.5)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_warmth_upper_bound():
    bad = dict(VALID_PAYLOAD, warmth=1.5)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_warmth_boundary_accepted():
    """Exactly ±1.0 should be accepted (inclusive bounds)."""
    for w in (-1.0, 1.0, 0.0):
        m = ContinuityPrefix.model_validate(dict(VALID_PAYLOAD, warmth=w))
        assert m.warmth == w


def test_focal_length_below_min():
    bad = dict(VALID_PAYLOAD, focal_length_mm=10)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_focal_length_above_max():
    bad = dict(VALID_PAYLOAD, focal_length_mm=200)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_focal_length_boundaries_accepted():
    """Exactly 18 and 85 should be accepted."""
    for f in (18, 85):
        m = ContinuityPrefix.model_validate(dict(VALID_PAYLOAD, focal_length_mm=f))
        assert m.focal_length_mm == f


def test_aperture_below_min():
    bad = dict(VALID_PAYLOAD, aperture_f=1.0)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_aperture_above_max():
    bad = dict(VALID_PAYLOAD, aperture_f=22.0)
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_aperture_boundaries_accepted():
    """Exactly 1.4 and 16.0 should be accepted."""
    for a in (1.4, 16.0):
        m = ContinuityPrefix.model_validate(dict(VALID_PAYLOAD, aperture_f=a))
        assert m.aperture_f == a


def test_visual_style_invalid_literal():
    bad = dict(VALID_PAYLOAD, visual_style="retro")
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_bgm_mood_invalid_literal():
    bad = dict(VALID_PAYLOAD, bgm_mood="melancholy")
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_audience_profile_too_short():
    """D-16 requires substantive descriptor — min_length=10."""
    bad = dict(VALID_PAYLOAD, audience_profile="short")
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_missing_required_field_color_palette():
    bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "color_palette"}
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_missing_all_d10_components():
    """Only visual_style present — all other required fields should fail."""
    bad = {"visual_style": "cinematic"}
    with pytest.raises(ValidationError):
        ContinuityPrefix.model_validate(bad)


def test_all_three_visual_styles_accepted():
    for style in ("photorealistic", "cinematic", "documentary"):
        m = ContinuityPrefix.model_validate(dict(VALID_PAYLOAD, visual_style=style))
        assert m.visual_style == style


def test_all_three_bgm_moods_accepted():
    for mood in ("ambient", "tension", "uplift"):
        m = ContinuityPrefix.model_validate(dict(VALID_PAYLOAD, bgm_mood=mood))
        assert m.bgm_mood == mood


def test_model_dump_round_trip():
    m1 = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    dumped = m1.model_dump()
    m2 = ContinuityPrefix.model_validate(dumped)
    assert m2.model_dump() == dumped


def test_model_dump_json_round_trip():
    """JSON round trip (Plan 07 adapter path — model_validate_json + model_dump_json)."""
    m1 = ContinuityPrefix.model_validate(VALID_PAYLOAD)
    json_str = m1.model_dump_json()
    m2 = ContinuityPrefix.model_validate_json(json_str)
    assert m2.model_dump() == m1.model_dump()


def test_existing_models_not_broken():
    """Regression: Phase 5 I2VRequest + ShotstackRenderRequest still importable."""
    from scripts.orchestrator.api.models import (  # noqa: F401
        I2VRequest,
        ShotstackRenderRequest,
        TypecastRequest,
    )
