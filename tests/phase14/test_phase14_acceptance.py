"""Phase 14 E2E Acceptance Wrapper.

phase14_acceptance.py 를 subprocess 로 호출하여 5 SC + 2 audit 게이트 결과를
단일 pytest 테스트 집합으로 감싸 CI/로컬에서 `pytest tests/phase14/` 단독
실행이 Phase 14 gate 판정을 대변하게 한다 (Phase 7 test_phase07_acceptance.py
패턴 재사용).

acceptance.py 자체는 phase05/06/07 sweep + full regression 을 포함하므로
fixture scope="module" 로 1회만 실행하고 7 테스트가 결과 JSON 을 재사용.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# tests/phase14/test_phase14_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]
_ACCEPT_MODULE = "scripts.validate.phase14_acceptance"
_JSON_PATH = (
    REPO
    / ".planning"
    / "phases"
    / "14-api-adapter-remediation"
    / "14-05-acceptance.json"
)


@pytest.fixture(scope="module")
def acceptance_result():
    """phase14_acceptance.py 실행 후 JSON 산출물 반환.

    scope="module" — acceptance.py 내부 full regression 이 10분 이상 소요될 수
    있으므로 8 tests 가 fixture 를 재사용한다. subprocess timeout 30분 (1800s).
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", _ACCEPT_MODULE],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )
    assert _JSON_PATH.exists(), (
        f"acceptance JSON 산출 부재: {_JSON_PATH}\n"
        f"stdout_tail:\n{(proc.stdout or '')[-1500:]}\n"
        f"stderr_tail:\n{(proc.stderr or '')[-500:]}"
    )
    summary = json.loads(_JSON_PATH.read_text(encoding="utf-8"))
    return proc.returncode, summary, proc.stdout or ""


def _find_check(summary: dict, label_prefix: str) -> dict:
    for c in summary["checks"]:
        if c["label"].startswith(label_prefix):
            return c
    raise AssertionError(
        f"check with label prefix {label_prefix!r} not found in summary"
    )


def test_phase14_acceptance_all_passed(acceptance_result):
    """Phase 14 5 SC + 2 audit 전체 green — rc=0 + all_passed=True."""
    rc, summary, stdout = acceptance_result
    assert rc == 0, (
        f"phase14_acceptance.py rc={rc}\nstdout_tail:\n{stdout[-1500:]}"
    )
    assert summary["all_passed"] is True, (
        f"all_passed=False. checks={[(c['label'], c.get('rc')) for c in summary['checks']]}"
    )


def test_phase14_sc1_phase05_06_07_zero_failures(acceptance_result):
    """SC#1 — ADAPT-04 Success Criteria #1 (phase05/06/07 sweep = 0 failures)."""
    _, summary, _ = acceptance_result
    sc1 = _find_check(summary, "SC#1")
    assert sc1["rc"] == 0, f"SC#1 failed: {sc1.get('stdout_tail', '')[-500:]}"


def test_phase14_sc2_contract_files_exist(acceptance_result):
    """SC#2 — ADAPT-01/02/03: 3 contract test files exist."""
    _, summary, _ = acceptance_result
    sc2 = _find_check(summary, "SC#2")
    assert sc2["rc"] == 0, f"Missing contract files: {sc2.get('missing', [])}"


def test_phase14_sc3_adapter_contracts_doc(acceptance_result):
    """SC#3 — ADAPT-05: wiki/render/adapter_contracts.md exists + 7 adapter rows."""
    _, summary, _ = acceptance_result
    sc3 = _find_check(summary, "SC#3")
    assert sc3["rc"] == 0, (
        f"SC#3 failed — missing_adapters={sc3.get('missing_adapters', [])}"
    )


def test_phase14_sc4_adapter_contract_marker_gate(acceptance_result):
    """SC#4 — ADAPT-06: pytest -m adapter_contract 단독 gate green."""
    _, summary, _ = acceptance_result
    sc4 = _find_check(summary, "SC#4")
    assert sc4["rc"] == 0, f"SC#4 failed: {sc4.get('stdout_tail', '')[-500:]}"


def test_phase14_sc5_full_regression(acceptance_result):
    """SC#5 — ADAPT-04 #5: pytest tests/ full regression exit 0."""
    _, summary, _ = acceptance_result
    sc5 = _find_check(summary, "SC#5")
    assert sc5["rc"] == 0, f"SC#5 failed: {sc5.get('stdout_tail', '')[-500:]}"


def test_phase14_harness_audit_min_80(acceptance_result):
    """AUDIT — harness_audit 점수 >= 80 (AUDIT-01/02)."""
    _, summary, _ = acceptance_result
    audit = _find_check(summary, "AUDIT harness")
    assert audit["rc"] == 0, (
        f"harness_audit < 80 or failed: {audit.get('stdout_tail', '')[-500:]}"
    )


def test_phase14_drift_scan_no_a_class(acceptance_result):
    """AUDIT — drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 clear)."""
    _, summary, _ = acceptance_result
    drift = _find_check(summary, "AUDIT drift")
    assert drift["rc"] == 0, (
        f"drift_scan A급 detected: {drift.get('stdout_tail', '')[-500:]}"
    )
