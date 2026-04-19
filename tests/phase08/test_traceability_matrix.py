"""Wave 7 — orphan guard asserting 08-TRACEABILITY.md REQ + SC coverage.

Plan 08-08 Task 1 — asserts every Phase 8 REQ (PUB-01..05 + REMOTE-01..03)
has at least one test file whose stem matches a registered marker; fails
if a new REQ is added without test coverage or a test file is renamed
without updating the marker map. Also asserts the 3 anchor markers
(A/B/C) and 2 Pitfall corrections (6, 7) are acknowledged in the matrix.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
TESTS_DIR = _REPO / "tests" / "phase08"
MATRIX = (
    _REPO
    / ".planning"
    / "phases"
    / "08-remote-publishing-production-metadata"
    / "08-TRACEABILITY.md"
)


PHASE8_REQS = [
    "PUB-01",
    "PUB-02",
    "PUB-03",
    "PUB-04",
    "PUB-05",
    "REMOTE-01",
    "REMOTE-02",
    "REMOTE-03",
]
PHASE8_SCS = ["SC1", "SC2", "SC3", "SC4", "SC5", "SC6"]


REQ_TO_TEST_MARKERS: dict[str, list[str]] = {
    "PUB-01": ["test_ai_disclosure_anchor"],
    "PUB-02": [
        "test_uploader_mocked_e2e",
        "test_oauth_installed_flow",
        "test_token_refresh",
        "test_no_selenium_anchor",
    ],
    "PUB-03": [
        "test_publish_lock_48h",
        "test_kst_window_weekday",
        "test_kst_window_weekend",
    ],
    "PUB-04": [
        "test_production_metadata_schema",
        "test_metadata_html_comment",
    ],
    "PUB-05": [
        "test_pinned_comment",
        "test_endscreen_nonexistent_anchor",
    ],
    "REMOTE-01": ["test_github_remote_create"],
    "REMOTE-02": ["test_github_push_main"],
    "REMOTE-03": ["test_submodule_add"],
}


def _test_stems() -> set[str]:
    return {p.stem for p in TESTS_DIR.glob("test_*.py")}


@pytest.fixture(scope="module")
def trace_text() -> str:
    assert MATRIX.exists(), f"{MATRIX} missing"
    return MATRIX.read_text(encoding="utf-8")


def test_traceability_md_exists() -> None:
    assert MATRIX.exists(), f"08-TRACEABILITY.md missing: {MATRIX}"


@pytest.mark.parametrize("req_id", PHASE8_REQS)
def test_each_requirement_appears_in_traceability(
    trace_text: str, req_id: str
) -> None:
    assert f"| {req_id} " in trace_text or f"| **{req_id}** " in trace_text, (
        f"REQ {req_id} not found as table row header in 08-TRACEABILITY.md"
    )


@pytest.mark.parametrize("sc_id", PHASE8_SCS)
def test_each_sc_appears_in_traceability(
    trace_text: str, sc_id: str
) -> None:
    assert sc_id in trace_text, (
        f"SC {sc_id} not referenced anywhere in 08-TRACEABILITY.md"
    )


def test_three_anchors_documented(trace_text: str) -> None:
    assert "ANCHOR A" in trace_text
    assert "ANCHOR B" in trace_text
    assert "ANCHOR C" in trace_text


def test_pitfall_corrections_documented(trace_text: str) -> None:
    assert "Pitfall 6" in trace_text
    assert "Pitfall 7" in trace_text


def test_eight_plan_rows_in_audit_trail(trace_text: str) -> None:
    rows = re.findall(r"^\| 08-0[1-8] \|", trace_text, flags=re.MULTILINE)
    assert len(rows) >= 8, f"Expected >= 8 plan rows, found {len(rows)}"


def test_correction_keys_containssynthetic_vs_custom(
    trace_text: str,
) -> None:
    """Both names must be documented for transparency."""
    assert "containsSyntheticMedia" in trace_text
    assert "syntheticMedia" in trace_text


def test_end_screen_marked_as_unsupported(trace_text: str) -> None:
    text_lower = trace_text.lower()
    assert (
        "end-screen" in text_lower
        or "end_screen" in text_lower
        or "endscreen" in text_lower
    )


def test_no_orphan_plan_numbers(trace_text: str) -> None:
    """No plan 08-09 or 08-10 — Phase 8 is 8 plans exactly."""
    orphans = re.findall(r"08-(09|10|11|12)", trace_text)
    assert not orphans, f"Unexpected plan number references: {orphans}"


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


def test_every_registered_marker_has_a_real_file() -> None:
    """Guard against silent typos — every marker in REQ_TO_TEST_MARKERS
    must correspond to a real tests/phase08/test_*.py file on disk."""
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
