"""Deterministic Kling I2V adapter mock for Phase 7 integration tests.

Per CONTEXT D-16 + D-3: returns fixed Path on success, optional fault injection
controlled by ``allow_fault_injection`` (production-safe default False).

Per RESEARCH Correction 2: raises plain ``RuntimeError`` (never a
breaker-trigger subclass, which does not exist) on injected failures. The
breaker itself emits ``CircuitBreakerOpenError`` after 3 raises in Plan 07-05.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_KLING_VIDEO = _FIXTURES / "mock_kling.mp4"


@dataclass
class KlingMock:
    """Mock for scripts.orchestrator.api.kling_i2v.KlingI2VAdapter.

    Shadows the real adapter's ``image_to_video(prompt, anchor_frame,
    duration_seconds)`` signature. Accepts ``*args, **kwargs`` so tests
    that do not construct I2VRequest-style inputs still succeed — the
    real adapter validates inputs; the mock validates only that the
    call arrives.
    """

    fault_mode: Optional[Literal["circuit_3x", "runway_failover"]] = None
    allow_fault_injection: bool = False
    call_count: int = field(default=0)
    fixture_path: Path = field(default_factory=lambda: _KLING_VIDEO)

    def _maybe_inject_fault(self) -> None:
        if not self.allow_fault_injection or self.fault_mode is None:
            return
        self.call_count += 1
        if self.fault_mode == "circuit_3x" and self.call_count <= 3:
            raise RuntimeError(f"mock Kling circuit_3x failure #{self.call_count}")
        if self.fault_mode == "runway_failover" and self.call_count == 1:
            raise RuntimeError("mock Kling runway_failover #1")

    def image_to_video(self, *args, **kwargs) -> Path:
        self._maybe_inject_fault()
        # Success path: return deterministic fixture path.
        if not self.allow_fault_injection:
            self.call_count += 1
        return self.fixture_path


__all__ = ["KlingMock"]
