"""TEST-02 primary: verify_all_dispatched() is the COMPLETE precondition.

Exercises GateGuard directly (unit level) + ShortsPipeline (integration level).
Proves exactly 13 dispatches are required to allow COMPLETE transition; 12 or
fewer raises IncompleteDispatch when transition is attempted.

Anchors:
- CONTEXT D-5 (research-corrected: ``dispatched_count == 13``, NOT 17).
- SC2: E2E run reaches COMPLETE with ``dispatched_count == 13``.
- scripts/orchestrator/gate_guard.py:169-176 (verify_all_dispatched).
- scripts/orchestrator/shorts_pipeline.py:661-673 (_transition_to_complete).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator import (
    AudioSegment,
    GateName,
    IncompleteDispatch,
    ShortsPipeline,
    Verdict,
)
from scripts.orchestrator.gate_guard import GateGuard

# Phase 7 mocks live at tests/phase07/mocks/. Since tests/ is not a Python
# package (no tests/__init__.py), we add tests/phase07/ to sys.path so the
# mocks package becomes importable as ``mocks.*`` — mirrors the Wave 1 pattern
# in test_mock_kling_adapter.py:12-19.
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.elevenlabs_mock import ElevenLabsMock  # noqa: E402
from mocks.kling_mock import KlingMock  # noqa: E402
from mocks.runway_mock import RunwayMock  # noqa: E402
from mocks.shotstack_mock import ShotstackMock  # noqa: E402
from mocks.typecast_mock import TypecastMock  # noqa: E402


def _pass() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


# ---------------------------------------------------------------------------
# Unit-level: GateGuard.verify_all_dispatched contract
# ---------------------------------------------------------------------------


def test_verify_returns_false_when_empty():
    g = GateGuard(None, "sid_empty")
    assert g.verify_all_dispatched() is False


def test_verify_returns_false_with_12_gates():
    """12 of 13 operational gates dispatched — verify must return False."""
    g = GateGuard(None, "sid_12")
    operational = [gt for gt in GateName if gt not in (GateName.IDLE, GateName.COMPLETE)]
    # dispatch first 12 only (MONITOR intentionally skipped)
    for gate in operational[:12]:
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is False
    assert len(g.dispatched) == 12


def test_verify_returns_true_with_all_13_operational():
    g = GateGuard(None, "sid_13")
    operational = [gt for gt in GateName if gt not in (GateName.IDLE, GateName.COMPLETE)]
    for gate in operational:
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is True
    assert len(g.dispatched) == 13


def test_verify_returns_false_when_monitor_missing():
    """MONITOR (the last operational gate) specifically missing → False."""
    g = GateGuard(None, "sid_no_monitor")
    operational = [gt for gt in GateName if gt not in (GateName.IDLE, GateName.COMPLETE)]
    for gate in operational:
        if gate is GateName.MONITOR:
            continue
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is False
    # and once MONITOR arrives it flips to True
    g.dispatch(GateName.MONITOR, _pass())
    assert g.verify_all_dispatched() is True


# ---------------------------------------------------------------------------
# Integration-level: full ShortsPipeline run must reach COMPLETE with 13.
# ---------------------------------------------------------------------------


def _producer_output(tmp_path: Path, duration_seconds: int = 5) -> dict:
    return {
        "artifact_path": str(tmp_path / "art.json"),
        "prompt": "mock prompt",
        "duration_seconds": duration_seconds,
        "anchor_frame": str(tmp_path / "anchor.png"),
        # POLISH-gate consumers expect a scenes list; pipeline tolerates absent.
        "scenes": [
            {
                "prompt": "scene prompt",
                "duration_seconds": duration_seconds,
                "anchor_frame": str(tmp_path / "anchor.png"),
            }
        ],
    }


def test_e2e_complete_transition_allowed_exactly_at_13(
    tmp_path: Path, _fake_env: None, tmp_session_id: str,
):
    """Integration: full ShortsPipeline.run() dispatches 13, reaches COMPLETE."""
    # POLISH artifact must carry a scenes list so _run_assets has work;
    # producer_invoker is the only Producer entry — return the same dict each call.
    producer = MagicMock(return_value=_producer_output(tmp_path))
    supervisor = MagicMock(return_value=_pass())

    pipeline = ShortsPipeline(
        session_id=tmp_session_id,
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=TypecastMock(),
        elevenlabs_adapter=ElevenLabsMock(),
        shotstack_adapter=ShotstackMock(),
        producer_invoker=producer,
        supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )

    # Short-circuit VoiceFirstTimeline + patch typecast to return proper
    # AudioSegment dataclasses (the real TypecastAdapter.generate would — our
    # Wave-1 mock returns dicts for the Typecast adapter's OWN tests). 07-04
    # only cares that 13 dispatches happen; 07-03 covers audio/video plumbing.
    audio_seg = AudioSegment(
        index=0, start=0.0, end=3.0, duration=3.0, path=tmp_path / "mock.wav",
    )
    with patch.object(pipeline.timeline, "align", return_value=[]), \
         patch.object(pipeline.timeline, "insert_transition_shots", return_value=[]), \
         patch.object(pipeline.typecast, "generate", return_value=[audio_seg]):
        result = pipeline.run()

    assert result["dispatched_count"] == 13, (
        f"E2E dispatched_count {result['dispatched_count']} != 13 (Correction 1 violated)"
    )
    assert result["final_gate"] == "COMPLETE"
    assert pipeline.gate_guard.verify_all_dispatched() is True
    assert len(pipeline.gate_guard.dispatched) == 13


def test_complete_transition_raises_incomplete_dispatch_when_12(
    tmp_path: Path, _fake_env: None,
):
    """Calling _transition_to_complete with only 12 gates dispatched → IncompleteDispatch."""
    pipeline = ShortsPipeline(
        session_id="sid_incomplete",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=TypecastMock(),
        elevenlabs_adapter=ElevenLabsMock(),
        shotstack_adapter=ShotstackMock(),
        producer_invoker=MagicMock(return_value=_producer_output(tmp_path)),
        supervisor_invoker=MagicMock(return_value=_pass()),
        asset_sourcer_invoker=lambda p: tmp_path / "still.png",
    )
    operational = [gt for gt in GateName if gt not in (GateName.IDLE, GateName.COMPLETE)]
    # Dispatch only first 12 (MONITOR skipped)
    for gate in operational[:12]:
        pipeline.gate_guard.dispatch(gate, _pass())
    assert pipeline.gate_guard.verify_all_dispatched() is False
    with pytest.raises(IncompleteDispatch):
        pipeline._transition_to_complete()


def test_missing_for_complete_reports_monitor_only_when_12_done(
    tmp_path: Path, _fake_env: None,
):
    """Diagnostic contract: missing_for_complete lists exactly what is not yet dispatched."""
    pipeline = ShortsPipeline(
        session_id="sid_missing",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=TypecastMock(),
        elevenlabs_adapter=ElevenLabsMock(),
        shotstack_adapter=ShotstackMock(),
        producer_invoker=MagicMock(return_value=_producer_output(tmp_path)),
        supervisor_invoker=MagicMock(return_value=_pass()),
        asset_sourcer_invoker=lambda p: tmp_path / "still.png",
    )
    operational = [gt for gt in GateName if gt not in (GateName.IDLE, GateName.COMPLETE)]
    for gate in operational[:12]:
        pipeline.gate_guard.dispatch(gate, _pass())
    missing = pipeline.gate_guard.missing_for_complete()
    assert GateName.MONITOR in missing
    assert len(missing) == 1
