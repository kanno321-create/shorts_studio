"""Unit tests for scripts.wiki.frontmatter — parse_frontmatter + validate_node + is_ready.

Covers D-17 contract:
    - Happy path: 5-field block returns dict with category/status/tags/updated/source_notebook
    - Missing frontmatter block raises ValueError
    - Missing required field raises ValueError with field name
    - Invalid category enum raises ValueError with enum list
    - Invalid status enum raises ValueError with enum list
    - Non-ISO updated raises ValueError
    - is_ready returns True only for status: ready
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.wiki.frontmatter import (
    is_ready,
    parse_frontmatter,
    validate_node,
)


def test_parse_valid(fixtures_dir: Path):
    fm = parse_frontmatter(fixtures_dir / "wiki_node_valid.md")
    assert fm["category"] == "algorithm"
    assert fm["status"] == "ready"
    assert fm["source_notebook"] == "shorts-production-pipeline-bible"
    assert fm["updated"] == "2026-04-19"


def test_parse_missing_block(tmp_path: Path):
    p = tmp_path / "no_block.md"
    p.write_text("# No frontmatter here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no frontmatter block"):
        parse_frontmatter(p)


def test_validate_node_happy(fixtures_dir: Path):
    # Should not raise
    validate_node(fixtures_dir / "wiki_node_valid.md")


def test_validate_node_missing_fields(fixtures_dir: Path):
    with pytest.raises(ValueError, match="source_notebook"):
        validate_node(fixtures_dir / "wiki_node_missing_fields.md")


def test_validate_invalid_category(tmp_path: Path):
    p = tmp_path / "bad_cat.md"
    p.write_text(
        "---\ncategory: bogus\nstatus: ready\ntags: [x]\n"
        "updated: 2026-04-19\nsource_notebook: y\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="category"):
        validate_node(p)


def test_validate_invalid_status(tmp_path: Path):
    p = tmp_path / "bad_status.md"
    p.write_text(
        "---\ncategory: algorithm\nstatus: archived\ntags: [x]\n"
        "updated: 2026-04-19\nsource_notebook: y\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="status"):
        validate_node(p)


def test_validate_invalid_date(tmp_path: Path):
    p = tmp_path / "bad_date.md"
    p.write_text(
        "---\ncategory: algorithm\nstatus: ready\ntags: [x]\n"
        "updated: April 19\nsource_notebook: y\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="updated"):
        validate_node(p)


def test_is_ready_true(fixtures_dir: Path):
    assert is_ready(fixtures_dir / "wiki_node_valid.md") is True


def test_is_ready_false_on_missing_fields(fixtures_dir: Path):
    # wiki_node_missing_fields.md has status: stub, so is_ready() is False
    assert is_ready(fixtures_dir / "wiki_node_missing_fields.md") is False


def test_is_ready_false_on_nonexistent(tmp_path: Path):
    assert is_ready(tmp_path / "nope.md") is False
