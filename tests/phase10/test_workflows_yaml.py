"""Phase 10 Plan 04 — GH Actions workflow YAML 검증.

stdlib re 기반 (PyYAML 선택적) — CI 에 PyYAML 이 없어도 통과.

Tests:
    yml-1  test_workflow_yaml_files_parseable         : 4 파일 syntax + on:/jobs:/cron 블록
    yml-2  test_workflow_secrets_reference_shape      : GH secrets 참조 확인 (YOUTUBE_TOKEN_JSON 등)
    yml-3  test_workflow_permissions_minimal          : drift-scan-weekly 만 issues: write, 나머지는 부재
    yml-4  test_drift_scan_weekly_has_label_creation  : BLOCKER #2 — gh label create 3종 redundant step
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"
_WORKFLOW_NAMES = (
    "analytics-daily",
    "drift-scan-weekly",
    "skill-patch-count-monthly",
    "harness-audit-monthly",
)


def _text(name: str) -> str:
    return (_WORKFLOWS / f"{name}.yml").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", _WORKFLOW_NAMES)
def test_workflow_yaml_files_parseable(name: str) -> None:
    """yml-1: 각 YAML 이 on: / cron / jobs: 블록을 갖춘다 (syntax 검증)."""
    p = _WORKFLOWS / f"{name}.yml"
    assert p.exists(), f"{name}.yml missing"
    text = p.read_text(encoding="utf-8")

    assert re.search(r"^on:\s*$", text, re.MULTILINE), f"{name}: `on:` block missing"
    assert re.search(
        r"cron:\s*'[0-9 */,-]+'", text
    ), f"{name}: cron expression missing"
    assert re.search(r"^jobs:\s*$", text, re.MULTILINE), f"{name}: `jobs:` block missing"
    assert re.search(
        r"workflow_dispatch", text
    ), f"{name}: workflow_dispatch manual trigger missing"


def test_workflow_secrets_reference_shape() -> None:
    """yml-2: analytics-daily 는 YOUTUBE_TOKEN_JSON / YOUTUBE_CLIENT_SECRET / RECENT_VIDEO_IDS 참조."""
    analytics = _text("analytics-daily")
    assert "secrets.YOUTUBE_TOKEN_JSON" in analytics, (
        "analytics-daily: YOUTUBE_TOKEN_JSON secret 참조 없음"
    )
    assert "secrets.YOUTUBE_CLIENT_SECRET" in analytics, (
        "analytics-daily: YOUTUBE_CLIENT_SECRET secret 참조 없음"
    )
    assert "secrets.RECENT_VIDEO_IDS" in analytics, (
        "analytics-daily: RECENT_VIDEO_IDS secret 참조 없음"
    )

    drift = _text("drift-scan-weekly")
    assert "secrets.GITHUB_TOKEN" in drift, (
        "drift-scan-weekly: GITHUB_TOKEN secret 참조 없음 (gh CLI 인증용)"
    )


def test_workflow_permissions_minimal() -> None:
    """yml-3: drift-scan-weekly 만 issues: write, 나머지 3은 포함하지 않는다 (least-privilege)."""
    drift = _text("drift-scan-weekly")
    assert re.search(r"issues:\s*write", drift), (
        "drift-scan-weekly: `issues: write` permission 필요 (gh issue create)"
    )

    for name in ("analytics-daily", "skill-patch-count-monthly", "harness-audit-monthly"):
        text = _text(name)
        assert not re.search(r"issues:\s*write", text), (
            f"{name}: `issues: write` 불필요 (least-privilege 위반)"
        )


def test_drift_scan_weekly_has_label_creation() -> None:
    """yml-4 (BLOCKER #2): drift-scan-weekly 가 gh label create drift/phase-10/auto 를 호출한다.

    Wave 0 manual dispatch 가 primary 방어선이지만, GH Actions step 에서도 redundant safety
    로 label 부재 422 에러를 방지한다. `|| true` 로 이미 존재 시 무시.
    """
    drift = _text("drift-scan-weekly")
    assert re.search(r"gh label create drift\b", drift), (
        "drift-scan-weekly: gh label create drift step 누락"
    )
    assert re.search(r"gh label create phase-10\b", drift), (
        "drift-scan-weekly: gh label create phase-10 step 누락"
    )
    assert re.search(r"gh label create auto\b", drift), (
        "drift-scan-weekly: gh label create auto step 누락"
    )


def test_drift_scan_weekly_uses_harness_separate_checkout() -> None:
    """WARNING #4: harness 는 submodule 이 아니라 별도 checkout step + --harness-path."""
    drift = _text("drift-scan-weekly")
    assert "Checkout naberal_harness" in drift, (
        "drift-scan-weekly: harness 별도 checkout step 누락"
    )
    assert "--harness-path" in drift, (
        "drift-scan-weekly: --harness-path flag 전달 누락 (graceful fallback)"
    )
    assert "submodules: recursive" not in drift, (
        "drift-scan-weekly: harness 는 submodule 이 아님 — recursive 금지"
    )
