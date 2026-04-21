"""Phase 13 Wave 4 Task 13-05-03 — subprocess integration tests for phase13_live_smoke.py runner.

Two-tier strategy:
- Tier 1 (always-run): dry-run subprocess (no --live flag) — $0 cost, verifies CLI wiring.
- Tier 2 (opt-in @pytest.mark.live_smoke): full --live subprocess run — requires `--run-live` CLI flag to activate. Skipped otherwise (CLAUDE.md 금기 #8 일일 업로드 방지).

대표님께 드리는 보고:
    Tier 1 은 실 과금 없이 runner CLI 가 정상 동작하는지 확인합니다.
    Tier 2 는 대표님 승인 후에만 `pytest --run-live` 로 활성화됩니다.

References:
- scripts/smoke/phase13_live_smoke.py (Task 13-05-01)
- tests/phase13/conftest.py (fixtures, --run-live 옵션)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "smoke" / "phase13_live_smoke.py"


def _run_runner(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """phase13_live_smoke.py subprocess 실행 헬퍼 (Windows cp949 대응)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(RUNNER_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=env,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Tier 1 — dry-run (no --live flag, $0 cost)
# ---------------------------------------------------------------------------


def test_smoke_runner_dry_run_help_exits_zero():
    """CLI --help 가 4 플래그 (--live / --max-attempts / --budget-cap-usd / --verbose-compression) 을 모두 노출한다."""
    result = _run_runner(["--help"], timeout=30)
    assert result.returncode == 0, f"--help 실패 rc={result.returncode} stderr={result.stderr[-500:]}"
    help_text = result.stdout + result.stderr
    # 4 CLI flags 존재 검증
    assert "--live" in help_text, "--live flag not advertised in --help"
    assert "--max-attempts" in help_text, "--max-attempts flag not advertised"
    assert "--budget-cap-usd" in help_text, "--budget-cap-usd flag not advertised"
    assert "--verbose-compression" in help_text, "--verbose-compression flag not advertised"


# ---------------------------------------------------------------------------
# Tier 2 — opt-in live run (@pytest.mark.live_smoke, --run-live required)
# ---------------------------------------------------------------------------


@pytest.mark.live_smoke
def test_smoke_runner_live_subprocess_full_e2e(request, tmp_path):
    """실 과금 full E2E — 대표님 승인 지점에서만 활성.

    `pytest --run-live` 가 없으면 conftest.py 의 `pytest_collection_modifyitems`
    훅이 자동 skip 처리한다.

    실행 조건:
    - ANTHROPIC_API_KEY (또는 Claude CLI Max subscription)
    - config/client_secret.json + config/youtube_token.json (Phase 8 OAuth)
    - .env 파일
    - budget_cap_usd=$5.00 upper bound

    예상 비용: $1.50 ~ $3.00 (Kling 8 cuts × $0.35 + Typecast $0.12 + Nano $0.04).
    """
    if not request.config.getoption("--run-live", default=False):
        pytest.skip("--run-live not passed — live smoke subprocess skipped (대표님 승인 필요)")

    # Redirect publish lock to tmp path (금기 #8 일일 업로드 방지 + 48h+ 카운터 미소진)
    lock_path = tmp_path / "publish_lock_phase13_live.json"
    env_override = os.environ.copy()
    env_override["PYTHONIOENCODING"] = "utf-8"
    env_override["SHORTS_PUBLISH_LOCK_PATH"] = str(lock_path)

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--live",
            "--budget-cap-usd",
            "5.00",
            "--max-attempts",
            "2",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=env_override,
        timeout=1800,  # 30 min budget for full E2E live run
    )

    # Exit code 0 = smoke completed green
    assert result.returncode == 0, (
        f"Live smoke rc={result.returncode} — stderr tail:\n{result.stderr[-2000:]}"
    )

    # Evidence anchoring 검증 — 5 evidence files 존재
    evidence_dir = REPO_ROOT / ".planning" / "phases" / "13-live-smoke" / "evidence"
    assert evidence_dir.exists(), f"Evidence dir missing: {evidence_dir}"

    # 5 evidence file types (timestamped — glob 로 최근 생성 확인)
    required_globs = [
        "producer_output_*.json",
        "supervisor_output_*.json",
        "smoke_upload_*.json",
        "budget_usage_*.json",
        "smoke_e2e_*.json",
    ]
    for pattern in required_globs:
        matches = list(evidence_dir.glob(pattern))
        assert matches, f"Evidence file pattern missing: {pattern}"
