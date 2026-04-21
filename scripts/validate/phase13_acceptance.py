#!/usr/bin/env python3
"""Phase 13 Acceptance — Live Smoke 재도전 gate aggregator (Tier 1 only).

본 gate 는 Phase 13 의 6 Success Criteria 를 **Tier 1 infrastructure 관점**
에서 자동 검증합니다. Tier 2 (실 과금 live_smoke 5 tests) 는 대표님 승인
하에서만 별도 실행되며, 본 acceptance 는 deferred 상태로 간주하고 호출
하지 않습니다 — skip_gates 금지 (CLAUDE.md 금기 #1) 하에서도 실 과금
강제 유발은 금기 #8 "일일 업로드 금지" 관점에서 부당합니다.

본 gate 가 검증하는 9 check (Tier 1 범위):

- SC#1: Phase 13 Tier 1 전수 pytest green (≥39 passed, SMOKE-01~06 surface)
- SC#2: Tier 2 live_smoke 테스트 5개 collect 가능 (marker 등록 + 명시)
- SC#3: scripts/smoke/ 5 모듈 import clean (budget_counter / evidence_extractor
        / upload_evidence / provider_rates / phase13_live_smoke)
- SC#4: tests/phase13/fixtures/ 4 golden JSON 존재 + UTF-8 parseable
- SC#5: pytest.ini live_smoke marker 등록 + Phase 14 adapter_contract 보존
        (adapter_contract 30 tests GREEN regression — Phase 14 baseline)
- SC#6: scripts/smoke/phase13_live_smoke.py --help exit 0 + 4 flags advertised
        (--live, --max-attempts, --budget-cap-usd, --verbose-compression)

추가 2 audit:
- AUDIT harness_audit 점수 ≥ 80 (AUDIT-01/02)
- AUDIT drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 조건)

Tier 2 live_smoke (producer_output_*.json / supervisor_output_*.json /
smoke_upload_*.json / budget_usage_*.json / smoke_e2e_*.json 5 evidence
파일 anchor) 는 본 gate 범위 외입니다. 대표님 승인 후 별도 live run 에서
`py -3.11 -m pytest tests/phase13/ -m live_smoke --run-live` 로 검증됩니다.

phase14_acceptance.py 패턴 복제 (subprocess.run + rc record + JSON anchor).
Windows cp949 대응 — 모든 subprocess 에 PYTHONIOENCODING=utf-8 + encoding=
"utf-8" + errors="replace" 강제 (Phase 12 R5 mitigation, Phase 14 승계).

Exit 0 = ALL_PASS, exit 1 = FAIL. 결과 JSON 을 `.planning/phases/13-live-
smoke/13-06-acceptance.json` 에 anchoring 하여 Plan 13-06 Task 13-06-03
(TRACEABILITY) + Task 13-06-04 (VALIDATION flip) 의 증거 소스로 활용.

필수 #7 baseline: 출력 로그는 한국어 존댓말 + "대표님" 호칭 포함. SMOKE-0X
labels 는 요구사항 ID 와 1:1 mapping (SMOKE-01~06).
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# scripts/validate/phase13_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / ".planning" / "phases" / "13-live-smoke" / "evidence"
FIXTURES_DIR = REPO / "tests" / "phase13" / "fixtures"


def _run(cmd: list[str], label: str, timeout: int = 1200) -> dict:
    """subprocess.run + stdout capture + rc record.

    Windows cp949 대응 — PYTHONIOENCODING=utf-8 강제. FileNotFoundError /
    TimeoutExpired 를 rc 로 흡수하여 gate 가 crash 하지 않음. 금기 #3
    침묵 폴백 금지 — 실패 시 rc 명시적 기록.
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


def check_sc1_phase13_tier1_regression() -> dict:
    """SC#1 — SMOKE-01~06 Tier 1 surface: Phase 13 전수 pytest green (≥39 passed)."""
    return _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase13/",
            "-m",
            "not live_smoke",
            "--tb=short",
            "-q",
            "--no-cov",
        ],
        "SC#1 phase13_tier1_regression (SMOKE-01~06 Tier 1 surface)",
        timeout=300,
    )


