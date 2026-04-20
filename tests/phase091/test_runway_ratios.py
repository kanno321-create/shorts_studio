"""RED stub for REQ-091-05 — Wave 1 RunwayI2VAdapter VALID_RATIOS_BY_MODEL.

Frozen contract additions (Wave 1 Plan 04):
    VALID_RATIOS_BY_MODEL: dict[str, list[str]]
    RunwayI2VAdapter(api_key, model, ratio, ...)  # constructor gains model + ratio
"""
from __future__ import annotations

import pytest


def test_valid_ratios_dict_exists() -> None:
    """REQ-091-05: VALID_RATIOS_BY_MODEL contains gen3a_turbo + gen4.5 per D-12."""
    from scripts.orchestrator.api.runway_i2v import VALID_RATIOS_BY_MODEL

    assert "gen3a_turbo" in VALID_RATIOS_BY_MODEL
    assert "gen4.5" in VALID_RATIOS_BY_MODEL
    assert "768:1280" in VALID_RATIOS_BY_MODEL["gen3a_turbo"]
    assert "720:1280" in VALID_RATIOS_BY_MODEL["gen4.5"]


def test_unknown_model_raises_korean() -> None:
    """REQ-091-05: unknown model raises ValueError with '알 수 없는 model' Korean substring."""
    from scripts.orchestrator.api.runway_i2v import RunwayI2VAdapter

    with pytest.raises(ValueError, match="알 수 없는 model"):
        RunwayI2VAdapter(api_key="k", model="nonsense")


def test_invalid_ratio_for_gen45_raises() -> None:
    """REQ-091-05: gen4.5 + unsupported ratio (768:1280) raises ValueError."""
    from scripts.orchestrator.api.runway_i2v import RunwayI2VAdapter

    with pytest.raises(ValueError):
        RunwayI2VAdapter(api_key="k", model="gen4.5", ratio="768:1280")


def test_ratio_auto_selects_first_valid() -> None:
    """REQ-091-05: when ratio not given, adapter selects first valid ratio for model."""
    from scripts.orchestrator.api.runway_i2v import RunwayI2VAdapter

    adapter = RunwayI2VAdapter(api_key="k", model="gen3a_turbo")
    assert adapter.ratio == "16:9"
