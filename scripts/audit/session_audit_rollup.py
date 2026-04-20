#!/usr/bin/env python3
"""Session audit 30-day rolling — AUDIT-01 / Phase 10 SC#3.

Usage:
    python -m scripts.audit.session_audit_rollup            # default: audit + append + rolling check
    python -m scripts.audit.session_audit_rollup --dry-run  # check rolling avg only (no jsonl mutation)
    python -m scripts.audit.session_audit_rollup --skip-audit  # rolling check only, no subprocess
    python -m scripts.audit.session_audit_rollup --threshold 75  # override default 80

Exit codes:
    0 = rolling avg ≥ threshold (healthy)
    1 = rolling avg < threshold (unhealthy) → F-AUDIT-NN appended to FAILURES.md + stderr warning
    2 = argparse error (uncaught exception)

Design:
    - Subprocess ``scripts.validate.harness_audit`` (NOT direct import) — decouples failure modes,
      preserves harness_audit testability, and lets this CLI remain independent of its internal API.
    - Append JSONL record to ``logs/session_audit.jsonl`` (gitignored; ``logs/.gitkeep`` tracked).
    - Rolling 30-day avg via ``zoneinfo.ZoneInfo("Asia/Seoul")`` — stdlib only (no 3rd-party tz libs).
    - avg < threshold → append ``## F-AUDIT-NN`` heading to ``FAILURES.md`` via direct ``open('a')``
      (bypasses Claude Write/Edit hook since subprocess file I/O is out of hook scope — the
      strict-prefix append-only invariant is still honoured because mode ``a`` cannot truncate).
    - 0 records in window (신규 스튜디오) → avg defaults to 100.0, exit 0 (pass). This prevents
      the first session from failing before any data accumulates.

D-2 Lock compliance:
    This CLI does NOT modify ``.claude/hooks/session_start.py``, ``.claude/skills/*/SKILL.md``,
    ``.claude/agents/*/SKILL.md``, or ``CLAUDE.md``. It runs as an external rollup; dispatch is
    via Plan 10-04 Scheduler (GH Actions cron / Windows Task) or manual invocation by 대표님.

Header-style note (Rule 1 auto-fix vs plan draft):
    Plan draft proposed ``### F-AUDIT-NN`` (level 3), but existing FAILURES.md uses
    ``## F-CTX-01`` / ``## F-D2-NN`` (level 2). This module uses level 2 for consistency
    with the established convention — also aligns ``append_failures()`` with the
    ``skill_patch_counter.append_failures()`` sibling pattern. See SUMMARY Deviations.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KST = ZoneInfo("Asia/Seoul")
DEFAULT_THRESHOLD = 80
DEFAULT_WINDOW_DAYS = 30
DEFAULT_JSONL = Path("logs/session_audit.jsonl")
DEFAULT_FAILURES = Path("FAILURES.md")


def run_harness_audit(studio_root: Path) -> dict:
    """Invoke ``scripts.validate.harness_audit`` via subprocess and return the parsed JSON.

    Uses ``--threshold 0`` so harness_audit returns exit 0 regardless of the audit score —
    this CLI performs its own rolling-window threshold check separately. Non-zero returncode
    therefore indicates a real subprocess failure (import error, crash, etc.) which must raise
    explicitly per project Rule 3 (no silent try/except fallback).

    The audit JSON is written by harness_audit to a temp file via ``--json-out``; we read
    and delete the temp file here to keep ``logs/`` pristine.
    """
    # NamedTemporaryFile with delete=False so we control cleanup explicitly (Windows).
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.validate.harness_audit",
                "--json-out", str(tmp_path),
                "--threshold", "0",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(studio_root),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"harness_audit subprocess failed rc={result.returncode}\n"
                f"stdout: {result.stdout[-500:]}\n"
                f"stderr: {result.stderr[-500:]}"
            )
        return json.loads(tmp_path.read_text(encoding="utf-8"))
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            # Best-effort cleanup; don't mask a real error with a cleanup exception.
            pass


def append_session_record(
    jsonl: Path, audit_json: dict, now: datetime
) -> dict:
    """Append a single-line JSON record to ``jsonl``. Returns the record dict.

    Record schema:
        {
            "timestamp": ISO-8601 KST with offset,
            "score": int (from audit_json, default 0),
            "violations_count": int (len of 'violations' list if present),
            "warnings_count": int (len of 'warnings' list if present),
        }

    ``ensure_ascii=False`` so Korean content round-trips unescaped.
    """
    record = {
        "timestamp": now.isoformat(),
        "score": int(audit_json.get("score", 0)),
        "violations_count": len(audit_json.get("violations", [])),
        "warnings_count": len(audit_json.get("warnings", [])),
    }
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def rolling_avg(
    jsonl: Path,
    days: int = DEFAULT_WINDOW_DAYS,
    now: datetime | None = None,
) -> tuple[float, int]:
    """Return ``(avg_score, sample_count)`` over the last ``days`` days of ``jsonl``.

    - If jsonl is absent / empty → ``(100.0, 0)`` (신규 스튜디오 pass).
    - Corrupt lines (malformed JSON) are skipped silently (no raise) — they don't imply
      a new failure mode; just a dropped datapoint.
    - Timestamps parsed via ``datetime.fromisoformat`` then ``astimezone(KST)`` so
      naive ISO strings or non-KST offsets still map to the same wall-clock window.
    """
    if now is None:
        now = datetime.now(KST)
    cutoff = now - timedelta(days=days)
    if not jsonl.exists():
        return (100.0, 0)

    scores: list[int] = []
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                # Corrupt line — skip but don't raise. Rolling math tolerates gaps.
                continue
            ts_raw = record.get("timestamp")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw)
            except ValueError:
                continue
            if ts.tzinfo is None:
                # Assume KST for naive timestamps (deterministic fallback).
                ts = ts.replace(tzinfo=KST)
            ts = ts.astimezone(KST)
            if ts >= cutoff:
                scores.append(int(record.get("score", 0)))

    if not scores:
        return (100.0, 0)
    return (sum(scores) / len(scores), len(scores))


def append_failures(
    failures: Path,
    avg: float,
    sample_count: int,
    threshold: int,
    now: datetime,
) -> str:
    """Append ``## F-AUDIT-NN`` entry to ``FAILURES.md``; return the new entry id.

    Level-2 heading (##) for consistency with existing F-CTX-NN / F-D2-NN entries.
    ``open('a')`` bypasses the Claude pre_tool_use Write/Edit hook — the strict-prefix
    invariant (``check_failures_append_only``) is preserved because mode ``a`` only
    appends bytes after the current EOF and cannot truncate.
    """
    if not failures.exists():
        raise FileNotFoundError(f"FAILURES.md not found at {failures}")

    existing = failures.read_text(encoding="utf-8")
    ids = re.findall(r"##\s+F-AUDIT-(\d{2})", existing)
    next_id = max((int(i) for i in ids), default=0) + 1
    entry_id = f"F-AUDIT-{next_id:02d}"

    body: list[str] = [
        "",
        "---",
        "",
        f"## {entry_id} — Session audit rolling avg 미달 "
        f"({now.date().isoformat()}, session_audit_rollup)",
        "",
        f"**증상**: 최근 {DEFAULT_WINDOW_DAYS}일 rolling 평균 점수 "
        f"{avg:.1f} < 임계값 {threshold}.",
        "",
        f"**Sample count**: {sample_count}",
        f"**Measurement timestamp**: {now.isoformat()}",
        "",
        "**조치**:",
        "1. `scripts/validate/harness_audit.py` 수동 실행 → 최신 violations/warnings 확인.",
        "2. SKILL 500줄 초과 / description 1024자 초과 / deprecated_patterns drift 등 "
        "원인 분류.",
        "3. D-2 Lock 기간 중이면 본 `FAILURES.md` 에 근본 원인 기록 + 해결 계획 append-only "
        "(SKILL patch 금지 유지).",
        "4. Lock 해제 후에는 해결 commit 에 본 엔트리 reference 필수.",
        "",
        "**연계**: Plan 10-02 drift_scan (A급 drift 병행 확인) + Plan 10-08 ROLLBACK.md 참조.",
        "",
    ]
    with failures.open("a", encoding="utf-8") as f:
        f.write("\n".join(body))
    return entry_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Session audit 30-day rolling — AUDIT-01 / Phase 10 SC#3",
    )
    parser.add_argument(
        "--studio-root", type=Path, default=Path("."),
        help="Studio repository root (default: cwd).",
    )
    parser.add_argument(
        "--jsonl", type=Path, default=DEFAULT_JSONL,
        help=f"Session audit jsonl path (default: {DEFAULT_JSONL}).",
    )
    parser.add_argument(
        "--failures", type=Path, default=DEFAULT_FAILURES,
        help=f"FAILURES.md path (default: {DEFAULT_FAILURES}).",
    )
    parser.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD,
        help=f"Rolling-avg pass threshold (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--window-days", type=int, default=DEFAULT_WINDOW_DAYS,
        help=f"Rolling window in days (default: {DEFAULT_WINDOW_DAYS}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute rolling avg without mutating jsonl or FAILURES.md.",
    )
    parser.add_argument(
        "--skip-audit", action="store_true",
        help="Skip the harness_audit subprocess (rolling check only).",
    )
    args = parser.parse_args(argv)

    studio_root = args.studio_root.resolve()
    now = datetime.now(KST)

    # Decide what record to build
    record: dict
    if args.skip_audit:
        record = {"timestamp": now.isoformat(), "skipped_audit": True}
    elif args.dry_run:
        # Dry-run still calls harness_audit (for observability) but does not append.
        audit_json = run_harness_audit(studio_root)
        record = {
            "timestamp": now.isoformat(),
            "score": int(audit_json.get("score", 0)),
            "violations_count": len(audit_json.get("violations", [])),
            "warnings_count": len(audit_json.get("warnings", [])),
            "dry_run_would_append_to": str(args.jsonl),
        }
    else:
        audit_json = run_harness_audit(studio_root)
        record = append_session_record(args.jsonl, audit_json, now)

    avg, count = rolling_avg(args.jsonl, args.window_days, now)
    summary = {
        "current_record": record,
        "rolling_avg": round(avg, 2),
        "sample_count": count,
        "threshold": args.threshold,
        "window_days": args.window_days,
        "passes": avg >= args.threshold,
        "dry_run": args.dry_run,
        "skip_audit": args.skip_audit,
    }

    # Fail path: append to FAILURES.md only on a real (non-dry-run) failure with ≥1 sample
    if avg < args.threshold and not args.dry_run and count > 0:
        entry_id = append_failures(
            args.failures, avg, count, args.threshold, now,
        )
        summary["failures_appended"] = entry_id
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(
            f"[FAIL] rolling avg {avg:.1f} < {args.threshold} — "
            f"FAILURES.md appended: {entry_id}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
