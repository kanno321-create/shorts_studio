"""Emergency scheduler shutdown — Phase 10 Plan 08.

Reverses the Phase 8 ``publish_lock`` 48h+jitter gate by writing a future
``last_upload_iso`` timestamp into ``.planning/publish_lock.json`` so the next
``scripts.publisher.publish_lock.assert_can_publish()`` call raises
``PublishLockViolation`` for the configured block window (default 49 hours).
On Windows the companion Windows Task Scheduler tasks registered by
``scripts/schedule/windows_tasks.ps1`` (``ShortsStudio_Pipeline`` /
``ShortsStudio_Upload`` / ``ShortsStudio_NotifyFailure``) are unregistered
via the ``-Unregister`` parameter of that same PowerShell script.

Usage
-----
    python -m scripts.rollback.stop_scheduler                       # block + unregister + json stdout
    python -m scripts.rollback.stop_scheduler --dry-run             # inspect only, zero side effects
    python -m scripts.rollback.stop_scheduler --block-hours 72 --skip-unregister
    python -m scripts.rollback.stop_scheduler --skip-publish-lock   # tasks only

Environment
-----------
    SHORTS_PUBLISH_LOCK_PATH    override lock path (same as publish_lock.py).

Related
-------
    ``.planning/phases/10-sustained-operations/ROLLBACK.md`` — runbook that
    invokes this CLI for all three emergency scenarios.
    ``scripts/publisher/publish_lock.py`` — the gate this CLI weaponizes.
    ``scripts/schedule/windows_tasks.ps1`` — the PowerShell companion.

D-2 Lock (FAIL-04) safety
-------------------------
This CLI writes to ``.planning/publish_lock.json`` (gitignored upload history
file) and invokes a PowerShell subprocess — no touch to ``.claude/`` /
``CLAUDE.md`` / ``.claude/skills/`` / ``.claude/hooks/``. Safe for D-2 Lock
period (2026-04-20 ~ 2026-06-20).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows cp949 stdout guard — Korean stderr / JSON roundtrip on emergency path.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_LOCK_PATH = Path(".planning/publish_lock.json")
DEFAULT_PS1 = Path("scripts/schedule/windows_tasks.ps1")

# Must stay in sync with ``scripts/schedule/windows_tasks.ps1`` Register block.
WINDOWS_TASKS: tuple[str, str, str] = (
    "ShortsStudio_Pipeline",
    "ShortsStudio_Upload",
    "ShortsStudio_NotifyFailure",
)


def block_publish(lock_path: Path, hours: int = 49,
                  now: datetime | None = None) -> dict:
    """Write ``publish_lock.json`` with a future ``last_upload_iso``.

    Schema is identical to ``scripts.publisher.publish_lock.record_upload``
    output so ``assert_can_publish`` recognises it without migration:
    ``{last_upload_iso, jitter_applied_min, _schema}``. ``jitter_applied_min``
    is forced to 0 so the block window is exactly ``hours`` hours — callers
    who want longer blocks should bump ``hours`` rather than inflate jitter.

    Parameters
    ----------
    lock_path
        Absolute or repo-relative path to the lock file. Parent dirs are
        created on demand (``.planning/`` may not yet exist on a fresh clone).
    hours
        Forward block window. Default 49 beats the 48h+jitter floor and
        absorbs a few minutes of wall-clock drift. Raise for longer blocks.
    now
        Inject a frozen UTC clock for deterministic tests. Defaults to
        ``datetime.now(timezone.utc)`` in production.

    Returns
    -------
    dict
        The payload written to disk (for stdout / test assertions).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    future = now + timedelta(hours=hours)
    payload = {
        "last_upload_iso": future.isoformat(),
        "jitter_applied_min": 0,
        "_schema": 1,
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def unregister_windows_tasks(ps1: Path = DEFAULT_PS1,
                             dry_run: bool = False) -> dict:
    """Invoke ``powershell.exe -File windows_tasks.ps1 -Unregister``.

    Gracefully degrades on non-Windows platforms — returns a structured
    ``{unregistered: False, reason: "non-Windows..."}`` dict instead of
    raising. Dry-run mode returns ``{would_unregister: [...]}`` without any
    subprocess invocation.

    Parameters
    ----------
    ps1
        Path to the PowerShell registration script. Must exist on disk;
        a missing file is reported but not raised — caller inspects dict.
    dry_run
        When True, return the would-unregister task list without invoking
        subprocess. Useful for auditing + pre-flight checks.

    Returns
    -------
    dict
        Structured summary of what happened. Keys always include
        ``platform`` + ``unregistered``. Additional keys vary by branch:
        ``dry_run`` / ``would_unregister`` for dry-run, ``returncode`` /
        ``stdout`` / ``stderr`` for real invocation, ``reason`` for skipped.
    """
    if sys.platform != "win32":
        return {
            "platform": sys.platform,
            "unregistered": False,
            "reason": "non-Windows platform — PowerShell task unregister skipped",
            "tasks": list(WINDOWS_TASKS),
        }
    if dry_run:
        return {
            "platform": sys.platform,
            "unregistered": False,
            "dry_run": True,
            "would_unregister": list(WINDOWS_TASKS),
        }
    if not ps1.exists():
        return {
            "platform": sys.platform,
            "unregistered": False,
            "reason": f"ps1 not found at {ps1}",
            "tasks": list(WINDOWS_TASKS),
        }
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(ps1),
            "-Unregister",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "platform": sys.platform,
        "unregistered": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-400:] if result.stdout else "",
        "stderr": result.stderr[-400:] if result.stderr else "",
        "tasks": list(WINDOWS_TASKS),
    }


