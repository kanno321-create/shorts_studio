"""E2E wrapper around scripts/validate/phase06_acceptance.py (SC 1-6).

Mirrors tests/phase05/test_phase05_acceptance.py. Invokes the acceptance
CLI as a subprocess and asserts:
  - Script exists and is syntactically valid Python.
  - Exit code 0 (all 6 SC pass).
  - All six SC labels appear in stdout.
  - Every SC row is marked PASS.

Adjacent regression checks:
  - tests/phase06/ (excluding this wrapper, to avoid recursion) is green.
  - tests/phase05/ is still green — Phase 6 work must not regress prior
    phase contracts.

Phase 6 closes when this wrapper exits 0.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
ACCEPTANCE = _REPO / "scripts" / "validate" / "phase06_acceptance.py"


def test_acceptance_script_exists() -> None:
    assert ACCEPTANCE.exists(), f"Plan 01 did not create {ACCEPTANCE}"


def test_acceptance_script_is_valid_python() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(ACCEPTANCE)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_acceptance_e2e_exits_zero() -> None:
    """Full Phase 6 SC 1-6 run must PASS all 6."""
    result = subprocess.run(
        [sys.executable, str(ACCEPTANCE)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print("=== STDOUT ===")
        print(result.stdout)
        print("=== STDERR ===")
        print(result.stderr)
    assert result.returncode == 0, (
        f"phase06_acceptance.py exit {result.returncode}:\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_acceptance_output_contains_all_6_sc() -> None:
    result = subprocess.run(
        [sys.executable, str(ACCEPTANCE)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    for label in ["SC1:", "SC2:", "SC3:", "SC4:", "SC5:", "SC6:"]:
        assert label in result.stdout, f"{label} missing from acceptance output"


def test_acceptance_all_sc_report_pass() -> None:
    """Every SC row in the markdown table must be marked PASS."""
    result = subprocess.run(
        [sys.executable, str(ACCEPTANCE)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    pass_count = sum(
        1
        for line in result.stdout.splitlines()
        if line.startswith("|") and "PASS" in line
    )
    assert pass_count >= 6, f"Only {pass_count} SC rows marked PASS, expected >=6"


def test_full_phase06_suite_green() -> None:
    """Regression: tests/phase06/ all pass (excluding this wrapper to avoid recursion)."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/",
            "-q",
            "--no-cov",
            "--ignore=tests/phase06/test_phase06_acceptance.py",
        ],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-1000:])
    assert result.returncode == 0, "tests/phase06/ has failing tests"


def test_phase05_suite_still_green() -> None:
    """Regression: Phase 5's 329+ tests untouched by Phase 6 changes."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase05/", "-q", "--no-cov"],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(_REPO),
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-1000:])
    assert result.returncode == 0, (
        "Phase 5 regression — Phase 6 changes broke prior phase"
    )
