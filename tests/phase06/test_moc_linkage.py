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
    """Sanity: MOC frontmatter status stays scaffold (not promoted to ready)."""
    for moc_rel, _ in MOC_CHECK_EXPECTATIONS:
        moc = repo_root / "wiki" / moc_rel
        text = moc.read_text(encoding="utf-8")
        assert "status: scaffold" in text, f"{moc}: MOC status MUST stay scaffold (D-17 structural)"
