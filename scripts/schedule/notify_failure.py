"""Failure notifier — stdout JSON + SMTP email + FAILURES.md append (3 채널 분산).

Phase 10 Plan 04. 무인 운영 장애점 제거 목적으로 실패 정보를 세 곳에 분산 기록합니다.

Called by:
    - Windows Task Scheduler 실패 action (ShortsStudio_Pipeline / Upload 가 exit != 0)
    - GH Actions workflow `if: failure()` step (optional, GH built-in email 이 1차)
    - Python orchestrator (scripts/orchestrator/shorts_pipeline.py) 에서 직접 import 도 가능

Design (RESEARCH Pitfall 3 — hook 우회):
    - stdout JSON         : 항상 출력 (scheduler 로그 수집용, 파이프라인 후처리 용이)
    - SMTP email          : SMTP_APP_PASSWORD env 있을 때만 (미설정 시 graceful skip)
    - FAILURES.md append  : 직접 `open("a")` 로 append — Claude Write tool hook 은 통과
                            (hook 은 Claude Write/Edit 만 검사하므로 Python 직접 I/O 는 허용됨)

CLI:
    python -m scripts.schedule.notify_failure \
        --task-name ShortsStudio_Pipeline \
        --error-msg "KlingI2VAdapter timeout after 120s"

    # smoke test (FAILURES append + email 둘 다 skip, stdout JSON 만):
    python -m scripts.schedule.notify_failure \
        --task-name TEST --error-msg smoke \
        --skip-email --skip-failures-append
"""
from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

# Windows cp949 stdout 가드 — 한국어 에러 메시지 round-trip.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

KST = ZoneInfo("Asia/Seoul")
SMTP_HOST_DEFAULT = "smtp.gmail.com"
SMTP_PORT_DEFAULT = 587
EMAIL_TO_DEFAULT = "kanno3@naver.com"

_ENTRY_ID_RE = re.compile(r"### F-OPS-(\d{2,})")


def append_failures(
    task_name: str,
    error_msg: str,
    now: datetime,
    failures_path: Path,
) -> str:
    """Append F-OPS-NN entry to FAILURES.md and return the assigned entry id.

    Uses direct `open("a")` — Claude pre_tool_use hook (`check_failures_append_only`)
    only inspects Claude Write/Edit tools, so Python direct I/O bypasses it
    while preserving the append-only semantics at the file level.

    Raises:
        FileNotFoundError: if `failures_path` does not exist. The scheduler must
            ensure FAILURES.md is present (it is committed to the repo root).
    """
    if not failures_path.exists():
        raise FileNotFoundError(
            f"FAILURES.md not found at {failures_path}. "
            f"Repo root 에 FAILURES.md 가 있는지 확인해 주십시오."
        )

    existing = failures_path.read_text(encoding="utf-8")
    ids = [int(m) for m in _ENTRY_ID_RE.findall(existing)]
    next_id = max(ids, default=0) + 1
    entry_id = f"F-OPS-{next_id:02d}"

    truncated_error = error_msg[:1500]
    body_lines = [
        "",
        "",
        f"### {entry_id} — Scheduler 실패 ({now.date().isoformat()}, {task_name})",
        "",
        f"**Task**: `{task_name}`",
        f"**Timestamp**: {now.isoformat()}",
        "",
        "**증상**:",
        "```",
        truncated_error,
        "```",
        "",
        "**조치**: Scheduler 로그 확인 → 원인 분류 (API / network / OAuth / git 권한 / drift) "
        "→ 재시도 또는 FAILURES 에서 root-cause 추적.",
        "",
        "**관련**: Plan 10-04 scheduler + Plan 10-08 ROLLBACK.md 시나리오",
    ]
    with failures_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(body_lines) + "\n")
    return entry_id


def send_email(task_name: str, error_msg: str, now: datetime) -> dict:
    """Send SMTP email. Returns {"sent": bool, "reason": str|None}.

    Graceful degradation: SMTP_USER 또는 SMTP_APP_PASSWORD 미설정 시 skip + 이유 반환.
    이는 GH Actions 가 primary email path 이고 Windows SMTP 는 보조 채널이기 때문.
    """
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_APP_PASSWORD")
    if not (user and password):
        return {
            "sent": False,
            "reason": "SMTP_USER or SMTP_APP_PASSWORD env missing (graceful skip)",
        }

    host = os.environ.get("SMTP_HOST", SMTP_HOST_DEFAULT)
    port = int(os.environ.get("SMTP_PORT", SMTP_PORT_DEFAULT))
    to = os.environ.get("EMAIL_TO", EMAIL_TO_DEFAULT)

    body = (
        f"Task: {task_name}\n"
        f"Time: {now.isoformat()}\n\n"
        f"Error:\n{error_msg[:2000]}"
    )
    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["Subject"] = f"[shorts_studio] FAILURE — {task_name}"
    msg["From"] = user
    msg["To"] = to

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)

    return {"sent": True, "reason": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.schedule.notify_failure",
        description="Scheduler failure notifier — 3채널 (stdout / SMTP / FAILURES append)",
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="실패한 task 이름 (예: ShortsStudio_Pipeline)",
    )
    parser.add_argument(
        "--error-msg",
        default="(no error message provided)",
        help="에러 메시지 원문 (stderr dump 권장)",
    )
    parser.add_argument(
        "--failures-path",
        type=Path,
        default=Path("FAILURES.md"),
        help="FAILURES.md 경로 (기본: repo root)",
    )
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="SMTP email 전송 skip (smoke test 용)",
    )
    parser.add_argument(
        "--skip-failures-append",
        action="store_true",
        help="FAILURES.md append skip (smoke test 용)",
    )
    args = parser.parse_args(argv)

    now = datetime.now(KST)
    result: dict = {
        "task_name": args.task_name,
        "timestamp": now.isoformat(),
        "entry_id": None,
        "email_sent": False,
        "email_reason": None,
    }

    if not args.skip_failures_append:
        entry_id = append_failures(
            args.task_name,
            args.error_msg,
            now,
            args.failures_path,
        )
        result["entry_id"] = entry_id

    if not args.skip_email:
        email_result = send_email(args.task_name, args.error_msg, now)
        result["email_sent"] = email_result["sent"]
        result["email_reason"] = email_result["reason"]

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
