"""AGENT-STD-01 — scoped AGENT.md × 5 XML block schema compliance.

Plan 02 populate: 14 producer GREEN (13 new + trend-collector from Plan 01).
Plan 03 populate: 17 inspector GREEN (total 31 = disk reality — see 12-01 SUMMARY
deviation #1 for 30→31 reconciliation).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))

from verify_agent_md_schema import (  # noqa: E402
    _collect_all_agent_mds,
    verify_file,
    EXCLUDED_AGENTS,
)


# 13 producer migrated in Wave 2 (this plan) + 1 from Plan 01 = 14 v1.2 producers.
PRODUCERS_V1_2 = [
    "trend-collector",  # Plan 01 Task 4
    "niche-classifier",
    "researcher",
    "director",
    "scripter",
    "metadata-seo",
    "scene-planner",
    "shot-planner",
    "script-polisher",
    "voice-producer",
    "asset-sourcer",
    "thumbnail-designer",
    "assembler",
    "publisher",
]


def test_all_scoped_agents_have_5_blocks():
    """Plan 02 완료 시 14 producer GREEN — inspector 17 은 Plan 03 대상.

    Disk reality = 31 AGENT.md (14 producer + 17 inspector, harvest-importer +
    shorts-supervisor 제외, Plan 01 SUMMARY deviation #1 참조).
    """
    targets = _collect_all_agent_mds()
    assert len(targets) >= 14, (
        f"expected >= 14 (14 producer already-migrated), got {len(targets)}"
    )
    # All 14 producers must pass (Plan 02 완료 기준).
    producer_paths = [p for p in targets if "producers" in p.parts]
    assert len(producer_paths) == 14, (
        f"expected exactly 14 producer AGENT.md (14 migrated + harvest-importer "
        f"excluded), got {len(producer_paths)}"
    )
    producer_violations: list[tuple[str, list[str]]] = []
    for path in producer_paths:
        ok, missing = verify_file(path)
        if not ok:
            rel = (
                path.relative_to(REPO_ROOT)
                if REPO_ROOT in path.parents
                else path
            )
            producer_violations.append((str(rel), missing))
    if producer_violations:
        pytest.fail(
            f"{len(producer_violations)}/14 producer AGENT.md violate 5-block "
            f"schema after Wave 2: "
            + ", ".join(
                f"{r}: {m}" for r, m in producer_violations[:5]
            )
        )


def test_excluded_agents_not_scanned():
    """harvest-importer + shorts-supervisor 는 Phase 12 scope 밖."""
    assert "harvest-importer" in EXCLUDED_AGENTS
    assert "shorts-supervisor" in EXCLUDED_AGENTS
    targets = _collect_all_agent_mds()
    for p in targets:
        parts = set(p.parts)
        assert "harvest-importer" not in parts, (
            f"harvest-importer leaked into scan: {p}"
        )
        assert "shorts-supervisor" not in parts, (
            f"shorts-supervisor leaked into scan: {p}"
        )


@pytest.mark.parametrize("producer", PRODUCERS_V1_2)
def test_producer_has_version_1_2_and_rub_06(producer):
    """Each producer AGENT.md: version 1.2 + RUB-06 mirror + 샘플링 금지 literal."""
    p = (
        REPO_ROOT
        / ".claude"
        / "agents"
        / "producers"
        / producer
        / "AGENT.md"
    )
    assert p.exists(), f"{producer}/AGENT.md missing"
    text = p.read_text(encoding="utf-8")
    assert "version: 1.2" in text, (
        f"{producer} frontmatter not bumped to 1.2"
    )
    assert "inspector_prompt 읽기 금지 (RUB-06 GAN 분리 mirror)" in text, (
        f"{producer} missing RUB-06 mirror in <constraints>"
    )
    assert "매 호출마다 전수 읽기, 샘플링 금지" in text, (
        f"{producer} missing 샘플링 금지 literal in <mandatory_reads>"
    )


# 17 inspectors migrated in Wave 3 (this plan, Plan 03).
# Phase 4 maxTurns matrix authoritative:
#   ins-factcheck=10, ins-tone-brand=5,
#   ins-blueprint-compliance=1, ins-timing-consistency=1, ins-schema-integrity=1,
#   나머지 12 inspectors=3 (default).
INSPECTORS_V1_1 = [
    ("structural", "ins-schema-integrity"),
    ("structural", "ins-timing-consistency"),
    ("structural", "ins-blueprint-compliance"),
    ("content", "ins-factcheck"),
    ("content", "ins-narrative-quality"),
    ("content", "ins-korean-naturalness"),
    ("style", "ins-thumbnail-hook"),
    ("style", "ins-tone-brand"),
    ("style", "ins-readability"),
    ("compliance", "ins-license"),
    ("compliance", "ins-platform-policy"),
    ("compliance", "ins-safety"),
    ("technical", "ins-audio-quality"),
    ("technical", "ins-render-integrity"),
    ("technical", "ins-subtitle-alignment"),
    ("media", "ins-mosaic"),
    ("media", "ins-gore"),
]


@pytest.mark.parametrize("category,inspector", INSPECTORS_V1_1)
def test_inspector_has_version_1_1_and_rub_06_mirror(category, inspector):
    """Each inspector AGENT.md: version 1.1 + RUB-06 mirror (producer_prompt
    direction, inverse of Producer's inspector_prompt mirror) + 샘플링 금지
    literal. Plan 03 Wave 3 acceptance."""
    p = (
        REPO_ROOT
        / ".claude"
        / "agents"
        / "inspectors"
        / category
        / inspector
        / "AGENT.md"
    )
    assert p.exists(), f"{category}/{inspector}/AGENT.md missing"
    text = p.read_text(encoding="utf-8")
    assert "version: 1.1" in text, (
        f"{inspector} frontmatter not bumped to 1.1"
    )
    assert "producer_prompt 읽기 금지 (RUB-06 GAN 분리 mirror)" in text, (
        f"{inspector} missing RUB-06 mirror in <constraints>"
    )
    assert "매 호출마다 전수 읽기, 샘플링 금지" in text, (
        f"{inspector} missing 샘플링 금지 literal in <mandatory_reads>"
    )


# Issue #1 fix — Structural 3 matrix reciprocity regression test.
# Plan 04 wiki/agent_skill_matrix.md marks Structural Inspector
# `progressive-disclosure` cell = n/a. Reciprocity contract requires the
# literal to be absent from the AGENT.md entirely.
STRUCTURAL_3_NO_PROGRESSIVE_DISCLOSURE = [
    "ins-schema-integrity",
    "ins-timing-consistency",
    "ins-blueprint-compliance",
]


@pytest.mark.parametrize("inspector", STRUCTURAL_3_NO_PROGRESSIVE_DISCLOSURE)
def test_structural_inspector_no_progressive_disclosure(inspector):
    """Plan 04 matrix marks Structural 3 progressive-disclosure = n/a.
    AGENT.md literal presence breaks `verify_agent_skill_matrix.py
    --fail-on-drift` reciprocity invariant. Plan 03 Issue #1 lock."""
    p = (
        REPO_ROOT
        / ".claude"
        / "agents"
        / "inspectors"
        / "structural"
        / inspector
        / "AGENT.md"
    )
    text = p.read_text(encoding="utf-8")
    assert "progressive-disclosure" not in text, (
        f"{inspector} AGENT.md has 'progressive-disclosure' literal — "
        f"matrix SSOT (Plan 04) marks this cell n/a for Structural Inspectors. "
        f"Reciprocity verifier will FAIL."
    )


def test_total_31_agents_scanned():
    """14 producer + 17 inspector = 31 AGENT.md in scope after Wave 3.

    Plan 01 SUMMARY deviation #1 reconciliation: disk reality is 31, not the
    plan's stated 30. Plan 03 closes the 17-inspector gap (Wave 0/2 already
    landed 1 + 13 = 14 producers).
    """
    targets = _collect_all_agent_mds()
    assert len(targets) == 31, (
        f"expected 31 (14 producer + 17 inspector), got {len(targets)}"
    )
