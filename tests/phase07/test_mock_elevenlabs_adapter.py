"""Unit tests for ElevenLabsMock."""
from __future__ import annotations

import sys
from pathlib import Path

_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.elevenlabs_mock import ElevenLabsMock  # noqa: E402


def test_generate_with_timestamps_returns_list():
    mock = ElevenLabsMock()
    result = mock.generate_with_timestamps(text="some text for timestamping")
    assert isinstance(result, list)
    assert len(result) == 2


def test_segment_shape():
    mock = ElevenLabsMock()
    result = mock.generate_with_timestamps(text="test")
    for seg in result:
        assert "word" in seg and "start_s" in seg and "end_s" in seg
        assert seg["voice_id"] == "rachel_mock"


def test_increments_call_count():
    mock = ElevenLabsMock()
    for _ in range(3):
        mock.generate_with_timestamps(text="x")
    assert mock.call_count == 3


def test_production_safe_default():
    assert ElevenLabsMock().allow_fault_injection is False


def test_fixture_path_points_to_elevenlabs_wav():
    mock = ElevenLabsMock()
    result = mock.generate_with_timestamps(text="hello")
    assert result[0]["audio_path"].endswith("mock_elevenlabs.wav")
