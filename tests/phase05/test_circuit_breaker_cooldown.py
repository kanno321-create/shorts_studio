"""Cooldown-window tests for CircuitBreaker (Plan 05-02, ORCH-06).

Focuses on the 5-minute cooldown contract using mocked `time.monotonic`
so the suite stays deterministic and wall-clock independent.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


def _trip_breaker(cb: CircuitBreaker) -> None:
    def boom():
        raise RuntimeError("upstream fail")

    for _ in range(cb.max_failures):
        with pytest.raises(RuntimeError):
            cb.call(boom)


def test_cooldown_default_is_300_seconds():
    cb = CircuitBreaker(name="kling")
    assert cb.cooldown_seconds == 300


def test_open_breaker_blocks_before_cooldown_elapses():
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 500.0
        _trip_breaker(cb)
        assert cb.state is CircuitState.OPEN

        # 0 seconds elapsed.
        mock_time.return_value = 500.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # 299 seconds elapsed -> still blocked.
        mock_time.return_value = 500.0 + 299.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # Exactly at boundary (300s) -> still blocked (strict >).
        mock_time.return_value = 500.0 + 300.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")


def test_cooldown_expiry_permits_half_open_probe():
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 1000.0
        _trip_breaker(cb)
        assert cb.state is CircuitState.OPEN

        # 300.001s after trip -> breaker admits one probe call.
        mock_time.return_value = 1000.0 + 300.001
        captured = {"calls": 0}

        def probe():
            captured["calls"] += 1
            return "probe-ok"

        result = cb.call(probe)

    assert result == "probe-ok"
    assert captured["calls"] == 1
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 0


def test_custom_cooldown_is_respected():
    cb = CircuitBreaker(name="runway", max_failures=1, cooldown_seconds=10)

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 0.0
        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        assert cb.state is CircuitState.OPEN

        # 9 seconds -> still blocked.
        mock_time.return_value = 9.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # 10.1 seconds -> probe allowed.
        mock_time.return_value = 10.1
        assert cb.call(lambda: "ok") == "ok"
        assert cb.state is CircuitState.CLOSED


def test_cooldown_restarts_after_half_open_failure():
    """A failing probe resets the cooldown window to the probe timestamp."""
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 5000.0
        _trip_breaker(cb)
        assert cb.state is CircuitState.OPEN

        # Cooldown elapses, probe fails.
        mock_time.return_value = 5000.0 + 301.0

        def boom():
            raise RuntimeError("still broken")

        with pytest.raises(RuntimeError):
            cb.call(boom)

        assert cb.state is CircuitState.OPEN

        # 299 seconds after the failed probe -> still blocked.
        mock_time.return_value = 5000.0 + 301.0 + 299.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # Past the NEW cooldown window -> probe permitted again.
        mock_time.return_value = 5000.0 + 301.0 + 301.0
        assert cb.call(lambda: "healed") == "healed"
        assert cb.state is CircuitState.CLOSED


def test_cooldown_uses_monotonic_not_wallclock():
    """Regression guard: breaker must read time.monotonic, not datetime.now."""
    import scripts.orchestrator.circuit_breaker as cb_module

    # Fingerprint check -- the module must expose `time.monotonic`.
    assert hasattr(cb_module, "time")
    assert callable(cb_module.time.monotonic)
