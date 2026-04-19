"""Pydantic validation tests for Phase 5 API adapter request models.

Covers every VIDEO-01 / VIDEO-02 / D-13 / D-14 / D-17 / ORCH-11 invariant
that :mod:`scripts.orchestrator.api.models` promises to enforce at parse
time. If a contract weakens, one of these tests breaks loudly.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api.models import (
    I2VRequest,
    ShotstackRenderRequest,
    TypecastRequest,
)


# ---------------------------------------------------------------------------
# I2VRequest — VIDEO-01 / VIDEO-02 contract
# ---------------------------------------------------------------------------


def test_valid_i2v_request():
    r = I2VRequest(
        prompt="디텍티브가 문을 연다",
        anchor_frame=Path("a.png"),
        duration_seconds=5,
    )
    assert r.duration_seconds == 5
    assert r.move_count == 1
    assert r.anchor_frame == Path("a.png")


def test_duration_below_min_rejected():
    with pytest.raises(ValidationError):
        I2VRequest(
            prompt="x",
            anchor_frame=Path("a.png"),
            duration_seconds=3,
        )


def test_duration_above_max_rejected():
    with pytest.raises(ValidationError):
        I2VRequest(
            prompt="x",
            anchor_frame=Path("a.png"),
            duration_seconds=9,
        )


def test_duration_boundary_4_and_8():
    """Both endpoints of the 4-8s range are inclusive per D-14."""
    I2VRequest(prompt="x", anchor_frame=Path("a.png"), duration_seconds=4)
    I2VRequest(prompt="x", anchor_frame=Path("a.png"), duration_seconds=8)


def test_move_count_must_be_one():
    """D-14: exactly 1 move. Literal[1] rejects 0, 2, ..."""
    with pytest.raises(ValidationError):
        I2VRequest(
            prompt="x",
            anchor_frame=Path("a.png"),
            duration_seconds=5,
            move_count=2,  # type: ignore[arg-type]
        )


def test_anchor_frame_required():
    """D-13: no anchor_frame => no request."""
    with pytest.raises(ValidationError):
        I2VRequest(prompt="x", duration_seconds=5)  # type: ignore[call-arg]


def test_empty_prompt_rejected():
    with pytest.raises(ValidationError):
        I2VRequest(
            prompt="",
            anchor_frame=Path("a.png"),
            duration_seconds=5,
        )


def test_optional_style_and_negative_prompt_defaults():
    r = I2VRequest(
        prompt="x",
        anchor_frame=Path("a.png"),
        duration_seconds=5,
    )
    assert r.style_prefix is None
    assert r.negative_prompt is None


# ---------------------------------------------------------------------------
# ShotstackRenderRequest — ORCH-11 / D-17 contract
# ---------------------------------------------------------------------------


def test_shotstack_default_resolution_is_hd():
    """ORCH-11: first pass defaults to 720p."""
    r = ShotstackRenderRequest(timeline_entries=[{"x": 1}])
    assert r.resolution == "hd"


def test_shotstack_default_aspect_is_9_16():
    r = ShotstackRenderRequest(timeline_entries=[{"x": 1}])
    assert r.aspect_ratio == "9:16"


def test_shotstack_filter_order_d17():
    """D-17: color grade -> saturation -> film grain, in that order."""
    r = ShotstackRenderRequest(timeline_entries=[{"x": 1}])
    assert r.filters_order == ["color_grade", "saturation", "film_grain"]


def test_shotstack_rejects_empty_timeline():
    with pytest.raises(ValidationError):
        ShotstackRenderRequest(timeline_entries=[])


def test_shotstack_rejects_unknown_resolution():
    with pytest.raises(ValidationError):
        ShotstackRenderRequest(
            timeline_entries=[{"x": 1}],
            resolution="8k",  # type: ignore[arg-type]
        )


def test_shotstack_accepts_4k_for_opt_in_upscale():
    r = ShotstackRenderRequest(
        timeline_entries=[{"x": 1}],
        resolution="4k",
    )
    assert r.resolution == "4k"


# ---------------------------------------------------------------------------
# TypecastRequest
# ---------------------------------------------------------------------------


def test_typecast_request_valid():
    r = TypecastRequest(scene_id=0, text="탐정님, 이것은 흥미롭군요")
    assert r.emotion_style == "neutral"
    assert r.voice_id == "detective_hao"


def test_typecast_request_rejects_empty_text():
    with pytest.raises(ValidationError):
        TypecastRequest(scene_id=0, text="")


def test_typecast_request_rejects_negative_scene_id():
    with pytest.raises(ValidationError):
        TypecastRequest(scene_id=-1, text="x")
