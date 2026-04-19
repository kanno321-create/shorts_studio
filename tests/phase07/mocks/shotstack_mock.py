"""Deterministic Shotstack adapter mock for Phase 7.

Shadows scripts.orchestrator.api.shotstack.ShotstackAdapter methods used by
shorts_pipeline:

* :meth:`render` — ``render(payload_or_timeline) -> dict`` (v2 envelope).
  The real adapter signature is ``render(timeline: list, resolution, aspect_ratio)``
  but the mock accepts ``*args, **kwargs`` so either calling convention works.
* :meth:`upscale` — Phase 5 NOOP returning ``{"status": "skipped", ...}``.
* :meth:`create_ken_burns_clip` — ORCH-12 Fallback lane (standalone
  Shotstack POST per RESEARCH Correction 3). Returns a local :class:`Path`
  to the downloaded MP4 fixture.

Per D-20 the render response conforms to the real Shotstack v2 envelope:
``{"response": {"id": str, "url": str, "message": "Created"},
"success": True, "status": "done"}``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_RENDER_MP4 = _FIXTURES / "mock_shotstack.mp4"
_KENBURNS_MP4 = _FIXTURES / "mock_shotstack.mp4"  # same placeholder


@dataclass
class ShotstackMock:
    """Mock for scripts.orchestrator.api.shotstack.ShotstackAdapter."""

    allow_fault_injection: bool = False
    render_call_count: int = field(default=0)
    upscale_call_count: int = field(default=0)
    ken_burns_call_count: int = field(default=0)
    render_path: Path = field(default_factory=lambda: _RENDER_MP4)
    ken_burns_path: Path = field(default_factory=lambda: _KENBURNS_MP4)
    last_render_payload: Optional[object] = field(default=None)
    last_ken_burns_args: Optional[dict] = field(default=None)

    def render(self, payload=None, *args, **kwargs) -> dict:
        self.render_call_count += 1
        self.last_render_payload = payload
        return {
            "response": {
                "id": f"mock_shotstack_{self.render_call_count:03d}",
                "url": f"file://{self.render_path.as_posix()}",
                "message": "Created",
            },
            "success": True,
            "status": "done",
            "url": f"file://{self.render_path.as_posix()}",
            "id": f"mock_shotstack_{self.render_call_count:03d}",
        }

    def upscale(self, *args, **kwargs) -> dict:
        self.upscale_call_count += 1
        return {"status": "skipped", "reason": "mock upscale NOOP"}

    def create_ken_burns_clip(
        self,
        image_path: Path,
        duration_s: float,
        scale_from: float = 1.0,
        scale_to: float = 1.15,
        pan_direction: str = "left_to_right",
    ) -> Path:
        self.ken_burns_call_count += 1
        self.last_ken_burns_args = {
            "image_path": image_path,
            "duration_s": duration_s,
            "scale_from": scale_from,
            "scale_to": scale_to,
            "pan_direction": pan_direction,
        }
        return self.ken_burns_path


__all__ = ["ShotstackMock"]
