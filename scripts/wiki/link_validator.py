"""Wiki reference validator for @wiki/shorts/<path>.md refs in agent prompts.

Per CONTEXT D-3, agent prompts under .claude/agents/ reference wiki nodes
using the literal ``@wiki/shorts/<category>/<node>.md`` format. This module
walks agent markdown and asserts:

  1. Every referenced path exists under the wiki root.
  2. The target node has ``status: ready`` (D-17 — stub/scaffold nodes are
     not agent-visible).

Stdlib-only. No pyyaml. Uses scripts.wiki.frontmatter for schema access.
"""
from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import parse_frontmatter

# D-3: literal ``@wiki/shorts/`` prefix; capture path portion after it up to
# the first ``.md``. Only forward-slash paths allowed (no ``../`` traversal,
# no absolute paths, no backslashes).
_REF_RE = re.compile(r"@wiki/shorts/([\w\-\_/]+\.md)")


def find_refs_in_file(md_path: Path) -> list[str]:
    """Return all @wiki/shorts/X.md references mentioned in a markdown file.

    Silent-empty on read error (OSError) — caller decides whether missing
    refs are significant.
    """
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return ["@wiki/shorts/" + m.group(1) for m in _REF_RE.finditer(text)]


def validate_all_agent_refs(
    agents_root: Path,
    wiki_root: Path,
) -> list[tuple[Path, str, str]]:
    """Walk agents_root recursively and check every @wiki/shorts/ ref.

    Args:
        agents_root: directory scanned via rglob("*.md"). Typically
            ``.claude/agents/``.
        wiki_root: directory where @wiki/shorts/X.md resolves to
            ``<wiki_root>/X.md``. Typically ``wiki/``.

    Returns:
        List of ``(agent_path, ref_string, problem_description)`` tuples.
        Empty list means every reference is valid and points at a
        ``status: ready`` target.
    """
    problems: list[tuple[Path, str, str]] = []
    for agent_md in agents_root.rglob("*.md"):
        for ref in find_refs_in_file(agent_md):
            # Strip the @wiki/shorts/ prefix to build a filesystem path.
            rel = ref[len("@wiki/shorts/"):]
            target = wiki_root / rel
            if not target.exists():
                problems.append((agent_md, ref, "target file does not exist"))
                continue
            try:
                fm = parse_frontmatter(target)
            except ValueError as e:
                problems.append(
                    (agent_md, ref, f"target frontmatter invalid: {e}")
                )
                continue
            if fm.get("status") != "ready":
                problems.append(
                    (
                        agent_md,
                        ref,
                        f"target status='{fm.get('status')}' (must be 'ready')",
                    )
                )
    return problems


__all__ = ["find_refs_in_file", "validate_all_agent_refs"]
