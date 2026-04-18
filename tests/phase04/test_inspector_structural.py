"""Phase 4 Wave 1a — Structural Inspector compliance tests.

Enforces plan 04-02 contract for the 3 Structural Inspector AGENT.md files:
    - ins-blueprint-compliance
    - ins-timing-consistency
    - ins-schema-integrity

All 6 tests must PASS (no skip, no xfail).
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

STRUCTURAL_DIR = _REPO_ROOT / ".claude/agents/inspectors/structural"
EXPECTED_NAMES = {
    "ins-blueprint-compliance",
    "ins-timing-consistency",
    "ins-schema-integrity",
}


@pytest.fixture(scope="module")
def structural_agents():
    """Return list of (path, meta, body) tuples for every Structural Inspector AGENT.md."""
    files = sorted(STRUCTURAL_DIR.rglob("AGENT.md"))
    loaded = []
    for f in files:
        meta, body = parse_frontmatter(f)
        loaded.append((f, meta, body))
    return loaded


# -----------------------------------------------------------------------------
# Test 1 — exactly 3 structural inspectors exist
# -----------------------------------------------------------------------------
def test_exactly_3_structural_inspectors(structural_agents):
    assert (
        len(structural_agents) == 3
    ), f"Expected exactly 3 Structural Inspectors, found {len(structural_agents)}"
    names = {meta["name"] for _, meta, _ in structural_agents}
    assert names == EXPECTED_NAMES, (
        f"Expected {EXPECTED_NAMES}, got {names}"
    )


# -----------------------------------------------------------------------------
# Test 2 — frontmatter has role=inspector, category=structural, maxTurns=1
# -----------------------------------------------------------------------------
def test_frontmatter_role_category_maxturns(structural_agents):
    for path, meta, _body in structural_agents:
        assert meta.get("role") == "inspector", (
            f"{path.name}: role={meta.get('role')!r}, expected 'inspector'"
        )
        assert meta.get("category") == "structural", (
            f"{path.name}: category={meta.get('category')!r}, expected 'structural'"
        )
        # maxTurns may be stored as string from flat YAML parser
        max_turns = int(meta.get("maxTurns", "0"))
        assert max_turns == 1, (
            f"{path.name}: maxTurns={max_turns}, expected 1 (RUB-05 structural regex-only)"
        )


# -----------------------------------------------------------------------------
# Test 3 — LogicQA block present with main_q + 5 sub_qs (q1..q5)
# -----------------------------------------------------------------------------
def test_logicqa_block_present(structural_agents):
    for path, _meta, body in structural_agents:
        assert "<main_q>" in body, f"{path.name}: missing <main_q> (RUB-01)"
        assert "<sub_qs>" in body, f"{path.name}: missing <sub_qs> (RUB-01)"
        for q_id in ("q1", "q2", "q3", "q4", "q5"):
            assert re.search(rf"\b{q_id}\s*:", body), (
                f"{path.name}: missing sub-question {q_id} (RUB-01 5 sub-qs required)"
            )


# -----------------------------------------------------------------------------
# Test 4 — MUST REMEMBER contains RUB-02 (창작 금지) + RUB-06 (producer_prompt)
# -----------------------------------------------------------------------------
def test_must_remember_contains_rub_violations(structural_agents):
    for path, _meta, body in structural_agents:
        mr_match = re.search(r"## MUST REMEMBER.*?\Z", body, re.DOTALL)
        assert mr_match, f"{path.name}: no MUST REMEMBER section (AGENT-09)"
        mr = mr_match.group(0)
        assert "창작 금지" in mr, (
            f"{path.name}: MUST REMEMBER missing '창작 금지' (RUB-02)"
        )
        assert "producer_prompt" in mr, (
            f"{path.name}: MUST REMEMBER missing 'producer_prompt' reference (RUB-06)"
        )


# -----------------------------------------------------------------------------
# Test 5 — Inputs table does NOT list producer_prompt/producer_system_context as Flag
# -----------------------------------------------------------------------------
def test_inputs_no_producer_prompt_or_system_context(structural_agents):
    for path, _meta, body in structural_agents:
        # Extract Inputs section (until next top-level header)
        inputs_match = re.search(r"## Inputs.*?(?=\n## )", body, re.DOTALL)
        assert inputs_match, f"{path.name}: no Inputs section"
        inputs = inputs_match.group(0)
        # No table row with producer_prompt as a Flag (| `producer_prompt` | ...)
        assert not re.search(r"\|\s*`?producer_prompt`?\s*\|", inputs), (
            f"{path.name}: Inputs table contains producer_prompt as Flag (RUB-06 violation)"
        )
        assert not re.search(r"\|\s*`?producer_system_context`?\s*\|", inputs), (
            f"{path.name}: Inputs table contains producer_system_context as Flag (RUB-06 violation)"
        )


# -----------------------------------------------------------------------------
# Test 6 — ins-schema-integrity body contains 9:16 + 1080×1920 + 59 (CONTENT-05)
# -----------------------------------------------------------------------------
def test_ins_schema_integrity_content_05(structural_agents):
    target = None
    for path, meta, body in structural_agents:
        if meta["name"] == "ins-schema-integrity":
            target = (path, body)
            break
    assert target is not None, "ins-schema-integrity AGENT.md not found"
    path, body = target
    assert "9:16" in body, f"{path.name}: missing '9:16' (CONTENT-05)"
    assert ("1080×1920" in body) or ("1080x1920" in body), (
        f"{path.name}: missing '1080×1920' or '1080x1920' (CONTENT-05)"
    )
    assert "59" in body, f"{path.name}: missing '59' (CONTENT-05 59초 제약)"
