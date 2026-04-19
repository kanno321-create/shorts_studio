"""NotebookLM integration per D-7 (external skill reference only, no code duplication).

Phase 6 Plan 03: query_notebook wrapper
Phase 6 Plan 04: library.json channel-bible entry (consumes query_notebook for canary check)
Phase 6 Plan 05: Fallback Chain (imports query_notebook as Tier 0 backend)

External skill is located at ``shorts_naberal/.claude/skills/notebooklm`` per D-7 —
studios/shorts never duplicates the Playwright venv or browser_state. Access is
subprocess-only via this wrapper.
"""
from __future__ import annotations

from .query import DEFAULT_SKILL_PATH, FOLLOW_UP_MARKER, query_notebook

__all__ = ["query_notebook", "DEFAULT_SKILL_PATH", "FOLLOW_UP_MARKER"]
