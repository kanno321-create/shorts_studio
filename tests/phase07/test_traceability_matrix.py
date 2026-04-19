"""Automated REQ/SC coverage guard for 07-TRACEABILITY.md.

Plan 07-08 Task 2 — asserts every Phase 7 REQ (TEST-01..04 + AUDIT-02)
has at least one test file whose stem matches a registered marker; fails
if a new REQ is added without test coverage or a test file is renamed
without updating the marker map. Also asserts the 3 Research Correction
markers are acknowledged in the matrix.
"""
from __future__ import annotations

from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
TESTS_DIR = _REPO / "tests" / "phase07"
MATRIX = (
    _REPO
    / ".planning"
    / "phases"
    / "07-integration-test"
    / "07-TRACEABILITY.md"
)


PHASE7_REQS = ["TEST-01", "TEST-02", "TEST-03", "TEST-04", "AUDIT-02"]
PHASE7_SCS = ["SC1", "SC2", "SC3", "SC4", "SC5"]


REQ_TO_TEST_MARKERS: dict[str, list[str]] = {
    "TEST-01": ["test_e2e_happy_path", "test_notebooklm_tier2_only"],
    "TEST-02": [
        "test_operational_gate_count_equals_13",
        "test_verify_all_dispatched_13",
        "test_gate_order_violation",
        "test_checkpointer_atomic_writes_13",
    ],
    "TEST-03": [
        "test_circuit_breaker_3x_open",
        "test_cooldown_300s_enforced",
    ],
    "TEST-04": [
        "test_fallback_ken_burns_thumbnail",
        "test_failures_append_on_retry_exceeded",
    ],
    "AUDIT-02": [
        "test_harness_audit_json_schema",
        "test_harness_audit_score_ge_80",
        "test_skill_500_line_scan",
        "test_a_rank_drift_zero",
        "test_agent_count_invariant",
        "test_description_1024_scan",
    ],
}


def _test_stems() -> set[str]:
    return {p.stem for p in TESTS_DIR.glob("test_*.py")}


def test_traceability_md_exists() -> None:
    assert MATRIX.exists(), f"07-TRACEABILITY.md missing: {MATRIX}"


def test_every_req_present_in_matrix() -> None:
    content = MATRIX.read_text(encoding="utf-8")
    for req in PHASE7_REQS:
        assert req in content, f"{req} missing from 07-TRACEABILITY.md"


def test_every_sc_present_in_matrix() -> None:
    content = MATRIX.read_text(encoding="utf-8")
    for sc in PHASE7_SCS:
        assert sc in content, f"{sc} missing from 07-TRACEABILITY.md"


def test_every_req_has_at_least_one_test_file() -> None:
    stems = _test_stems()
    uncovered: list[str] = []
    for req, markers in REQ_TO_TEST_MARKERS.items():
        found = [m for m in markers if any(m in s for s in stems)]
        if not found:
            uncovered.append(req)
    assert uncovered == [], (
        f"UNCOVERED REQs (no matching test file on disk): {uncovered}"
    )


def test_correction_markers_present() -> None:
    """RESEARCH Corrections 1/2/3 MUST be acknowledged in traceability."""
    content = MATRIX.read_text(encoding="utf-8")
    assert "Correction 1" in content or "13 operational" in content, (
        "Correction 1 (13 operational gates) anchor missing from matrix"
    )
    assert "Correction 2" in content or "CircuitBreakerOpenError" in content, (
        "Correction 2 (CircuitBreakerOpenError) anchor missing from matrix"
    )
    assert "Correction 3" in content or "THUMBNAIL" in content, (
        "Correction 3 (THUMBNAIL ken-burns target) anchor missing from matrix"
    )


def test_plan_summary_lists_all_8_plans() -> None:
    content = MATRIX.read_text(encoding="utf-8")
    for plan_id in (
        "07-01",
        "07-02",
        "07-03",
        "07-04",
        "07-05",
        "07-06",
        "07-07",
        "07-08",
    ):
        assert plan_id in content, (
            f"Plan {plan_id} missing from Plan Summary table"
        )


def test_every_registered_marker_has_a_real_file() -> None:
    """Guard against silent typos — every marker in REQ_TO_TEST_MARKERS
    must correspond to a real tests/phase07/test_*.py file on disk."""
    stems = _test_stems()
    orphans: list[str] = []
    for req, markers in REQ_TO_TEST_MARKERS.items():
        for m in markers:
            if not any(m in s for s in stems):
                orphans.append(f"{req}: {m}")
    assert orphans == [], (
        f"Marker(s) in REQ_TO_TEST_MARKERS with no corresponding test file: "
        f"{orphans}"
    )
