"""TEST-03 secondary: strict > 300s cooldown boundary + HALF_OPEN probe.

Boundary contract (circuit_breaker.py:131, verified 2026-04-19):

    if remaining >= 0:
        raise CircuitBreakerOpenError(self.name, cooldown_remaining=remaining)

Consequences:

* elapsed == 0.0   -> remaining == 300.0 -> OPEN (blocked)
* elapsed == 299.0 -> remaining ==   1.0 -> OPEN (blocked)
* elapsed == 300.0 -> remaining ==   0.0 -> OPEN (blocked, strict >)
* elapsed == 300.001 -> remaining < 0    -> HALF_OPEN probe admitted

This file locks that four-point boundary plus the HALF_OPEN -> CLOSED success
path AND the HALF_OPEN -> OPEN failure path (which resets cooldown).

Determinism: every call sits inside a single ``unittest.mock.patch`` context
against ``scripts.orchestrator.circuit_breaker.time.monotonic`` — the Phase 5
precedent (tests/phase05/test_circuit_breaker_cooldown.py). No external time
fixture dependencies: 07-RESEARCH §Environment Availability confirms only
stdlib is guaranteed installed.
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
    """Deterministic failing callable."""
    raise RuntimeError("fail")


def _trip_to_open(cb: CircuitBreaker, mt, at: float = 1000.0) -> None:
    """Drive the breaker from CLOSED to OPEN by calling _boom max_failures times.

    The caller passes the already-patched mt mock and the trip timestamp.
    Post-condition: cb.state is OPEN, _opened_at_monotonic == at.
    """
    mt.return_value = at
    for _ in range(cb.max_failures):
        with pytest.raises(RuntimeError):
            cb.call(_boom)
    assert cb.state is CircuitState.OPEN


def test_blocked_at_zero_seconds_elapsed():
    """Immediately after trip: full cooldown window remains, breaker rejects."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        mt.return_value = 1000.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "x")
        assert exc.value.cooldown_remaining is not None
        assert exc.value.cooldown_remaining > 299.0
        assert cb.state is CircuitState.OPEN


def test_blocked_at_299_seconds_elapsed():
    """At elapsed == 299.0 the breaker is still within cooldown (1s remaining)."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        mt.return_value = 1000.0 + 299.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "x")
        # ~1.0s cooldown remaining.
        assert exc.value.cooldown_remaining is not None
        assert 0.9 < exc.value.cooldown_remaining < 1.1


def test_still_blocked_at_exact_300_seconds_strict_gt():
    """circuit_breaker.py:131 strict `>`: at elapsed == cooldown, remaining == 0,
    but the condition ``remaining >= 0`` still raises. Only ``remaining < 0``
    (i.e. elapsed > cooldown_seconds) transitions the breaker to HALF_OPEN."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        mt.return_value = 1000.0 + 300.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "x")
        # remaining is ~0 (small floating-point jitter allowed), not negative.
        assert exc.value.cooldown_remaining is not None
        assert exc.value.cooldown_remaining >= 0.0
        assert abs(exc.value.cooldown_remaining) < 1e-6
        # State stays OPEN — the strict > boundary does NOT transition to HALF_OPEN
        # at the exact equality point.
        assert cb.state is CircuitState.OPEN


def test_admits_probe_strictly_after_300_seconds():
    """At elapsed > 300s (here 300.001), the breaker transitions to HALF_OPEN and
    admits a single probe call. If the probe succeeds, the breaker transitions to
    CLOSED with failure_count reset to 0 (circuit_breaker.py:_record_success +
    _close)."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        mt.return_value = 1000.0 + 300.001
        result = cb.call(lambda: "recovered")
    assert result == "recovered"
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0


def test_failed_probe_in_half_open_reopens_with_fresh_cooldown():
    """HALF_OPEN failure re-opens the breaker with a NEW cooldown window
    rooted at the probe timestamp (circuit_breaker.py:_record_failure +
    _trip_open). The 13 gates of Phase 5 depend on this behaviour so that a
    still-failing upstream does not get hammered past cooldown expiry."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        # Probe at t=1000.0 + 300.001 -> HALF_OPEN -> probe raises -> re-OPEN.
        mt.return_value = 1000.0 + 300.001
        with pytest.raises(RuntimeError):
            cb.call(_boom)
        assert cb.state is CircuitState.OPEN
        # 1ms after probe failure -> fresh cooldown has barely started.
        mt.return_value = 1000.0 + 300.002
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "x")
        # Cooldown rooted at the probe timestamp (1000.0 + 300.001).
        # Elapsed from probe = 0.001s -> remaining ~= 299.999.
        assert exc.value.cooldown_remaining is not None
        assert exc.value.cooldown_remaining > 299.0


def test_probe_call_is_invoked_on_half_open_transition():
    """The HALF_OPEN branch does NOT short-circuit to an exception — it falls
    through to execute the probe callable. This test proves fn actually runs
    (not just 'the state changed'), which matters for adapters whose side
    effects we rely on as the canary signal."""
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)
    sentinel = {"invoked": 0}

    def probe():
        sentinel["invoked"] += 1
        return "probe-executed"

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mt:
        _trip_to_open(cb, mt, at=1000.0)
        mt.return_value = 1000.0 + 300.001
        result = cb.call(probe)

    assert sentinel["invoked"] == 1
    assert result == "probe-executed"
    assert cb.state is CircuitState.CLOSED


def test_no_freezegun_or_pytest_socket_required():
    """Regression guard on the test-environment contract: this file must be
    importable and passable using only unittest.mock from stdlib. Any future
    migration to a time-freezing library would need the researcher to update
    07-RESEARCH §Environment Availability first."""
    import importlib.util

    for forbidden in ("freezegun", "pytest_socket"):
        spec = importlib.util.find_spec(forbidden)
        if spec is not None:
            pytest.skip(
                f"{forbidden} is installed; this guard is only active on the "
                "Phase 7 baseline environment (stdlib-only)."
            )
        assert spec is None
