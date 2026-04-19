"""D-14 immutability gate — _imported_from_shorts_naberal.md MUST NOT drift.

Per Phase 6 RESEARCH.md §Area 10 Immutability (lines 1123-1165):
The Phase 3 harvest-archive of shorts_naberal FAILURES.md lives at
`.claude/failures/_imported_from_shorts_naberal.md` and is a frozen
learning artifact. Any byte-level drift since the Phase 3 freeze must
stop Phase 6 / trigger a commit-trail investigation.

Invariants asserted here:
  1. The file exists.
  2. Full-file sha256 == the canonical Phase 3 hash (2026-04-19).
  3. Line count == 500 (secondary D-14 invariant).
  4. Boundary: distinct bytes from the Phase 6 seeded FAILURES.md.
  5. No accidental schema promotion into wiki/ (the imported content is
     .claude/failures/ only).

If these ever fail, investigate with:
    git log --oneline -- .claude/failures/_imported_from_shorts_naberal.md
    git checkout HEAD -- .claude/failures/_imported_from_shorts_naberal.md
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

# D-14 invariant: full-file sha256 verified 2026-04-19 per RESEARCH Area 10 line 1129
EXPECTED_FULL_FILE_SHA256 = "a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa"
EXPECTED_LINE_COUNT = 500


@pytest.fixture
def imported_file(repo_root: Path) -> Path:
    return repo_root / ".claude" / "failures" / "_imported_from_shorts_naberal.md"


def test_file_exists(imported_file: Path) -> None:
    """Baseline: the D-14 target archive must exist on disk."""
    assert imported_file.exists(), f"D-14 target missing: {imported_file}"


def test_full_file_sha256_unchanged(imported_file: Path) -> None:
    """D-14: _imported_from_shorts_naberal.md MUST remain byte-for-byte identical."""
    actual = hashlib.sha256(imported_file.read_bytes()).hexdigest()
    assert actual == EXPECTED_FULL_FILE_SHA256, (
        f"D-14 VIOLATION: _imported_from_shorts_naberal.md modified since Phase 3.\n"
        f"  Expected sha256: {EXPECTED_FULL_FILE_SHA256}\n"
        f"  Actual sha256:   {actual}\n"
        f"  Restore via: git checkout HEAD -- .claude/failures/_imported_from_shorts_naberal.md\n"
        f"  (See RESEARCH Area 10 lines 1123-1165 for Phase 3 commit trail.)"
    )


def test_line_count_500(imported_file: Path) -> None:
    """D-14 secondary: line count MUST remain 500."""
    lines = imported_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == EXPECTED_LINE_COUNT, (
        f"D-14 VIOLATION: line count {len(lines)} != {EXPECTED_LINE_COUNT}"
    )


def test_imported_not_equal_to_failures_md(repo_root: Path) -> None:
    """Sanity: FAILURES.md (Plan 08 seed) is distinct from the imported archive."""
    a = repo_root / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
    b = repo_root / ".claude" / "failures" / "FAILURES.md"
    assert a.exists() and b.exists()
    assert a.read_bytes() != b.read_bytes(), (
        "CRITICAL: FAILURES.md content matches imported archive — D-14 boundary broken"
    )


def test_imported_path_not_in_wiki(repo_root: Path) -> None:
    """Sanity: D-14 file lives in .claude/failures/, not wiki/ (no accidental schema promotion)."""
    wiki = repo_root / "wiki"
    if wiki.exists():
        for md in wiki.rglob("*.md"):
            text = md.read_text(encoding="utf-8", errors="replace")
            assert "FAIL-011: 기존 프로젝트 구조 확인 없이" not in text, (
                f"D-14 VIOLATION: imported failures content appears in wiki/: {md}"
            )
