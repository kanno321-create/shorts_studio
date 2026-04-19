"""D-17 wiki node frontmatter parser + validator (stdlib-only).

Per Phase 6 CONTEXT D-17, every wiki node under studios/shorts/wiki/ MUST
declare a 5-field YAML-lite frontmatter block:

    ---
    category: <algorithm|ypp|render|kpi|continuity_bible>
    status:   <stub|ready>
    tags:     [tag1, tag2, ...]
    updated:  YYYY-MM-DD
    source_notebook: <notebook_id_or_hardcoded>
    ---

`status: scaffold` is accepted as a legacy Phase 2 placeholder only at the
CLI layer (verify_wiki_frontmatter.py --allow-scaffold). `validate_node`
itself treats scaffold as valid-enum but the CLI decides policy.

Only `status: ready` nodes are agent-visible per D-17 — the link validator
(scripts/wiki/link_validator.py) enforces that.

No pyyaml dependency per RESEARCH line 132 DECISION (stdlib-only).
"""
from __future__ import annotations

import re
from pathlib import Path

_ALLOWED_CATEGORIES = {"algorithm", "ypp", "render", "kpi", "continuity_bible"}
# `scaffold` = legacy Phase 2 MOC placeholder tolerated by CLI --allow-scaffold.
# `ready`    = Phase 6 promoted (agent-visible).
# `stub`     = WIP draft (not agent-visible).
_ALLOWED_STATUS = {"stub", "ready", "scaffold"}
_REQUIRED_FIELDS = {"category", "status", "tags", "updated", "source_notebook"}
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(md_path: Path) -> dict:
    """Parse a YAML-lite frontmatter block from a markdown file.

    Returns:
        dict with the raw key/value strings from the frontmatter block
        (values are kept as-is, not parsed into lists/dates).

    Raises:
        ValueError: if the file does not begin with a ``---\\n ... \\n---\\n``
            block.
        FileNotFoundError: if md_path does not exist (propagated from
            Path.read_text).
    """
    text = md_path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{md_path}: no frontmatter block")
    body = m.group(1)
    out: dict = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def validate_node(md_path: Path) -> None:
    """Assert a wiki node file satisfies D-17 schema.

    Checks: 5 required fields present, category + status enum valid,
    updated is ISO YYYY-MM-DD.

    Raises:
        ValueError: on first violation, with path + offending field in
            the message.
    """
    fm = parse_frontmatter(md_path)
    missing = _REQUIRED_FIELDS - fm.keys()
    if missing:
        raise ValueError(f"{md_path}: missing frontmatter fields {sorted(missing)}")
    cat = fm["category"]
    if cat not in _ALLOWED_CATEGORIES:
        raise ValueError(
            f"{md_path}: category '{cat}' not in {sorted(_ALLOWED_CATEGORIES)}"
        )
    status = fm["status"]
    if status not in _ALLOWED_STATUS:
        raise ValueError(
            f"{md_path}: status '{status}' not in {sorted(_ALLOWED_STATUS)}"
        )
    if not _DATE_RE.match(fm["updated"]):
        raise ValueError(
            f"{md_path}: updated '{fm['updated']}' not ISO YYYY-MM-DD"
        )


def is_ready(md_path: Path) -> bool:
    """Return True iff node has status: ready (agent-visible per D-17).

    Silent False on any parse/read error — callers that need a loud
    failure should use validate_node instead.
    """
    try:
        fm = parse_frontmatter(md_path)
        return fm.get("status") == "ready"
    except (ValueError, FileNotFoundError):
        return False


__all__ = ["parse_frontmatter", "validate_node", "is_ready"]
