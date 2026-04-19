"""Automated 17-REQ coverage test for Phase 5.

Asserts each REQ ID from REQUIREMENTS.md Phase 5 section appears in at
least one test file in ``tests/phase05/`` whose stem matches a
registered marker. If a new REQ is added in the future or a test file is
renamed without updating ``REQ_TO_MARKERS`` below, this test fails
loudly so the drift is visible in CI before the traceability doc goes
stale.

Also verifies the companion doc ``05-TRACEABILITY.md`` exists and names
every REQ.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO / "tests" / "phase05"
TRACEABILITY = (
    REPO / ".planning" / "phases" / "05-orchestrator-v2-write" / "05-TRACEABILITY.md"
)
VALIDATION = (
    REPO / ".planning" / "phases" / "05-orchestrator-v2-write" / "05-VALIDATION.md"
)
REQUIREMENTS = REPO / ".planning" / "REQUIREMENTS.md"

# The 17 Phase 5 REQs (per REQUIREMENTS.md Phase 5 section).
PHASE5_REQS: list[str] = [
    "ORCH-01", "ORCH-02", "ORCH-03", "ORCH-04", "ORCH-05", "ORCH-06",
    "ORCH-07", "ORCH-08", "ORCH-09", "ORCH-10", "ORCH-11", "ORCH-12",
    "VIDEO-01", "VIDEO-02", "VIDEO-03", "VIDEO-04", "VIDEO-05",
]

# REQ -> list of test-file stem substrings. A REQ is considered covered
# if at least one ``tests/phase05/test_*.py`` file's stem contains at
# least one of its markers. Multiple markers per REQ = OR relation (any
# match covers the REQ); the matrix favors redundancy so single-file
# deletion does not silently break coverage.
REQ_TO_MARKERS: dict[str, list[str]] = {
    "ORCH-01": ["test_line_count", "test_shorts_pipeline"],
    "ORCH-02": ["test_gate_enum", "test_dag_declaration", "test_shorts_pipeline"],
    "ORCH-03": ["test_gate_guard", "test_exceptions"],
    "ORCH-04": ["test_verify_all_dispatched", "test_shorts_pipeline"],
    "ORCH-05": ["test_checkpointer_roundtrip", "test_checkpointer_resume"],
    "ORCH-06": ["test_circuit_breaker", "test_circuit_breaker_cooldown"],
    "ORCH-07": ["test_dag_declaration", "test_gate_guard"],
    "ORCH-08": ["test_hook_skip_gates_block", "test_blacklist_grep",
                "test_deprecated_patterns_json"],
    "ORCH-09": ["test_hook_todo_next_session_block", "test_blacklist_grep",
                "test_deprecated_patterns_json"],
    "ORCH-10": ["test_voice_first_timeline", "test_shorts_pipeline",
                "test_typecast_adapter", "test_elevenlabs_adapter"],
    "ORCH-11": ["test_low_res_first", "test_shotstack_adapter"],
    "ORCH-12": ["test_fallback_shot", "test_shorts_pipeline"],
    "VIDEO-01": ["test_hook_t2v_block", "test_kling_adapter", "test_blacklist_grep",
                 "test_hook_allows_i2v"],
    "VIDEO-02": ["test_i2v_request_schema", "test_voice_first_timeline"],
    "VIDEO-03": ["test_transition_shots", "test_voice_first_timeline"],
    "VIDEO-04": ["test_kling_runway_failover", "test_kling_adapter"],
    "VIDEO-05": ["test_shotstack_adapter"],
}


def _test_file_stems() -> set[str]:
    return {p.stem for p in TESTS_DIR.glob("test_*.py")}


def test_seventeen_phase5_reqs() -> None:
    """Sanity: Phase 5 has exactly 17 REQs (12 ORCH + 5 VIDEO)."""
    assert len(PHASE5_REQS) == 17


def test_marker_map_covers_every_req() -> None:
    """REQ_TO_MARKERS must contain an entry for each PHASE5_REQS ID."""
    missing = [req for req in PHASE5_REQS if req not in REQ_TO_MARKERS]
    assert not missing, f"REQ_TO_MARKERS missing entries for: {missing}"


def test_every_req_has_test_coverage() -> None:
    """Every Phase 5 REQ has at least one matching test file on disk."""
    stems = _test_file_stems()
    uncovered: list[tuple[str, list[str]]] = []
    for req in PHASE5_REQS:
        markers = REQ_TO_MARKERS[req]
        if not any(marker in stem for stem in stems for marker in markers):
            uncovered.append((req, markers))
    assert not uncovered, (
        "UNCOVERED REQs (no test stem matches any marker): " + ", ".join(
            f"{req} (markers: {markers})" for req, markers in uncovered
        )
    )


def test_traceability_doc_exists() -> None:
    """Plan 10 Task 3 produced the traceability matrix doc."""
    assert TRACEABILITY.exists(), f"Missing traceability doc: {TRACEABILITY}"


def test_traceability_doc_names_every_req() -> None:
    """Every Phase 5 REQ ID appears in the traceability matrix doc body."""
    content = TRACEABILITY.read_text(encoding="utf-8", errors="replace")
    missing = [req for req in PHASE5_REQS if req not in content]
    assert not missing, f"Traceability doc missing REQs: {missing}"


def test_validation_doc_exists() -> None:
    """Phase 5 VALIDATION.md must be present for Plan 10 Task 4 to flip."""
    assert VALIDATION.exists(), f"Missing validation doc: {VALIDATION}"


def test_requirements_doc_marks_all_phase5_reqs_complete() -> None:
    """All 17 Phase 5 REQs appear as [x] complete in REQUIREMENTS.md."""
    content = REQUIREMENTS.read_text(encoding="utf-8", errors="replace")
    not_complete: list[str] = []
    for req in PHASE5_REQS:
        needle = f"- [x] **{req}**"
        if needle not in content:
            not_complete.append(req)
    assert not not_complete, (
        "REQs not marked complete in REQUIREMENTS.md: " + ", ".join(not_complete)
    )


def test_no_bogus_marker_files_referenced() -> None:
    """Every marker string in REQ_TO_MARKERS must match at least one real test file.

    Defense against typos in the marker map itself — if a marker points
    to a file that doesn't exist, the map is lying and future coverage
    assertions would pass vacuously for some other REQ that shares a
    valid marker.
    """
    stems = _test_file_stems()
    bogus: list[tuple[str, str]] = []
    for req, markers in REQ_TO_MARKERS.items():
        for marker in markers:
            if not any(marker in stem for stem in stems):
                bogus.append((req, marker))
    assert not bogus, (
        "Bogus markers (no matching test file on disk):\n" + "\n".join(
            f"  {req}: marker '{marker}' has no matching file in tests/phase05/"
            for req, marker in bogus
        )
    )
