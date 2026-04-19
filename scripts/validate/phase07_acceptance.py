#!/usr/bin/env python3
"""Phase 7 Success Criteria 1-5 acceptance verifier.

Mirrors scripts/validate/phase05_acceptance.py and phase06_acceptance.py:
subprocess invokes each SC's primary pytest target, collects PASS/FAIL,
prints a markdown table, returns 0 iff all 5 SCs PASS.

SC mapping (canonical — see .planning/phases/07-integration-test/07-PLAN.md):
  SC1: E2E mock + NotebookLM tier-2-only   -> test_e2e_happy_path.py
                                             + test_notebooklm_tier2_only.py
  SC2: 13 operational gates + dispatch     -> 4 Plan 07-04 tests
  SC3: CircuitBreaker 3x + 300s cooldown   -> 2 Plan 07-05 tests
  SC4: Fallback ken-burns no CIRCUIT_OPEN  -> 2 Plan 07-06 tests
  SC5: harness-audit >= 80 + drift 0       -> harness_audit.py + 6 Plan
                                             07-07 tests

Run: python scripts/validate/phase07_acceptance.py
Exit 0 = ALL SC green. Exit 1 = any SC FAIL. Prints markdown table so
downstream tooling can capture it.

Stdlib-only. UTF-8 subprocess encoding + errors="replace" to survive
Windows cp949 environments (D-22 / STATE decision #28 — cp949 default
codec cannot decode em-dash or Korean pytest output).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# scripts/validate/phase07_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], cwd: Path = REPO, timeout: int = 180) -> tuple[int, str, str]:
    """Run a subprocess; return (returncode, stdout, stderr).

    Uses UTF-8 decoding with replacement to survive cp949 environments.
    FileNotFoundError and TimeoutExpired are caught so the CLI never
    crashes on infrastructure gaps.
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, "", f"timeout: {e}"
    return p.returncode, p.stdout or "", p.stderr or ""


def main() -> int:
    # SC1: E2E mock pipeline + NotebookLM tier-2-only
    rc1a, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_e2e_happy_path.py",
            "-q",
            "--no-cov",
        ]
    )
    rc1b, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_notebooklm_tier2_only.py",
            "-q",
            "--no-cov",
        ]
    )
    sc1 = "PASS" if rc1a == 0 and rc1b == 0 else "FAIL"

    # SC2: 13 operational gates + verify_all_dispatched
    rc2, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_operational_gate_count_equals_13.py",
            "tests/phase07/test_verify_all_dispatched_13.py",
            "tests/phase07/test_gate_order_violation.py",
            "tests/phase07/test_checkpointer_atomic_writes_13.py",
            "-q",
            "--no-cov",
        ]
    )
    sc2 = "PASS" if rc2 == 0 else "FAIL"

    # SC3: CircuitBreaker 3x + strict > 300s cooldown
    rc3, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_circuit_breaker_3x_open.py",
            "tests/phase07/test_cooldown_300s_enforced.py",
            "-q",
            "--no-cov",
        ]
    )
    sc3 = "PASS" if rc3 == 0 else "FAIL"

    # SC4: Fallback ken-burns (THUMBNAIL only) + FAILURES append-only
    rc4, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_fallback_ken_burns_thumbnail.py",
            "tests/phase07/test_failures_append_on_retry_exceeded.py",
            "-q",
            "--no-cov",
        ]
    )
    sc4 = "PASS" if rc4 == 0 else "FAIL"

    # SC5: harness-audit >= 80 + 6 dimension tests (JSON, score, SKILL, drift,
    # agents, descriptions)
    rc5a, _, _ = _run(
        [
            sys.executable,
            "scripts/validate/harness_audit.py",
            "--threshold",
            "80",
        ]
    )
    rc5b, _, _ = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase07/test_harness_audit_json_schema.py",
            "tests/phase07/test_harness_audit_score_ge_80.py",
            "tests/phase07/test_skill_500_line_scan.py",
            "tests/phase07/test_a_rank_drift_zero.py",
            "tests/phase07/test_agent_count_invariant.py",
            "tests/phase07/test_description_1024_scan.py",
            "-q",
            "--no-cov",
        ]
    )
    sc5 = "PASS" if rc5a == 0 and rc5b == 0 else "FAIL"

    # Windows cp949 guard for the table print below.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    print("| SC | Status | Coverage |")
    print("|----|--------|----------|")
    print(f"| SC1: E2E mock + NotebookLM tier-2-only | {sc1} | TEST-01 |")
    print(f"| SC2: verify_all_dispatched 13 operational gates | {sc2} | TEST-02 |")
    print(f"| SC3: CircuitBreaker 3x + 300s cooldown | {sc3} | TEST-03 |")
    print(f"| SC4: Fallback ken-burns no CIRCUIT_OPEN | {sc4} | TEST-04 |")
    print(f"| SC5: harness-audit >= 80 + drift 0 + SKILL <= 500 | {sc5} | AUDIT-02 |")

    all_pass = all(s == "PASS" for s in (sc1, sc2, sc3, sc4, sc5))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
