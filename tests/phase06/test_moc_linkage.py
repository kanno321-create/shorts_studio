r"""Integration: every Phase 6 ready node filename appears checked in its MOC.

Plan 02 flips 5 MOC Planned-Nodes checkboxes from `[ ]` to `[x]` for the
promoted node. This test parameterizes over (MOC path, node filename) and
asserts the exact `- [x] \`<node>.md\`` bullet pattern.

Also verifies MOC frontmatter status stays `scaffold` (MOC is a
table-of-contents, not a ready leaf — D-17 structural).
"""
from __future__ import annotations
import re
from pathlib import Path

import pytest


# Map: (MOC path relative to wiki/, expected node filename that must be checked [x])
MOC_CHECK_EXPECTATIONS = [
    ("algorithm/MOC.md", "ranking_factors.md"),
    ("ypp/MOC.md", "entry_conditions.md"),
    ("render/MOC.md", "remotion_kling_stack.md"),
    ("kpi/MOC.md", "retention_3second_hook.md"),
    ("continuity_bible/MOC.md", "channel_identity.md"),
]


@pytest.mark.parametrize("moc_rel,node_name", MOC_CHECK_EXPECTATIONS)
def test_moc_has_checked_box_for_node(repo_root: Path, moc_rel: str, node_name: str):
    """Every ready node promoted this plan has [x] in its category MOC.md."""
    moc = repo_root / "wiki" / moc_rel
    assert moc.exists(), f"{moc} missing"
    text = moc.read_text(encoding="utf-8")
    # Match `- [x] `<node_name>`` pattern (bullet + checked + backticked filename)
    pattern = re.compile(rf"^-\s*\[x\]\s*`{re.escape(node_name)}`", re.MULTILINE)
    assert pattern.search(text), (
        f"{moc}: no `- [x] \\`{node_name}\\`` bullet found. "
        f"Either flip existing [ ] or append new [x] line."
    )


def test_moc_frontmatter_unchanged_scaffold(repo_root: Path):
    """MOC frontmatter status — scaffold OR partial allowed, ready/complete blocked.

    D-17 invariant 은 "MOC-as-TOC 는 ready 로 승격되지 않는다" 이며, Phase 9.1
    에서 production-bible-driven update 가 `scaffold → partial` 로의 정당 승격을
    발생시켰다. 따라서 본 테스트는 (scaffold|partial) 를 허용하고 (ready|complete)
    만 drift 로 차단한다. 출처: Phase 14 RESEARCH §Bucket B B-1.
    """
    import re

    for moc_rel, _ in MOC_CHECK_EXPECTATIONS:
        moc = repo_root / "wiki" / moc_rel
        text = moc.read_text(encoding="utf-8")
        assert re.search(r"^status:\s*(scaffold|partial)\b", text, re.MULTILINE), (
            f"{moc}: MOC status MUST be 'scaffold' or 'partial' (D-17 structural, "
            "Phase 9.1 legitimate progression). Actual text head: "
            f"{text[:200]!r}"
        )
        assert not re.search(r"^status:\s*(ready|complete)\b", text, re.MULTILINE), (
            f"{moc}: MOC status MUST NOT be 'ready' or 'complete' (D-17 invariant). "
            "MOC-as-TOC 는 영구 half-baked 상태 유지."
        )
