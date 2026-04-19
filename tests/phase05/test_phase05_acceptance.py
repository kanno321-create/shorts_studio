"""End-to-end Phase 5 acceptance wrapper.

Invokes ``scripts/validate/phase05_acceptance.py`` and
``scripts/validate/verify_hook_blocks.py`` via subprocess and asserts
both exit 0 and that the acceptance output enumerates all 6 Success
Criteria. This is the highest-level automated gate closing Phase 5 —
when all tests in this file are green, Phase 5 is shippable.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ACCEPTANCE = REPO / "scripts" / "validate" / "phase05_acceptance.py"
HOOK_BLOCKS = REPO / "scripts" / "validate" / "verify_hook_blocks.py"


def _run(args: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=str(REPO),
    )


def test_acceptance_script_exists() -> None:
    """Plan 01 created scripts/validate/phase05_acceptance.py."""
    assert ACCEPTANCE.exists(), f"Plan 01 did not create {ACCEPTANCE}"


def test_verify_hook_blocks_script_exists() -> None:
    """Plan 01 created scripts/validate/verify_hook_blocks.py."""
    assert HOOK_BLOCKS.exists(), f"Plan 01 did not create {HOOK_BLOCKS}"


def test_acceptance_script_compiles() -> None:
    """phase05_acceptance.py must be syntactically valid Python."""
    result = _run([sys.executable, "-m", "py_compile", str(ACCEPTANCE)], timeout=15)
    assert result.returncode == 0, f"phase05_acceptance.py syntax error: {result.stderr}"


def test_acceptance_e2e_exit_zero() -> None:
    """SC 1-6 all PASS: phase05_acceptance.py exits 0."""
    result = _run([sys.executable, str(ACCEPTANCE)])
    assert result.returncode == 0, (
        f"phase05_acceptance.py exit {result.returncode}\n"
        f"=== STDOUT ===\n{result.stdout}\n"
        f"=== STDERR ===\n{result.stderr}"
    )


def test_acceptance_output_contains_all_six_sc() -> None:
    """Acceptance output must enumerate all 6 Success Criteria labels."""
    result = _run([sys.executable, str(ACCEPTANCE)])
    missing = [label for label in ("SC1", "SC2", "SC3", "SC4", "SC5", "SC6")
               if label not in result.stdout]
    assert not missing, (
        f"Acceptance output missing SC labels: {missing}\n"
        f"Actual stdout:\n{result.stdout}"
    )


def test_acceptance_output_reports_all_pass() -> None:
    """Every SC row in the acceptance output must report PASS (not FAIL)."""
    result = _run([sys.executable, str(ACCEPTANCE)])
    assert result.returncode == 0, "prerequisite test_acceptance_e2e_exit_zero failed"
    fail_rows = [line for line in result.stdout.splitlines()
                 if "| FAIL |" in line]
    assert not fail_rows, (
        f"Acceptance output contains FAIL rows:\n" + "\n".join(fail_rows)
    )


def test_verify_hook_blocks_cli_passes() -> None:
    """Plan 01's verify_hook_blocks.py CLI must exit 0 (all 5 hook checks green)."""
    result = _run([sys.executable, str(HOOK_BLOCKS)], timeout=30)
    assert result.returncode == 0, (
        f"verify_hook_blocks.py exit {result.returncode}\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


def test_pytest_phase05_sweep_green() -> None:
    """tests/phase05/ (excluding this file to avoid recursion) all exit 0."""
    result = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase05/",
            "-q",
            "--no-cov",
            "--ignore=tests/phase05/test_phase05_acceptance.py",
        ],
        timeout=300,
    )
    if result.returncode != 0:
        # surface last 2000 chars for diagnostics
        pytest.fail(
            "tests/phase05/ has failing tests\n"
            f"stdout(tail)={result.stdout[-2000:]}\n"
            f"stderr(tail)={result.stderr[-1000:]}"
        )
