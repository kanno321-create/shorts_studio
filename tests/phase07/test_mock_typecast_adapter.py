"""Unit tests for TypecastMock — D-18 contract."""
from __future__ import annotations

import sys
from pathlib import Path

_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.typecast_mock import TypecastMock  # noqa: E402


def test_generate_returns_list_of_segments():
    mock = TypecastMock()
    result = mock.generate(script="안녕하세요")
    assert isinstance(result, list)
    assert len(result) == 1
    seg = result[0]
    assert seg["text"] == "안녕하세요"
    assert seg["duration_seconds"] == 3.0
    assert seg["emotion_applied"] is True
    assert seg["speak_v2_url"].startswith("file://")


def test_generate_increments_call_count():
    mock = TypecastMock()
    mock.generate()
    mock.generate()
    assert mock.call_count == 2


def test_production_safe_default():
    assert TypecastMock().allow_fault_injection is False


def test_korean_script_roundtrip():
    """D-22: cp949/UTF-8 round-trip anchor."""
    mock = TypecastMock()
    result = mock.generate(script="한국어 대본 테스트")
    assert result[0]["text"] == "한국어 대본 테스트"


def test_fixture_path_points_to_mock_typecast_wav():
    mock = TypecastMock()
    result = mock.generate(script="x")
    assert result[0]["audio_path"].endswith("mock_typecast.wav")
