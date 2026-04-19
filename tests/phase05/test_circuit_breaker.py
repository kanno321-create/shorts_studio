"""Tests for CircuitBreaker state machine (Plan 05-02, ORCH-06).

Covers CLOSED -> OPEN -> HALF_OPEN -> CLOSED | OPEN transitions per
CONTEXT D-6. Uses monotonic-time mocking for determinism.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


# ---------------------------------------------------------------------------
# Construction & defaults
# ---------------------------------------------------------------------------


def test_default_construction_starts_closed():
    """A fresh breaker is CLOSED with zero failure count."""
    cb = CircuitBreaker(name="kling")
    assert cb.name == "kling"
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.max_failures == 3
    assert cb.cooldown_seconds == 300


def test_custom_thresholds_respected():
    cb = CircuitBreaker(name="runway", max_failures=5, cooldown_seconds=60)
    assert cb.max_failures == 5
    assert cb.cooldown_seconds == 60


# ---------------------------------------------------------------------------
# CLOSED state behaviour
# ---------------------------------------------------------------------------


def test_closed_state_allows_successful_call():
    cb = CircuitBreaker(name="kling")
    result = cb.call(lambda x: x + 1, 41)
    assert result == 42
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0


def test_closed_state_propagates_exceptions_and_increments_failure_count():
    cb = CircuitBreaker(name="kling")

    def boom():
        raise RuntimeError("upstream 5xx")

    with pytest.raises(RuntimeError, match="upstream 5xx"):
        cb.call(boom)

    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 1


def test_closed_success_resets_failure_count():
    cb = CircuitBreaker(name="kling")

    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        cb.call(boom)
    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.failure_count == 2

    # Successful call resets the counter.
    cb.call(lambda: "ok")
    assert cb.failure_count == 0
    assert cb.state is CircuitState.CLOSED


# ---------------------------------------------------------------------------
# CLOSED -> OPEN transition
# ---------------------------------------------------------------------------


def test_transitions_to_open_after_max_failures():
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)

    def boom():
        raise RuntimeError("fail")

    for _ in range(3):
        with pytest.raises(RuntimeError):
            cb.call(boom)

    assert cb.state is CircuitState.OPEN
    assert cb.failure_count == 3


def test_open_state_short_circuits_calls():
    """OPEN breaker raises CircuitBreakerOpenError without invoking fn."""
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    def boom():
        raise RuntimeError("fail")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            cb.call(boom)
    assert cb.state is CircuitState.OPEN

    called = {"count": 0}

    def tracer():
        called["count"] += 1
        return "unreachable"

    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        cb.call(tracer)

    assert called["count"] == 0
    assert "kling" in str(exc_info.value)


def test_open_error_carries_breaker_name():
    cb = CircuitBreaker(name="runway", max_failures=1)

    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.state is CircuitState.OPEN

    try:
        cb.call(lambda: None)
    except CircuitBreakerOpenError as err:
        assert err.breaker_name == "runway"
    else:  # pragma: no cover - defensive
        pytest.fail("Expected CircuitBreakerOpenError")


# ---------------------------------------------------------------------------
# HALF_OPEN transitions
# ---------------------------------------------------------------------------


def test_half_open_success_closes_breaker():
    """After cooldown, first successful call transitions OPEN -> CLOSED."""
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    def boom():
        raise RuntimeError("x")

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 1000.0
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(boom)
        assert cb.state is CircuitState.OPEN

        # Advance past cooldown window.
        mock_time.return_value = 1000.0 + 301.0
        result = cb.call(lambda: "recovered")

    assert result == "recovered"
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0


def test_half_open_failure_reopens_breaker():
    """Failure during HALF_OPEN snaps back to OPEN with fresh cooldown."""
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    def boom():
        raise RuntimeError("x")

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 2000.0
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(boom)
        assert cb.state is CircuitState.OPEN

        # Advance past cooldown, retry fails.
        mock_time.return_value = 2000.0 + 301.0
        with pytest.raises(RuntimeError):
            cb.call(boom)

        assert cb.state is CircuitState.OPEN

        # Second attempt still within new cooldown must short-circuit.
        mock_time.return_value = 2000.0 + 302.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")


# ---------------------------------------------------------------------------
# call() argument forwarding
# ---------------------------------------------------------------------------


def test_call_forwards_args_and_kwargs():
    cb = CircuitBreaker(name="kling")

    def add(a, b, *, c=0):
        return a + b + c

    assert cb.call(add, 1, 2, c=3) == 6


# ---------------------------------------------------------------------------
# to_dict serialization (consumed by Checkpointer)
# ---------------------------------------------------------------------------


def test_to_dict_serializes_closed_state():
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    snapshot = cb.to_dict()

    assert snapshot == {
        "name": "kling",
        "state": "closed",
        "failure_count": 0,
        "max_failures": 3,
        "cooldown_seconds": 300,
        "opened_at": None,
    }


def test_to_dict_serializes_open_state_with_iso_timestamp():
    cb = CircuitBreaker(name="runway", max_failures=1, cooldown_seconds=60)

    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        cb.call(boom)

    snapshot = cb.to_dict()
    assert snapshot["name"] == "runway"
    assert snapshot["state"] == "open"
    assert snapshot["failure_count"] == 1
    assert snapshot["max_failures"] == 1
    assert snapshot["cooldown_seconds"] == 60
    # opened_at must be an ISO-8601 UTC string (JSON-friendly primitive).
    assert isinstance(snapshot["opened_at"], str)
    assert snapshot["opened_at"].endswith("Z") or "+" in snapshot["opened_at"]


def test_to_dict_values_are_json_primitives():
    """to_dict must return only JSON-serializable primitives for Checkpointer."""
    import json

    cb = CircuitBreaker(name="kling", max_failures=1)

    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        cb.call(boom)

    # Round-trip through json confirms no datetime / enum leakage.
    blob = json.dumps(cb.to_dict())
    restored = json.loads(blob)
    assert restored["state"] == "open"
    assert restored["name"] == "kling"
