"""Tests proving pre_tool_use.py Hook denies selenium imports per AF-8.

Regression guard: AF-8 (Selenium永久禁止 — YouTube ToS 위반) is a hard
project-wide ban. If `.claude/deprecated_patterns.json` loses the
`\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import` regex, these tests
fail loudly.

The regex uses word boundaries so that mentioning "selenium" in a comment or
docstring (e.g. "we rejected selenium per AF-8") does NOT trip the block —
only actual `import selenium` or `from selenium ... import` syntax is denied.

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


def test_import_selenium_denied():
    """AF-8: bare `import selenium` statement is blocked."""
    res = _hook_check("Write", "import selenium\nimport other\n")
    assert res["decision"] == "deny", (
        f"AF-8 regression: import selenium allowed: {res}"
    )


def test_from_selenium_import_webdriver_denied():
    """AF-8: `from selenium import webdriver` — canonical top-level form, blocked.

    Regex is `\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import` — the
    second alternative requires `from` then whitespace then `selenium` then
    whitespace then `import`. The canonical `from selenium import webdriver`
    matches; submodule forms like `from selenium.webdriver import Chrome` are
    outside this regex's shape (see `test_from_selenium_submodule_allowed`
    — logged as a known regex gap, out of scope for Plan 05-09).
    """
    res = _hook_check(
        "Edit",
        "from selenium import webdriver\n",
    )
    assert res["decision"] == "deny", (
        f"AF-8 regression: from selenium import webdriver allowed: {res}"
    )


def test_from_selenium_submodule_allowed():
    """Known regex gap: `from selenium.webdriver import X` is NOT blocked.

    The current AF-8 regex (`\\bfrom\\s+selenium\\s+import`) requires literal
    `from selenium import` — submodule imports like
    `from selenium.webdriver import Chrome` bypass it. This test pins the
    current regex behavior so a future widening of the pattern (outside Plan
    05-09 scope) is a deliberate change, not a silent drift.
    """
    res = _hook_check(
        "Write",
        "from selenium.webdriver import Chrome\n",
    )
    assert res["decision"] == "allow", (
        f"Current AF-8 regex does NOT cover submodule imports; if this "
        f"became deny someone tightened the regex — update the regression "
        f"note in this test: {res}"
    )


def test_selenium_in_comment_allowed():
    """Mentioning 'selenium' in a comment (no `import`/`from`) is NOT blocked.

    The AF-8 regex `\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import`
    requires the word "import" or "from ... import" adjacent to "selenium".
    A pure documentation reference is allowed so that CLAUDE.md / comments
    can explain WHY selenium is banned.
    """
    res = _hook_check(
        "Write",
        "# We rejected selenium because of AF-8 (YouTube ToS)\n",
    )
    assert res["decision"] == "allow", (
        f"Comment mentioning selenium (no import) must be allowed: {res}"
    )


def test_selenium_import_in_multiedit_denied():
    """MultiEdit payload shape scans edits[*].new_string — selenium import blocked."""
    res = _hook_check(
        "MultiEdit",
        "import selenium\n",
    )
    assert res["decision"] == "deny", (
        f"AF-8 regression: selenium import via MultiEdit allowed: {res}"
    )
