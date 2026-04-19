"""Tests proving pre_tool_use.py Hook denies T2V patterns per VIDEO-01 / D-13.

Regression guard: if .claude/deprecated_patterns.json loses the T2V regex or
the Hook contract changes, these tests fail loudly.

Each test spawns pre_tool_use.py as a fresh subprocess via sys.executable with
a JSON payload on stdin and asserts the Hook's stdout contains
{"decision": "deny"} for forbidden T2V content.

Covers ORCH / VIDEO-01 deliverable: Hook denies Write/Edit/MultiEdit adding
`t2v`, `text_to_video`, or `text2video` identifiers.

Payload shape per Claude Code PreToolUse spec (matches verify_hook_blocks.py
reference implementation from Plan 01):
    - Write     -> input.content
    - Edit      -> input.new_string (+ old_string)
    - MultiEdit -> input.edits[*].new_string
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# tests/phase05/test_hook_t2v_block.py -> parents[2] = studios/shorts/
STUDIO_ROOT = Path(__file__).resolve().parents[2]
HOOK = STUDIO_ROOT / ".claude" / "hooks" / "pre_tool_use.py"


def _hook_check(
    tool_name: str,
    content: str,
    file_path: str = "scripts/orchestrator/shorts_pipeline.py",
) -> dict:
    """Spawn pre_tool_use.py with a mock payload; return parsed JSON response.

    Honors the per-tool payload shape the Hook reads (Plan 01 Task 4 learning).
    """
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


def test_t2v_word_denied():
    """D-13: bare 't2v' as an identifier (e.g. function name) is blocked."""
    res = _hook_check("Write", "def make_t2v_clip():\n    pass\n")
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 't2v' identifier allowed: {res}"
    )


def test_text_to_video_denied():
    """D-13: literal `text_to_video` function name is blocked (Write)."""
    res = _hook_check(
        "Write",
        "def text_to_video(prompt: str) -> str:\n    return ''\n",
    )
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 'text_to_video' allowed: {res}"
    )


def test_text2video_denied():
    """D-13: literal `text2video` (no underscore) is blocked (Edit)."""
    res = _hook_check("Edit", "# Calling the text2video API endpoint\n")
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 'text2video' allowed: {res}"
    )


def test_t2v_inside_comment_denied():
    """Hook regex matches anywhere in content — comment inclusion does NOT exempt."""
    res = _hook_check(
        "Write",
        "# legacy note: we used to support t2v rendering here\n",
    )
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 't2v' in comment allowed: {res}"
    )


def test_t2v_inside_python_string_denied():
    """Any occurrence is blocked — prevents workarounds via dynamic strings."""
    res = _hook_check("Write", "API_NAME = 'text_to_video_v1'\n")
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 'text_to_video' in string literal allowed: {res}"
    )


def test_text_to_video_in_multiedit_denied():
    """MultiEdit payload shape carries edits[*].new_string — must also be scanned."""
    res = _hook_check(
        "MultiEdit",
        "from . import text_to_video as _t2v\n",
    )
    assert res["decision"] == "deny", (
        f"VIDEO-01 regression: 'text_to_video' in MultiEdit allowed: {res}"
    )
