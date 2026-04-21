"""UFL-03 runner PipelinePauseSignal graceful exit.

phase13_live_smoke.py 의 ``_handle_pause_signal`` 헬퍼가 PipelinePauseSignal
을 수신하면 evidence 파일 (pause_*.json) 을 기록하고 exit 0 을 반환하는지
검증합니다.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.orchestrator.gates import GateName
from scripts.orchestrator.shorts_pipeline import PipelinePauseSignal


class TestRunnerCatch:
    """UFL-03 _handle_pause_signal 계약 검증 (대표님)."""

    def test_runner_returns_0_on_pause_signal(self, tmp_path: Path):
        """pause signal 수신 시 exit 0 반환 (graceful exit)."""
        from scripts.smoke.phase13_live_smoke import _handle_pause_signal
        sig = PipelinePauseSignal(GateName.SCRIPT)
        exit_code = _handle_pause_signal(sig, tmp_path / "ev")
        assert exit_code == 0, (
            "대표님, PipelinePauseSignal 수신 시 graceful exit 0 이어야 합니다"
        )

    def test_evidence_written_with_paused_status(self, tmp_path: Path):
        """evidence pause_*.json 파일 기록 + status='PAUSED' payload."""
        from scripts.smoke.phase13_live_smoke import _handle_pause_signal
        ev_dir = tmp_path / "ev"
        ev_dir.mkdir()
        sig = PipelinePauseSignal(GateName.VOICE)
        _handle_pause_signal(sig, ev_dir)
        pause_logs = list(ev_dir.glob("pause_*.json"))
        assert pause_logs, "대표님, evidence pause log 가 생성되지 않았습니다"
        data = json.loads(pause_logs[0].read_text(encoding="utf-8"))
        assert data["status"] == "PAUSED"
        assert data["paused_at"] == "VOICE"

    def test_signal_paused_at_stored(self):
        """PipelinePauseSignal.paused_at attribute 보존 + str 포맷."""
        sig = PipelinePauseSignal(GateName.THUMBNAIL)
        assert sig.paused_at == GateName.THUMBNAIL
        assert "THUMBNAIL" in str(sig), (
            "대표님, Signal 문자열 표현에 gate name 이 포함되어야 합니다"
        )
