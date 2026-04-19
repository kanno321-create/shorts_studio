"""Wave 4 PUB-05 ANCHOR B — captions.insert + endScreen + end_screen_subscribe_cta NOT an API call.

Per RESEARCH Pitfall 7 + CONTEXT D-09:

- ``captions.insert`` is for SUBTITLES, not end-screens. Phase 4 AGENT.md
  mentions it incorrectly; the publisher module MUST NOT call it.
- ``endScreen`` is NOT a writable field on the videos resource —
  YouTube Studio UI only. Any ``endScreen=...`` assignment or
  ``"endScreen": ...`` dict key in executable code is a violation.
- ``end_screen_subscribe_cta`` is a PLAN-level intent (Phase 4 AGENT.md
  emits it on the funnel key). The publisher reads it from the plan
  dict but MUST NOT translate it into any ``.execute()`` API call.
  Mentions in comments documenting the drop are permitted.

Four redundant checks layered here so a future regression can't slip
through any single defence:

1. Textual scan of executable lines (non-comment) for ``.captions().insert(``.
2. Textual scan for ``endScreen=`` assignment or ``"endScreen":`` dict key.
3. Textual scan for the escalation pattern ``end_screen_subscribe_cta =
   True ... .execute(`` (plan-intent → API-call).
4. AST walk for any ``youtube.captions().insert(...)`` Call node.

If any of these fires, the uploader has regressed and the smoke test
(Plan 08-06) would burn real YouTube channel history — BLOCK at CI.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_PUBLISHER_DIR = _REPO_ROOT / "scripts" / "publisher"


def _scan(pattern: str) -> list[str]:
    """Return ``file:lineno:line`` hits for executable (non-comment) lines.

    A line is treated as a pure comment when its first non-whitespace
    character is ``#``. Triple-quoted docstrings are NOT filtered here —
    the callers pick patterns specific enough that docstring mentions
    don't trigger. Each hit is truncated to 100 chars for readable
    assertion messages.
    """
    rx = re.compile(pattern)
    hits: list[str] = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if rx.search(line):
                hits.append(f"{py}:{i}:{line.strip()[:100]}")
    return hits


def test_zero_captions_insert_call_sites():
    """ANCHOR B step 1 — no .captions().insert(...) chain in executable code."""
    hits = _scan(r"\.captions\(\)\.insert\(")
    assert not hits, f"ANCHOR B violation (captions.insert): {hits}"


def test_zero_endscreen_assignment_or_dict_key():
    """ANCHOR B step 2 — no endScreen= nor 'endScreen':."""
    hits = _scan(r"\bendScreen\s*=|[\"']endScreen[\"']\s*:")
    assert not hits, f"ANCHOR B violation (endScreen): {hits}"


def test_end_screen_subscribe_cta_not_invoked_as_api():
    """ANCHOR B step 3 — end_screen_subscribe_cta may be mentioned in
    comments or READ from plan dict, but MUST NOT drive a .execute() call.
    """
    hits = _scan(r"end_screen_subscribe_cta\s*=\s*True.*\.execute\(")
    assert not hits, f"ANCHOR B violation (end_screen as API): {hits}"


def test_ast_no_captions_insert_call():
    """ANCHOR B step 4 — AST walk for any ``x.captions().insert(...)`` Call."""
    violations: list[str] = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "insert"
                and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Attribute)
                and node.func.value.func.attr == "captions"
            ):
                violations.append(f"{py}:{node.lineno}")
    assert not violations, f"ANCHOR B AST violation: {violations}"


def test_pitfall_7_reference_present_in_uploader():
    """Drop-documentation guardrail — if the uploader silently omits the
    end-screen mapping, the inline comment MUST reference the reason so a
    future reader doesn't re-add it by mistake.
    """
    source = (_PUBLISHER_DIR / "youtube_uploader.py").read_text(encoding="utf-8")
    assert (
        "Pitfall 7" in source
        or "D-09" in source
        or "end_screen_subscribe_cta" in source
    ), "Uploader must document the end-screen drop reason (Pitfall 7 / D-09)"