def _resolve_lock_path(cli_value: Path | None) -> Path:
    """CLI flag > env var > DEFAULT_LOCK_PATH. Mirrors publish_lock.py _lock_path."""
    if cli_value is not None:
        return cli_value
    env = os.environ.get("SHORTS_PUBLISH_LOCK_PATH")
    if env:
        return Path(env)
    return DEFAULT_LOCK_PATH


def main(argv: list[str] | None = None) -> int:
    """CLI entry point — emit JSON summary to stdout, return 0 on success."""
    parser = argparse.ArgumentParser(
        prog="python -m scripts.rollback.stop_scheduler",
        description="Emergency scheduler shutdown — Phase 10 Plan 08 rollback CLI",
    )
    parser.add_argument(
        "--block-hours", type=int, default=49,
        help="Forward block window in hours (default 49, beats 48h+jitter floor)",
    )
    parser.add_argument(
        "--lock-path", type=Path, default=None,
        help="Override publish_lock.json path (CLI flag > env > default)",
    )
    parser.add_argument(
        "--ps1", type=Path, default=DEFAULT_PS1,
        help="Path to scripts/schedule/windows_tasks.ps1",
    )
    parser.add_argument(
        "--skip-publish-lock", action="store_true",
        help="Skip publish_lock.json write (only unregister tasks)",
    )
    parser.add_argument(
        "--skip-unregister", action="store_true",
        help="Skip PowerShell Unregister-ScheduledTask call",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Inspect only — no publish_lock write, no subprocess call",
    )
    args = parser.parse_args(argv)

    resolved_lock = _resolve_lock_path(args.lock_path)
    now_utc = datetime.now(timezone.utc)

    summary: dict = {
        "invocation_ts": now_utc.isoformat(),
        "dry_run": args.dry_run,
        "block_hours": args.block_hours,
    }

    # --- Publish lock step ---------------------------------------------------
    if args.skip_publish_lock:
        summary["publish_lock"] = {"skipped": True}
    elif args.dry_run:
        summary["publish_lock_would_write"] = {
            "lock_path": str(resolved_lock),
            "future_iso": (now_utc + timedelta(hours=args.block_hours)).isoformat(),
            "_schema": 1,
        }
    else:
        summary["publish_lock"] = block_publish(
            resolved_lock, args.block_hours, now_utc,
        )
        summary["publish_lock"]["lock_path"] = str(resolved_lock)

    # --- Unregister step -----------------------------------------------------
    if args.skip_unregister:
        summary["tasks_unregister"] = {"skipped": True}
    else:
        summary["tasks_unregister"] = unregister_windows_tasks(
            args.ps1, args.dry_run,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
