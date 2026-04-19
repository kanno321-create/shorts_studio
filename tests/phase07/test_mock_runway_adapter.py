"""Unit tests for RunwayMock — mirror of kling test but with runway fixture path."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.runway_mock import RunwayMock  # noqa: E402


def test_default_success_returns_fixture_path():
    result = RunwayMock().image_to_video()
    assert isinstance(result, Path)
    assert result.name == "mock_runway.mp4"


def test_production_safe_default():
    assert RunwayMock().allow_fault_injection is False


def test_fault_ignored_when_disabled():
    mock = RunwayMock(fault_mode="circuit_3x", allow_fault_injection=False)
    for _ in range(3):
        assert isinstance(mock.image_to_video(), Path)


def test_circuit_3x_raises_three_times():
    mock = RunwayMock(fault_mode="circuit_3x", allow_fault_injection=True)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            mock.image_to_video()
    assert isinstance(mock.image_to_video(), Path)


def test_runway_failover_raises_once():
    mock = RunwayMock(fault_mode="runway_failover", allow_fault_injection=True)
    with pytest.raises(RuntimeError):
        mock.image_to_video()
    assert isinstance(mock.image_to_video(), Path)


def test_not_circuit_breaker_trigger_error():
    mock = RunwayMock(fault_mode="circuit_3x", allow_fault_injection=True)
    with pytest.raises(RuntimeError) as exc:
        mock.image_to_video()
    assert type(exc.value) is RuntimeError


def test_accepts_real_adapter_signature_args():
    """RunwayMock.image_to_video accepts (prompt, anchor_frame, duration_seconds)."""
    mock = RunwayMock()
    result = mock.image_to_video(
        prompt="test",
        anchor_frame=Path("/tmp/a.jpg"),
        duration_seconds=5,
    )
    assert isinstance(result, Path)
