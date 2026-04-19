"""Unit tests for scripts.wiki.link_validator — @wiki/shorts/<path>.md contract.

Covers D-3 contract:
    - Literal @wiki/shorts/ prefix required (no absolute paths, no relative traversal)
    - find_refs_in_file extracts every mention
    - validate_all_agent_refs flags missing targets
    - validate_all_agent_refs flags status != ready
    - validate_all_agent_refs returns [] when every target is status: ready
"""
from __future__ import annotations

from pathlib import Path

from scripts.wiki.link_validator import find_refs_in_file, validate_all_agent_refs


def test_find_refs_extracts_expected_paths(tmp_path: Path):
    agent = tmp_path / "AGENT.md"
    agent.write_text(
        "See @wiki/shorts/algorithm/ranking_factors.md and "
        "@wiki/shorts/kpi/retention_3second_hook.md for details.",
        encoding="utf-8",
    )
    refs = find_refs_in_file(agent)
    assert "@wiki/shorts/algorithm/ranking_factors.md" in refs
    assert "@wiki/shorts/kpi/retention_3second_hook.md" in refs
    assert len(refs) == 2


def test_find_refs_ignores_absolute_paths(tmp_path: Path):
    agent = tmp_path / "AGENT.md"
    agent.write_text(
        "See /abs/path/file.md and wiki/shorts/no_at_prefix.md", encoding="utf-8"
    )
    refs = find_refs_in_file(agent)
    assert refs == []


def test_validate_all_agent_refs_flags_missing_target(tmp_path: Path):
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "a.md").write_text(
        "Ref: @wiki/shorts/algorithm/nonexistent.md", encoding="utf-8"
    )
    wiki = tmp_path / "wiki"
    (wiki / "algorithm").mkdir(parents=True)
    problems = validate_all_agent_refs(agents, wiki)
    assert len(problems) == 1
    assert problems[0][2] == "target file does not exist"


def test_validate_all_agent_refs_flags_stub_status(tmp_path: Path):
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "a.md").write_text(
        "Ref: @wiki/shorts/algorithm/stub_node.md", encoding="utf-8"
    )
    wiki = tmp_path / "wiki"
    (wiki / "algorithm").mkdir(parents=True)
    (wiki / "algorithm" / "stub_node.md").write_text(
        "---\ncategory: algorithm\nstatus: stub\ntags: [x]\n"
        "updated: 2026-04-19\nsource_notebook: none\n---\n# Stub\n",
        encoding="utf-8",
    )
    problems = validate_all_agent_refs(agents, wiki)
    assert len(problems) == 1
    assert "stub" in problems[0][2]


def test_validate_all_agent_refs_clean_on_ready_target(tmp_path: Path):
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "a.md").write_text(
        "Ref: @wiki/shorts/algorithm/good_node.md", encoding="utf-8"
    )
    wiki = tmp_path / "wiki"
    (wiki / "algorithm").mkdir(parents=True)
    (wiki / "algorithm" / "good_node.md").write_text(
        "---\ncategory: algorithm\nstatus: ready\ntags: [x]\n"
        "updated: 2026-04-19\nsource_notebook: shorts-production-pipeline-bible\n---\n"
        "# Good\n",
        encoding="utf-8",
    )
    assert validate_all_agent_refs(agents, wiki) == []
