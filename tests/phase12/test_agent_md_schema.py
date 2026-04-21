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
