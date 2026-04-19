"""E2E wrapper asserting phase07_acceptance.py exit 0 + all 5 SC PASS.

Phase 7 gate closure (Plan 07-08 Task 1 test half).

Covers Plan acceptance:
- phase07_acceptance.py script exists and is syntactically valid
- Executing it exits 0 (all 5 SCs PASS)
- Output contains all 5 SC labels (SC1..SC5)
- At least 5 "PASS" rows in the output table
- Full tests/phase07/ suite (excluding this wrapper to avoid recursion) green
- Phase 4/5/6 regression baseline (809) preserved
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_ACCEPT = _REPO / "scripts" / "validate" / "phase07_acceptance.py"


def test_acceptance_script_exists() -> None:
    assert _ACCEPT.exists(), f"phase07_acceptance.py missing: {_ACCEPT}"


def test_acceptance_script_valid_python() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(_ACCEPT)],
        capture_output=True,
        text=True,
        timeout=20,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_acceptance_exits_zero() -> None:
    """All 5 SCs must PASS (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if result.returncode != 0:
        # Print tail for diagnostic visibility.
        print("=== STDOUT ===")
        print(result.stdout)
        print("=== STDERR ===")
        print(result.stderr[-2000:] if result.stderr else "")
    assert result.returncode == 0, (
        f"phase07_acceptance.py exit {result.returncode}"
    )


def test_acceptance_output_contains_all_5_sc_labels() -> None:
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    for sc in ("SC1:", "SC2:", "SC3:", "SC4:", "SC5:"):
        assert sc in result.stdout, (
            f"{sc} missing from acceptance output:\n{result.stdout}"
        )


def test_acceptance_all_sc_marked_pass() -> None:
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    pass_rows = sum(
        1
        for line in result.stdout.splitlines()
        if line.startswith("|") and "PASS" in line
    )
    assert pass_rows >= 5, (
        f"Only {pass_rows} SC rows PASS, expected >=5\n{result.stdout}"
    )


def test_full_phase07_suite_green_excluding_wrapper() -> None:
    """Regression: tests/phase07/ all green (excluding this wrapper to avoid recursion)."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/",
            "-q",
            "--no-cov",
            "--ignore=tests/phase07/test_phase07_acceptance.py",
        ],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-1500:])
    assert result.returncode == 0, "tests/phase07/ has failing tests"


def test_phase_4_5_6_still_green() -> None:
    """D-23 regression: Phase 4/5/6 baseline preserved."""
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
        timeout=600,
    )
    assert result.returncode == 0, (
        f"Phase 4/5/6 regression — Phase 7 work broke prior phases\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )
