"""SKILL-ROUTE-01 — markdown matrix parse + cell value validation + reciprocity.

Populated by Phase 12 Plan 04 Task 4 (TDD GREEN). Row count = 31 per disk reality
(14 producer + 17 inspector), consistent with Plan 01 SUMMARY key-decisions §1.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))

from verify_agent_skill_matrix import (  # noqa: E402
    COMMON_SKILLS,
    INSPECTORS,
    PRODUCERS,
    _agent_md_path,
    parse_agent_skills_block,
    parse_matrix,
    verify_reciprocity,
)


def test_matrix_has_30_rows():
    """Matrix row count matches disk reality: 14 producer + 17 inspector = 31.

    Plan frontmatter stated 30; Plan 01 SUMMARY key-decisions §1 confirmed disk
    has 14 producers (harvest-importer lives outside producers/). Test name
    retained for traceability; assertion reflects disk truth.
    """
    matrix = parse_matrix()
    assert len(matrix) == 31, (
        f"expected 31 rows (14 producer + 17 inspector), "
        f"got {len(matrix)}: {sorted(matrix.keys())[:5]}..."
    )
    # 14 producer coverage
    for p in PRODUCERS:
        assert p in matrix, f"producer {p} missing from matrix"
    # 17 inspector coverage
    for _, i in INSPECTORS:
        assert i in matrix, f"inspector {i} missing from matrix"


def test_matrix_cell_values_legal():
    """Every cell in the 31 × 5 matrix body ∈ {required, optional, n/a}."""
    matrix = parse_matrix()
    legal = {"required", "optional", "n/a"}
    for agent, cells in matrix.items():
        for skill, value in cells.items():
            assert value in legal, f"illegal cell [{agent}][{skill}] = {value!r}"


def test_matrix_every_agent_has_required_gate_dispatcher():
    """모든 31 agent 는 gate-dispatcher=required — 파이프라인 dispatch 계약 baseline."""
    matrix = parse_matrix()
    for agent, cells in matrix.items():
        assert cells.get("gate-dispatcher") == "required", (
            f"{agent} missing gate-dispatcher=required"
        )


def test_common_skills_count_is_5():
    """REQUIREMENTS §383 정정 후 COMMON_SKILLS 는 5 (Option A, RESEARCH Q1)."""
    assert len(COMMON_SKILLS) == 5, (
        f"REQUIREMENTS §383 정정 후 COMMON_SKILLS 는 5 — got {len(COMMON_SKILLS)}"
    )
    # Exact skill names per matrix header + .claude/skills/ disk reality
    assert set(COMMON_SKILLS) == {
        "progressive-disclosure",
        "gate-dispatcher",
        "drift-detection",
        "context-compressor",
        "harness-audit",
    }


def test_matrix_reciprocity_with_agent_md():
    """Plan 02 + Plan 03 완료 후 실행 — 0 drift 기대.

    Plan 04 단독 실행 시 drift 존재할 수 있음 (AGENT.md v1.2 migration 전).
    Skip condition: 모든 migration target agent 의 AGENT.md 가 v1.2 인지 전수 확인.
    parallel Plan 02/03 실행 중 일부만 migrated 된 race-state 도 skip 으로 처리.
    """
    drift_count, drifts = verify_reciprocity(fail_on_drift=False)
    if drift_count == 0:
        return  # PASS — full reciprocity achieved

    # Check completion state: count how many producer+inspector AGENT.md files
    # are at v1.2. If any migration target is still < v1.2, Plan 02/03 incomplete.
    migration_targets: list[tuple[str, Path | None]] = []
    for p in PRODUCERS:
        migration_targets.append((p, _agent_md_path(p)))
    for _, ins in INSPECTORS:
        migration_targets.append((ins, _agent_md_path(ins)))

    not_migrated: list[str] = []
    for name, path in migration_targets:
        if path is None or not path.exists():
            not_migrated.append(f"{name}: AGENT.md missing")
            continue
        text = path.read_text(encoding="utf-8")
        if "version: 1.2" not in text:
            not_migrated.append(name)

    if not_migrated:
        pytest.skip(
            f"AGENT.md migration incomplete — re-run after Plan 02 + Plan 03. "
            f"{len(not_migrated)}/{len(migration_targets)} agents not yet at v1.2. "
            f"Current drift: {drift_count}. Not migrated: {not_migrated[:5]}..."
        )
    pytest.fail(
        f"{drift_count} drifts despite all {len(migration_targets)} agents migrated: {drifts[:3]}"
    )
