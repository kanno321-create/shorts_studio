"""Phase 13 E2E Acceptance Wrapper (Tier 1 only).

phase13_acceptance.py 를 subprocess 로 호출하여 8 check (6 SC + 2 audit)
결과를 단일 pytest 테스트 집합으로 감싸 `pytest tests/phase13/test_phase13_
acceptance.py` 단독 호출이 Phase 13 gate 판정을 대변하게 한다 (Phase 14
test_phase14_acceptance.py 패턴 복제).

본 wrapper 는 Tier 1 전용 — Tier 2 live_smoke 5 tests (producer/supervisor/
upload/readback/live_run) 는 대표님 승인 후 별도 live run 에서 검증됩니다.
본 wrapper 는 Tier 2 evidence 존재를 assert 하지 않고, 대신 Tier 2 test
collection (≥5) 및 live_smoke runner --help 계약만 검증합니다.

acceptance.py 자체는 pytest subprocess (phase13 Tier 1 + adapter_contract
regression) 를 내포하므로 fixture scope="module" 로 1회만 실행하고 10
테스트가 결과 JSON 을 재사용합니다. subprocess timeout 1500s (25min)
— acceptance.py 내부 최대 1200s + subprocess overhead.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# tests/phase13/test_phase13_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]
_ACCEPT_MODULE = "scripts.validate.phase13_acceptance"
_JSON_PATH = (
    REPO
    / ".planning"
    / "phases"
    / "13-live-smoke"
    / "13-06-acceptance.json"
)


@pytest.fixture(scope="module")
def acceptance_result():
    """phase13_acceptance.py 실행 후 JSON 산출물 반환 (대표님 용).

    scope="module" — acceptance.py 내부 phase13 tier1 + adapter_contract
    regression 이 ~5-10분 소요될 수 있으므로 10 tests 가 fixture 를
    재사용합니다. subprocess timeout 25분 (1500s).
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
        timeout=1500,
    )
    assert _JSON_PATH.exists(), (
        f"acceptance JSON 산출 부재 대표님: {_JSON_PATH}\n"
        f"stdout_tail:\n{(proc.stdout or '')[-1500:]}\n"
        f"stderr_tail:\n{(proc.stderr or '')[-500:]}"
    )
    summary = json.loads(_JSON_PATH.read_text(encoding="utf-8"))
    return proc.returncode, summary, proc.stdout or ""


def _find_check(summary: dict, label_prefix: str) -> dict:
    """summary.checks 에서 label_prefix 로 시작하는 check 조회."""
    for c in summary["checks"]:
        if c["label"].startswith(label_prefix):
            return c
    raise AssertionError(
        f"check with label prefix {label_prefix!r} not found in summary "
        f"(labels={[c['label'] for c in summary['checks']]})"
    )


def test_phase13_acceptance_all_passed(acceptance_result):
    """Phase 13 6 SC + 2 audit 전수 green — rc=0 + all_passed=True."""
    rc, summary, stdout = acceptance_result
    assert rc == 0, (
        f"phase13_acceptance.py rc={rc} 대표님\nstdout_tail:\n{stdout[-1500:]}"
    )
    assert summary["all_passed"] is True, (
        f"all_passed=False 대표님. checks="
        f"{[(c['label'], c.get('rc')) for c in summary['checks']]}"
    )


def test_phase13_acceptance_json_shape(acceptance_result):
    """acceptance.json 존재 + shape — checks 배열 ≥8 items + requirements 6건."""
    _, summary, _ = acceptance_result
    assert "checks" in summary, "acceptance JSON 에 checks 키 부재 대표님"
    assert len(summary["checks"]) >= 8, (
        f"checks 개수 부족 대표님: {len(summary['checks'])} < 8"
    )
    assert summary.get("phase") == "13-live-smoke"
    assert summary.get("tier") == "tier1_only"
    reqs = summary.get("requirements", [])
    assert set(reqs) == {"SMOKE-01", "SMOKE-02", "SMOKE-03", "SMOKE-04", "SMOKE-05", "SMOKE-06"}, (
        f"requirements 6건 SMOKE-01~06 부재 대표님: {reqs}"
    )
    assert "deferred" in summary, "deferred 블록 부재 대표님 (Tier 2 명시 필요)"
    assert "tier2_live_smoke" in summary["deferred"]


