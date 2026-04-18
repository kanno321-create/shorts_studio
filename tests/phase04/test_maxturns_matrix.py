"""Phase 4 Wave 4 — maxTurns matrix enforcement (RUB-05, plan 04-09).

RESEARCH.md §8.5 lines 1434-1451 maxTurns matrix:
    - ins-factcheck                    = 10  (다중 source 교차 검증)
    - ins-tone-brand                   =  5  (채널바이블 대조)
    - ins-blueprint-compliance         =  1  (순수 regex)
    - ins-timing-consistency           =  1  (순수 regex)
    - ins-schema-integrity             =  1  (순수 regex)
    - 모든 기타 (Inspector + Producer + Supervisor) = 3

Walks all .claude/agents/**/AGENT.md (excluding harvest-importer Phase 3 deprecated).
Asserts maxTurns matches matrix 100%.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

AGENTS_DIR = _REPO_ROOT / ".claude/agents"

# Matrix of non-default maxTurns values
EXPECTED_NON_DEFAULT = {
    "ins-factcheck": 10,
    "ins-tone-brand": 5,
    "ins-blueprint-compliance": 1,
    "ins-timing-consistency": 1,
    "ins-schema-integrity": 1,
}
DEFAULT_MAX_TURNS = 3


def _agent_md_paths():
    """All AGENT.md under .claude/agents/, excluding harvest-importer (Phase 3 deprecated)."""
    paths = []
    for p in AGENTS_DIR.rglob("AGENT.md"):
        if "harvest-importer" in str(p):
            continue
        paths.append(p)
    return sorted(paths)


# -----------------------------------------------------------------------------
# Test 1 — each agent's maxTurns matches matrix
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("md_path", _agent_md_paths(), ids=lambda p: p.parent.name)
def test_maxturns_value_matches_matrix(md_path: pathlib.Path):
    meta, _body = parse_frontmatter(md_path)
    name = meta.get("name")
    assert name, f"{md_path}: missing 'name' in frontmatter"

    actual = int(meta.get("maxTurns", "0"))
    expected = EXPECTED_NON_DEFAULT.get(name, DEFAULT_MAX_TURNS)

    assert actual == expected, (
        f"{name} ({md_path.relative_to(_REPO_ROOT)}): "
        f"maxTurns={actual}, expected {expected} (RUB-05 matrix)"
    )


# -----------------------------------------------------------------------------
# Test 2 — exactly 5 agents have non-default maxTurns (once Wave 1-4 complete)
# -----------------------------------------------------------------------------
def test_non_default_maxturns_count():
    paths = _agent_md_paths()
    non_default_found = {}
    for p in paths:
        meta, _body = parse_frontmatter(p)
        name = meta.get("name")
        mt = int(meta.get("maxTurns", "0"))
        if mt != DEFAULT_MAX_TURNS:
            non_default_found[name] = mt

    # Once all Phase 4 waves complete, exactly 5 non-default agents expected.
    # During in-progress waves, the EXPECTED set is the UPPER bound; subset OK.
    actual_set = set(non_default_found.keys())
    expected_set = set(EXPECTED_NON_DEFAULT.keys())

    # Every non-default agent found must be in the expected matrix
    unexpected = actual_set - expected_set
    assert not unexpected, (
        f"Unexpected non-default maxTurns agents: {unexpected}. "
        f"Expected set: {expected_set}"
    )

    # And the values must match exactly
    for name, value in non_default_found.items():
        assert value == EXPECTED_NON_DEFAULT[name], (
            f"{name}: maxTurns={value}, expected {EXPECTED_NON_DEFAULT[name]}"
        )


# -----------------------------------------------------------------------------
# Test 3 — harvest-importer is explicitly excluded
# -----------------------------------------------------------------------------
def test_harvest_importer_excluded():
    paths = _agent_md_paths()
    for p in paths:
        assert "harvest-importer" not in str(p), (
            f"harvest-importer should be excluded (Phase 3 deprecated), got {p}"
        )


# -----------------------------------------------------------------------------
# Test 4 — total agent count sanity (32 target = 17 inspector + 14 producer + 1 supervisor)
#           During in-progress waves, count is LOWER bound.
# -----------------------------------------------------------------------------
def test_agent_count_sanity():
    paths = _agent_md_paths()
    total = len(paths)
    # At least Wave 0 FOUNDATION + 17 inspectors + this plan's 6 = 23+. Upper bound 32.
    assert total <= 32, (
        f"Agent count {total} exceeds 32 (harvest-importer excluded). "
        f"Target roster: 17 inspector + 14 producer + 1 supervisor = 32."
    )
    assert total >= 17 + 5 + 1, (
        f"Agent count {total} below minimum for Wave 4 plan 04-09 completion "
        f"(17 inspector + 5 Producer Support + 1 Supervisor = 23)."
    )
