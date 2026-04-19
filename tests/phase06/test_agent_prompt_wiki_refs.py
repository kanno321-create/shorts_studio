"""Plan 06-10 — Agent prompt @wiki/shorts/ reference validation (WIKI-05).

Validates that the 15 target agents enumerated in Plan 10 frontmatter each
carry at least one ``@wiki/shorts/<category>/<node>.md`` reference, that no
Phase 6 placeholder strings remain in any AGENT.md file, that every
referenced wiki node exists with ``status: ready`` per D-17, and that D-3
prefix discipline (``@wiki/shorts/`` literal, never a bare path) holds
across the whole ``.claude/agents/`` tree.

Follows the test skeleton in Plan 10 Task 2 (lines 297-406).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.wiki.frontmatter import parse_frontmatter
from scripts.wiki.link_validator import validate_all_agent_refs


REF_RE = re.compile(r"@wiki/shorts/([\w\-\_/]+\.md)")


# The 15 agents Plan 10 targeted (RESEARCH Area 9 line 1041-1057 surface audit).
PLAN_10_TARGET_AGENTS = [
    "inspectors/content/ins-factcheck",
    "inspectors/content/ins-korean-naturalness",
    "inspectors/content/ins-narrative-quality",
    "inspectors/style/ins-thumbnail-hook",
    "inspectors/technical/ins-audio-quality",
    "inspectors/technical/ins-render-integrity",
    "inspectors/technical/ins-subtitle-alignment",
    "producers/director",
    "producers/metadata-seo",
    "producers/niche-classifier",
    "producers/researcher",
    "producers/scene-planner",
    "producers/scripter",
    "producers/shot-planner",
    "producers/trend-collector",
]


def test_no_phase6_placeholder_anywhere_in_agents(repo_root: Path):
    """Every AGENT.md in .claude/agents/ is free of Phase 6 placeholder strings."""
    forbidden_phrases = [
        "Phase 6 채움",
        "Phase 6 wiring",
        "Phase 6 Continuity Bible에서 정의",
        "Phase 6에서 정의",
        "Phase 6에서 채워짐",
    ]
    hits: list[tuple[Path, str]] = []
    for agent_md in (repo_root / ".claude" / "agents").rglob("AGENT.md"):
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        for phrase in forbidden_phrases:
            if phrase in text:
                hits.append((agent_md, phrase))
    assert hits == [], f"Remaining Phase 6 placeholders: {hits}"


def test_every_target_agent_has_wiki_ref(repo_root: Path):
    """Every Plan 10 target agent carries >=1 @wiki/shorts/<path>.md reference."""
    agents_root = repo_root / ".claude" / "agents"
    no_refs: list[str] = []
    for rel in PLAN_10_TARGET_AGENTS:
        agent_md = agents_root / rel / "AGENT.md"
        assert agent_md.exists(), f"Target agent missing: {agent_md}"
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        refs = REF_RE.findall(text)
        if not refs:
            no_refs.append(rel)
    assert no_refs == [], f"Target agents without @wiki/shorts refs: {no_refs}"


def test_validate_all_agent_refs_clean(repo_root: Path):
    """Plan 01's validator: every @wiki/shorts/...md resolves + status=ready."""
    problems = validate_all_agent_refs(
        repo_root / ".claude" / "agents",
        repo_root / "wiki",
    )
    assert problems == [], f"Broken refs: {problems[:5]}"


def test_at_least_15_refs_across_all_agents(repo_root: Path):
    """Aggregate ref count across all AGENT.md files must clear 15 (one per target min)."""
    agents_root = repo_root / ".claude" / "agents"
    total_refs = 0
    for agent_md in agents_root.rglob("AGENT.md"):
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        total_refs += len(REF_RE.findall(text))
    assert total_refs >= 15, f"Expected >=15 @wiki/shorts refs, found {total_refs}"


def test_all_referenced_nodes_have_ready_status(repo_root: Path):
    """Every referenced wiki node exists on disk AND carries status=ready (D-17)."""
    agents_root = repo_root / ".claude" / "agents"
    wiki_root = repo_root / "wiki"
    for agent_md in agents_root.rglob("AGENT.md"):
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        for ref_path in REF_RE.findall(text):
            target = wiki_root / ref_path
            assert target.exists(), (
                f"{agent_md}: ref @wiki/shorts/{ref_path} missing on disk"
            )
            fm = parse_frontmatter(target)
            assert fm.get("status") == "ready", (
                f"{agent_md} refs @wiki/shorts/{ref_path} with status="
                f"{fm.get('status')!r}"
            )


def test_no_bare_wiki_path_without_at_prefix(repo_root: Path):
    """D-3: paths must carry @wiki/shorts/ prefix, not a bare wiki/shorts/... path."""
    agents_root = repo_root / ".claude" / "agents"
    bare_refs: list[tuple[Path, str]] = []
    bare_re = re.compile(r"(?<!@)wiki/shorts/[\w\-\_/]+\.md")
    for agent_md in agents_root.rglob("AGENT.md"):
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        for m in bare_re.finditer(text):
            bare_refs.append((agent_md, m.group(0)))
    assert bare_refs == [], (
        f"Bare wiki/shorts refs (missing @ prefix) found: {bare_refs[:5]}"
    )


def test_ref_distribution_across_ready_nodes(repo_root: Path):
    """Each of the 5 Plan 02 ready wiki nodes is referenced by at least one agent."""
    agents_root = repo_root / ".claude" / "agents"
    expected_nodes = {
        "continuity_bible/channel_identity.md",
        "algorithm/ranking_factors.md",
        "render/remotion_kling_stack.md",
        "kpi/retention_3second_hook.md",
        "ypp/entry_conditions.md",
    }
    referenced: set[str] = set()
    for agent_md in agents_root.rglob("AGENT.md"):
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        for ref_path in REF_RE.findall(text):
            referenced.add(ref_path)
    unreferenced = expected_nodes - referenced
    assert unreferenced == set(), (
        f"Plan 02 ready nodes not referenced by any agent: {unreferenced}"
    )


def test_target_agents_ref_sane_minimum_diversity(repo_root: Path):
    """Producer/Inspector agents should reference at least one D-10/D-17 ready node appropriate to role."""
    agents_root = repo_root / ".claude" / "agents"
    # Simple invariant: every target agent references >=1 of the 5 ready nodes.
    ready_paths = {
        "continuity_bible/channel_identity.md",
        "algorithm/ranking_factors.md",
        "render/remotion_kling_stack.md",
        "kpi/retention_3second_hook.md",
        "ypp/entry_conditions.md",
    }
    agents_without_ready_ref: list[str] = []
    for rel in PLAN_10_TARGET_AGENTS:
        agent_md = agents_root / rel / "AGENT.md"
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        refs = set(REF_RE.findall(text))
        if not (refs & ready_paths):
            agents_without_ready_ref.append(rel)
    assert agents_without_ready_ref == [], (
        f"Target agents not referencing any Plan 02 ready node: "
        f"{agents_without_ready_ref}"
    )
