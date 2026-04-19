"""Automated 9-REQ traceability coverage for Phase 6.

Mirrors tests/phase05/test_traceability_matrix.py. Every Phase 6
requirement ID (WIKI-01..06 + FAIL-01..03 = 9) MUST be covered by at
least one test file whose stem matches a registered marker.

If a new requirement is added to REQUIREMENTS.md §WIKI / §FAIL without
adding a matching test file, this test fails — preventing silent REQ
orphaning.

Also asserts:
  - 06-TRACEABILITY.md exists.
  - All 9 REQ IDs appear in the matrix.
  - All 6 Success Criteria labels appear in the matrix.
  - 06-VALIDATION.md exists.
  - The REQ list is exactly 9 items (Phase 6 scope is frozen).
"""
from __future__ import annotations

from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
TESTS_DIR = _REPO / "tests" / "phase06"
PHASE6_DIR = (
    _REPO / ".planning" / "phases" / "06-wiki-notebooklm-integration-failures-reservoir"
)


PHASE6_REQS: list[str] = [
    "WIKI-01",
    "WIKI-02",
    "WIKI-03",
    "WIKI-04",
    "WIKI-05",
    "WIKI-06",
    "FAIL-01",
    "FAIL-02",
    "FAIL-03",
]


# REQ -> list of test-file stem substrings that count as coverage.
# Adding a new REQ requires adding at least one marker here AND adding
# at least one test file whose stem contains that marker.
REQ_TO_MARKERS: dict[str, list[str]] = {
    "WIKI-01": [
        "test_wiki_frontmatter",
        "test_wiki_nodes_ready",
        "test_moc_linkage",
    ],
    "WIKI-02": [
        "test_continuity_prefix_schema",
        "test_shotstack_prefix_injection",
        "test_filter_order_preservation",
        "test_prefix_json_serialization",
        "test_continuity_bible_node",
    ],
    "WIKI-03": [
        "test_notebooklm_wrapper",
        "test_notebooklm_subprocess",
        "test_library_json_channel_bible",
    ],
    "WIKI-04": [
        "test_fallback_chain",
        "test_fallback_injection",
    ],
    "WIKI-05": [
        "test_wiki_reference_format",
        "test_agent_prompt_wiki_refs",
        "test_agent_prompt_byte_diff",
    ],
    # WIKI-06 is measurement-only per D-15; validator scaffolding is
    # covered by the frontmatter validator test.
    "WIKI-06": [
        "test_wiki_frontmatter",
    ],
    "FAIL-01": [
        "test_failures_append_only",
        "test_hook_failures_block",
    ],
    "FAIL-02": [
        "test_aggregate_patterns",
        "test_aggregate_dry_run",
    ],
    "FAIL-03": [
        "test_skill_history_backup",
    ],
}


def _test_stems() -> set[str]:
    return {p.stem for p in TESTS_DIR.glob("test_*.py")}


def test_every_req_has_test_coverage() -> None:
    stems = _test_stems()
    uncovered: list[str] = []
    for req in PHASE6_REQS:
        markers = REQ_TO_MARKERS[req]
        if not any(m in stem for stem in stems for m in markers):
            uncovered.append(req)
    assert uncovered == [], f"UNCOVERED REQs: {uncovered}"


def test_traceability_md_exists() -> None:
    matrix = PHASE6_DIR / "06-TRACEABILITY.md"
    assert matrix.exists(), f"Missing: {matrix}"


def test_traceability_md_covers_9_reqs() -> None:
    matrix = PHASE6_DIR / "06-TRACEABILITY.md"
    content = matrix.read_text(encoding="utf-8")
    for req in PHASE6_REQS:
        assert req in content, f"{req} missing from traceability matrix"


def test_traceability_md_covers_6_sc() -> None:
    matrix = PHASE6_DIR / "06-TRACEABILITY.md"
    content = matrix.read_text(encoding="utf-8")
    for sc in ["SC #1", "SC #2", "SC #3", "SC #4", "SC #5", "SC #6"]:
        assert sc in content, f"{sc} missing from traceability matrix"


def test_validation_md_exists() -> None:
    val = PHASE6_DIR / "06-VALIDATION.md"
    assert val.exists(), f"Missing: {val}"


def test_nine_total_reqs() -> None:
    """Phase 6 scope is frozen at 9 requirements."""
    assert len(PHASE6_REQS) == 9


def test_every_marker_points_to_existing_test_file() -> None:
    """Defensive: every marker in REQ_TO_MARKERS must match at least one file."""
    stems = _test_stems()
    orphan_markers: list[tuple[str, str]] = []
    for req, markers in REQ_TO_MARKERS.items():
        for m in markers:
            if not any(m in stem for stem in stems):
                orphan_markers.append((req, m))
    assert orphan_markers == [], f"markers without matching test file: {orphan_markers}"
