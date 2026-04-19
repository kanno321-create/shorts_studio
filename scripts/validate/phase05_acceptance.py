#!/usr/bin/env python3
"""Phase 5 Success Criteria 1~6 acceptance verifier.

Run: python scripts/validate/phase05_acceptance.py
Exit 0 = ALL SC green. Exit 1 = any failure.
Prints a markdown table of results so downstream tooling can capture it.

Covers:
    SC1 : shorts_pipeline.py line count in [500, 800]   (Plan 07)
    SC2 : 0 skip_gates occurrences in scripts/orchestrator/
    SC3 : GateGuard.dispatch + verify_all_dispatched     (Plans 04/07)
    SC4 : CircuitBreaker + regen loop fallback           (Plans 02/07)
    SC5 : 0 T2V occurrences + I2V only                    (Plans 06/07)
    SC6 : Low-Res First + VoiceFirstTimeline              (Plans 05/07)

At Wave 1 (after Plan 01 only), SC3-6 are expected to FAIL because the
underlying plans haven't shipped yet. This script must NOT crash in that
case — it must cleanly report FAIL rows and exit 1.
Stdlib-only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# scripts/validate/phase05_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]
PIPELINE = REPO / "scripts" / "orchestrator" / "shorts_pipeline.py"
ORCH_DIR = REPO / "scripts" / "orchestrator"


def _run(cmd: list[str], cwd: Path = REPO) -> tuple[int, str, str]:
    """Run a subprocess; return (returncode, stdout, stderr).

    Uses UTF-8 decoding with replacement to survive cp949 environments
    (STATE decision #28 — Windows default codec cannot decode em-dash or
    Korean characters that pytest output may contain).
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, "", f"timeout: {e}"
    return p.returncode, p.stdout or "", p.stderr or ""


def sc1_line_count() -> tuple[bool, str]:
    """SC 1: 500 <= lines <= 800 in shorts_pipeline.py."""
    if not PIPELINE.exists():
        return False, "shorts_pipeline.py does not exist (Plan 07 incomplete)"
    with PIPELINE.open("r", encoding="utf-8", errors="replace") as fh:
        n = sum(1 for _ in fh)
    ok = 500 <= n <= 800
    return ok, f"{n} lines ({'OK' if ok else 'OUT OF RANGE [500,800]'})"


def sc2_skip_gates_grep() -> tuple[bool, str]:
    """SC 2: 0 occurrences of skip_gates in scripts/orchestrator/."""
    if not ORCH_DIR.exists():
        return False, "scripts/orchestrator/ missing"
    rc, out, _ = _run(["grep", "-r", "skip_gates", str(ORCH_DIR)])
    ok = rc != 0  # grep rc=1 means no match (good)
    return ok, "0 matches" if ok else f"FOUND:\n{out[:500]}"


def sc3_gate_guard_works() -> tuple[bool, str]:
    """SC 3: GateGuard.dispatch raises on FAIL + verify_all_dispatched at COMPLETE."""
    rc, _, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase05/test_gate_guard.py",
            "tests/phase05/test_verify_all_dispatched.py",
            "-q",
            "--no-cov",
        ]
    )
    return rc == 0, "pytest green" if rc == 0 else err[-500:]


def sc4_circuit_and_regen() -> tuple[bool, str]:
    """SC 4: CircuitBreaker state machine + 3-retry fallback."""
    rc, _, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase05/test_circuit_breaker.py",
            "tests/phase05/test_circuit_breaker_cooldown.py",
            "tests/phase05/test_fallback_shot.py",
            "-q",
            "--no-cov",
        ]
    )
    return rc == 0, "pytest green" if rc == 0 else err[-500:]


def sc5_no_t2v() -> tuple[bool, str]:
    """SC 5: 0 forbidden text-to-video identifiers in scripts/orchestrator/.

    Uses case-sensitive grep so the `T2VForbidden` guard class (which CONTEXT
    D-13 mandates the plan export as a runtime sentinel) is not a false
    positive. Byte-pattern caught here: lowercase `t2v` (function/attr
    position), `text_to_video`, `text2video`. These are the literal tokens
    a future dev would type to re-introduce the banned code path; the
    pre_tool_use Hook catches them with the same spelling.

    Binary files (__pycache__) and the exception-class identifier
    `T2VForbidden` (PascalCase + Forbidden suffix) are excluded by design.
    """
    if not ORCH_DIR.exists():
        return False, "scripts/orchestrator/ missing"
    rc, out, _ = _run(
        [
            "grep",
            "-rnE",
            "--binary-files=without-match",
            "--include=*.py",
            r"(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video",
            str(ORCH_DIR),
        ]
    )
    ok = rc != 0
    return ok, "0 forbidden T-2-V refs" if ok else f"FOUND:\n{out[:500]}"


def sc6_low_res_and_voice_first() -> tuple[bool, str]:
    """SC 6: Low-Res First render + VoiceFirstTimeline alignment."""
    rc, _, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase05/test_low_res_first.py",
            "tests/phase05/test_voice_first_timeline.py",
            "-q",
            "--no-cov",
        ]
    )
    return rc == 0, "pytest green" if rc == 0 else err[-500:]


CHECKS = [
    ("SC1: shorts_pipeline.py in 500-800 lines", sc1_line_count),
    ("SC2: 0 skip_gates occurrences", sc2_skip_gates_grep),
    ("SC3: GateGuard + verify_all_dispatched", sc3_gate_guard_works),
    ("SC4: CircuitBreaker + regen loop fallback", sc4_circuit_and_regen),
    ("SC5: 0 T2V occurrences + I2V only", sc5_no_t2v),
    ("SC6: Low-Res First + VoiceFirstTimeline", sc6_low_res_and_voice_first),
]


def main() -> int:
    print("| SC | Result | Detail |")
    print("|----|--------|--------|")
    all_ok = True
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 — deliberate catch-all for CLI
            ok, detail = False, f"EXCEPTION: {e}"
        all_ok = all_ok and ok
        mark = "PASS" if ok else "FAIL"
        detail_compact = detail.replace("\n", " ")[:100]
        print(f"| {name} | {mark} | {detail_compact} |")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
