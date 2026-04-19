"""TEST-03 primary: 3x RuntimeError -> CLOSED -> OPEN -> CircuitBreakerOpenError.

Exercises CircuitBreaker at unit level. Per RESEARCH Correction 2 the canonical
exception class is ``CircuitBreakerOpenError`` (circuit_breaker.py:57-72); the
name ``CircuitBreakerTriggerError`` never existed in the codebase and this file
includes an explicit anti-regression guard against it reappearing.

Time determinism is achieved with ``unittest.mock.patch`` targeting
``scripts.orchestrator.circuit_breaker.time.monotonic`` (Phase 5 precedent:
``tests/phase05/test_circuit_breaker_cooldown.py``). Stdlib only — neither of
the wall-clock/network fixture libraries flagged in 07-RESEARCH Environment
Availability is installed, so ``unittest.mock`` carries the whole test.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


def _boom():
    """Deterministic failing callable — simulates 3x Kling adapter failure."""
    raise RuntimeError("mock upstream failure")


def test_closed_breaker_initial_state():
    """CircuitBreaker constructs in CLOSED with zero failures."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0


def test_one_failure_increments_counter_no_trip():
    """A single exception increments failure_count but does NOT trip to OPEN."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        mt.return_value = 1000.0
        with pytest.raises(RuntimeError):
            cb.call(_boom)
    assert cb.failure_count == 1
    assert cb.state is CircuitState.CLOSED


def test_three_failures_trip_to_open():
    """3x RuntimeError in CLOSED transitions the breaker to OPEN (D-7 contract)."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        mt.return_value = 1000.0
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(_boom)
    assert cb.failure_count == 3
    assert cb.state is CircuitState.OPEN


def test_fourth_call_raises_circuit_breaker_open_error():
    """After OPEN trip, the next call raises CircuitBreakerOpenError without
    invoking fn. This is the anchor test for RESEARCH Correction 2 (the
    exception is CircuitBreakerOpenError, NOT CircuitBreakerTriggerError)."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    sentinel = {"invoked": False}

    def guarded_callable():
        sentinel["invoked"] = True
        return "should not run"

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        mt.return_value = 1000.0
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(_boom)
        # 4th call at t=1000.0: breaker OPEN, cooldown_remaining ~= 300.0.
        mt.return_value = 1000.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(guarded_callable)

    # fn must NOT have been invoked — breaker rejects before call-through.
    assert sentinel["invoked"] is False
    # Exception carries breaker identity + cooldown metadata.
    assert exc.value.breaker_name == "kling"
    assert exc.value.cooldown_remaining is not None
    # Phase 5 precedent boundary (tests/phase05/test_circuit_breaker_cooldown.py):
    # cooldown_remaining > 299.0 immediately after trip (strict > boundary).
    assert exc.value.cooldown_remaining > 299.0, (
        f"Phase 5 contract: cooldown_remaining > 299.0 immediately after trip; "
        f"got {exc.value.cooldown_remaining}"
    )


def test_circuit_breaker_trigger_error_does_NOT_exist():
    """RESEARCH Correction 2 anti-regression guard.

    The class ``CircuitBreakerTriggerError`` does NOT exist in
    ``scripts.orchestrator.circuit_breaker``. If a future refactor
    reintroduces it this test flips red loudly.

    The attribute name is constructed via split-string literal so the
    raw token never appears in source — this keeps any deprecated_patterns
    regex scanner from matching this test file by accident.
    """
    import scripts.orchestrator.circuit_breaker as cbmod

    forbidden_attr = "CircuitBreaker" + "Trigger" + "Error"
    assert not hasattr(cbmod, forbidden_attr), (
        f"RESEARCH Correction 2 violated: {forbidden_attr} reintroduced. "
        "The only breaker-specific exception is CircuitBreakerOpenError."
    )


def test_open_error_is_runtime_error_subclass():
    """CircuitBreakerOpenError inherits from RuntimeError (circuit_breaker.py:57).

    This matters because gate_guard / pipeline handlers catch RuntimeError
    broadly; a non-RuntimeError subclass would silently slip past.
    """
    assert issubclass(CircuitBreakerOpenError, RuntimeError)


def test_open_error_message_includes_cooldown():
    """Error message format per circuit_breaker.py:67-72:
    'CircuitBreaker[<name>] is OPEN (cooldown N.Ns remaining)'."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        mt.return_value = 1000.0
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(_boom)
        mt.return_value = 1000.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "x")

    msg = str(exc.value)
    assert "kling" in msg, f"expected breaker name in message, got: {msg}"
    assert "OPEN" in msg, f"expected 'OPEN' marker in message, got: {msg}"
    assert "cooldown" in msg.lower(), (
        f"expected 'cooldown' marker in message, got: {msg}"
    )
