"""FAIL-01 subprocess integration tests for pre_tool_use.py Hook (D-11).

Spawns pre_tool_use.py as a fresh subprocess via sys.executable with payloads
modeling real Claude Code PreToolUse invocations and asserts the decision /
reason JSON shape matches the append-only contract.

Also includes regression guards:
    - Existing Phase 5 patterns (skip_gates) still deny
    - Edit on unrelated files not blocked for FAILURES-specific reason
    - _imported_from_shorts_naberal.md path is NOT blocked by the FAILURES check
      (D-14 immutability is separate enforcement, handled in Plan 11)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


# tests/phase06/test_hook_failures_block.py -> parents[2] = studios/shorts/
_REPO = Path(__file__).resolve().parents[2]
HOOK = _REPO / ".claude" / "hooks" / "pre_tool_use.py"


def _invoke_hook(tool_name: str, tool_input: dict) -> dict:
    """Run pre_tool_use.py as subprocess; return parsed JSON decision dict."""
    payload = {"tool_name": tool_name, "input": tool_input}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=10,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, (
        f"Hook exited {proc.returncode}: stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def test_hook_blocks_edit_on_failures_md():
    """Edit with non-empty old_string on FAILURES.md -> deny with D-11 reason."""
    result = _invoke_hook(
        "Edit",
        {
            "file_path": str(_REPO / ".claude" / "failures" / "FAILURES.md"),
            "old_string": "existing line to modify",
            "new_string": "new text",
        },
    )
    assert result["decision"] == "deny"
    assert "append-only" in result["reason"].lower() or "D-11" in result["reason"]


def test_hook_blocks_write_overwriting_failures_md():
    """Write with totally different content on existing FAILURES.md -> deny."""
    failures_path = _REPO / ".claude" / "failures" / "FAILURES.md"
    # failures_path exists from Task 2 seeding; if not, hook cannot compare prefix
    assert failures_path.exists(), "FAILURES.md must be seeded before this test"
    result = _invoke_hook(
        "Write",
        {
            "file_path": str(failures_path),
            "content": "# TOTALLY DIFFERENT\n\nNo prefix match.\n",
        },
    )
    assert result["decision"] == "deny"
    assert (
        "prefix" in result["reason"].lower() or "append-only" in result["reason"].lower()
    )


def test_hook_allows_edit_on_other_files():
    """Edit on unrelated file must NOT be denied for FAILURES-specific reason."""
    result = _invoke_hook(
        "Edit",
        {
            "file_path": str(
                _REPO / "scripts" / "orchestrator" / "shorts_pipeline.py"
            ),
            "old_string": "some_existing_var = 1",
            "new_string": "some_existing_var = 2",
        },
    )
    # May be allow or deny by other rules (deprecated_patterns regex) — but if deny,
    # the reason must NOT be the FAILURES append-only reason.
    if result["decision"] == "deny":
        assert "append-only" not in result.get("reason", "").lower()
        assert "FAILURES.md" not in result.get("reason", "")


def test_hook_allows_edit_on_imported_failures_file():
    """D-14 _imported_from_shorts_naberal.md is not 'FAILURES.md' basename —
    check_failures_append_only does not fire here. (Actual D-14 immutability
    enforcement is Plan 11's sha256 check.)"""
    result = _invoke_hook(
        "Edit",
        {
            "file_path": str(
                _REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
            ),
            "old_string": "existing text",
            "new_string": "modified",
        },
    )
    # Whatever the decision is, the FAILURES-specific append-only reason must NOT
    # appear for the imported file.
    if result["decision"] == "deny":
        assert "FAILURES.md" not in result.get("reason", "")


def test_hook_existing_phase5_blacklist_still_blocks():
    """Regression: skip_gates is still blocked by Phase 5 regex (8 patterns total)."""
    result = _invoke_hook(
        "Write",
        {
            "file_path": str(_REPO / "scripts" / "orchestrator" / "bad_skip.py"),
            "content": "def foo(skip_gates=True):\n    pass\n",
        },
    )
    assert result["decision"] == "deny"
    assert "skip_gates" in result["reason"].lower() or "CONFLICT_MAP" in result[
        "reason"
    ] or "ORCH-08" in result["reason"]


def test_hook_multiedit_on_failures_denied():
    """MultiEdit with non-empty old_string on FAILURES.md -> deny."""
    result = _invoke_hook(
        "MultiEdit",
        {
            "file_path": str(_REPO / ".claude" / "failures" / "FAILURES.md"),
            "edits": [
                {"old_string": "existing entry", "new_string": "modified"},
            ],
        },
    )
    assert result["decision"] == "deny"


def test_hook_write_append_to_failures_allowed():
    """Write that preserves existing FAILURES.md content as prefix -> allow."""
    failures_path = _REPO / ".claude" / "failures" / "FAILURES.md"
    assert failures_path.exists()
    existing = failures_path.read_text(encoding="utf-8")
    new_content = existing + "\n### FAIL-999: test append\n- transient test entry\n"
    result = _invoke_hook(
        "Write",
        {
            "file_path": str(failures_path),
            "content": new_content,
        },
    )
    # The content itself does NOT contain any Phase 5 deprecated pattern, so this
    # should be allowed by the append-only check. (If deny comes from another
    # check, we only care that it's not the FAILURES-specific reason.)
    if result["decision"] == "deny":
        # Must not be the append-only reason — that would be a false positive
        assert "append-only" not in result.get("reason", "").lower()
        assert "prefix" not in result.get("reason", "").lower()
    else:
        assert result["decision"] == "allow"
