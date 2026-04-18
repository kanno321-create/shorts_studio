"""Phase 4 Plan 10 — VALIDATION row 4-10-03.

RUB-01 LogicQA schema: all 17 inspector AGENT.md files must declare exactly
5 sub_qs (q1..q5) inside a <sub_qs>...</sub_qs> block, plus a <main_q> block.

Rationale: LogicQA Main-Q + 5 Sub-Qs majority vote requires exactly 5 votes
for a stable tie-free outcome (2/3 threshold). Any drift (q6, q3, etc.)
breaks the voting semantics and must FAIL this gate.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

if str(pathlib.Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

INSPECTORS_DIR = pathlib.Path(".claude/agents/inspectors")
INSPECTOR_PATHS = sorted(INSPECTORS_DIR.rglob("AGENT.md"))


def test_exactly_17_inspectors() -> None:
    assert len(INSPECTOR_PATHS) == 17, (
        f"Expected 17 inspectors, got {len(INSPECTOR_PATHS)}. "
        f"Paths: {[str(p) for p in INSPECTOR_PATHS]}"
    )


@pytest.mark.parametrize("md_path", INSPECTOR_PATHS, ids=[p.parent.name for p in INSPECTOR_PATHS])
def test_logicqa_block_has_exactly_5_subqs(md_path: pathlib.Path) -> None:
    _, body = parse_frontmatter(md_path)
    m = re.search(r"<sub_qs>(.*?)</sub_qs>", body, re.DOTALL)
    assert m, f"{md_path}: missing <sub_qs>...</sub_qs> block (RUB-01)"
    sub_qs_content = m.group(1)

    # Count q1..q5 tokens (anchored: "q1:", "q2:", ... with optional whitespace)
    sub_count = sum(
        1
        for qid in ("q1", "q2", "q3", "q4", "q5")
        if re.search(rf"\b{qid}\s*:", sub_qs_content)
    )
    assert sub_count == 5, (
        f"{md_path}: expected exactly 5 sub_qs (q1..q5), found {sub_count} "
        f"(RUB-01 LogicQA schema)"
    )

    # Guard against drift (q6, q7, ...)
    assert not re.search(r"\bq6\s*:", sub_qs_content), (
        f"{md_path}: unexpected q6 — LogicQA requires exactly 5 sub_qs (RUB-01)"
    )
    assert not re.search(r"\bq7\s*:", sub_qs_content), (
        f"{md_path}: unexpected q7 — LogicQA requires exactly 5 sub_qs (RUB-01)"
    )


@pytest.mark.parametrize("md_path", INSPECTOR_PATHS, ids=[p.parent.name for p in INSPECTOR_PATHS])
def test_main_q_block_present(md_path: pathlib.Path) -> None:
    _, body = parse_frontmatter(md_path)
    assert "<main_q>" in body, f"{md_path}: missing <main_q> (RUB-01 LogicQA)"
    assert "</main_q>" in body, f"{md_path}: missing </main_q> (RUB-01 LogicQA)"
