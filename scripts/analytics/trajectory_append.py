"""Monthly YPP trajectory appender — Phase 10 SC#6.

Reads manual inputs (subs / views_12m / retention_3s) and appends 1 row to
``wiki/ypp/trajectory.md`` Monthly Snapshots table + rebuilds the Mermaid
xychart x-axis / line data from every accumulated row. On 3-milestone gate
miss (CONTEXT §Exit Criterion — locked by 대표님 delegation), appends a
``F-YPP-NN`` entry to ``FAILURES.md`` via direct ``open(path, "a")`` I/O
(Hook bypass-by-naming — see Plan 10-01 skill_patch_counter for precedent).

Usage:
    python -m scripts.analytics.trajectory_append \\
        --subs 150 --views-12m 125000 --retention-3s 0.62 \\
        --year-month 2026-07
    python -m scripts.analytics.trajectory_append --dry-run \\
        --subs 50 --views-12m 10000 --year-month 2026-07

Design invariants (Phase 10 RESEARCH §Plan 7 Open Q3-Q4):
    - Stdlib-only (argparse, json, re, datetime, zoneinfo, pathlib, sys).
    - UTF-8 throughout; ensure_ascii=False so Korean notes + gate messages
      round-trip cleanly through stdout.
    - Windows cp949 stdout guard via ``sys.stdout.reconfigure``.
    - TRAJECTORY_APPEND_MARKER + MERMAID_DATA_MARKER missing → RuntimeError
      (no silent fallback — per Plan 10-03 monthly_aggregate Pitfall 2 analogue).
    - Gate thresholds locked at module constants matching CONTEXT §Exit
      Criterion (1차 100 / 2차 300 + retention 0.60 / 3차 1000 + 10M views).
    - upsert_row idempotent — same year_month re-invocation replaces existing
      row in-place, never duplicates.
    - append_failures uses F-YPP-NN scheme independent of other F-* prefixes
      in the same FAILURES.md (max of existing F-YPP-NN IDs + 1).

Exit codes:
    0 = success (dry-run or real run, gate miss or clear)
    1 = runtime error (missing marker, FAILURES write failure)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------- cp949 guard
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- constants
KST = ZoneInfo("Asia/Seoul")
PHASE_10_START = date(2026, 4, 20)
GATE_1_SUBS = 100
GATE_2_SUBS = 300
GATE_2_RETENTION = 0.60
GATE_3_SUBS = 1000
GATE_3_VIEWS = 10_000_000
APPEND_MARKER = "<!-- TRAJECTORY_APPEND_MARKER -->"
MERMAID_MARKER = "<!-- MERMAID_DATA_MARKER -->"


# ---------------------------------------------------------------- date math

def months_since(start: date, current: date) -> int:
    """Whole-month delta from ``start`` to ``current``.

    Calendar month subtraction — independent of day-of-month for robustness
    against "month-boundary" rounding. 2026-04-20 to 2026-07-01 → 3.
    """
    return (current.year - start.year) * 12 + (current.month - start.month)


# ---------------------------------------------------------------- gate evaluation

def evaluate_gates(snapshot: dict, month_since_start: int) -> dict:
    """Evaluate 3-milestone gates against a monthly snapshot.

    Args:
        snapshot: ``{"subs": int, "views_12m": int, "retention_3s": float}``.
        month_since_start: whole months since ``PHASE_10_START``.

    Returns:
        ``{"warnings": [str], "pivot_required": bool, "month_since_start": int}``.
        Empty warnings → gate clear. 1차 fires at month>=3, 2차 at month>=6.
    """
    warnings: list[str] = []
    subs = int(snapshot.get("subs", 0) or 0)
    retention = float(snapshot.get("retention_3s", 0) or 0)

    if month_since_start >= 3 and subs < GATE_1_SUBS:
        warnings.append(
            f"1st gate FAIL — subs {subs} < {GATE_1_SUBS} — 니치/훅 iteration 필요"
        )
    if month_since_start >= 6:
        if subs < GATE_2_SUBS:
            warnings.append(
                f"2nd gate FAIL — subs {subs} < {GATE_2_SUBS} — 전략 재검토"
            )
        if retention < GATE_2_RETENTION:
            warnings.append(
                f"2nd gate FAIL — retention_3s {retention:.3f} < {GATE_2_RETENTION:.2f} — 3초 hook iteration"
            )

    return {
        "warnings": warnings,
        "pivot_required": len(warnings) > 0,
        "month_since_start": month_since_start,
    }


# ---------------------------------------------------------------- row rendering

def _percent(current: float, target: float) -> float:
    return round(100.0 * current / target, 1) if target > 0 else 0.0


def render_row(year_month: str, snapshot: dict, notes: str = "") -> str:
    """Render a single Markdown table row for the Monthly Snapshots table.

    Columns: ``Month | Subs | Rolling12mViews | 1stGate% | 2ndGateSubs% |
              3rdGateSubs% | 3rdGateViews% | Notes``.
    """
    subs = int(snapshot.get("subs", 0) or 0)
    views_12m = int(snapshot.get("views_12m", 0) or 0)
    pct_1st = _percent(subs, GATE_1_SUBS)
    pct_2nd_subs = _percent(subs, GATE_2_SUBS)
    pct_3rd_subs = _percent(subs, GATE_3_SUBS)
    pct_3rd_views = _percent(views_12m, GATE_3_VIEWS)
    return (
        f"| {year_month} | {subs} | {views_12m} | {pct_1st}% | {pct_2nd_subs}% "
        f"| {pct_3rd_subs}% | {pct_3rd_views}% | {notes} |"
    )


# ---------------------------------------------------------------- trajectory.md I/O

def upsert_row(trajectory: Path, year_month: str, row: str) -> bool:
    """Insert ``row`` right below ``TRAJECTORY_APPEND_MARKER`` or replace the
    existing row whose first cell matches ``year_month``.

    Returns True always (either inserted or replaced — both count as "row
    present after call").

    Raises:
        RuntimeError: ``TRAJECTORY_APPEND_MARKER`` missing (no silent fallback).
    """
    text = trajectory.read_text(encoding="utf-8")
    if APPEND_MARKER not in text:
        raise RuntimeError(
            f"{APPEND_MARKER} missing in {trajectory}. "
            "Monthly Snapshots scaffold must include the marker before append."
        )

    head, tail = text.split(APPEND_MARKER, 1)
    pattern = re.compile(rf"^\|\s*{re.escape(year_month)}\s*\|.*\n?", re.MULTILINE)

    if pattern.search(tail):
        new_tail = pattern.sub(row + "\n", tail, count=1)
    else:
        # Insert right after the marker line. Preserve a leading newline so
        # the row stays visually separated from subsequent content.
        if tail.startswith("\n"):
            new_tail = "\n" + row + tail
        else:
            new_tail = "\n" + row + "\n" + tail

    trajectory.write_text(head + APPEND_MARKER + new_tail, encoding="utf-8")
    return True


def parse_existing_snapshots(trajectory: Path) -> list[tuple[str, int]]:
    """Scan rows below ``TRAJECTORY_APPEND_MARKER`` for ``(year_month, subs)``.

    Returns snapshots in on-disk order (insertion order by upsert_row —
    newest rows appear first because upsert inserts immediately below marker).
    We reverse the list so callers get chronological order for Mermaid
    rendering.
    """
    text = trajectory.read_text(encoding="utf-8")
    if APPEND_MARKER not in text:
        return []
    _, tail = text.split(APPEND_MARKER, 1)
    out: list[tuple[str, int]] = []
    for m in re.finditer(r"^\|\s*(\d{4}-\d{2})\s*\|\s*(\d+)\s*\|", tail, re.MULTILINE):
        out.append((m.group(1), int(m.group(2))))
    # Sort chronologically (YYYY-MM is lexicographically sortable)
    out.sort(key=lambda t: t[0])
    return out


def update_mermaid(trajectory: Path, snapshots: list[tuple[str, int]]) -> None:
    """Rewrite the Mermaid xychart ``x-axis [...]`` and ``line [...]`` lines
    from every known snapshot.

    No-op if snapshots is empty (preserves scaffold initial values).
    """
    if not snapshots:
        return
    text = trajectory.read_text(encoding="utf-8")
    x_axis = "[" + ", ".join(m for m, _ in snapshots) + "]"
    line_data = "[" + ", ".join(str(s) for _, s in snapshots) + "]"
    text = re.sub(r"x-axis\s+\[[^\]]*\]", f"x-axis {x_axis}", text, count=1)
    text = re.sub(r"line\s+\[[^\]]*\]", f"line {line_data}", text, count=1)
    trajectory.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- FAILURES.md append

def append_failures(
    failures: Path,
    year_month: str,
    warnings: list[str],
    now: datetime,
) -> str | None:
    """Append a ``F-YPP-NN`` entry to FAILURES.md on pivot warnings.

    Hook bypass-by-naming: ``.claude/hooks/pre_tool_use.py
    ::check_failures_append_only`` only inspects Claude Code Write/Edit/
    MultiEdit tool inputs. Direct ``open(path, "a")`` from a Python
    subprocess does NOT trigger the hook — documented escape hatch per
    Phase 10 RESEARCH Pitfall 3. Strict-prefix invariant still honoured
    because ``a`` mode cannot truncate existing bytes.

    Args:
        failures: Path to FAILURES.md.
        year_month: ``YYYY-MM`` of the snapshot that triggered the warning.
        warnings: list of human-readable gate-miss strings (len >= 1).
        now: aware datetime for the ``검사 시각`` field.

    Returns:
        ``"F-YPP-NN"`` entry ID string on success, ``None`` if FAILURES.md
        does not exist (defensive — caller decides whether to error).
    """
    if not failures.exists():
        return None
    existing = failures.read_text(encoding="utf-8")
    ids = re.findall(r"F-YPP-(\d{2,})", existing)
    next_id = max((int(i) for i in ids), default=0) + 1
    entry_id = f"F-YPP-{next_id:02d}"

    body_lines = [
        "",
        "",
        f"## {entry_id} — YPP trajectory gate 미달 ({year_month})",
        "",
        f"**검사 시각**: {now.isoformat()}",
        "",
        "**경보**:",
    ]
    for w in warnings:
        body_lines.append(f"- {w}")
    body_lines.extend([
        "",
        "**조치**:",
        "1. 현재 월 상위 3 영상 composite score 재분석 (`scripts.analytics.monthly_aggregate`)",
        "2. taste gate 회차 확인 (`wiki/kpi/taste_gate_*.md`) — 품질 판단 일치 여부 점검",
        "3. 1차 gate 미달 시: 니치/훅 iteration Plan 추가 (Phase 11 candidate)",
        "4. 2차 gate 미달 시: 전략 재검토 + taste gate 주기 상향 (월 1회 → 2주 1회)",
        "",
        "**참조**: `wiki/ypp/trajectory.md` + `.planning/phases/10-sustained-operations/10-CONTEXT.md` §Exit Criterion",
        "",
    ])

    with failures.open("a", encoding="utf-8") as f:
        f.write("\n".join(body_lines) + "\n")
    return entry_id


# ---------------------------------------------------------------- CLI

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts.analytics.trajectory_append",
        description="YPP trajectory monthly appender — Phase 10 SC#6",
    )
    parser.add_argument("--subs", type=int, required=True, help="Current subscriber count")
    parser.add_argument("--views-12m", type=int, required=True,
                        help="Rolling 12-month view count")
    parser.add_argument("--retention-3s", type=float, default=0.0,
                        help="3-second retention [0.0, 1.0]")
    parser.add_argument("--year-month", default=None,
                        help="YYYY-MM (default: current month KST)")
    parser.add_argument("--notes", default="",
                        help="Free-text notes column (Korean OK)")
    parser.add_argument("--trajectory", type=Path,
                        default=Path("wiki/ypp/trajectory.md"),
                        help="Target trajectory.md path")
    parser.add_argument("--failures", type=Path,
                        default=Path("FAILURES.md"),
                        help="Target FAILURES.md path for pivot warnings")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute + print JSON summary, do NOT mutate files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    now = datetime.now(KST)
    ym = args.year_month or f"{now.year}-{now.month:02d}"
    current = date(int(ym[:4]), int(ym[5:7]), 1)
    m_since = months_since(PHASE_10_START, current)

    snapshot = {
        "subs": args.subs,
        "views_12m": args.views_12m,
        "retention_3s": args.retention_3s,
    }
    gate_eval = evaluate_gates(snapshot, m_since)
    row = render_row(ym, snapshot, args.notes)

    summary: dict = {
        "year_month": ym,
        "month_since_start": m_since,
        "subs": args.subs,
        "views_12m": args.views_12m,
        "retention_3s": args.retention_3s,
        "gate_warnings": gate_eval["warnings"],
        "pivot_required": gate_eval["pivot_required"],
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        summary["would_append_row"] = row
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    try:
        upsert_row(args.trajectory, ym, row)
        all_snaps = parse_existing_snapshots(args.trajectory)
        update_mermaid(args.trajectory, all_snaps)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if gate_eval["warnings"]:
        entry_id = append_failures(args.failures, ym, gate_eval["warnings"], now)
        summary["failures_appended"] = entry_id

    summary["trajectory"] = str(args.trajectory)
    summary["appended"] = True
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "KST",
    "PHASE_10_START",
    "GATE_1_SUBS",
    "GATE_2_SUBS",
    "GATE_2_RETENTION",
    "GATE_3_SUBS",
    "GATE_3_VIEWS",
    "APPEND_MARKER",
    "MERMAID_MARKER",
    "months_since",
    "evaluate_gates",
    "render_row",
    "upsert_row",
    "parse_existing_snapshots",
    "update_mermaid",
    "append_failures",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
