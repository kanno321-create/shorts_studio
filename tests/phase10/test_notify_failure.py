"""Phase 10 Plan 04 — scripts.schedule.notify_failure unit tests.

Tests:
    ps-4     test_windows_tasks_ps1_documents_publish_lock_pacing  : BLOCKER #1 publish_lock 문서화
    ps-1/2/3 test_windows_tasks_ps1_*                              : Register-ScheduledTask 3회 + RunLevel + idempotent
    notify-1 test_notify_failure_appends_to_failures_md            : tmp FAILURES.md append + F-OPS-NN
    notify-2 test_notify_failure_smtp_skipped_if_env_missing       : env 미설정 → skip + exit 0
    notify-3 test_notify_failure_smtp_called_when_env_set          : monkeypatch + smtplib mock
    notify-4 test_notify_failure_stdout_json_always                : 항상 stdout JSON
    notify-5 test_notify_failure_next_id_increments                : F-OPS-01 존재 → F-OPS-02
    notify-6 test_notify_failure_cli_task_name_required            : --task-name 미제공 → argparse exit 2
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.schedule import notify_failure as nf  # noqa: E402

_PS1 = _REPO_ROOT / "scripts" / "schedule" / "windows_tasks.ps1"


# ---------------------------------------------------------------------------
# PowerShell script structural tests (no PowerShell runtime required)
# ---------------------------------------------------------------------------


def test_windows_tasks_ps1_contains_three_register() -> None:
    """ps-1: PowerShell 스크립트에 Register-ScheduledTask 3회 호출 (Pipeline/Upload/NotifyFailure)."""
    text = _PS1.read_text(encoding="utf-8")
    # Register-ScheduledTask 본체 호출만 카운트 (함수 정의/주석 제외)
    register_calls = re.findall(r"Register-ShortsTask\s+`?", text)
    assert len(register_calls) >= 3, (
        f"Register-ShortsTask helper 가 3회 이상 호출되어야 함. 발견: {len(register_calls)}"
    )
    # 각 task 이름 presence
    for tn in ("ShortsStudio_Pipeline", "ShortsStudio_Upload", "ShortsStudio_NotifyFailure"):
        assert tn in text, f"Task 이름 {tn} 누락"


def test_windows_tasks_ps1_uses_runlevel_highest() -> None:
    """ps-2: RunLevel Highest 지정 (Pitfall 4 — 관리자 권한 필수)."""
    text = _PS1.read_text(encoding="utf-8")
    assert re.search(r"-RunLevel\s+Highest", text), "-RunLevel Highest 누락"


def test_windows_tasks_ps1_idempotent() -> None:
    """ps-3: -Force flag 또는 Unregister-ScheduledTask 선행 (재실행 안전)."""
    text = _PS1.read_text(encoding="utf-8")
    assert "Unregister-ScheduledTask" in text, "Unregister 선행 로직 누락"
    assert "-Force" in text, "-Force 덮어쓰기 flag 누락"


def test_windows_tasks_ps1_documents_publish_lock_pacing() -> None:
    """ps-4 (BLOCKER #1): publish_lock.assert_can_publish / AF-1 / 주 3~4편 중 1개 이상 언급.

    CLAUDE.md 도메인 절대 규칙 #8 — 일일 트리거가 봇 패턴처럼 보이지 않도록 pace
    gating 설계 의도를 스크립트 본문에 문서화.
    """
    text = _PS1.read_text(encoding="utf-8")
    has_any = (
        "publish_lock.assert_can_publish" in text
        or "AF-1" in text
        or "AF-11" in text
        or "주 3~4편" in text
    )
    assert has_any, (
        "windows_tasks.ps1 에 publish_lock pacing / AF-1 / AF-11 / 주 3~4편 중 "
        "1개 이상 언급 필수 (BLOCKER #1)"
    )


# ---------------------------------------------------------------------------
# notify_failure.py fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_failures(tmp_path: Path) -> Path:
    """seed FAILURES.md with a single F-OPS-01 entry to test monotonic id increment."""
    p = tmp_path / "FAILURES.md"
    p.write_text(
        "# FAILURES.md — test seed\n\n"
        "### F-OPS-01 — 기존 엔트리\n\n"
        "**Task**: `seed`\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def fresh_failures(tmp_path: Path) -> Path:
    """seed FAILURES.md with NO F-OPS entries (fresh install)."""
    p = tmp_path / "FAILURES.md"
    p.write_text(
        "# FAILURES.md — shorts_studio\n\n> regime\n\n"
        "## F-CTX-01 — 세션 간 컨텍스트 단절\n",
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# notify_failure unit tests
# ---------------------------------------------------------------------------


def test_notify_failure_appends_to_failures_md(
    fresh_failures: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """notify-1: fresh FAILURES.md → F-OPS-01 추가 + prefix 유지."""
    monkeypatch.delenv("SMTP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    before = fresh_failures.read_text(encoding="utf-8")

    rc = nf.main([
        "--task-name", "ShortsStudio_Pipeline",
        "--error-msg", "Kling timeout after 120s",
        "--failures-path", str(fresh_failures),
        "--skip-email",
    ])
    assert rc == 0
    after = fresh_failures.read_text(encoding="utf-8")
    assert after.startswith(before), "기존 본문 preservation 실패 (append-only 위반)"
    assert "### F-OPS-01" in after
    assert "ShortsStudio_Pipeline" in after
    assert "Kling timeout after 120s" in after


def test_notify_failure_smtp_skipped_if_env_missing(
    fresh_failures: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """notify-2: SMTP_APP_PASSWORD 미설정 → email skip + exit 0 + reason 명시."""
    monkeypatch.delenv("SMTP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)

    rc = nf.main([
        "--task-name", "TEST",
        "--error-msg", "smoke",
        "--failures-path", str(fresh_failures),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["email_sent"] is False
    assert data["email_reason"] is not None and "missing" in data["email_reason"]


def test_notify_failure_smtp_called_when_env_set(
    fresh_failures: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """notify-3: SMTP env 설정 + smtplib mock → 1회 send_message 호출."""
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "dummy")
    monkeypatch.setenv("EMAIL_TO", "kanno3@naver.com")

    smtp_instance = MagicMock()
    smtp_instance.__enter__ = MagicMock(return_value=smtp_instance)
    smtp_instance.__exit__ = MagicMock(return_value=False)
    smtp_cls = MagicMock(return_value=smtp_instance)
    monkeypatch.setattr(nf.smtplib, "SMTP", smtp_cls)

    rc = nf.main([
        "--task-name", "ShortsStudio_Upload",
        "--error-msg", "OAuth token expired",
        "--failures-path", str(fresh_failures),
        "--skip-failures-append",
    ])
    assert rc == 0
    assert smtp_cls.call_count == 1, "smtplib.SMTP 생성자 1회 호출 기대"
    assert smtp_instance.starttls.call_count == 1
    assert smtp_instance.login.call_count == 1
    assert smtp_instance.send_message.call_count == 1

    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["email_sent"] is True


def test_notify_failure_stdout_json_always(
    fresh_failures: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """notify-4: skip 모드에서도 항상 stdout JSON 출력."""
    monkeypatch.delenv("SMTP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    rc = nf.main([
        "--task-name", "TEST",
        "--error-msg", "smoke",
        "--failures-path", str(fresh_failures),
        "--skip-email",
        "--skip-failures-append",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)  # JSON parseable
    assert data["task_name"] == "TEST"
    assert data["entry_id"] is None  # skip-failures-append → None
    assert data["email_sent"] is False


def test_notify_failure_next_id_increments(
    tmp_failures: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """notify-5: 기존 F-OPS-01 존재 → 다음 호출 시 F-OPS-02 추가."""
    monkeypatch.delenv("SMTP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)

    rc = nf.main([
        "--task-name", "ShortsStudio_NotifyFailure",
        "--error-msg", "second failure",
        "--failures-path", str(tmp_failures),
        "--skip-email",
    ])
    assert rc == 0
    text = tmp_failures.read_text(encoding="utf-8")
    assert "### F-OPS-02" in text
    # 기존 F-OPS-01 보존 확인
    assert "### F-OPS-01" in text


def test_notify_failure_cli_task_name_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """notify-6: --task-name 미제공 → argparse SystemExit code 2."""
    with pytest.raises(SystemExit) as exc:
        nf.main(["--error-msg", "no task name"])
    assert exc.value.code == 2
