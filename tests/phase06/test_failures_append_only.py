"""FAIL-01 unit tests for check_failures_append_only (D-11).

In-process import of the Hook helper; verifies the decision matrix:
    - Edit with non-empty old_string -> deny
    - Edit with empty old_string -> allow (insertion at start)
    - Write with new content NOT starting with existing -> deny
    - Write with new content starting with existing -> allow (strict append)
    - Write when file does not exist -> allow (first-time create)
    - MultiEdit with any non-empty old_string -> deny
    - MultiEdit with only empty old_strings -> allow
    - Path separator agnostic (backslash on Windows also recognized)
    - Unrelated files pass through (no file_path issue)
    - _imported_from_shorts_naberal.md is EXEMPT (basename != FAILURES.md) — D-14 handled elsewhere

Directly imports pre_tool_use from studios/shorts/.claude/hooks/ by adding that dir to sys.path.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


# tests/phase06/test_failures_append_only.py -> parents[2] = studios/shorts/
_REPO = Path(__file__).resolve().parents[2]
_HOOK_PATH = _REPO / ".claude" / "hooks"
if str(_HOOK_PATH) not in sys.path:
    sys.path.insert(0, str(_HOOK_PATH))

pre_tool_use = importlib.import_module("pre_tool_use")
check_failures_append_only = pre_tool_use.check_failures_append_only


def test_edit_existing_line_denied():
    """Edit with a non-empty old_string on FAILURES.md must deny."""
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "old_string": "### FAIL-001: existing entry",
            "new_string": "### FAIL-001: modified",
        },
    )
    assert result is not None
    assert "append-only" in result.lower() or "D-11" in result


def test_edit_empty_old_string_allowed():
    """Edit with empty old_string (insertion at start) is allowed."""
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "old_string": "",
            "new_string": "new content",
        },
    )
    assert result is None


def test_edit_whitespace_only_old_string_allowed():
    """old_string = whitespace only is treated as empty (no semantic modification)."""
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "old_string": "   \n  ",
            "new_string": "content",
        },
    )
    assert result is None


def test_imported_file_exempt_from_append_only():
    """D-14: _imported_from_shorts_naberal.md is NOT FAILURES.md — this check passes it through.

    (Actual immutability of the imported file is enforced by a separate sha256 check
    in Plan 11; check_failures_append_only only guards FAILURES.md.)
    """
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": "/repo/.claude/failures/_imported_from_shorts_naberal.md",
            "old_string": "some existing line",
            "new_string": "modified",
        },
    )
    assert result is None


def test_unrelated_file_passes_through():
    """File with unrelated basename is never blocked by this check."""
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": "/repo/scripts/foo.py",
            "old_string": "x = 1",
            "new_string": "x = 2",
        },
    )
    assert result is None


def test_write_without_prefix_denied(tmp_path: Path):
    """Write whose new content is NOT a strict prefix-preserving extension -> deny."""
    f = tmp_path / "FAILURES.md"
    f.write_text("existing content line 1\nexisting content line 2\n", encoding="utf-8")
    result = check_failures_append_only(
        "Write",
        {
            "file_path": str(f),
            "content": "totally new different content",
        },
    )
    assert result is not None
    assert "prefix" in result.lower() or "append-only" in result.lower()


def test_write_with_prefix_allowed(tmp_path: Path):
    """Write that appends new text AFTER preserving existing content verbatim -> allow."""
    f = tmp_path / "FAILURES.md"
    existing = "existing content line 1\nexisting content line 2\n"
    f.write_text(existing, encoding="utf-8")
    result = check_failures_append_only(
        "Write",
        {
            "file_path": str(f),
            "content": existing + "\n### FAIL-003: new entry\n",
        },
    )
    assert result is None


def test_write_to_nonexistent_failures_allowed(tmp_path: Path):
    """First-time creation of FAILURES.md — no existing content, always allowed."""
    f = tmp_path / "FAILURES.md"
    assert not f.exists()
    result = check_failures_append_only(
        "Write",
        {
            "file_path": str(f),
            "content": "# FAILURES\n\nFirst entry\n",
        },
    )
    assert result is None


def test_multiedit_nonempty_old_string_denied():
    """MultiEdit with any edit having non-empty old_string -> deny."""
    result = check_failures_append_only(
        "MultiEdit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "edits": [
                {"old_string": "existing line", "new_string": "modified"},
            ],
        },
    )
    assert result is not None
    assert "append-only" in result.lower() or "D-11" in result


def test_multiedit_only_empty_old_strings_allowed():
    """MultiEdit with all empty old_strings (pure insertion) -> allow."""
    result = check_failures_append_only(
        "MultiEdit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "edits": [
                {"old_string": "", "new_string": "appended text"},
            ],
        },
    )
    assert result is None


def test_multiedit_mixed_denied():
    """MultiEdit with even one non-empty old_string among several -> deny."""
    result = check_failures_append_only(
        "MultiEdit",
        {
            "file_path": "/repo/.claude/failures/FAILURES.md",
            "edits": [
                {"old_string": "", "new_string": "fine"},
                {"old_string": "existing", "new_string": "bad"},
            ],
        },
    )
    assert result is not None


def test_windows_path_separator_recognized():
    """Path separator agnostic: backslashes should still be recognized as FAILURES.md."""
    result = check_failures_append_only(
        "Edit",
        {
            "file_path": r"C:\repo\.claude\failures\FAILURES.md",
            "old_string": "some line",
            "new_string": "modified",
        },
    )
    assert result is not None


def test_missing_file_path_allowed():
    """Empty / missing file_path -> allow (not our concern, other checks handle)."""
    assert check_failures_append_only("Edit", {}) is None
    assert (
        check_failures_append_only(
            "Edit", {"file_path": "", "old_string": "x", "new_string": "y"}
        )
        is None
    )


def test_non_basename_match_with_substring_allowed():
    """A file literally named FAILURES.md.bak or FAILURES_INDEX.md should NOT be blocked."""
    assert (
        check_failures_append_only(
            "Edit",
            {
                "file_path": "/repo/.claude/failures/FAILURES_INDEX.md",
                "old_string": "some existing line",
                "new_string": "modified",
            },
        )
        is None
    )
    assert (
        check_failures_append_only(
            "Edit",
            {
                "file_path": "/repo/.claude/failures/FAILURES.md.bak",
                "old_string": "some existing line",
                "new_string": "modified",
            },
        )
        is None
    )
