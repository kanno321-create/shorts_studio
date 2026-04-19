"""WIKI-01: verify every D-2 category has at least one status=ready node.

Phase 6 Plan 02 authors 5 ready nodes (one per D-2 category). This test
file proves:
  1. All 5 categories host at least one status=ready leaf (not MOC).
  2. Each of the 5 named nodes (algorithm/ranking_factors etc.) parses
     valid D-17 frontmatter with status=ready and matching category.
  3. Every Phase 6 ready node backlinks to its MOC via [[MOC]].
"""
from __future__ import annotations
from pathlib import Path

import pytest

from scripts.wiki.frontmatter import parse_frontmatter, is_ready


CATEGORIES = ["algorithm", "ypp", "render", "kpi", "continuity_bible"]


def test_all_5_categories_have_at_least_one_ready_node(repo_root: Path):
    wiki = repo_root / "wiki"
    missing = []
    for cat in CATEGORIES:
        cat_dir = wiki / cat
        assert cat_dir.is_dir(), f"wiki/{cat}/ missing"
        ready_nodes = [
            p for p in cat_dir.glob("*.md")
            if p.name != "MOC.md" and is_ready(p)
        ]
        if not ready_nodes:
            missing.append(cat)
    assert missing == [], f"Categories without ready node: {missing}"


def test_algorithm_ranking_factors_ready(repo_root: Path):
    p = repo_root / "wiki" / "algorithm" / "ranking_factors.md"
    assert p.exists()
    fm = parse_frontmatter(p)
    assert fm["status"] == "ready"
    assert fm["category"] == "algorithm"


def test_ypp_entry_conditions_ready(repo_root: Path):
    p = repo_root / "wiki" / "ypp" / "entry_conditions.md"
    assert p.exists()
    fm = parse_frontmatter(p)
    assert fm["status"] == "ready"
    assert fm["category"] == "ypp"


def test_render_remotion_kling_stack_ready(repo_root: Path):
    p = repo_root / "wiki" / "render" / "remotion_kling_stack.md"
    assert p.exists()
    fm = parse_frontmatter(p)
    assert fm["status"] == "ready"
    assert fm["category"] == "render"


def test_kpi_retention_3second_hook_ready(repo_root: Path):
    p = repo_root / "wiki" / "kpi" / "retention_3second_hook.md"
    assert p.exists()
    fm = parse_frontmatter(p)
    assert fm["status"] == "ready"
    assert fm["category"] == "kpi"


def test_continuity_bible_channel_identity_ready(repo_root: Path):
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    assert p.exists()
    fm = parse_frontmatter(p)
    assert fm["status"] == "ready"
    assert fm["category"] == "continuity_bible"


def test_ready_nodes_reference_moc(repo_root: Path):
    """Every Phase 6 ready node backlinks to its MOC."""
    wiki = repo_root / "wiki"
    files = [
        wiki / "algorithm" / "ranking_factors.md",
        wiki / "ypp" / "entry_conditions.md",
        wiki / "render" / "remotion_kling_stack.md",
        wiki / "kpi" / "retention_3second_hook.md",
        wiki / "continuity_bible" / "channel_identity.md",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert "[[MOC]]" in text, f"{f}: missing [[MOC]] backlink"
