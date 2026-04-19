"""D-12: A급 drift 0 — all deprecated_pattern_matches zero.

Plan 07-07 Task 7-07-04. Hard gate: after Wave 0-3 authored 132 Phase 7
tests, this plan re-runs the audit to confirm those additions introduced
no drift. Four distinct angles:

1. Every entry in deprecated_pattern_matches dict is 0.
2. Aggregate a_rank_drift_count == 0.
3. Phase 7 test authors must use split-literal / negative-assertion
   patterns (test_circuit_breaker_3x_open M3 protection) — asserted
   indirectly via audit aggregate == 0 after Phase 7 tests exist.
4. deprecated_patterns.json still carries all 8 regex (6 Phase 5 core +
   2 Phase 6 FAIL-01/FAIL-03 audit-trail markers).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"


def _run_audit_json(tmp_path: Path) -> dict:
    out = tmp_path / "audit.json"
    subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_all_deprecated_patterns_match_zero(tmp_path: Path):
    report = _run_audit_json(tmp_path)
    matches = report["deprecated_pattern_matches"]
    non_zero = {k: v for k, v in matches.items() if v != 0}
    assert non_zero == {}, (
        f"D-12 A급 drift violated: non-zero deprecated pattern matches: "
        f"{non_zero}"
    )


def test_a_rank_drift_count_is_zero(tmp_path: Path):
    report = _run_audit_json(tmp_path)
    assert report["a_rank_drift_count"] == 0, (
        f"a_rank_drift_count={report['a_rank_drift_count']} (expected 0)"
    )


def test_phase07_additions_do_not_trigger_drift_aggregate(tmp_path: Path):
    """Phase 7 test files (Wave 0-3 + Wave 4) must not re-introduce drift.

    After all Phase 7 test files are committed (Waves 0-3 = 132 tests,
    Wave 4 = this plan's 6 files), the audit aggregate must still be 0.
    Scanner is scoped to production code paths (scripts/orchestrator/ +
    scripts/hc_checks/) per the Phase 5 precedent, so Phase 7 tests only
    influence drift if they modify orchestrator/hc_checks directly.
    """
    report = _run_audit_json(tmp_path)
    total = sum(report["deprecated_pattern_matches"].values())
    assert total == 0, (
        f"deprecated_pattern_matches aggregate {total} != 0 after Phase 7 "
        f"tests authored. Breakdown: {report['deprecated_pattern_matches']}"
    )


def test_deprecated_patterns_json_has_at_least_8_entries():
    """Phase 5 (6) + Phase 6 (+2) = 8 deprecated_patterns.json entries minimum."""
    pj = _REPO / ".claude" / "deprecated_patterns.json"
    assert pj.exists(), f"Missing: {pj}"
    raw = json.loads(pj.read_text(encoding="utf-8"))
    patterns = raw.get("patterns", raw) if isinstance(raw, dict) else raw
    assert len(patterns) >= 8, (
        f"Expected >= 8 deprecated_patterns entries (6 Phase5 + 2 Phase6), "
        f"got {len(patterns)}"
    )


def test_every_deprecated_pattern_has_dict_entry(tmp_path: Path):
    """Every regex in deprecated_patterns.json must produce a key in the
    audit's deprecated_pattern_matches dict (one-to-one correspondence).
    """
    pj = _REPO / ".claude" / "deprecated_patterns.json"
    raw = json.loads(pj.read_text(encoding="utf-8"))
    patterns = raw.get("patterns", raw) if isinstance(raw, dict) else raw
    report = _run_audit_json(tmp_path)
    matches = report["deprecated_pattern_matches"]
    # Scanner should emit one key per pattern — at least as many keys as
    # patterns (could be more if legacy entries linger).
    assert len(matches) >= len(patterns), (
        f"deprecated_pattern_matches has {len(matches)} keys but "
        f"{len(patterns)} patterns defined"
    )
