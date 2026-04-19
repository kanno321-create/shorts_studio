"""Wave 6 — 986 regression baseline preserved post-Phase 8.

Direct analogue of tests/phase07/test_regression_809_green.py (D-23 invariant):
Phase 4 (244) + Phase 5 (329) + Phase 6 (177) + Phase 7 (236) = 986 tests.

Each per-phase test subprocess-runs pytest scoped to that phase folder and
asserts exit 0. The combined test runs all four phases together and asserts
`986 passed` appears in stdout so test-count drift is caught explicitly.

Combined sweep can take ~8-10 minutes on Windows. All 5 subprocess calls are
guarded with 600-1200s timeouts. Intended to run in the nightly / pre-merge
regression sweep alongside `scripts/validate/phase08_acceptance.py`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]


def test_phase04_green() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase04", "-q", "--no-cov"],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert result.returncode == 0, (
        f"Phase 4 regression broke:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_phase05_green() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase05", "-q", "--no-cov"],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert result.returncode == 0, (
        f"Phase 5 regression broke:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_phase06_green() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase06", "-q", "--no-cov"],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert result.returncode == 0, (
        f"Phase 6 regression broke:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_phase07_green() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase07", "-q", "--no-cov"],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    assert result.returncode == 0, (
        f"Phase 7 regression broke:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_combined_986_green() -> None:
    """Phase 4+5+6+7 combined sweep must stay at 986 passed tests."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase04",
            "tests/phase05",
            "tests/phase06",
            "tests/phase07",
            "-q",
            "--no-cov",
        ],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1200,
    )
    assert result.returncode == 0, (
        f"Combined Phase 4+5+6+7 regression broke:\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )
    # Assert test-count line `986 passed` appears — catches test-count drift.
    assert "986 passed" in result.stdout, (
        f"Expected '986 passed' in combined regression stdout; got:\n"
        f"{result.stdout[-2000:]}"
    )
