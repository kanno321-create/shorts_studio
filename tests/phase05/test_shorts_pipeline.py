"""Contract tests for ShortsPipeline __init__ and method surface (Plan 07).

Covers:
    - Every operational GATE has a ``_run_<gate>`` method
    - ``GATE_INSPECTORS`` covers all 13 operational gates
    - ``__init__`` wires 5 CircuitBreakers with D-6 defaults (3 / 300s)
    - ``max_retries_per_gate`` defaults to 3 (D-12)
    - ``_transition_to_complete`` raises :class:`IncompleteDispatch`
      when no gates are dispatched
    - Default invokers raise :class:`NotImplementedError`
    - No forbidden tokens (skip_gates / t2v / TODO next-session) in source
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.orchestrator import (
    GATE_INSPECTORS,
    GateName,
    IncompleteDispatch,
    ShortsPipeline,
    Verdict,
)


def _make_pipeline(tmp_path: Path, **overrides) -> ShortsPipeline:
    kwargs: dict = dict(
        session_id="s_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=MagicMock(),
        producer_invoker=MagicMock(return_value={"artifact_path": "/tmp/x"}),
        supervisor_invoker=MagicMock(
            return_value=Verdict(
                result="PASS",
                score=90,
                evidence=[],
                semantic_feedback="",
                inspector_name="shorts-supervisor",
            )
        ),
        asset_sourcer_invoker=MagicMock(return_value=Path("/tmp/stock.png")),
    )
    kwargs.update(overrides)
    return ShortsPipeline(**kwargs)


def test_pipeline_has_13_gate_methods(tmp_path: Path) -> None:
    """Every operational GateName has a ``_run_<name>`` method on the class."""

    pipeline = _make_pipeline(tmp_path)
    for gate in GateName:
        if gate in (GateName.IDLE, GateName.COMPLETE):
            continue
        method_name = f"_run_{gate.name.lower()}"
        assert hasattr(pipeline, method_name), (
            f"ShortsPipeline missing {method_name} for {gate.name}"
        )


def test_gate_inspectors_covers_all_operational() -> None:
    """``GATE_INSPECTORS`` keys equal the operational GateName set (13 entries)."""

    operational = {
        g.name
        for g in GateName
        if g not in (GateName.IDLE, GateName.COMPLETE)
    }
    assert set(GATE_INSPECTORS.keys()) == operational
    assert len(GATE_INSPECTORS) == 13


def test_init_wires_5_circuit_breakers(tmp_path: Path) -> None:
    """5 breakers (kling/runway/typecast/elevenlabs/shotstack) at D-6 defaults."""

    pipeline = _make_pipeline(tmp_path)
    assert pipeline.kling_breaker.name == "kling"
    assert pipeline.runway_breaker.name == "runway"
    assert pipeline.typecast_breaker.name == "typecast"
    assert pipeline.elevenlabs_breaker.name == "elevenlabs"
    assert pipeline.shotstack_breaker.name == "shotstack"
    for breaker in (
        pipeline.kling_breaker,
        pipeline.runway_breaker,
        pipeline.typecast_breaker,
        pipeline.elevenlabs_breaker,
        pipeline.shotstack_breaker,
    ):
        assert breaker.max_failures == 3
        assert breaker.cooldown_seconds == 300


def test_max_retries_default_is_3(tmp_path: Path) -> None:
    """D-12 regeneration ceiling defaults to 3 retries per gate."""

    pipeline = _make_pipeline(tmp_path)
    assert pipeline.max_retries == 3


def test_incomplete_dispatch_raises_on_complete_before_any_gate(
    tmp_path: Path,
) -> None:
    """_transition_to_complete raises IncompleteDispatch on empty dispatched set."""

    pipeline = _make_pipeline(tmp_path)
    with pytest.raises(IncompleteDispatch):
        pipeline._transition_to_complete()


@pytest.fixture
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Populate all five API env vars so adapter __init__ doesn't raise ValueError."""

    for var in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        monkeypatch.setenv(var, "fake")


def test_default_producer_invoker_raises_not_implemented(
    tmp_path: Path, _fake_env: None
) -> None:
    """The default producer_invoker rejects calls with NotImplementedError."""

    pipeline = ShortsPipeline(
        session_id="s_test", state_root=tmp_path / "state"
    )
    with pytest.raises(NotImplementedError):
        pipeline._default_producer_invoker("trend-collector", "TREND", {})


def test_default_supervisor_invoker_raises_not_implemented(
    tmp_path: Path, _fake_env: None
) -> None:
    """The default supervisor_invoker rejects calls with NotImplementedError."""

    pipeline = ShortsPipeline(
        session_id="s_test", state_root=tmp_path / "state"
    )
    with pytest.raises(NotImplementedError):
        pipeline._default_supervisor_invoker(GateName.TREND, {})


def test_default_asset_sourcer_raises_not_implemented(
    tmp_path: Path, _fake_env: None
) -> None:
    """The default asset_sourcer_invoker rejects calls with NotImplementedError."""

    pipeline = ShortsPipeline(
        session_id="s_test", state_root=tmp_path / "state"
    )
    with pytest.raises(NotImplementedError):
        pipeline._default_asset_sourcer("a prompt")


def test_pipeline_source_has_no_forbidden_tokens() -> None:
    """Physical D-8 / D-9 / D-13 invariants on the source file.

    The keystone file must not contain the forbidden tokens anywhere
    (docstrings, comments, or code). This test runs grep as a meta-check
    to catch accidental regressions; the Hook blocks them at write time,
    this test confirms post-write.
    """

    src = Path("scripts/orchestrator/shorts_pipeline.py").read_text(
        encoding="utf-8"
    )
    assert "skip_gates" not in src, "D-8 violated in shorts_pipeline.py"
    # D-13: case-insensitive absence of the whole family.
    assert "text_to_video" not in src, "D-13 text_to_video violated"
    assert "text2video" not in src, "D-13 text2video violated"
    # t2v as a case-insensitive isolated token (not part of words).
    import re

    assert not re.search(
        r"(?<![A-Za-z_])t2v(?![A-Za-z_])", src, flags=re.IGNORECASE
    ), "D-13 t2v literal present"
    assert "TODO(next-session)" not in src, "D-9 violated"


def test_gate_context_default_state(tmp_path: Path) -> None:
    """GateContext initial state is empty collections + session_id."""

    pipeline = _make_pipeline(tmp_path)
    ctx = pipeline.ctx
    assert ctx.session_id == "s_test"
    assert ctx.config == {}
    assert ctx.channel_bible == {}
    assert ctx.retry_counts == {}
    assert ctx.artifacts == {}
    assert ctx.audio_segments == []
    assert ctx.video_cuts == []
    assert ctx.fallback_indices == []


def test_line_count_is_within_budget() -> None:
    """ORCH-01 / D-1: shorts_pipeline.py stays in [500, 800] lines."""

    src = Path("scripts/orchestrator/shorts_pipeline.py")
    line_count = sum(1 for _ in src.open(encoding="utf-8"))
    assert 500 <= line_count <= 800, (
        f"shorts_pipeline.py is {line_count} lines (must be in [500, 800])"
    )