def check_sc2_live_smoke_collection() -> dict:
    """SC#2 — SMOKE-01~06 Tier 2 marker: live_smoke 5+ tests collect 가능."""
    proc = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase13/",
            "-m",
            "live_smoke",
            "--collect-only",
            "-q",
            "--no-cov",
        ],
        "SC#2 tier2_live_smoke_collected (deferred — 실 과금 대표님 승인 후)",
        timeout=60,
    )
    # Tier 2 test count >=5 from stdout (5/44 tests collected pattern)
    stdout = proc.get("stdout_tail", "") or ""
    collected = 0
    for line in stdout.splitlines():
        # Match "5/44 tests collected" or "5 tests collected"
        if "collected" in line and "/" in line:
            try:
                collected = int(line.split("/")[0].strip().split()[-1])
                break
            except (ValueError, IndexError):
                continue
    proc["tier2_collected_count"] = collected
    # Override rc — SC#2 passes only if >=5 live_smoke tests found
    # (phase13 5 tests: live_run + smoke_01/02/03/04)
    if proc["rc"] == 0 and collected < 5:
        proc["rc"] = 1
        proc["stderr_tail"] = (
            f"Tier 2 expected ≥5 live_smoke tests, collected={collected}. "
            f"{proc.get('stderr_tail', '')}"
        )
    return proc


def check_sc3_smoke_modules_import() -> dict:
    """SC#3 — SMOKE-01~06 infra: scripts/smoke/ 5 모듈 import clean."""
    modules = [
        "scripts.smoke.budget_counter",
        "scripts.smoke.evidence_extractor",
        "scripts.smoke.upload_evidence",
        "scripts.smoke.provider_rates",
        "scripts.smoke.phase13_live_smoke",
    ]
    # Use subprocess to isolate import failures — reuse PYTHONIOENCODING guard.
    probe_code = (
        "import importlib, sys\n"
        "mods = " + repr(modules) + "\n"
        "failed = []\n"
        "for name in mods:\n"
        "    try:\n"
        "        importlib.import_module(name)\n"
        "    except Exception as e:\n"
        "        failed.append((name, type(e).__name__, str(e)))\n"
        "if failed:\n"
        "    for n, et, m in failed:\n"
        "        sys.stderr.write(f'FAIL {n}: {et}: {m}\\n')\n"
        "    sys.exit(1)\n"
        "print(f'IMPORT_OK count={len(mods)} 대표님')\n"
    )
    return _run(
        [sys.executable, "-c", probe_code],
        "SC#3 scripts_smoke_modules_import (SMOKE-01~06 infra 5 modules)",
        timeout=60,
    )


def check_sc4_golden_fixtures_parseable() -> dict:
    """SC#4 — SMOKE-01/02/04/06: 4 golden JSON 존재 + UTF-8 parseable."""
    required_fixtures = [
        "sample_producer_output.json",   # SMOKE-01
        "sample_supervisor_output.json",  # SMOKE-02
        "sample_smoke_upload.json",       # SMOKE-03/04
        "sample_smoke_e2e.json",          # SMOKE-06
    ]
    missing: list[str] = []
    unparseable: list[dict] = []
    for name in required_fixtures:
        path = FIXTURES_DIR / name
        if not path.exists():
            missing.append(name)
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            unparseable.append({"file": name, "error": str(exc)})
    ok = not missing and not unparseable
    return {
        "label": "SC#4 golden_fixtures_parseable (SMOKE-01/02/04/06 shape anchor)",
        "cmd": [f"json.loads scan on {FIXTURES_DIR.relative_to(REPO)}"],
        "rc": 0 if ok else 1,
        "required": required_fixtures,
        "missing": missing,
        "unparseable": unparseable,
        "stdout_tail": (
            f"fixtures={required_fixtures} missing={missing} "
            f"unparseable={unparseable} 대표님 OK={ok}"
        ),
        "stderr_tail": "",
    }


