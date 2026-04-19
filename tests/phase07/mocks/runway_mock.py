"""Deterministic Runway Gen-3 Alpha Turbo I2V adapter mock for Phase 7.

Shadows scripts.orchestrator.api.runway_i2v.RunwayI2VAdapter.image_to_video.
Same fault injection semantics as :class:`KlingMock` (D-3 + D-17). Used by
the Kling→Runway failover scenario tests (TEST-03 secondary path) — the
Kling mock raises ``runway_failover`` once, ShortsPipeline catches, then
instantiates this RunwayMock which returns a successful path on first call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_RUNWAY_VIDEO = _FIXTURES / "mock_runway.mp4"


@dataclass
class RunwayMock:
    """Mock for scripts.orchestrator.api.runway_i2v.RunwayI2VAdapter."""

    fault_mode: Optional[Literal["circuit_3x", "runway_failover"]] = None
    allow_fault_injection: bool = False
    call_count: int = field(default=0)
    fixture_path: Path = field(default_factory=lambda: _RUNWAY_VIDEO)

    def _maybe_inject_fault(self) -> None:
        if not self.allow_fault_injection or self.fault_mode is None:
            return
        self.call_count += 1
        if self.fault_mode == "circuit_3x" and self.call_count <= 3:
            raise RuntimeError(f"mock Runway circuit_3x failure #{self.call_count}")
        if self.fault_mode == "runway_failover" and self.call_count == 1:
            raise RuntimeError("mock Runway runway_failover #1")

    def image_to_video(self, *args, **kwargs) -> Path:
        self._maybe_inject_fault()
        if not self.allow_fault_injection:
            self.call_count += 1
        return self.fixture_path


__all__ = ["RunwayMock"]
