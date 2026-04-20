"""Phase 10 Plan 1 — skill_patch_counter tests (FAIL-04 / SC#1).

Task 1 (fixture-only, 3 tests): Verify conftest infrastructure works before
Task 2 introduces the actual skill_patch_counter invocations. Task 2 will
extend this file with 8+ CLI regression tests (Test A-H per PLAN.md).
"""
from __future__ import annotations

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Task 1: conftest infrastructure tests (fixture-only, no CLI invocation yet).
# ---------------------------------------------------------------------------


def test_tmp_git_repo_fixture_creates_repo(tmp_git_repo: Path) -> None:
    """conftest.tmp_git_repo must initialise .git/ in tmp_path."""
    assert (tmp_git_repo / ".git").is_dir(), "tmp_git_repo must contain .git/"
    # Seed commit present
    out = subprocess.run(
        ["git", "-C", str(tmp_git_repo), "log", "--oneline"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    assert "seed repo" in out.stdout, "seed commit must exist"


def test_make_forbidden_commit_helper(tmp_git_repo: Path, make_commit) -> None:
    """conftest.make_commit helper must return a real commit hash."""
    commit_hash = make_commit(
        {"CLAUDE.md": "# modified\n"},
        "docs(test): synthetic CLAUDE.md edit",
    )
    assert len(commit_hash) == 40, "commit hash should be 40 hex chars"
    # Verify the commit actually lives in git
    out = subprocess.run(
        ["git", "-C", str(tmp_git_repo), "log", "-1", commit_hash, "--name-only"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    assert "CLAUDE.md" in out.stdout, "CLAUDE.md must appear in commit name-only output"


def test_reports_gitkeep_exists(repo_root: Path) -> None:
    """reports/.gitkeep must exist in the real repo root (Plan 1 output target)."""
    gk = repo_root / "reports" / ".gitkeep"
    assert gk.exists(), f"{gk} must exist as Plan 1 report output directory placeholder"
