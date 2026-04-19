"""NotebookLM subprocess wrapper per D-6 + D-7.

Contract
--------
- **D-6 (single-string query discipline)**: ``question`` MUST be a pre-composed
  single string. No newlines, no echo-to-stdin, no multi-question concatenation.
  The question flows through argv as a single list item — the Phase 6 CONTEXT
  D-6 anchor for the ``feedback_notebooklm_query.md`` memory rule.
- **D-7 (external skill reference, not copy)**: Call the external
  ``secondjob_naberal/.claude/skills/notebooklm`` skill via ``subprocess.run``.
  Never import its modules, never duplicate its Playwright venv, never copy
  browser_state. Path is resolved via (kwarg → env var → hardcoded fallback).
  Path anchor updated 2026-04-20 (session #24): migrated from the legacy
  ``shorts_naberal`` install to the active ``secondjob_naberal`` registry
  which holds the ``script-production-deep-research`` (대본제작용) notebook
  — the Phase 10 SCRIPT-gate RAG primary.

Encoding
--------
Per Phase 5 STATE decision #28, ``subprocess.run`` is invoked with
``encoding='utf-8'`` to survive the Windows cp949 default codec. Korean answers
and em-dashes in stderr would otherwise raise UnicodeDecodeError mid-pipeline.

Error propagation
-----------------
- Non-zero returncode -> ``RuntimeError`` carrying stderr (no silent swallow
  per Project Rule 3 — CLAUDE.md forbids silent fallback).
- Missing skill directory -> ``FileNotFoundError``.
- Subprocess hang beyond ``timeout_s + 30`` -> ``subprocess.TimeoutExpired``
  surfaces naturally.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# D-7 hardcoded fallback path — updated 2026-04-20 session #24.
# Legacy path was ``shorts_naberal`` (3 notebooks, no 대본제작용). Active
# registry lives at ``secondjob_naberal`` (5 notebooks, includes the
# 대본제작용 / ``script-production-deep-research`` required for SCRIPT gate).
# Env var ``NOTEBOOKLM_SKILL_PATH`` overrides for CI/portability/tests.
DEFAULT_SKILL_PATH = Path(r"C:/Users/PC/Desktop/secondjob_naberal/.claude/skills/notebooklm")

# FOLLOW_UP_REMINDER marker emitted at the tail of every ``ask_question.py``
# answer. Wrapper strips it so downstream consumers see clean answer text.
# Literal per RESEARCH Area 3 line 595.
FOLLOW_UP_MARKER = "EXTREMELY IMPORTANT: Is that ALL you need"


def _resolve_skill_path(skill_path: Path | None) -> Path:
    """Resolve the skill path per D-7 precedence: kwarg > env var > hardcoded."""
    if skill_path is not None:
        return skill_path
    env = os.environ.get("NOTEBOOKLM_SKILL_PATH")
    if env:
        return Path(env)
    return DEFAULT_SKILL_PATH


def _strip_follow_up(answer: str) -> str:
    """Remove the FOLLOW_UP_REMINDER marker and everything after it."""
    if FOLLOW_UP_MARKER in answer:
        return answer.split(FOLLOW_UP_MARKER)[0].rstrip()
    return answer


def query_notebook(
    question: str,
    notebook_id: str,
    timeout_s: int = 600,
    skill_path: Path | None = None,
) -> str:
    """Call the external NotebookLM skill's ``ask_question.py`` and return answer.

    Args:
        question: Pre-composed single string per D-6. No newlines, no
            multi-question bundling. Passed as a single argv item — Korean
            content survives because argv boundaries are not shell-parsed.
        notebook_id: Explicit notebook id per D-4 (no fallback to the skill's
            ``active_notebook_id``). Caller decides general vs channel-bible.
        timeout_s: Answer generation timeout in seconds. Subprocess timeout
            is ``timeout_s + 30`` to allow Playwright browser teardown.
        skill_path: Optional override. When ``None`` the resolver consults
            ``NOTEBOOKLM_SKILL_PATH`` env var, then falls back to
            ``DEFAULT_SKILL_PATH``.

    Returns:
        Answer text with the FOLLOW_UP_REMINDER marker and everything after
        it stripped. Trailing whitespace normalized.

    Raises:
        FileNotFoundError: Resolved skill directory does not exist.
        RuntimeError: Subprocess returned non-zero (auth expired, notebook
            missing, Playwright crash). Message carries stderr.
        subprocess.TimeoutExpired: Exceeded ``timeout_s + 30`` seconds.
    """
    sp = _resolve_skill_path(skill_path)
    if not sp.exists():
        raise FileNotFoundError(f"NotebookLM skill not found at {sp}")

    run_py = sp / "scripts" / "run.py"
    cmd = [
        sys.executable,
        str(run_py),
        "ask_question.py",
        "--question", question,
        "--notebook-id", notebook_id,
        "--timeout", str(timeout_s),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s + 30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"NotebookLM query failed (rc={result.returncode}) "
            f"notebook_id={notebook_id}: {result.stderr}"
        )
    return _strip_follow_up(result.stdout)
