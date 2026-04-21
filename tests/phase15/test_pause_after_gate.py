"""UFL-03 GateGuard dispatch pause_after_gate trigger.

GateGuard.__init__ 실제 signature (Phase 15 확장 후):
    (checkpointer, session_id, ctx_config: dict | None = None)

dispatch(gate: GateName, verdict: Verdict, artifact_path=None) — verdict 은
Verdict dataclass (result/score/evidence/semantic_feedback/inspector_name).

대표님 --pause-after GATE 지정 시 해당 GATE 완료 후 PipelinePauseSignal 이
raise 되는지 검증합니다.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.orchestrator.gate_guard import GateGuard, Verdict
from scripts.orchestrator.gates import GateName
from scripts.orchestrator.shorts_pipeline import PipelinePauseSignal


def _mk_verdict() -> Verdict:
    """PASS Verdict (실제 dataclass) — 공용 헬퍼."""
    return Verdict(
        result="PASS",
        score=100,
        evidence=[],
        semantic_feedback="",
        inspector_name="test",
    )


class TestPauseAfterDispatch:
    """UFL-03 GateGuard pause_after_gate 계약 검증 (대표님)."""

    def test_signal_raised_when_gate_matches(self):
        """ctx_config['pause_after_gate'] == gate.name 이면 Signal raise."""
        checkpointer = MagicMock()
        ctx_config = {"pause_after_gate": "SCRIPT"}
        guard = GateGuard(checkpointer, "test_pause_sid", ctx_config=ctx_config)
        verdict = _mk_verdict()
        with pytest.raises(PipelinePauseSignal) as exc:
            guard.dispatch(GateName.SCRIPT, verdict)
        assert exc.value.paused_at == GateName.SCRIPT, (
            "대표님, paused_at attribute 가 GateName.SCRIPT 이어야 합니다"
        )

    def test_signal_not_raised_for_other_gate(self):
        """pause_after_gate 이외 gate 에서는 정상 dispatch (Signal 없음)."""
        checkpointer = MagicMock()
        ctx_config = {"pause_after_gate": "SCRIPT"}
        guard = GateGuard(checkpointer, "test_sid2", ctx_config=ctx_config)
        verdict = _mk_verdict()
        # NICHE != SCRIPT → signal 없음, 정상 return + dispatched set 에 추가
        guard.dispatch(GateName.NICHE, verdict)
        assert GateName.NICHE in guard.dispatched

    def test_no_config_no_signal(self):
        """ctx_config 미지정 (None) → 기본 dict = {} → signal 없음."""
        checkpointer = MagicMock()
        guard = GateGuard(checkpointer, "test_sid3")
        verdict = _mk_verdict()
        guard.dispatch(GateName.SCRIPT, verdict)  # 예외 없음
        assert GateName.SCRIPT in guard.dispatched, (
            "대표님, ctx_config 미지정 시 pause signal 이 발생하면 안 됩니다"
        )
