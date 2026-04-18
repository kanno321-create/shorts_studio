"""Stdlib-only YAML-ish frontmatter parser for AGENT.md files.

Contract: returns (meta: dict, body: str). Raises ValueError on missing or unclosed frontmatter.

Intentional scope limit: handles flat `key: value` pairs only (no nested lists/maps).
AGENT.md frontmatters in Phase 4 are flat by spec (name, description, version, role, category, maxTurns, phase, deprecated_after).
"""
from __future__ import annotations

import pathlib


def parse_frontmatter(md_path: pathlib.Path) -> tuple[dict, str]:
    """Parse YAML frontmatter block from a Markdown file.

    Args:
        md_path: pathlib.Path to the .md file.

    Returns:
        (meta, body):
            meta  — dict of frontmatter keys (stripped of wrapping quotes).
            body  — text after the closing "---\\n" delimiter.

    Raises:
        ValueError: if the file does not start with "---\\n" or the frontmatter is unclosed.
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{md_path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{md_path}: unclosed frontmatter")
    front = text[4:end]
    body = text[end + 5:]
    meta: dict = {}
    for line in front.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body
