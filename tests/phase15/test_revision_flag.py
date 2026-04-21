"""UFL-01 --revision-from flag integration test.

대표님의 re-work loop 를 지원하기 위해 특정 GATE 이후의 checkpoint 를 삭제
하고 ShortsPipeline.run() 의 resume 경로로 재실행하는 ``_apply_revision``
helper 의 계약을 검증합니다.

- ``GateName.SCRIPT`` 부터 재실행 요청 시 gate_05 ~ gate_13 (9 files) 삭제,
  gate_00 ~ gate_04 는 보존.
- 존재하지 않는 session 은 빈 리스트 반환 (예외 없이 graceful).
- malformed filename (gate_XX.json / not_a_gate.json) 은 건드리지 않음.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestrator.gates import GateName
from scripts.smoke.phase13_live_smoke import _apply_revision


class TestApplyRevision:
    """UFL-01 _apply_revision helper 의 계약 고정 (대표님)."""

    def test_deletes_gates_at_and_after_target(self, fake_state_dir: Path):
        """GateName.SCRIPT (idx=5) 부터 idx=13 까지 9 files 삭제, 나머지 보존."""
        state_root = fake_state_dir.parent  # tmp_path / "state"
        deleted = _apply_revision(
            state_root,
            fake_state_dir.name,  # session_id
            GateName.SCRIPT,
        )
        # gate_05 (SCRIPT) 부터 gate_13 (MONITOR) — 9 files 삭제
        assert len(deleted) == 9, (
            f"대표님, SCRIPT 부터는 9 files 삭제 기대했는데 {len(deleted)} 반환"
        )
        # 타깃 이상 gate 는 삭제
        assert not (fake_state_dir / "gate_05.json").exists()
        assert not (fake_state_dir / "gate_13.json").exists()
        # 타깃 미만 gate 는 보존
        assert (fake_state_dir / "gate_04.json").exists()
        assert (fake_state_dir / "gate_00.json").exists()

    def test_deletes_only_target_and_above(self, fake_state_dir: Path):
        """GateName.THUMBNAIL (idx=10) 이상 gate 만 삭제."""
        state_root = fake_state_dir.parent
        _apply_revision(state_root, fake_state_dir.name, GateName.THUMBNAIL)
        # gate_10 ~ gate_13 (4 files) 삭제
        assert not (fake_state_dir / "gate_10.json").exists()
        assert not (fake_state_dir / "gate_13.json").exists()
        # gate_09 이하 보존
        assert (fake_state_dir / "gate_09.json").exists()
        assert (fake_state_dir / "gate_00.json").exists()

    def test_handles_missing_state_dir_gracefully(self, tmp_path: Path):
        """존재하지 않는 session → 빈 리스트 반환, 예외 없음 (대표님)."""
        result = _apply_revision(tmp_path, "nonexistent_sid", GateName.SCRIPT)
        assert result == [], (
            "대표님, 존재하지 않는 session 은 조용히 빈 리스트를 반환해야 합니다"
        )

    def test_skips_malformed_filenames(self, tmp_path: Path):
        """gate_XX.json (non-numeric) 과 not_a_gate.json 은 무시 + preserve."""
        state = tmp_path / "state" / "sid1"
        state.mkdir(parents=True)
        (state / "gate_05.json").write_text("{}", encoding="utf-8")
        (state / "not_a_gate.json").write_text("{}", encoding="utf-8")
        (state / "gate_XX.json").write_text("{}", encoding="utf-8")
        _apply_revision(tmp_path / "state", "sid1", GateName.SCRIPT)
        # 정상 filename 은 삭제
        assert not (state / "gate_05.json").exists()
        # malformed 는 보존
        assert (state / "not_a_gate.json").exists()
        assert (state / "gate_XX.json").exists()
