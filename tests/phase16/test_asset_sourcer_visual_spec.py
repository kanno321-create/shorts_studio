"""Phase 16-04 W1-ASSET-SOURCER-EXT — asset-sourcer AGENT.md v1.3 텍스트 계약 검증.

description ≤1024자, frontmatter version: 1.3, visual_spec + sources_manifest 스키마 언급,
characterLeftSrc/characterRightSrc 좌우 고정 (Q4), 33 상한 유지 문구 포함.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENT_PATH_FRAGMENT = Path(".claude") / "agents" / "producers" / "asset-sourcer" / "AGENT.md"


@pytest.fixture(scope="module")
def asset_sourcer_md(repo_root: Path) -> str:
    p = repo_root / AGENT_PATH_FRAGMENT
    assert p.exists(), f"asset-sourcer AGENT.md 미존재: {p}"
    return p.read_text(encoding="utf-8")


def test_version_is_1_3(asset_sourcer_md: str) -> None:
    """frontmatter version: 1.3."""
    assert re.search(r"^version:\s*1\.3\s*$", asset_sourcer_md, re.MULTILINE), (
        "version: 1.3 frontmatter line not found"
    )


def test_description_under_1024_chars(asset_sourcer_md: str) -> None:
    """description 필드 ≤ 1024 chars (Anthropic agent spec 제약)."""
    m = re.search(
        r"^description:\s*(.+?)\n(?:\w+:|---)",
        asset_sourcer_md,
        re.DOTALL | re.MULTILINE,
    )
    assert m is not None, "description frontmatter not found"
    desc = m.group(1).strip()
    assert len(desc) <= 1024, f"description {len(desc)} > 1024 chars"


def test_visual_spec_mentioned_5_plus(asset_sourcer_md: str) -> None:
    """'visual_spec' 문구 ≥ 5회 (description + role + output + constraints)."""
    count = len(re.findall(r"visual_spec", asset_sourcer_md))
    assert count >= 5, f"visual_spec 언급 부족: {count}"


def test_sources_manifest_mentioned_3_plus(asset_sourcer_md: str) -> None:
    """'sources_manifest' 문구 ≥ 3회."""
    count = len(re.findall(r"sources_manifest", asset_sourcer_md))
    assert count >= 3, f"sources_manifest 언급 부족: {count}"


def test_visual_spec_builder_delegated(asset_sourcer_md: str) -> None:
    """visual_spec_builder 위임 명시 (Q2)."""
    assert "visual_spec_builder" in asset_sourcer_md, (
        "visual_spec_builder delegation 미기재"
    )


def test_character_left_assistant_right_detective(asset_sourcer_md: str) -> None:
    """Q4 고정: characterLeft=assistant, characterRight=detective."""
    left_ok = re.search(
        r"characterLeftSrc[^\n]*assistant", asset_sourcer_md
    ) or "character_assistant.png" in asset_sourcer_md
    right_ok = re.search(
        r"characterRightSrc[^\n]*detective", asset_sourcer_md
    ) or "character_detective.png" in asset_sourcer_md
    assert left_ok, "characterLeft = assistant Q4 매핑 미기재"
    assert right_ok, "characterRight = detective Q4 매핑 미기재"


def test_33_cap_present_32_not(asset_sourcer_md: str) -> None:
    """'33 상한 유지' 포함, '32 상한' 배제 (CLAUDE.md 금기 #9 세션 #33 amend)."""
    assert "33 상한 유지" in asset_sourcer_md, "33 상한 유지 문구 누락"
    assert "32 상한" not in asset_sourcer_md, "32 상한 문구 존재 (구형, 제거 필요)"


def test_scene_sources_5_enforcement(asset_sourcer_md: str) -> None:
    """scene_sources >=5 강제 (Pitfall 5) 언급."""
    assert re.search(
        r"scene_sources.{0,20}5|scene_sources_count", asset_sourcer_md
    ), "scene_sources ≥5 강제 언급 누락"
