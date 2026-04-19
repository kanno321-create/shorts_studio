"""Deterministic Typecast TTS adapter mock for Phase 7 (D-18).

Shadows scripts.orchestrator.api.typecast.TypecastAdapter.generate. The real
adapter returns ``list[AudioSegment]`` (a dataclass from voice_first_timeline),
but Phase 7 E2E tests patch VoiceFirstTimeline.align to ``return []`` so the
downstream pipeline only needs dict-shaped segments — matching the lighter
CONTEXT D-18 contract. For fault-injection scenarios the mock is simple:
it does not currently need fault_mode (Plan 07-05 fault chain targets
Kling/Runway, not Typecast).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_TTS_WAV = _FIXTURES / "mock_typecast.wav"


@dataclass
class TypecastMock:
    """Mock for scripts.orchestrator.api.typecast.TypecastAdapter."""

    allow_fault_injection: bool = False
    call_count: int = field(default=0)
    fixture_path: Path = field(default_factory=lambda: _TTS_WAV)
    duration_seconds: float = 3.0

    def generate(self, *args, **kwargs) -> list:
        self.call_count += 1
        script = kwargs.get("script") or (args[0] if args else "mock script")
        return [
            {
                "audio_path": str(self.fixture_path),
                "start_ms": 0,
                "end_ms": int(self.duration_seconds * 1000),
                "text": script,
                "duration_seconds": self.duration_seconds,
                "emotion_applied": True,
                "speak_v2_url": f"file://{self.fixture_path.as_posix()}",
            }
        ]


__all__ = ["TypecastMock"]
