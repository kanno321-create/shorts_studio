"""Tests proving pre_tool_use.py Hook denies skip_gates= patterns per ORCH-08 / D-8.

Regression guard: if .claude/deprecated_patterns.json loses the `skip_gates\\s*=`
regex, these tests fail loudly and reveal the CONFLICT_MAP A-6 gap is back.

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


def test_skip_gates_True_denied():
    """ORCH-08: function signature with skip_gates=True is blocked."""
    res = _hook_check(
        "Write",
        "def run(session_id, skip_gates=True):\n    pass\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-08 regression: skip_gates=True allowed: {res}"
    )


def test_skip_gates_False_denied():
    """ORCH-08: even `skip_gates=False` is blocked — the param name itself is forbidden."""
    res = _hook_check(
        "Write",
        "def run(session_id, skip_gates=False):\n    pass\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-08 regression: skip_gates=False allowed: {res}"
    )


def test_skip_gates_whitespace_denied():
    """Regex uses `\\s*` — must match `skip_gates = ...` with surrounding whitespace."""
    res = _hook_check(
        "Edit",
        "skip_gates = os.getenv('DEBUG')\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-08 regression: skip_gates = (whitespace) allowed: {res}"
    )


def test_skip_gates_kwarg_call_denied():
    """Call-site kwarg `skip_gates=True` in a function invocation also blocked."""
    res = _hook_check(
        "Write",
        "pipeline.run(session_id='abc', skip_gates=True)\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-08 regression: call-site skip_gates=True allowed: {res}"
    )


def test_skip_gates_in_multiedit_denied():
    """MultiEdit payload shape must also scan edits[*].new_string."""
    res = _hook_check(
        "MultiEdit",
        "def run(skip_gates=True):\n    return None\n",
    )
    assert res["decision"] == "deny", (
        f"ORCH-08 regression: skip_gates= via MultiEdit allowed: {res}"
    )
