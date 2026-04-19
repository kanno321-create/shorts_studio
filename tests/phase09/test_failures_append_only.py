"""D-12: record_feedback.py write must be Phase 6 Hook check_failures_append_only compatible.

Plan 09-04 target. Pitfall 2: open('w') truncates — must use 'a' mode OR the
read+append+write-full pattern (Hook accepts either form because prior content is preserved
as prefix). Verify via AST scan + write-preserve assertion + Hook 3종 forbidden-pattern scan.

Wave 0 state: module not importable — pytest.importorskip skips entire module. Plan 09-04
ships the implementation and these tests flip to green.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = _REPO_ROOT / "scripts" / "taste_gate" / "record_feedback.py"

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_source_file_exists():
    """Plan 09-04 target: scripts/taste_gate/record_feedback.py exists on disk."""
    assert SRC.exists(), f"{SRC} not yet created (Plan 09-04 target)"


def test_no_open_w_for_failures():
    """D-12 Pitfall 2: no `open(FAILURES_PATH, 'w')` — either 'a' mode or read+append+write pattern."""
    src_text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
                assert mode != "w", (
                    "Pitfall 2: open(path, 'w') truncates FAILURES.md — must use 'a' or read+append+write"
                )


def test_append_preserves_prior_content(tmp_failures_md, freeze_kst_2026_04_01, monkeypatch):
    """D-12: append operation preserves existing FAILURES.md content as prefix."""
    prior = tmp_failures_md.read_text(encoding="utf-8")
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)
    block = record_feedback.build_failures_block(
        "2026-04",
        [{"video_id": "jkl012", "score": 3, "title": "t", "comment": "c"}],
    )
    record_feedback.append_to_failures(block)
    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after.startswith(prior), "D-12 violated: prior content not preserved as prefix"
    assert "[taste_gate] 2026-04" in after, "New taste_gate block not appended"


def test_no_skip_gates_string():
    """Hook 3종 차단: scripts/taste_gate/record_feedback.py MUST NOT contain skip_gates string."""
    src_text = SRC.read_text(encoding="utf-8")
    assert "skip_gates" not in src_text, "skip_gates physically banned (pre_tool_use Hook)"


def test_no_todo_next_session():
    """Hook 3종 차단: no TODO(next-session) patterns."""
    src_text = SRC.read_text(encoding="utf-8")
    assert "TODO(next-session)" not in src_text, "TODO(next-session) physically banned (pre_tool_use Hook)"


def test_no_try_except_silent_fallback():
    """Hook 3종 차단: no bare try/except: pass patterns (Pitfall 6)."""
    src_text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for h in node.handlers:
                if len(h.body) == 1 and isinstance(h.body[0], ast.Pass):
                    pytest.fail("try/except: pass silent fallback banned (Pitfall 6)")