def test_phase13_sc1_phase13_tier1_regression(acceptance_result):
    """SC#1 — SMOKE-01~06 Tier 1 surface: Phase 13 전수 pytest green."""
    _, summary, _ = acceptance_result
    sc1 = _find_check(summary, "SC#1")
    assert sc1["rc"] == 0, f"SC#1 failed 대표님: {sc1.get('stdout_tail', '')[-500:]}"


def test_phase13_sc2_tier2_live_smoke_collected(acceptance_result):
    """SC#2 — Tier 2 live_smoke 5+ tests collect 가능 (deferred execution)."""
    _, summary, _ = acceptance_result
    sc2 = _find_check(summary, "SC#2")
    assert sc2["rc"] == 0, f"SC#2 failed 대표님: {sc2.get('stderr_tail', '')[-500:]}"
    collected = sc2.get("tier2_collected_count", 0)
    assert collected >= 5, f"Tier 2 수 부족 대표님: {collected} < 5"


def test_phase13_sc3_scripts_smoke_modules_import(acceptance_result):
    """SC#3 — scripts/smoke/ 5 모듈 import clean."""
    _, summary, _ = acceptance_result
    sc3 = _find_check(summary, "SC#3")
    assert sc3["rc"] == 0, f"SC#3 import 실패 대표님: {sc3.get('stderr_tail', '')[-500:]}"


def test_phase13_sc4_golden_fixtures_parseable(acceptance_result):
    """SC#4 — 4 golden JSON fixtures 존재 + UTF-8 parseable."""
    _, summary, _ = acceptance_result
    sc4 = _find_check(summary, "SC#4")
    assert sc4["rc"] == 0, (
        f"SC#4 fixtures 실패 대표님 — missing={sc4.get('missing', [])} "
        f"unparseable={sc4.get('unparseable', [])}"
    )


def test_phase13_sc5_pytest_ini_markers_and_phase14_regression(acceptance_result):
    """SC#5 — pytest.ini live_smoke marker + Phase 14 adapter_contract 30 green."""
    _, summary, _ = acceptance_result
    sc5 = _find_check(summary, "SC#5")
    assert sc5["rc"] == 0, (
        f"SC#5 pytest.ini/adapter_contract regression 실패 대표님: "
        f"{sc5.get('stdout_tail', '')[-500:]}"
    )


def test_phase13_sc6_live_smoke_runner_help(acceptance_result):
    """SC#6 — phase13_live_smoke.py --help exit 0 + 4 flags advertised."""
    _, summary, _ = acceptance_result
    sc6 = _find_check(summary, "SC#6")
    assert sc6["rc"] == 0, (
        f"SC#6 runner --help 실패 대표님 — missing_flags="
        f"{sc6.get('missing_flags', [])}"
    )


def test_phase13_harness_audit_min_80(acceptance_result):
    """AUDIT — harness_audit 점수 ≥ 80 (AUDIT-01/02)."""
    _, summary, _ = acceptance_result
    audit = _find_check(summary, "AUDIT harness")
    assert audit["rc"] == 0, (
        f"harness_audit < 80 or failed 대표님: {audit.get('stdout_tail', '')[-500:]}"
    )


def test_phase13_drift_scan_no_a_class(acceptance_result):
    """AUDIT — drift_scan A급 drift 0 건 (AUDIT-03/04 Phase 차단 clear)."""
    _, summary, _ = acceptance_result
    drift = _find_check(summary, "AUDIT drift")
    assert drift["rc"] == 0, (
        f"drift_scan A급 detected 대표님: {drift.get('stdout_tail', '')[-500:]}"
    )
