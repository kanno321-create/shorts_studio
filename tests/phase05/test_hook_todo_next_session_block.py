"""Tests proving pre_tool_use.py Hook denies TODO(next-session) patterns per ORCH-09 / D-9.

Regression guard: if .claude/deprecated_patterns.json loses the
`TODO\\s*\\(\\s*next-session` regex, these tests fail loudly and the
CONFLICT_MAP A-5 gap is back.

The Hook allows ordinary `TODO:` or `TODO(fix this)` comments — only the
specific `TODO(next-session` marker is blocked (D-9: forbidden deferred-work
pattern).

Payload shape per Claude Code PreToolUse spec:
    - Write     -> input.content
    - Edit      -> input.new_string (+ old_string)
    - MultiEdit -> input.edits[*].new_string
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parents[2]
HOOK = STUDIO_ROOT / ".claude" / "hooks" / "pre_tool_use.py"


def _hook_check(
    tool_name: str,
    content: str,
    file_path: str = "scripts/orchestrator/shorts_pipeline.py",
) -> dict:
    tool_input: dict = {"file_path": file_path}
    if tool_name == "Write":
        tool_input["content"] = content
    elif tool_name == "Edit":
        tool_input["old_string"] = ""
        tool_input["new_string"] = content
    elif tool_name == "MultiEdit":
        tool_input["edits"] = [{"old_string": "", "new_string": content}]
    else:
        tool_input["content"] = content
    payload = {"tool_name": tool_name, "input": tool_input}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        cwd=str(STUDIO_ROOT),
    )
    assert proc.returncode == 0, (
        f"Hook exited {proc.returncode}: stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def test_todo_next_session_comment_denied():
    """ORCH-09: canonical `# TODO(next-session): ...` Python comment blocked."""
    res = _hook_check(
        "Edit",
        "# TODO(next-session): wire remaining inspectors\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-09 regression: TODO(next-session) allowed: {res}"
    )


def test_todo_next_session_no_colon_denied():
    """Regex does not require closing paren or colon — partial marker still blocked."""
    res = _hook_check(
        "Write",
        "# TODO(next-session) finish this before Phase 6\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-09 regression: TODO(next-session) without colon allowed: {res}"
    )


def test_todo_next_session_extra_whitespace_denied():
    """Regex uses `\\s*` around paren — `TODO  (  next-session` also blocked."""
    res = _hook_check(
        "Write",
        "# TODO  (  next-session  ): finish this\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-09 regression: TODO  (  next-session allowed: {res}"
    )


def test_todo_next_session_in_docstring_denied():
    """Inside triple-quoted docstring still scanned — blacklist applies to full content."""
    res = _hook_check(
        "Write",
        '"""This module is a TODO(next-session) placeholder."""\n',
    )
    assert res["decision"] == "deny", (
        f"ORCH-09 regression: TODO(next-session) in docstring allowed: {res}"
    )


def test_ordinary_todo_still_allowed():
    """Plain `TODO:` without `(next-session)` is NOT blocked — normal TODOs allowed."""
    res = _hook_check(
        "Write",
        "# TODO: refactor this function later\n",
    )
    assert res["decision"] == "allow", (
        f"Plain TODO comment must be allowed: {res}"
    )


def test_todo_next_session_in_multiedit_denied():
    """MultiEdit payload shape scans edits[*].new_string — TODO(next-session blocked."""
    res = _hook_check(
        "MultiEdit",
        "# TODO(next-session): finish remaining inspectors\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-09 regression: TODO(next-session) via MultiEdit allowed: {res}"
    )
