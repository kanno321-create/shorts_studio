"""Locks the backward-compatibility invariant (Pitfall 8) + new --json-out D-11 emission.

Per 07-01-PLAN.md task 7-01-02:
- Legacy text line 'HARNESS_AUDIT_SCORE: N' MUST still appear on stdout (unchanged).
- When '--json-out PATH' is passed, the D-11 6-key JSON schema MUST be written to PATH.
- Both outputs co-exist; passing --json-out does not suppress the legacy text line.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"


def test_audit_script_exists():
    assert _AUDIT.exists(), f"harness_audit.py missing at {_AUDIT}"


def test_text_output_backward_compatible():
    """Pitfall 8: existing 'HARNESS_AUDIT_SCORE: N' line MUST still be printed."""
    result = subprocess.run(
        [sys.executable, str(_AUDIT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    # Exit code may be 0 or 1 depending on threshold; we only care about stdout line.
    assert "HARNESS_AUDIT_SCORE:" in result.stdout, (
        f"Backward-compat broken — legacy text line missing.\nSTDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_json_out_flag_emits_d11_schema(tmp_path: Path):
    """--json-out PATH must create a JSON file with the D-11 6 mandatory keys."""
    out = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    # Text output still present alongside JSON emission.
    assert "HARNESS_AUDIT_SCORE:" in result.stdout, (
        f"Text output suppressed by --json-out (Pitfall 8 violation).\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    # JSON file created.
    assert out.exists(), (
        f"--json-out did not create {out}\nSTDERR:\n{result.stderr}"
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    # D-11 6 mandatory keys.
    required = {
        "score",
        "a_rank_drift_count",
        "skill_over_500_lines",
        "agent_count",
        "description_over_1024",
        "deprecated_pattern_matches",
    }
    missing = required - set(report.keys())
    assert not missing, f"D-11 missing keys: {missing}\nGot keys: {sorted(report.keys())}"


def test_json_types_match_d11_contract(tmp_path: Path):
    """D-11 field types: score=int, lists stay lists, dict stays dict."""
    out = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(report["score"], int), f"score is {type(report['score'])}"
    assert 0 <= report["score"] <= 100, f"score out of range: {report['score']}"
    assert isinstance(report["a_rank_drift_count"], int)
    assert isinstance(report["skill_over_500_lines"], list)
    assert isinstance(report["agent_count"], int)
    assert isinstance(report["description_over_1024"], list)
    assert isinstance(report["deprecated_pattern_matches"], dict)


def test_json_out_includes_phase_and_timestamp(tmp_path: Path):
    """Metadata keys beyond the 6 mandatory — phase + ISO-8601 timestamp."""
    out = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report.get("phase") == 7
    assert isinstance(report.get("timestamp"), str)
    # ISO-8601 Z suffix form per D-11 sample.
    assert report["timestamp"].endswith("Z"), f"timestamp not ISO-8601 Z-suffixed: {report['timestamp']}"


def test_deprecated_pattern_matches_scans_8_patterns(tmp_path: Path):
    """deprecated_pattern_matches dict should have entries for each of the 8 patterns."""
    out = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    matches = report["deprecated_pattern_matches"]
    # deprecated_patterns.json has 8 regex entries; the scanner should emit one key per.
    assert len(matches) == 8, (
        f"Expected 8 deprecated-pattern keys, got {len(matches)}: {list(matches.keys())}"
    )
    # All counts must be ints >= 0.
    for key, count in matches.items():
        assert isinstance(count, int), f"{key} count is {type(count)}"
        assert count >= 0, f"{key} count is negative: {count}"


def test_json_out_preserves_exit_code_on_score_ge_threshold(tmp_path: Path):
    """Exit code unchanged by --json-out; threshold default 80, current baseline 90."""
    out = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    # Current baseline score >= 80 so exit 0 expected. If baseline changes, this test
    # still locks the invariant that --json-out does not alter exit semantics.
    report = json.loads(out.read_text(encoding="utf-8"))
    expected_exit = 0 if report["score"] >= 80 else 1
    assert result.returncode == expected_exit, (
        f"Exit code {result.returncode} does not match score-derived {expected_exit}."
    )
