"""Phase 16-01 — 12 feedback 메모리 박제 검증.

REQ-PROD-INT-01 담당. Pure filesystem tests, parametrized across 12 keys.
각 key 당 4 assertion (exists + frontmatter + content + incidents cite)
= 12 * 4 = 48 assertions minimum.
"""
from __future__ import annotations

from pathlib import Path

import pytest

MEMORY_DIR = Path(__file__).resolve().parents[2] / ".claude" / "memory"

EXPECTED_FEEDBACKS = [
    "feedback_script_tone_seupnida",
    "feedback_duo_natural_dialogue",
    "feedback_subtitle_semantic_grouping",
    "feedback_video_clip_priority",
    "feedback_outro_signature",
    "feedback_series_ending_tiers",
    "feedback_detective_exit_cta",
    "feedback_watson_cta_pool",
    "feedback_dramatization_allowed",
    "feedback_info_source_distinction",
    "feedback_veo_supplementary_only",
    "feedback_number_split_subtitle",
]


@pytest.mark.parametrize("key", EXPECTED_FEEDBACKS)
def test_feedback_memory_exists(key: str) -> None:
    p = MEMORY_DIR / f"{key}.md"
    assert p.exists(), f"feedback 메모리 미존재: {p}"


@pytest.mark.parametrize("key", EXPECTED_FEEDBACKS)
def test_feedback_memory_has_frontmatter(key: str) -> None:
    text = (MEMORY_DIR / f"{key}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{key}: frontmatter 누락"
    assert f"memory_id: {key}" in text, f"{key}: memory_id 필드 누락"
    assert "status: active" in text, f"{key}: status:active 누락"
    assert "phase: 16-01" in text, f"{key}: phase:16-01 누락"


@pytest.mark.parametrize("key", EXPECTED_FEEDBACKS)
def test_feedback_memory_minimum_content(key: str) -> None:
    text = (MEMORY_DIR / f"{key}.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) >= 15, f"{key}: 실 콘텐츠 15줄 미달 ({len(lines)})"


@pytest.mark.parametrize("key", EXPECTED_FEEDBACKS)
def test_feedback_memory_cites_incidents(key: str) -> None:
    """feedback 메모리는 incidents.md 근거 인용 포함."""
    text = (MEMORY_DIR / f"{key}.md").read_text(encoding="utf-8")
    assert "incidents" in text, f"{key}: incidents 참조 누락"


@pytest.mark.parametrize("key", EXPECTED_FEEDBACKS)
def test_feedback_memory_has_source_refs(key: str) -> None:
    """source_refs frontmatter 필드 포함 (incidents.md + SKILL.md)."""
    text = (MEMORY_DIR / f"{key}.md").read_text(encoding="utf-8")
    assert "source_refs:" in text, f"{key}: source_refs 필드 누락"
    assert "theme_bible_raw/incidents.md" in text, (
        f"{key}: incidents.md 경로 인용 누락"
    )
