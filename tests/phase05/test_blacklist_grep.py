"""SC 2 + SC 5 + D-8/D-9/D-13 grep contract tests.

Pure-Python recursive grep across ``scripts/orchestrator/`` and
``scripts/hc_checks/`` asserting forbidden identifiers are absent.

These tests mirror the regexes ``scripts/validate/phase05_acceptance.py``
uses for SC 2 and SC 5 so a PASS here guarantees a PASS there. In
particular the T2V assertion is **case-sensitive word-boundary** — it
catches lowercase ``t2v`` (a future dev re-introducing the banned code
path with the literal identifier the pre_tool_use Hook denies) while
deliberately allowing PascalCase ``T2VForbidden`` (the runtime sentinel
class D-13 mandates) and uppercase ``T2V`` in docstrings/comments that
explain the ban. Matches verify_hook_blocks.py + phase05_acceptance.py
semantics exactly.

If any of these fail, Phase 5 cannot ship.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCH = REPO / "scripts" / "orchestrator"
HC = REPO / "scripts" / "hc_checks"


def _grep_recursive(
    pattern: str,
    *paths: Path,
    case_insensitive: bool = False,
    exclude_pycache: bool = True,
) -> list[str]:
    """Pure-Python recursive grep. Returns list of matching ``file:line: content`` strings.

    Walks only ``*.py`` files. Skips ``__pycache__`` directories by
    default so compiled bytecode is never false-positively matched.
    """
    flags = re.IGNORECASE if case_insensitive else 0
    regex = re.compile(pattern, flags)
    matches: list[str] = []
    for root in paths:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if exclude_pycache and "__pycache__" in p.parts:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if regex.search(line):
                    matches.append(f"{p.relative_to(REPO)}:{i}: {line.strip()}")
    return matches


def test_no_skip_gates_in_orchestrator() -> None:
    """SC 2 / D-8 / ORCH-08: ``skip_gates`` must not appear in scripts/orchestrator/."""
    matches = _grep_recursive(r"skip_gates", ORCH)
    assert matches == [], "SC 2 VIOLATED: skip_gates found:\n" + "\n".join(matches)


def test_no_skip_gates_in_hc_checks() -> None:
    """SC 2 extended: ``skip_gates`` must not appear in scripts/hc_checks/."""
    matches = _grep_recursive(r"skip_gates", HC)
    assert matches == [], "SC 2 VIOLATED in hc_checks:\n" + "\n".join(matches)


def test_no_t2v_in_orchestrator() -> None:
    """SC 5 / D-13 / VIDEO-01: forbidden T2V identifiers absent from scripts/orchestrator/.

    Uses the same **case-sensitive** word-boundary regex as
    ``phase05_acceptance.py`` so PascalCase ``T2VForbidden`` (the D-13
    runtime sentinel class name) and uppercase ``T2V`` documentation
    mentions are not false positives, while the literal lowercase
    identifiers a dev would type to re-introduce the banned code path
    (``t2v``, ``text_to_video``, ``text2video``) are caught.
    """
    pattern = r"(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video"
    matches = _grep_recursive(pattern, ORCH, case_insensitive=False)
    assert matches == [], "SC 5 VIOLATED: T2V patterns found:\n" + "\n".join(matches)


def test_no_t2v_in_hc_checks() -> None:
    """SC 5 extended: forbidden T2V identifiers absent from scripts/hc_checks/."""
    pattern = r"(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video"
    matches = _grep_recursive(pattern, HC, case_insensitive=False)
    assert matches == [], "SC 5 VIOLATED in hc_checks:\n" + "\n".join(matches)


def test_no_todo_next_session_in_orchestrator() -> None:
    """D-9 / ORCH-09: ``TODO(next-session)`` must not appear in scripts/orchestrator/."""
    matches = _grep_recursive(r"TODO\s*\(\s*next-session", ORCH)
    assert matches == [], "D-9 VIOLATED: TODO(next-session) found:\n" + "\n".join(matches)


def test_no_todo_next_session_in_hc_checks() -> None:
    """D-9 extended: ``TODO(next-session)`` must not appear in scripts/hc_checks/."""
    matches = _grep_recursive(r"TODO\s*\(\s*next-session", HC)
    assert matches == [], "D-9 VIOLATED in hc_checks:\n" + "\n".join(matches)


def test_no_segments_bracket_in_orchestrator() -> None:
    """Phase 3 canonical: ``cuts[]`` not ``segments[]`` (RESEARCH §10)."""
    matches = _grep_recursive(r"segments\s*\[\s*\]", ORCH)
    assert matches == [], "CANONICAL VIOLATED: segments[] found (use cuts[]):\n" + "\n".join(matches)


def test_no_selenium_imports_in_orchestrator() -> None:
    """AF-8: selenium imports forbidden anywhere in scripts/orchestrator/."""
    # Matches both ``import selenium`` and ``from selenium[.submodule] import ...``
    pattern = r"\bimport\s+selenium\b|\bfrom\s+selenium(\.[a-z_]+)*\s+import\b"
    matches = _grep_recursive(pattern, ORCH)
    assert matches == [], "AF-8 VIOLATED: selenium imports found:\n" + "\n".join(matches)


def test_no_selenium_imports_in_hc_checks() -> None:
    """AF-8 extended: selenium imports forbidden in scripts/hc_checks/."""
    pattern = r"\bimport\s+selenium\b|\bfrom\s+selenium(\.[a-z_]+)*\s+import\b"
    matches = _grep_recursive(pattern, HC)
    assert matches == [], "AF-8 VIOLATED in hc_checks:\n" + "\n".join(matches)


def test_orchestrator_package_exists() -> None:
    """Sanity — Plan 01 created scripts/orchestrator/."""
    assert ORCH.exists() and ORCH.is_dir(), "scripts/orchestrator/ missing"


def test_shorts_pipeline_exists() -> None:
    """Sanity — Plan 07 created the 500-800 line keystone."""
    assert (ORCH / "shorts_pipeline.py").exists(), "shorts_pipeline.py missing"
