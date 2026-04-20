"""Month-end KPI aggregator — Phase 10 Plan 10-03 (KPI-02).

Reads `data/kpi_daily/kpi_YYYY-MM-*.csv`, computes per-video mean metrics +
composite score, appends 1 row to `wiki/kpi/kpi_log.md` Part B.2 table
(directly after `<!-- PART_B_APPEND_MARKER -->`).

Usage:
    python -m scripts.analytics.monthly_aggregate --year-month 2026-04
    python -m scripts.analytics.monthly_aggregate --dry-run

Idempotent: if a row for the requested month already exists below the marker,
the second invocation is a no-op (returns `"appended": false` in JSON summary).

Design invariants (RESEARCH.md §Plan 3 Open Q4 + Plan 6 Open Q2):
    - stdlib only (csv + collections.defaultdict; no pandas)
    - composite = 0.5 * retention_3s + 0.3 * completion_rate + 0.2 * (avg_view_sec / 60)
    - `composite_score` exported for reuse by Plan 10-06 research_loop
    - Windows cp949 guard via sys.stdout.reconfigure
    - No silent fallback — missing MARKER raises RuntimeError (Pitfall 2 analogue)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ------------------------------------------------------------------ cp949 guard
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


KST = ZoneInfo("Asia/Seoul")
PART_B_MARKER = "<!-- PART_B_APPEND_MARKER -->"


# ------------------------------------------------------------------ core

def composite_score(metrics: dict) -> float:
    """Composite score — shared helper with Plan 10-06 research_loop.

    Weights (RESEARCH.md Plan 6 Open Q2):
        0.5 × retention_3s       (3-second hook)
        0.3 × completion_rate    (60-second Shorts completion)
        0.2 × (avg_view_sec / 60)  (normalized to 0..1 for 60-sec Shorts)

    Missing keys default to 0.0 — safe for partial metric dicts.

    Args:
        metrics: dict with any subset of {retention_3s, completion_rate, avg_view_sec}.

    Returns:
        float composite in [0, ~1.0]. Higher is better.
    """
    return (
        0.5 * float(metrics.get("retention_3s", 0.0) or 0.0)
        + 0.3 * float(metrics.get("completion_rate", 0.0) or 0.0)
        + 0.2 * (float(metrics.get("avg_view_sec", 0.0) or 0.0) / 60.0)
    )


def aggregate_month(
    daily_csv_dir: Path,
    year_month: str,
) -> dict[str, dict]:
    """Mean per-video metrics over all `kpi_YYYY-MM-*.csv` files in the dir.

    Args:
        daily_csv_dir: directory containing daily CSVs (may not exist).
        year_month: `YYYY-MM` string. Glob = `kpi_{year_month}-*.csv`.

    Returns:
        {video_id: {retention_3s, completion_rate, avg_view_sec, views,
                    sample_count, composite}}. Empty dict if no CSVs match.
    """
    monthly: dict[str, list[dict]] = defaultdict(list)
    if not daily_csv_dir.exists():
        return {}

    for daily in sorted(daily_csv_dir.glob(f"kpi_{year_month}-*.csv")):
        try:
            with daily.open(encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    vid = row.get("video_id", "").strip()
                    if not vid:
                        continue
                    monthly[vid].append({
                        "retention_3s": float(row.get("retention_3s", 0) or 0),
                        "completion_rate": float(row.get("completion_rate", 0) or 0),
                        "avg_view_sec": float(row.get("avg_view_sec", 0) or 0),
                        "views": float(row.get("views", 0) or 0),
                    })
        except OSError as exc:  # pragma: no cover — fs-path
            print(f"[WARN] skipped {daily}: {exc}", file=sys.stderr)
            continue

    out: dict[str, dict] = {}
    for vid, samples in monthly.items():
        n = len(samples)
        if n == 0:
            continue
        mean = {
            "retention_3s": sum(s["retention_3s"] for s in samples) / n,
            "completion_rate": sum(s["completion_rate"] for s in samples) / n,
            "avg_view_sec": sum(s["avg_view_sec"] for s in samples) / n,
            "views": sum(s["views"] for s in samples) / n,
            "sample_count": n,
        }
        mean["composite"] = composite_score(mean)
        out[vid] = mean
    return out


def _format_row(
    year_month: str,
    videos: dict[str, dict],
    top_n: int = 3,
) -> str:
    """Produce a single markdown table row for Part B.2.

    Columns: `Month | Videos | Avg 3s Retention | Avg Completion | Avg View (s) |
              Top Composite | Notes`
    """
    if not videos:
        return f"| {year_month} | 0 | n/a | n/a | n/a | n/a | no data |"

    top_sorted = sorted(
        videos.items(),
        key=lambda kv: kv[1].get("composite", 0.0),
        reverse=True,
    )[:top_n]
    top_ids = ", ".join(vid for vid, _ in top_sorted)
    avg_ret = sum(v.get("retention_3s", 0.0) for v in videos.values()) / len(videos)
    avg_comp = sum(v.get("completion_rate", 0.0) for v in videos.values()) / len(videos)
    avg_view = sum(v.get("avg_view_sec", 0.0) for v in videos.values()) / len(videos)
    top_composite = top_sorted[0][1].get("composite", 0.0) if top_sorted else 0.0

    return (
        f"| {year_month} | {len(videos)} | {avg_ret:.3f} | {avg_comp:.3f} "
        f"| {avg_view:.1f} | {top_composite:.3f} | top: {top_ids} |"
    )


def append_kpi_log_row(
    kpi_log: Path,
    year_month: str,
    videos: dict[str, dict],
    top_n: int = 3,
) -> bool:
    """Append 1 row to kpi_log.md Part B.2 immediately after PART_B_MARKER.

    Idempotent: if a row beginning with `| YYYY-MM |` already exists below the
    marker, this is a no-op and returns False.

    Args:
        kpi_log: Path to wiki/kpi/kpi_log.md (or tmp copy in tests).
        year_month: `YYYY-MM`.
        videos: output of aggregate_month(); may be empty (`no data` row).
        top_n: number of top-composite video_ids to list in Notes column.

    Returns:
        True if a new row was appended; False if this month was already present.

    Raises:
        RuntimeError: PART_B_APPEND_MARKER missing from kpi_log (no silent
            fallback per Pitfall 2 analogue).
    """
    text = kpi_log.read_text(encoding="utf-8")
    if PART_B_MARKER not in text:
        raise RuntimeError(
            f"PART_B_APPEND_MARKER missing in {kpi_log}. "
            f"Part B.2 scaffold must include `{PART_B_MARKER}` before aggregation."
        )

    post_marker = text.split(PART_B_MARKER, 1)[1]
    if re.search(
        rf"^\|\s*{re.escape(year_month)}\s*\|",
        post_marker,
        flags=re.MULTILINE,
    ):
        return False

    new_row = _format_row(year_month, videos, top_n=top_n)
    new_text = text.replace(PART_B_MARKER, f"{PART_B_MARKER}\n{new_row}", 1)
    kpi_log.write_text(new_text, encoding="utf-8")
    return True


# ------------------------------------------------------------------ CLI

def _previous_month_kst(now: datetime) -> str:
    """`YYYY-MM` of the month prior to `now` in KST."""
    if now.month == 1:
        return f"{now.year - 1}-12"
    return f"{now.year}-{now.month - 1:02d}"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts.analytics.monthly_aggregate",
        description="Monthly KPI aggregate + kpi_log.md append (Phase 10 KPI-02)",
    )
    parser.add_argument(
        "--year-month",
        default=None,
        help="YYYY-MM (default: previous month in KST)",
    )
    parser.add_argument(
        "--daily-dir",
        type=Path,
        default=Path("data/kpi_daily"),
        help="Directory with daily CSVs from fetch_kpi.py",
    )
    parser.add_argument(
        "--kpi-log",
        type=Path,
        default=Path("wiki/kpi/kpi_log.md"),
        help="Path to kpi_log.md (Part B.2 marker target)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute + print JSON summary, do NOT mutate kpi_log.md",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Number of top-composite video_ids to list in Notes column",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns exit code (0 OK)."""
    args = _parse_args(argv)

    ym = args.year_month or _previous_month_kst(datetime.now(KST))

    videos = aggregate_month(args.daily_dir, ym)
    top_composite = max(
        (v.get("composite", 0.0) for v in videos.values()),
        default=0.0,
    )
    summary: dict = {
        "year_month": ym,
        "videos_aggregated": len(videos),
        "top_composite": round(top_composite, 4),
        "daily_dir": str(args.daily_dir),
        "kpi_log": str(args.kpi_log),
    }

    if args.dry_run:
        summary["dry_run"] = True
        summary["videos_preview"] = {
            vid: {
                k: round(float(v), 4)
                for k, v in metrics.items()
                if isinstance(v, (int, float))
            }
            for vid, metrics in list(videos.items())[:5]
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    try:
        appended = append_kpi_log_row(args.kpi_log, ym, videos, top_n=args.top_n)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    summary["appended"] = appended
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "composite_score",
    "aggregate_month",
    "append_kpi_log_row",
    "main",
    "PART_B_MARKER",
    "KST",
]


if __name__ == "__main__":
    sys.exit(main())
