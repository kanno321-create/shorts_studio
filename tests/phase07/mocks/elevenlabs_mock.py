"""Deterministic ElevenLabs TTS adapter mock for Phase 7 (Typecast fallback path proof).

Shadows scripts.orchestrator.api.elevenlabs.ElevenLabsAdapter.generate_with_timestamps.
Returns a minimal word-level timestamp list compatible with VoiceFirstTimeline
alignment expectations (which is additionally patched in E2E tests).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_EL_WAV = _FIXTURES / "mock_elevenlabs.wav"


@dataclass
class ElevenLabsMock:
    """Mock for scripts.orchestrator.api.elevenlabs.ElevenLabsAdapter."""

    allow_fault_injection: bool = False
    call_count: int = field(default=0)
    fixture_path: Path = field(default_factory=lambda: _EL_WAV)
    voice_id: str = "rachel_mock"

    def generate_with_timestamps(self, *args, **kwargs) -> list:
        self.call_count += 1
        text = kwargs.get("text") or (args[0] if args else "mock")
        # Produce a minimal word-level timestamp list compatible with
        # VoiceFirstTimeline alignment expectations.
        return [
            {
                "word": text[:10],
                "start_s": 0.0,
                "end_s": 1.0,
                "audio_path": str(self.fixture_path),
                "voice_id": self.voice_id,
            },
            {
                "word": text[10:20] if len(text) >= 10 else text,
                "start_s": 1.0,
                "end_s": 3.0,
                "audio_path": str(self.fixture_path),
                "voice_id": self.voice_id,
            },
        ]


__all__ = ["ElevenLabsMock"]
