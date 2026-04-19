"""D-11: harness_audit.py --json-out emits 6-key schema (+ metadata).

Plan 07-07 Task 7-07-01. Locks the D-11 schema contract:
- 6 mandatory keys: score, a_rank_drift_count, skill_over_500_lines,
  agent_count, description_over_1024, deprecated_pattern_matches.
- Type constraints per interfaces block in 07-07-PLAN.md.
- Metadata: phase + ISO-8601 timestamp.

Complements tests/phase07/test_harness_audit_json_flag.py (Wave 0) by
adding per-key type + range assertions in dedicated focused tests so a
single dimension regression is immediately diagnosable.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"


@pytest.fixture
def audit_json(tmp_path: Path) -> dict:
    out = tmp_path / "audit.json"
    result = subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    assert out.exists(), (
        f"--json-out did not produce file; stderr:\n{result.stderr}\n"
        f"stdout:\n{result.stdout}"
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_d11_has_all_6_required_keys(audit_json):
    required = {
        "score",
        "a_rank_drift_count",
        "skill_over_500_lines",
        "agent_count",
        "description_over_1024",
        "deprecated_pattern_matches",
    }
    missing = required - set(audit_json.keys())
    assert not missing, f"D-11 missing keys: {missing}"


def test_score_is_int_0_to_100(audit_json):
    assert isinstance(audit_json["score"], int)
    assert 0 <= audit_json["score"] <= 100


def test_a_rank_drift_count_is_nonnegative_int(audit_json):
    assert isinstance(audit_json["a_rank_drift_count"], int)
    assert audit_json["a_rank_drift_count"] >= 0


def test_skill_over_500_lines_is_list_of_str(audit_json):
    assert isinstance(audit_json["skill_over_500_lines"], list)
    for item in audit_json["skill_over_500_lines"]:
        assert isinstance(item, str)


def test_agent_count_is_positive_int(audit_json):
    assert isinstance(audit_json["agent_count"], int)
    assert audit_json["agent_count"] >= 1


def test_description_over_1024_is_list_of_str(audit_json):
    assert isinstance(audit_json["description_over_1024"], list)
    for item in audit_json["description_over_1024"]:
        assert isinstance(item, str)


def test_deprecated_pattern_matches_is_dict(audit_json):
    assert isinstance(audit_json["deprecated_pattern_matches"], dict)
    for key, value in audit_json["deprecated_pattern_matches"].items():
        assert isinstance(key, str)
        assert isinstance(value, int)
        assert value >= 0


def test_metadata_fields_present(audit_json):
    assert "phase" in audit_json
    assert "timestamp" in audit_json
    assert isinstance(audit_json["timestamp"], str)
    assert audit_json["timestamp"].endswith("Z") or "T" in audit_json["timestamp"]