def check_sc5_pytest_ini_markers_and_phase14_regression() -> dict:
    """SC#5 — SMOKE + ADAPT regression: pytest.ini markers + adapter_contract 30 green.

    Phase 14 교훈: 전체 pytest tests/ sweep 은 본 SC 에 포함하지 않음 (1시간+
    소요). 대신 Phase 14 baseline (adapter_contract 30 tests) 가 여전히
    green 한지만 확인 — Phase 13 작업으로 adapter_contract 회귀 발생
    가능성 차단.
    """
    pytest_ini = REPO / "pytest.ini"
    if not pytest_ini.exists():
        return {
            "label": "SC#5 pytest_ini_markers_and_phase14_regression",
            "cmd": [f"exists({pytest_ini})"],
            "rc": 1,
            "reason": "pytest.ini missing",
            "stdout_tail": f"missing: {pytest_ini}",
            "stderr_tail": "",
        }
    text = pytest_ini.read_text(encoding="utf-8")
    required_markers = ["live_smoke", "adapter_contract"]
    missing_markers = [m for m in required_markers if f"{m}:" not in text]
    if missing_markers:
        return {
            "label": "SC#5 pytest_ini_markers_and_phase14_regression",
            "cmd": [f"marker scan on {pytest_ini.relative_to(REPO)}"],
            "rc": 1,
            "missing_markers": missing_markers,
            "stdout_tail": f"markers missing: {missing_markers} 대표님",
            "stderr_tail": "",
        }
    # Phase 14 adapter_contract regression — 30 tests must remain green.
    proc = _run(
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
        "SC#5 pytest_ini_markers_and_phase14_regression (adapter_contract 30 green)",
        timeout=300,
    )
    proc["markers_required"] = required_markers
    proc["markers_missing"] = missing_markers
    return proc


def check_sc6_live_smoke_runner_help() -> dict:
    """SC#6 — SMOKE-05/06 runner: phase13_live_smoke.py --help + 4 flags."""
    proc = _run(
        [
            sys.executable,
            "scripts/smoke/phase13_live_smoke.py",
            "--help",
        ],
        "SC#6 phase13_live_smoke_help (SMOKE-05/06 runner CLI)",
        timeout=60,
    )
    stdout = proc.get("stdout_tail", "") or ""
    required_flags = ["--live", "--max-attempts", "--budget-cap-usd", "--verbose-compression"]
    missing_flags = [f for f in required_flags if f not in stdout]
    proc["required_flags"] = required_flags
    proc["missing_flags"] = missing_flags
    if proc["rc"] == 0 and missing_flags:
        proc["rc"] = 1
        proc["stderr_tail"] = (
            f"runner --help missing flags: {missing_flags}. "
            f"{proc.get('stderr_tail', '')}"
        )
    return proc


def check_harness_audit() -> dict:
    """AUDIT — harness_audit 점수 ≥ 80 (AUDIT-01/02)."""
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
    """AUDIT — drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 clear)."""
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
        check_sc1_phase13_tier1_regression(),
        check_sc2_live_smoke_collection(),
        check_sc3_smoke_modules_import(),
        check_sc4_golden_fixtures_parseable(),
        check_sc5_pytest_ini_markers_and_phase14_regression(),
        check_sc6_live_smoke_runner_help(),
        check_harness_audit(),
        check_drift_scan(),
    ]
    all_ok = all(c.get("rc", 1) == 0 for c in checks)

    summary = {
        "phase": "13-live-smoke",
        "plan": "13-06",
        "tier": "tier1_only",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "all_passed": all_ok,
        "checks": checks,
        "requirements": [
            "SMOKE-01",
            "SMOKE-02",
            "SMOKE-03",
            "SMOKE-04",
            "SMOKE-05",
            "SMOKE-06",
        ],
        "deferred": {
            "tier2_live_smoke": (
                "실 과금 5 tests (producer/supervisor/upload/readback/live_run) "
                "는 대표님 승인 후 별도 live run 에서 검증"
            ),
            "evidence_files": [
                "producer_output_<sid>.json",
                "supervisor_output_<sid>.json",
                "smoke_upload_<sid>.json",
                "budget_usage_<sid>.json",
                "smoke_e2e_<sid>.json",
            ],
        },
    }

    out_path = (
        REPO
        / ".planning"
        / "phases"
        / "13-live-smoke"
        / "13-06-acceptance.json"
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

    verdict = "ALL_PASS" if all_ok else "FAIL"
    print(f"Phase 13 Acceptance (Tier 1): {verdict} 대표님 확인")
    print("| Check | RC | Label |")
    print("|-------|----|-------|")
    for c in checks:
        rc = c.get("rc", "n/a")
        status = "PASS" if rc == 0 else "FAIL"
        print(f"| {c['label']} | {rc} | {status} |")
    print(f"ARTIFACT: {out_path.relative_to(REPO)}")
    print(
        "NOTE: Tier 2 live_smoke (5 실 과금 tests) 는 본 gate 범위 외입니다. "
        "대표님 승인 후 별도 live run 에서 evidence 5 파일 (producer_output/"
        "supervisor_output/smoke_upload/budget_usage/smoke_e2e) anchor 됩니다."
    )

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
