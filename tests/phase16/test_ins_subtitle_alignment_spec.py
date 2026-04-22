"""Phase 16-03 W1-INS-FIX — ins-subtitle-alignment AGENT.md v1.1 → v1.2 spec 검증.

faster-whisper large-v3 전환 + subtitle-producer 상류 명시 + version bump + coverage ≥95% 추가.
WhisperX 언급은 레거시 컨텍스트만 (≤3 occurrences).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INS_AGENT_MD = (
    REPO_ROOT
    / ".claude"
    / "agents"
    / "inspectors"
    / "technical"
    / "ins-subtitle-alignment"
    / "AGENT.md"
)


class TestInsSubtitleAlignmentV12Spec:
    """ins-subtitle-alignment AGENT.md v1.2 Phase 16-03 전환 검증."""

    def test_agent_md_exists(self):
        assert INS_AGENT_MD.exists()

    def test_version_is_1_2(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"^version: 1\.2$", text, re.MULTILINE), "version should be 1.2"

    def test_description_under_1024_chars(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        assert m, "description not found"
        desc = m.group(1).strip()
        assert len(desc) <= 1024, f"description too long: {len(desc)} chars"

    def test_description_mentions_faster_whisper(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        desc = m.group(1).strip()
        assert "faster-whisper" in desc

    def test_description_mentions_large_v3(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        desc = m.group(1).strip()
        assert "large-v3" in desc

    def test_description_mentions_subtitle_producer(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        desc = m.group(1).strip()
        assert "subtitle-producer" in desc

    def test_role_section_mentions_faster_whisper(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        role_match = re.search(r"<role>\s*(.+?)\s*</role>", text, re.DOTALL)
        assert role_match, "<role> section not found"
        role = role_match.group(1)
        assert "faster-whisper" in role or "large-v3" in role

    def test_role_section_mentions_phase_16_03(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        role_match = re.search(r"<role>\s*(.+?)\s*</role>", text, re.DOTALL)
        role = role_match.group(1)
        assert "Phase 16-03" in role or "Plan 16-03" in role

    def test_coverage_95_mentioned(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"coverage.*95", text), "coverage ≥95% mention missing"

    def test_subtitle_producer_mentioned_at_least_thrice(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        count = text.count("subtitle-producer")
        assert count >= 3, f"subtitle-producer too few: {count}"

    def test_faster_whisper_or_large_v3_at_least_3_mentions(self):
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        count = text.count("faster-whisper") + text.count("large-v3")
        assert count >= 3, f"faster-whisper/large-v3 too few: {count}"

    def test_whisperx_reduced_to_legacy_context_only(self):
        """WhisperX 가 ≤ 3 회 언급 (레거시 주석 허용)."""
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        count = text.count("WhisperX")
        assert count <= 3, f"WhisperX count {count} > 3 (legacy context only limit)"

    def test_mandatory_reads_includes_subtitle_producer(self):
        """mandatory_reads 섹션에 subtitle-producer AGENT.md 참조."""
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        mr_match = re.search(
            r"<mandatory_reads>\s*(.+?)\s*</mandatory_reads>",
            text,
            re.DOTALL,
        )
        assert mr_match, "<mandatory_reads> not found"
        mr = mr_match.group(1)
        assert ".claude/agents/producers/subtitle-producer" in mr

    def test_drift_threshold_updated_to_150ms(self):
        """drift 임계값 ±150ms 로 업데이트."""
        text = INS_AGENT_MD.read_text(encoding="utf-8")
        assert "150ms" in text or "±150" in text or "0.150" in text
