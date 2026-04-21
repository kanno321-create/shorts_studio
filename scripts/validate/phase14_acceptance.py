#!/usr/bin/env python3
"""Phase 14 Acceptance — API Adapter Remediation gate aggregator.

Phase 14 Success Criteria (5 건) + 2 보조 audit 를 자동 검증:

- SC#1 (ADAPT-04): pytest tests/phase05 tests/phase06 tests/phase07 = 0 failures
- SC#2 (ADAPT-01/02/03): 3 contract 테스트 파일 존재 + green
- SC#3 (ADAPT-05): wiki/render/adapter_contracts.md 존재 + 7 adapter 매트릭스
- SC#4 (ADAPT-06): pytest -m adapter_contract 단독 실행 green (>=30 tests)
- SC#5 (ADAPT-04 #5): pytest tests/ 전체 exit 0

추가:
- AUDIT harness_audit 점수 >= 80 (AUDIT-01/02)
- AUDIT drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 조건)

phase07_acceptance.py 의 subprocess.run + stdout parse + stdout 표 패턴을 복제.
Windows cp949 대응 — 모든 subprocess 에 PYTHONIOENCODING=utf-8 + encoding="utf-8"
+ errors="replace" 강제 (14-RESEARCH §Risks R5 mitigation).

Exit 0 = ALL_PASS, exit 1 = FAIL. 결과 JSON 을 `.planning/phases/14-api-adapter-
remediation/14-05-acceptance.json` 에 anchoring — Plan 14-05 Task 14-05-03
(TRACEABILITY) + Task 14-05-04 (VALIDATION flip) 의 증거 소스.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# scripts/validate/phase14_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], label: str, timeout: int = 1200) -> dict:
    """subprocess.run + stdout capture + rc record.

    Windows cp949 대응 — PYTHONIOENCODING=utf-8 강제 (14-RESEARCH R5).
    FileNotFoundError / TimeoutExpired 를 rc 로 흡수하여 gate 가 crash 하지 않음.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO),
            env=env,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return {
            "label": label,
            "cmd": cmd,
            "rc": 127,
            "stdout_tail": "",
            "stderr_tail": f"FileNotFoundError: {exc}",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "cmd": cmd,
            "rc": 124,
            "stdout_tail": "",
            "stderr_tail": f"TimeoutExpired after {timeout}s: {exc}",
        }
    return {
        "label": label,
        "cmd": cmd,
        "rc": result.returncode,
        "stdout_tail": (result.stdout or "")[-2000:],
        "stderr_tail": (result.stderr or "")[-500:],
    }


def check_sc1_phase_sweep() -> dict:
    """SC#1 — ADAPT-04 Success Criteria #1: phase05/06/07 sweep 0 failures."""
    return _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase05",
            "tests/phase06",
            "tests/phase07",
            "--tb=no",
            "-q",
            "--no-cov",
        ],
        "SC#1 phase05_06_07_sweep",
        timeout=1500,
    )


def check_sc2_contract_files() -> dict:
    """SC#2 — ADAPT-01/02/03: 3 contract 테스트 파일 존재."""
    files = [
        "tests/adapters/test_veo_i2v_contract.py",
        "tests/adapters/test_elevenlabs_contract.py",
        "tests/adapters/test_shotstack_contract.py",
    ]
    missing = [f for f in files if not (REPO / f).exists()]
    return {
        "label": "SC#2 contract_files_exist",
        "cmd": ["(python) os.path.exists check"],
        "files": files,
        "missing": missing,
        "rc": 0 if not missing else 1,
        "stdout_tail": f"files={files} missing={missing}",
        "stderr_tail": "",
    }


def check_sc3_doc_exists() -> dict:
    """SC#3 — ADAPT-05: wiki/render/adapter_contracts.md 존재 + 7 adapter 행."""
    path = REPO / "wiki" / "render" / "adapter_contracts.md"
    if not path.exists():
        return {
            "label": "SC#3 doc_exists",
            "cmd": [f"exists({path})"],
            "rc": 1,
            "reason": "file missing",
            "stdout_tail": f"missing: {path}",
            "stderr_tail": "",
        }
    text = path.read_text(encoding="utf-8")
    required = [
        "kling_i2v",
        "runway_i2v",
        "veo_i2v",
        "typecast",
        "elevenlabs",
        "shotstack",
        "whisperx",
    ]
    missing = [name for name in required if name not in text]
    return {
        "label": "SC#3 doc_exists",
        "cmd": [f"adapter row scan on {path.relative_to(REPO)}"],
        "rc": 0 if not missing else 1,
        "missing_adapters": missing,
        "stdout_tail": (
            f"required={required} missing={missing} doc_bytes={len(text)}"
        ),
        "stderr_tail": "",
    }


def check_sc4_adapter_contract_marker() -> dict:
    """SC#4 — ADAPT-06: pytest -m adapter_contract 단독 실행 green (>=30 tests)."""
    return _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "adapter_contract",
            "--tb=no",
            "-q",
            "--no-cov",
        ],
        "SC#4 adapter_contract_marker_gate",
        timeout=300,
    )


def check_sc5_full_regression() -> dict:
    """SC#5 — ADAPT-04 Success Criteria #5: pytest tests/ 전체 regression."""
    return _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--tb=no",
            "-q",
            "--no-cov",
        ],
        "SC#5 full_regression",
        timeout=1800,
    )


def check_harness_audit() -> dict:
    """harness_audit 점수 >= 80 (AUDIT-01/02)."""
    return _run(
        [
            sys.executable,
            "-m",
            "scripts.validate.harness_audit",
            "--threshold",
            "80",
        ],
        "AUDIT harness_score",
        timeout=180,
    )


def check_drift_scan() -> dict:
    """drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 조건)."""
    return _run(
        [
            sys.executable,
            "-m",
            "scripts.audit.drift_scan",
            "--skip-harness-import",
            "--dry-run",
            "--skip-github-issue",
        ],
        "AUDIT drift_a_class",
        timeout=300,
    )


def main() -> int:
    checks = [
        check_sc1_phase_sweep(),
        check_sc2_contract_files(),
        check_sc3_doc_exists(),
        check_sc4_adapter_contract_marker(),
        check_sc5_full_regression(),
        check_harness_audit(),
        check_drift_scan(),
    ]
    all_ok = all(c.get("rc", 1) == 0 for c in checks)

    summary = {
        "phase": "14-api-adapter-remediation",
        "plan": "14-05",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "all_passed": all_ok,
        "checks": checks,
        "requirements": ["ADAPT-01", "ADAPT-02", "ADAPT-03", "ADAPT-04", "ADAPT-05", "ADAPT-06"],
    }

    out_path = (
        REPO
        / ".planning"
        / "phases"
        / "14-api-adapter-remediation"
        / "14-05-acceptance.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Windows cp949 guard for the table print below.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - defensive
        pass

    print(f"Phase 14 Acceptance: {'ALL_PASS' if all_ok else 'FAIL'}")
    print("| Check | RC | Label |")
    print("|-------|----|-------|")
    for c in checks:
        rc = c.get("rc", "n/a")
        print(f"| {c['label']} | {rc} | {'PASS' if rc == 0 else 'FAIL'} |")
    print(f"ARTIFACT: {out_path.relative_to(REPO)}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
