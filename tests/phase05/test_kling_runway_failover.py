"""Integration test for the VIDEO-04 Kling -> Runway failover contract.

The pipeline (Plan 07) owns the failover try/except; this test proves the
building blocks — :class:`CircuitBreaker` + both adapter seams — compose
correctly so Plan 07's wrapper will just work.

Scenarios covered:

1. Kling breaker trips OPEN after one failure; the next call raises
   :class:`CircuitBreakerOpenError` without invoking Kling; pipeline pattern
   catches it and routes to Runway.
2. Both circuits OPEN => the fallback attempt raises
   :class:`CircuitBreakerOpenError` too (no silent degradation).
3. Adapter-level exception (Kling raises, breaker still CLOSED): caller
   can still swap in Runway.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.api.kling_i2v import KlingI2VAdapter
from scripts.orchestrator.api.runway_i2v import RunwayI2VAdapter
from scripts.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
)


def _raise(exc: Exception):
    """Helper: return a zero-arg callable that raises ``exc`` when invoked."""

    def _inner():
        raise exc

    return _inner


# ---------------------------------------------------------------------------
# 1. Kling breaker OPEN -> pipeline pattern falls over to Runway.
# ---------------------------------------------------------------------------


def test_failover_pattern_kling_open_runway_called(tmp_path):
    """Simulate the VIDEO-04 failover contract.

    Kling breaker trips OPEN on a single failure (max_failures=1). The next
    call through the Kling breaker raises :class:`CircuitBreakerOpenError`
    without invoking the Kling function. Plan 07's pipeline catches the
    error and runs the Runway branch.
    """

    kling_breaker = CircuitBreaker("kling", max_failures=1)
    runway_breaker = CircuitBreaker("runway", max_failures=3)

    # Trip Kling: one failure is enough at max_failures=1.
    with pytest.raises(RuntimeError):
        kling_breaker.call(_raise(RuntimeError("kling 500")))
    from scripts.orchestrator.circuit_breaker import CircuitState

    assert kling_breaker.state is CircuitState.OPEN

    # Confirm OPEN short-circuits: the lambda would return "should-not-run"
    # but the breaker must raise before invoking it.
    def _kling_would_succeed():
        return tmp_path / "kling.mp4"

    with pytest.raises(CircuitBreakerOpenError):
        kling_breaker.call(_kling_would_succeed)

    # Pipeline pattern: catch CircuitBreakerOpenError, route to Runway.
    runway_called: list[bool] = []

    def _runway_success():
        runway_called.append(True)
        return tmp_path / "runway_output.mp4"

    try:
        result = kling_breaker.call(_kling_would_succeed)
    except CircuitBreakerOpenError:
        result = runway_breaker.call(_runway_success)

    assert runway_called == [True]
    assert result.name == "runway_output.mp4"


# ---------------------------------------------------------------------------
# 2. Both breakers OPEN -> the fallback also raises (no silent degrade).
# ---------------------------------------------------------------------------


def test_both_circuits_open_raises_circuit_open():
    kling_breaker = CircuitBreaker("kling", max_failures=1)
    runway_breaker = CircuitBreaker("runway", max_failures=1)

    with pytest.raises(RuntimeError):
        kling_breaker.call(_raise(RuntimeError("kling fail")))
    with pytest.raises(RuntimeError):
        runway_breaker.call(_raise(RuntimeError("runway fail")))

    # Pipeline wrapper: when the fallback also short-circuits, the caller
    # gets CircuitBreakerOpenError (Plan 07 translates it to RegenerationExhausted
    # via the failure journal; see Plan 05-02 SUMMARY).
    with pytest.raises(CircuitBreakerOpenError):
        try:
            kling_breaker.call(lambda: "x")
        except CircuitBreakerOpenError:
            runway_breaker.call(lambda: "y")


# ---------------------------------------------------------------------------
# 3. Adapter-level exception: caller swaps in Runway.
# ---------------------------------------------------------------------------


@patch("scripts.orchestrator.api.kling_i2v.KlingI2VAdapter._submit_and_poll")
@patch("scripts.orchestrator.api.runway_i2v.RunwayI2VAdapter._invoke_runway")
def test_adapter_level_failover(mock_runway, mock_kling, tmp_path):
    """Kling adapter raises; caller catches and runs the Runway adapter."""

    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"x")
    mock_kling.side_effect = RuntimeError("kling 500")
    mock_runway.return_value = tmp_path / "runway.mp4"

    kling = KlingI2VAdapter(api_key="fake-k")
    runway = RunwayI2VAdapter(api_key="fake-r")

    # Inline failover: Plan 07's pipeline will own this try/except.
    try:
        result = kling.image_to_video(prompt="x", anchor_frame=anchor, duration_seconds=5)
    except RuntimeError:
        result = runway.image_to_video(prompt="x", anchor_frame=anchor, duration_seconds=5)

    assert result.name == "runway.mp4"
    mock_kling.assert_called_once()
    mock_runway.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Breaker snapshot round-trip (Plan 05-03 Checkpointer consumer).
# ---------------------------------------------------------------------------


def test_breaker_snapshot_survives_serialisation():
    """CircuitBreaker.to_dict must stay JSON-primitive so Plan 05-03 can
    embed a Kling-breaker snapshot in the manifest and restore the failover
    state across process boundaries."""

    import json

    kling_breaker = CircuitBreaker("kling", max_failures=1)
    with pytest.raises(RuntimeError):
        kling_breaker.call(_raise(RuntimeError("fail")))

    snap = kling_breaker.to_dict()
    roundtrip = json.loads(json.dumps(snap))
    assert roundtrip["name"] == "kling"
    assert roundtrip["state"] == "open"
    assert isinstance(roundtrip["failure_count"], int)
