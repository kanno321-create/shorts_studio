"""Phase 16-03 Task 0 — Outro Research Findings 검증.

SUMMARY.md 에 Task 0 findings 가 3 증거 sub-heading + Option 결정 과 함께 박제됐는지,
evidence log 2 file 이 존재하는지 검증.

Plan 16-03 Task 16-03-W0-T0-OUTRO-RESEARCH 검증 근거.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[2] / ".planning" / "phases" / "16-production-integration-option-a"
SUMMARY = PHASE_DIR / "16-03-SUMMARY.md"
GREP_LOG = PHASE_DIR / "16-03-task0-grep-remotion.log"
TRIANG_LOG = PHASE_DIR / "16-03-task0-triangulation.log"


class TestOutroResearchFindings:
    """Task 0 Outro Research Findings 박제 검증."""

    def test_summary_file_exists(self):
        assert SUMMARY.exists(), f"16-03-SUMMARY.md missing: {SUMMARY}"
        assert SUMMARY.stat().st_size > 500, "SUMMARY.md too small"

    def test_summary_has_task0_heading(self):
        text = SUMMARY.read_text(encoding="utf-8")
        assert text.count("## Task 0 — Outro Research Findings") >= 1, "Task 0 heading 누락"

    def test_summary_has_three_evidence_subheadings(self):
        text = SUMMARY.read_text(encoding="utf-8")
        # 증거 요약 / 결론 / 선택 이유 3 sub-heading 전수 존재
        assert "### 증거 요약" in text, "### 증거 요약 누락"
        assert "### 결론" in text, "### 결론 누락"
        assert "### 선택 이유" in text, "### 선택 이유 누락"

    def test_summary_has_three_phase_evidence(self):
        text = SUMMARY.read_text(encoding="utf-8")
        # Phase A / Phase B / Phase C 3 증거 phase 전수 언급
        assert "Phase A" in text and "grep" in text.lower(), "Phase A (grep) 증거 누락"
        assert "Phase B" in text and "triangulation" in text.lower(), "Phase B (triangulation) 증거 누락"
        assert "Phase C" in text and ("shorts_naberal" in text or "_shared/signatures" in text), "Phase C (실 파일 스캔) 증거 누락"

    def test_summary_declares_option(self):
        """Option A or Option B 중 하나 명시적 선택."""
        text = SUMMARY.read_text(encoding="utf-8")
        has_a = "Option A" in text and "채택" in text
        has_b_decision = "Option B" in text and "채택" in text
        assert has_a or has_b_decision, "Option A 또는 Option B 결정 명시 누락"

    def test_option_a_decision_with_rationale(self):
        """Option A 선택된 경우 rationale (근거 요약) 섹션 존재."""
        text = SUMMARY.read_text(encoding="utf-8")
        if "**Option A" in text and "채택" in text:
            # Rationale 영역 (근거 요약) 번호 매김 또는 bullets 존재
            lower = text.lower()
            assert "근거" in text or "rationale" in lower, "Option A 근거 누락"

    def test_grep_evidence_log_exists(self):
        assert GREP_LOG.exists(), f"Task 0 grep evidence log missing: {GREP_LOG}"

    def test_triangulation_evidence_log_exists(self):
        assert TRIANG_LOG.exists(), f"Task 0 triangulation log missing: {TRIANG_LOG}"

    def test_triangulation_log_has_episode_data(self):
        text = TRIANG_LOG.read_text(encoding="utf-8")
        # 3 episode 이름 하나 이상 언급
        assert "zodiac-killer" in text, "zodiac-killer triangulation 데이터 누락"
        assert "clip" in text.lower(), "clips 구조 기록 누락"

    def test_veo_zero_enforcement_mentioned(self):
        """CLAUDE.md 금기 #11 — Veo API 신규 호출 금지 언급 확인."""
        text = SUMMARY.read_text(encoding="utf-8")
        assert "금기 #11" in text or "Veo" in text, "Veo 정책 언급 누락"
