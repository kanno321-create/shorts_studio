"""D-23 regression invariant: Phase 4 + 5 + 6 baseline preserved end-to-end.

Plan 07-08 Task 2 — four subprocess pytest calls confirm the 809-test
regression baseline (Phase 4: 244 + Phase 5: 329 + Phase 6: 236) is not
broken by any Phase 7 addition. Per-phase tests plus combined sweep.
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
        f"Phase 4 regression broken.\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
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
        f"Phase 5 regression broken.\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
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
        f"Phase 6 regression broken.\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_combined_baseline_passes() -> None:
    """D-23: Phase 4 + 5 + 6 combined must stay at 809 green."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase04",
            "tests/phase05",
            "tests/phase06",
            "-q",
            "--no-cov",
        ],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    assert result.returncode == 0, (
        f"Combined regression broken.\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )
