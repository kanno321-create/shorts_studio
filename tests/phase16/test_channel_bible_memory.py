"""Phase 16-01 — channel bible memory imprinting 검증.

REQ-PROD-INT-01 담당. Pure filesystem-based tests (no external deps).
"""
from __future__ import annotations

from pathlib import Path

import pytest

MEMORY_DIR = Path(__file__).resolve().parents[2] / ".claude" / "memory"


# ---------------------------------------------------------------------------
# incidents v1.0 (production_active)
# ---------------------------------------------------------------------------


def test_incidents_bible_memory_exists() -> None:
    path = MEMORY_DIR / "project_channel_bible_incidents_v1.md"
    assert path.exists(), f"incidents v1.0 박제 메모리 미존재: {path}"


def test_incidents_bible_has_ten_sections() -> None:
    """incidents.md 10 규칙 섹션 (§1~§10) + FAIL-SCR + Hook signature 등."""
    text = (MEMORY_DIR / "project_channel_bible_incidents_v1.md").read_text(
        encoding="utf-8"
    )
    section_headings = [ln for ln in text.splitlines() if ln.startswith("## ")]
    # 10 규칙 섹션 + FAIL-SCR + 관련 feedback + Hook signature + Duo + Voice Preset + 원본 참조
    assert len(section_headings) >= 10, (
        f"섹션 수 부족: {len(section_headings)} (10 이상 필요, 실제 "
        f"headings = {section_headings!r})"
    )


def test_incidents_bible_references_12_feedbacks() -> None:
    text = (MEMORY_DIR / "project_channel_bible_incidents_v1.md").read_text(
        encoding="utf-8"
    )
    expected = [
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
    missing = [k for k in expected if k not in text]
    assert not missing, f"feedback 미참조: {missing}"


def test_incidents_bible_declares_production_active() -> None:
    text = (MEMORY_DIR / "project_channel_bible_incidents_v1.md").read_text(
        encoding="utf-8"
    )
    assert "status: production_active" in text


def test_incidents_bible_fail_scr_mapping_present() -> None:
    text = (MEMORY_DIR / "project_channel_bible_incidents_v1.md").read_text(
        encoding="utf-8"
    )
    for code in ("FAIL-SCR-011", "FAIL-SCR-016", "FAIL-SCR-004", "FAIL-SCR-006"):
        assert code in text, f"FAIL-SCR code 누락: {code}"


def test_incidents_bible_hook_signature_9_seconds() -> None:
    """Hook signature 9.0초 하드 고정이 명시되어야 한다 (channel-incidents SKILL §)."""
    text = (MEMORY_DIR / "project_channel_bible_incidents_v1.md").read_text(
        encoding="utf-8"
    )
    assert "9.0" in text, "Hook clip duration 9.0초 하드 고정 누락"
    assert "incidents_intro_v4_silent_glare" in text, (
        "intro signature 파일명 누락"
    )


# ---------------------------------------------------------------------------
# 5 reference channel bibles (reference_only_phase_16)
# ---------------------------------------------------------------------------


REF_CHANNELS = ("wildlife", "humor", "politics", "trend", "documentary")


def test_five_reference_channel_bibles_exist() -> None:
    for ch in REF_CHANNELS:
        p = MEMORY_DIR / f"project_channel_bible_{ch}_ref.md"
        assert p.exists(), f"ref 메모리 미존재: {p}"
        text = p.read_text(encoding="utf-8")
        assert "status: reference_only_phase_16" in text
        assert len(text.splitlines()) >= 20, (
            f"{ch}: 실 콘텐츠 20줄 미달 ({len(text.splitlines())})"
        )


@pytest.mark.parametrize("channel", REF_CHANNELS)
def test_ref_channel_bible_has_frontmatter(channel: str) -> None:
    text = (MEMORY_DIR / f"project_channel_bible_{channel}_ref.md").read_text(
        encoding="utf-8"
    )
    assert text.startswith("---\n"), f"{channel}: frontmatter 누락"
    assert f"memory_id: project_channel_bible_{channel}_ref" in text
    assert f"channel: {channel}" in text
    assert "phase: 16-01" in text


@pytest.mark.parametrize("channel", REF_CHANNELS)
def test_ref_channel_bible_cites_source(channel: str) -> None:
    text = (MEMORY_DIR / f"project_channel_bible_{channel}_ref.md").read_text(
        encoding="utf-8"
    )
    assert f"theme_bible_raw/{channel}.md" in text, (
        f"{channel}: 원본 소스 경로 인용 누락"
    )


# ---------------------------------------------------------------------------
# MEMORY.md index
# ---------------------------------------------------------------------------


def test_memory_index_updated() -> None:
    text = (MEMORY_DIR / "MEMORY.md").read_text(encoding="utf-8")
    assert "Phase 16-01 Imprinted" in text
    assert "project_channel_bible_incidents_v1.md" in text
    for ref in REF_CHANNELS:
        assert f"project_channel_bible_{ref}_ref.md" in text, (
            f"MEMORY.md 에 {ref} ref 링크 누락"
        )


def test_memory_index_lists_all_12_feedbacks() -> None:
    text = (MEMORY_DIR / "MEMORY.md").read_text(encoding="utf-8")
    expected = [
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
    missing = [k for k in expected if f"{k}.md" not in text]
    assert not missing, f"MEMORY.md 에 feedback 링크 누락: {missing}"
