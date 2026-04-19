"""CircuitBreaker for the Orchestrator v2 write-path (ORCH-06).

Implements the CLOSED / OPEN / HALF_OPEN state machine specified in
``.planning/phases/05-orchestrator-v2-write/05-CONTEXT.md`` (D-6).

Design goals
------------
* **Stdlib-only.** No third-party dependencies; `tenacity` may be layered
  INSIDE a CLOSED breaker for transient retries by call sites, but the
  breaker core stays pure.
* **Deterministic.** Cooldown timing uses ``time.monotonic`` so tests can
  patch a single symbol (``scripts.orchestrator.circuit_breaker.time``)
  without wall-clock flakiness.
* **Checkpointer-friendly.** ``to_dict()`` returns only JSON primitives
  (strings, ints, None) — the ``opened_at`` timestamp is rendered as an
  ISO-8601 UTC string so Plan 05-03's Checkpointer can serialise the
  breaker snapshot without bespoke encoders.

Contract summary
----------------
* ``CLOSED`` → invokes ``fn``. Consecutive failures increment
  ``failure_count``; any success resets it. After ``max_failures``
  consecutive failures the breaker transitions to ``OPEN``.
* ``OPEN`` → ``call()`` raises ``CircuitBreakerOpenError`` without
  invoking ``fn`` until ``cooldown_seconds`` elapses on the monotonic
  clock (strict ``>``). After that it transitions to ``HALF_OPEN``.
* ``HALF_OPEN`` → admits exactly one probe call. Success → ``CLOSED``
  with ``failure_count`` cleared. Failure → back to ``OPEN`` with a
  fresh cooldown window rooted at the probe timestamp.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
]


class CircuitState(str, Enum):
    """Finite states for the breaker. Inherits from ``str`` so the
    value serialises trivially via ``to_dict`` without custom encoders.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a caller hits an OPEN breaker.

    Carries the breaker ``name`` so upstream handlers (ORCH-04 failure
    journal, ORCH-05 gate guard) can log which adapter tripped.
    """

    def __init__(self, breaker_name: str, cooldown_remaining: Optional[float] = None):
        self.breaker_name = breaker_name
        self.cooldown_remaining = cooldown_remaining
        suffix = (
            f" (cooldown {cooldown_remaining:.1f}s remaining)"
            if cooldown_remaining is not None
            else ""
        )
        super().__init__(f"CircuitBreaker[{breaker_name}] is OPEN{suffix}")


@dataclass
class CircuitBreaker:
    """Synchronous circuit breaker.

    Parameters
    ----------
    name:
        Human-readable identifier (``"kling"``, ``"runway"``…) used in
        error messages and checkpoint snapshots.
    max_failures:
        Consecutive failures in ``CLOSED`` that trigger ``OPEN``.
        Defaults to 3 per D-6.
    cooldown_seconds:
        Seconds the breaker stays ``OPEN`` before admitting a probe.
        Defaults to 300 (5 minutes) per D-6.
    """

    name: str
    max_failures: int = 3
    cooldown_seconds: int = 300
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    failure_count: int = field(default=0, init=False)
    # Monotonic timestamp of the most recent OPEN transition. ``None``
    # while the breaker is CLOSED.
    _opened_at_monotonic: Optional[float] = field(default=None, init=False, repr=False)
    # Wall-clock timestamp of the most recent OPEN transition, rendered
    # to ISO-8601 by ``to_dict`` for Checkpointer serialisation.
    _opened_at_wall: Optional[datetime] = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute ``fn(*args, **kwargs)`` subject to breaker policy.

        Behaviour by state:

        * ``CLOSED`` — runs ``fn``; increments failure count on exception,
          resets on success, flips to ``OPEN`` once the failure threshold
          is reached.
        * ``OPEN`` — checks the cooldown on ``time.monotonic``. If still
          within the window, raises :class:`CircuitBreakerOpenError`
          without invoking ``fn``. Otherwise transitions to ``HALF_OPEN``
          and falls through to execute a probe call.
        * ``HALF_OPEN`` — single probe: success closes the breaker,
          failure re-opens it with a fresh cooldown.
        """

        if self.state is CircuitState.OPEN:
            remaining = self._cooldown_remaining()
            if remaining > 0:
                raise CircuitBreakerOpenError(self.name, cooldown_remaining=remaining)
            # Cooldown elapsed → transition to HALF_OPEN and execute probe.
            self.state = CircuitState.HALF_OPEN

        try:
            result = fn(*args, **kwargs)
        except BaseException:
            self._record_failure()
            raise
        else:
            self._record_success()
            return result

    # ------------------------------------------------------------------
    # Serialisation for Checkpointer (Plan 05-03)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-primitive snapshot of breaker state.

        The Checkpointer embeds this dict directly in the run manifest;
        all values must therefore be ``str``, ``int``, or ``None`` — no
        ``datetime`` or ``Enum`` instances.
        """

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "cooldown_seconds": self.cooldown_seconds,
            "opened_at": (
                self._opened_at_wall.isoformat().replace("+00:00", "Z")
                if self._opened_at_wall is not None
                else None
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_failure(self) -> None:
        if self.state is CircuitState.HALF_OPEN:
            # Probe failed -> immediately back to OPEN with fresh cooldown.
            self._trip_open()
            return

        # CLOSED: count failures, trip on threshold.
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self._trip_open()

    def _record_success(self) -> None:
        if self.state is CircuitState.HALF_OPEN:
            # Probe succeeded -> fully close the breaker.
            self._close()
            return
        # CLOSED: reset the failure counter on any success.
        self.failure_count = 0

    def _trip_open(self) -> None:
        self.state = CircuitState.OPEN
        self._opened_at_monotonic = time.monotonic()
        self._opened_at_wall = datetime.now(timezone.utc)

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self._opened_at_monotonic = None
        self._opened_at_wall = None

    def _cooldown_remaining(self) -> float:
        """Seconds left in the current OPEN cooldown window.

        Returns ``0.0`` (or a negative value) once the cooldown has
        elapsed; ``call()`` treats ``> 0`` as "still blocked" so the
        boundary is strict.
        """

        if self._opened_at_monotonic is None:
            return 0.0
        elapsed = time.monotonic() - self._opened_at_monotonic
        return float(self.cooldown_seconds) - elapsed
