"""UFL-02 _PreScriptedProducerInvoker 계약 테스트.

대표님이 직접 준비한 .md/.txt 대본 파일을 SCRIPT gate 에서 scripter 대신
주입하는 경로를 검증합니다. 나머지 gate 는 real invoker 로 pass-through.

Phase 13 ``_PreSeededProducerInvoker`` (L155~228) 의 chain-wrapping 패턴을
승계합니다.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.smoke.phase13_live_smoke import _PreScriptedProducerInvoker


@pytest.fixture
def sample_script(tmp_path: Path) -> Path:
    """UTF-8 한국어 샘플 대본 — 대표님 수동 주입 시뮬레이션."""
    p = tmp_path / "sample_script.md"
    p.write_text(
        "# 대표님 수동 대본\n\n탐정: 이거 수상합니다.\n조수: 네, 확인해보죠.",
        encoding="utf-8",
    )
    return p


class TestPreScripted:
    """UFL-02 _PreScriptedProducerInvoker 계약 검증 (대표님)."""

    def test_script_gate_returns_seeded_output(self, sample_script: Path):
        """SCRIPT gate 호출 시 scripter skip, 파일 내용이 script_md 로 반환."""
        real = MagicMock()
        invoker = _PreScriptedProducerInvoker(real, sample_script)
        result = invoker("scripter", "SCRIPT", {"topic": "test"})
        assert result["gate"] == "SCRIPT"
        assert result["verdict"] == "PASS"
        assert result["script_md"] == sample_script.read_text(encoding="utf-8")
        assert result.get("user_provided") is True, (
            "대표님 수동 대본은 user_provided=True 로 표식되어야 합니다"
        )
        real.assert_not_called()  # scripter 를 실 호출 안 함

    def test_non_script_gate_passes_through(self, sample_script: Path):
        """SCRIPT 이외 gate 는 real invoker 로 위임."""
        real = MagicMock(return_value={"gate": "NICHE", "verdict": "PASS"})
        invoker = _PreScriptedProducerInvoker(real, sample_script)
        result = invoker("niche-classifier", "NICHE", {"topic": "x"})
        real.assert_called_once()
        assert result == {"gate": "NICHE", "verdict": "PASS"}

    def test_script_content_preserves_utf8_korean(self, sample_script: Path):
        """한국어 원문 UTF-8 무결성 (대표님 존댓말 baseline)."""
        invoker = _PreScriptedProducerInvoker(MagicMock(), sample_script)
        result = invoker("scripter", "SCRIPT", {})
        assert "탐정" in result["script_md"]
        assert "조수" in result["script_md"]

    def test_decisions_log_script_path(self, sample_script: Path):
        """decisions 필드에 파일 경로가 기록되어 evidence trail 보존."""
        invoker = _PreScriptedProducerInvoker(MagicMock(), sample_script)
        result = invoker("scripter", "SCRIPT", {})
        assert "decisions" in result, (
            "대표님 수동 대본 주입 이력은 decisions 에 남아야 합니다"
        )
        assert any(str(sample_script) in d for d in result["decisions"])

    def test_missing_file_raises_clear_error(self, tmp_path: Path):
        """존재하지 않는 파일 경로는 __init__ 에서 즉시 FileNotFoundError."""
        nonexist = tmp_path / "missing.md"
        with pytest.raises((FileNotFoundError, OSError)):
            _PreScriptedProducerInvoker(MagicMock(), nonexist)
