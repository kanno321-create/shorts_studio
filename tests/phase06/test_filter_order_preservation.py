"""D-19 Shotstack filter-order invariant — dedicated regression guard.

The canonical D-19 contract after preset injection:

    filters_order == ["continuity_prefix", "color_grade", "saturation", "film_grain"]

* ``continuity_prefix`` = FIRST (D-19 Phase 6 addition, first-in-chain)
* ``color_grade → saturation → film_grain`` = Phase 5 D-17 tail —
  MUST remain contiguous and in that exact order.

Pitfall 4 (06-RESEARCH lines 1275-1280) explicitly warns against re-arranging
the filter list; this suite exists to fail loudly at the first drift.
"""
from __future__ import annotations

from pathlib import Path

from scripts.orchestrator.api import shotstack
from scripts.orchestrator.api.models import ContinuityPrefix


CANONICAL_PREFIX = ContinuityPrefix.model_validate(
    {
        "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
        "warmth": 0.2,
        "focal_length_mm": 35,
        "aperture_f": 2.8,
        "visual_style": "cinematic",
        "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
        "bgm_mood": "ambient",
    }
)


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


def test_d19_filter_order_exact_equality(monkeypatch) -> None:
    """D-19 canonical: injection yields exact 4-element ordered list.

    Asserts byte-identical list equality:
        ['continuity_prefix', 'color_grade', 'saturation', 'film_grain']
    """
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: CANONICAL_PREFIX
    )
    adapter = shotstack.ShotstackAdapter(api_key="test")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    assert payload["timeline"]["filters"] == [
        "continuity_prefix",
        "color_grade",
        "saturation",
        "film_grain",
    ]


def test_d17_tail_contiguous_after_injection(monkeypatch) -> None:
    """D-17 Phase 5 tail remains contiguous + ordered after D-19 prepend."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: CANONICAL_PREFIX
    )
    adapter = shotstack.ShotstackAdapter(api_key="test")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    filters = payload["timeline"]["filters"]
    idx_cg = filters.index("color_grade")
    idx_sat = filters.index("saturation")
    idx_fg = filters.index("film_grain")
    assert idx_sat == idx_cg + 1, "saturation must immediately follow color_grade"
    assert idx_fg == idx_sat + 1, "film_grain must immediately follow saturation"


def test_caller_supplied_order_prepended_not_replaced(monkeypatch) -> None:
    """Prefix is PREPENDED; the caller's tail is preserved verbatim."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: CANONICAL_PREFIX
    )
    adapter = shotstack.ShotstackAdapter(api_key="test")
    custom_tail = ["color_grade", "saturation", "film_grain", "vignette"]
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=custom_tail,
    )
    filters = payload["timeline"]["filters"]
    assert filters[0] == "continuity_prefix"
    assert filters[1:] == custom_tail


def test_no_injection_does_not_break_empty_filters_order(monkeypatch) -> None:
    """Edge case: empty filters_order + no preset → still empty, no crash."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: None
    )
    adapter = shotstack.ShotstackAdapter(api_key="test")
    payload = adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=[],
    )
    assert payload["timeline"]["filters"] == []


def test_injection_without_mutating_caller_list(monkeypatch) -> None:
    """Caller's filters_order list must not be mutated in place."""
    monkeypatch.setattr(
        shotstack, "_load_continuity_preset", lambda path=None: CANONICAL_PREFIX
    )
    adapter = shotstack.ShotstackAdapter(api_key="test")
    caller_list = ["color_grade", "saturation", "film_grain"]
    adapter._build_timeline_payload(
        serialised_entries=_sample_entries(),
        resolution="hd",
        aspect_ratio="9:16",
        filters_order=caller_list,
    )
    assert caller_list == ["color_grade", "saturation", "film_grain"]


def test_phase5_shotstack_adapter_still_imports() -> None:
    """Regression: Phase 5 Plan 05-06 public symbols still available."""
    from scripts.orchestrator.api.shotstack import ShotstackAdapter  # noqa: F401

    # Class-level D-17 tuple unchanged
    assert ShotstackAdapter.FILTER_ORDER == (
        "color_grade",
        "saturation",
        "film_grain",
    )
    assert ShotstackAdapter.DEFAULT_RESOLUTION == "hd"
    assert ShotstackAdapter.DEFAULT_ASPECT == "9:16"
