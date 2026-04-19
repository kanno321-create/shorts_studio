"""Contract tests for .claude/deprecated_patterns.json.

Phase 5 Plan 01 Task 3 seeded this file with 6 required regex entries
that enforce ORCH-08, ORCH-09, VIDEO-01, and AF-8 policies at the
tool-call level. Without the file the pre_tool_use Hook silently allows
everything (RESEARCH §10).

Phase 6 Plan 08 (FAIL-01 / FAIL-03, D-11 / D-12 / D-14) extended the
baseline from 6 to 8 patterns — adding:
  - FAIL-01 [REMOVED]/[DELETED] marker regex (audit trail for the
    Python-level check_failures_append_only check).
  - FAIL-03 SKILL.md direct-write marker regex (audit trail for the
    Python-level backup_skill_before_write check).

These additions are legitimate contract evolution, not regressions:
production Hook behaviour is unchanged for the original 6 patterns and
the two new entries are additive guardrails. The count assertion below
therefore pins to 8 with an explicit comment pointing at the Phase 6
plan that evolved the baseline.
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


def test_pattern_count_baseline(repo_root):
    """Phase 5 baseline = 6 patterns; Phase 6 Plan 08 added FAIL-01 / FAIL-03 => 8.

    Further additions MUST update this baseline in the same commit that
    introduces them, preserving the contract-evolution audit trail.
    """
    path = repo_root / ".claude" / "deprecated_patterns.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["patterns"]) == 8, (
        "Phase 6 Plan 08 pinned deprecated_patterns.json at 8 entries "
        "(6 Phase 5 core + 2 Phase 6 FAIL-01/FAIL-03 audit-trail markers). "
        "If you intentionally added a new pattern, update this baseline "
        "in the same commit."
    )


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
    """Every pattern (Phase 5 core + Phase 6 audit-trail additions) must
    be a valid Python regex (re.compile succeeds).
    """
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
