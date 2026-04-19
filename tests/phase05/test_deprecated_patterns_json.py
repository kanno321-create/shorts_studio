"""Contract tests for .claude/deprecated_patterns.json (Phase 5 Plan 01 Task 3).

Without this file the pre_tool_use Hook silently allows everything
(RESEARCH §10). These tests assert the file exists, is valid JSON, and
contains the 6 required regex entries that enforce ORCH-08, ORCH-09,
VIDEO-01, AF-8 policies at the tool-call level.
"""
from __future__ import annotations

import json
import re


def test_file_exists(repo_root):
    path = repo_root / ".claude" / "deprecated_patterns.json"
    assert path.exists(), (
        f"Missing: {path} — Hook silently allows everything without it "
        f"(pre_tool_use.py load_patterns returns [])"
    )


def test_six_patterns(repo_root):
    path = repo_root / ".claude" / "deprecated_patterns.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["patterns"]) == 6


def test_required_regexes_present(repo_root):
    path = repo_root / ".claude" / "deprecated_patterns.json"
    patterns = json.loads(path.read_text(encoding="utf-8"))["patterns"]
    regexes = [p["regex"] for p in patterns]
    assert any("skip_gates" in r for r in regexes), "ORCH-08 regex missing"
    assert any("next-session" in r for r in regexes), "ORCH-09 regex missing"
    assert any(
        ("t2v" in r.lower()) or ("text_to_video" in r.lower()) for r in regexes
    ), "VIDEO-01 regex missing"
    assert any("selenium" in r for r in regexes), "AF-8 regex missing"


def test_every_regex_compiles(repo_root):
    """All 6 patterns must be valid Python regex (re.compile succeeds)."""
    path = repo_root / ".claude" / "deprecated_patterns.json"
    patterns = json.loads(path.read_text(encoding="utf-8"))["patterns"]
    for p in patterns:
        re.compile(p["regex"])  # raises re.error on invalid pattern


def test_every_pattern_has_reason(repo_root):
    """Every blocked pattern must explain why (for the deny message)."""
    path = repo_root / ".claude" / "deprecated_patterns.json"
    patterns = json.loads(path.read_text(encoding="utf-8"))["patterns"]
    for p in patterns:
        assert p.get("reason", "").strip(), "pattern missing reason field"
