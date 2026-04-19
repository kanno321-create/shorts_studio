"""Unit tests for KlingMock — signature + determinism + fault injection gating.

Per PLAN 07-02 Task 07-02-01 + CONTEXT D-16 + RESEARCH Correction 2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Phase 7 mocks live at tests/phase07/mocks/. Since tests/ is not a Python
# package (no tests/__init__.py), we add tests/phase07/ directly to sys.path
# so the mocks package becomes importable as `mocks.kling_mock`. This mirrors
# the Wave 0 pattern of keeping tests/phase07/ self-contained without
# requiring cross-phase package restructuring.
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.kling_mock import KlingMock  # noqa: E402


def test_default_success_returns_fixture_path():
    mock = KlingMock()
    result = mock.image_to_video()
    assert isinstance(result, Path)
    assert result.name == "mock_kling.mp4"
    assert mock.call_count == 1


def test_default_allows_fault_injection_is_false():
    """D-3: production-safe default."""
    assert KlingMock().allow_fault_injection is False


def test_fault_mode_ignored_when_allow_fault_injection_false():
    """D-3 enforcement: setting fault_mode without allow_fault_injection=True does NOT raise."""
    mock = KlingMock(fault_mode="circuit_3x", allow_fault_injection=False)
    # Three calls, no raise.
    for _ in range(3):
        result = mock.image_to_video()
        assert isinstance(result, Path)


def test_circuit_3x_raises_runtime_error_three_times_then_succeeds():
    mock = KlingMock(fault_mode="circuit_3x", allow_fault_injection=True)
    for i in range(1, 4):
        with pytest.raises(RuntimeError) as exc:
            mock.image_to_video()
        assert f"#{i}" in str(exc.value)
    # 4th call succeeds.
    result = mock.image_to_video()
    assert isinstance(result, Path)


def test_runway_failover_raises_once_then_succeeds():
    mock = KlingMock(fault_mode="runway_failover", allow_fault_injection=True)
    with pytest.raises(RuntimeError):
        mock.image_to_video()
    result = mock.image_to_video()
    assert isinstance(result, Path)


def test_mock_is_NOT_circuit_breaker_trigger_error():
    """RESEARCH §Correction 2: mocks raise plain RuntimeError, NOT the non-existent CircuitBreakerTriggerError."""
    mock = KlingMock(fault_mode="circuit_3x", allow_fault_injection=True)
    with pytest.raises(RuntimeError) as exc:
        mock.image_to_video()
    # Explicit type check: NOT a subclass of any *Trigger* exception.
    assert type(exc.value) is RuntimeError


def test_accepts_real_adapter_signature_args():
    """KlingMock.image_to_video must accept (prompt, anchor_frame, duration_seconds) per real adapter."""
    mock = KlingMock()
    result = mock.image_to_video(
        prompt="test motion",
        anchor_frame=Path("/tmp/anchor.jpg"),
        duration_seconds=5,
    )
    assert isinstance(result, Path)
