#!/usr/bin/env python3
"""failures_rotate.py — FAIL-PROTO-01 rotation CLI (Phase 12 Plan 05).

FAILURES.md 가 500줄 cap 초과 시 oldest entries 를 `.claude/failures/_archive/{YYYY-MM}.md`
로 이관. head 31줄 (schema + notice) 은 보존. idempotent (동일 상태 재실행 시 no-op).

CRITICAL: `_imported_from_shorts_naberal.md` 는 HARD-EXCLUDE (Phase 3 D-14 sha256-lock).
본 스크립트 는 `.claude/failures/FAILURES.md` 만 스캔 — glob 사용 금지.

Usage:
    py -3.11 scripts/audit/failures_rotate.py

Exit codes:
    0: no rotation needed (idempotent no-op) OR rotation succeeded
    1: error (file not found, permission, HARD-EXCLUDE violation, etc.)

D-A3-01 (500줄 cap) + D-A3-02 (archive month tag) + D-A3-03 (HARD-EXCLUDE imported) +
D-A3-04 (FAILURES_ROTATE_CTX=1 Hook whitelist bypass).
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Windows cp949 guard — mirror skill_patch_counter.py pattern
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

KST = ZoneInfo("Asia/Seoul")

REPO_ROOT = Path(__file__).resolve().parents[2]

# HARD-CODED paths — NO glob, NO wildcard (RESEARCH Pitfall 3 방지).
# Tests monkeypatch these three module-level names at test time.
FAILURES_FILE = REPO_ROOT / ".claude" / "failures" / "FAILURES.md"
ARCHIVE_DIR = REPO_ROOT / ".claude" / "failures" / "_archive"

# HARD-EXCLUDE basename — 절대 rotation 대상 아님 (D-14 sha256-lock, D-A3-03)
IMPORTED_FILE_BASENAME = "_imported_from_shorts_naberal.md"

CAP_LINES = 500
HEAD_PRESERVE_LINES = 31  # schema + notice (실측: FAILURES.md lines 1-31)


def _sha256(p: Path) -> str:
    """Stdlib sha256 helper for idempotency / D-14 invariant checks."""
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _assert_not_imported_file(path: Path) -> None:
    """D-A3-03 guard: refuse to rotate _imported_from_shorts_naberal.md (Phase 3 D-14 lock)."""
    if path.name == IMPORTED_FILE_BASENAME:
        raise RuntimeError(
            f"HARD-EXCLUDE violation: refuse to rotate {path.name} "
            f"(Phase 3 D-14 sha256-lock, D-A3-03 영구 면제)"
        )


def rotate() -> int:
    """Rotate FAILURES.md if over cap.

    Returns:
        1: rotated (oldest entries moved to _archive/{YYYY-MM}.md, head preserved)
        0: no-op (idempotent — file under cap, missing, or already rotated)

    Raises:
        RuntimeError: if FAILURES_FILE basename matches HARD-EXCLUDE list.
    """
    _assert_not_imported_file(FAILURES_FILE)

    if not FAILURES_FILE.exists():
        return 0  # nothing to rotate

    text = FAILURES_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) <= CAP_LINES:
        return 0  # idempotent — under cap, already rotated or never grew

    # Compute archive path (월 기준 KST)
    now = datetime.now(KST)
    month_tag = now.strftime("%Y-%m")
    archive_path = ARCHIVE_DIR / f"{month_tag}.md"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    # Oldest entries = line 32 ~ CAP_LINES (head 31 preserved, tail beyond CAP_LINES also preserved)
    # lines is 0-indexed; lines[0:31] = head (31 lines), lines[31:500] = archive body, lines[500:] = tail
    to_archive = lines[HEAD_PRESERVE_LINES:CAP_LINES]

    # Set env whitelist BEFORE write (Hook bypass via D-A3-04).
    # Direct Python I/O (open/write_text) does NOT route through pre_tool_use.py,
    # but we set the env var defensively in case a future refactor adds such routing
    # and for semantic clarity that this is the authorized rotation context.
    os.environ["FAILURES_ROTATE_CTX"] = "1"
    try:
        # 1. Archive append (oldest entries move)
        with archive_path.open("a", encoding="utf-8") as f:
            f.write(f"\n<!-- Rotated at {now.isoformat()} -->\n")
            f.write("\n".join(to_archive) + "\n")
        # 2. FAILURES.md rewrite: head (31) + tail (post-CAP_LINES)
        new_head = lines[:HEAD_PRESERVE_LINES]
        new_tail = lines[CAP_LINES:]
        new_content = "\n".join(new_head + new_tail) + "\n"
        FAILURES_FILE.write_text(new_content, encoding="utf-8")
    finally:
        # Always clean up env var (even on error) — prevents leak to sibling tests/agents
        os.environ.pop("FAILURES_ROTATE_CTX", None)

    return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exit 0 on success/no-op, 1 on error."""
    try:
        result = rotate()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if result == 1:
        now = datetime.now(KST)
        print(
            f"OK: rotated FAILURES.md "
            f"(oldest entries -> {ARCHIVE_DIR}/{now.strftime('%Y-%m')}.md, "
            f"head {HEAD_PRESERVE_LINES} lines preserved)"
        )
    else:
        print(f"OK: no rotation needed (FAILURES.md under {CAP_LINES} lines or missing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
