"""YouTube Analytics v2 daily KPI fetch — Phase 10 Plan 10-03 (KPI-01).

Usage:
    python -m scripts.analytics.fetch_kpi --video-ids abc,def --output-dir data/kpi_daily/
    python -m scripts.analytics.fetch_kpi --dry-run --video-ids abc

Called by:
    .github/workflows/analytics-daily.yml (Plan 10-04 Scheduler) — GH secret 주입
    후 호출. Windows Task Scheduler 도 동일 entry-point.

Design invariants (RESEARCH.md §Plan 3 Open Q1-Q4 + Plan 3 GREEN pseudocode):
    - stdlib + googleapiclient only (pandas 금지, Open Q4 결정)
    - `youtubeAnalytics` v2 `reports().query()` endpoint (Open Q1)
    - `yt-analytics.readonly` scope required (Open Q2 — oauth.py 에서 Wave 0 이미 확장)
    - retention_3s 는 v1 에서 audienceWatchRatio proxy. 정확도 개선은 Phase 11 candidate
      (10-CONTEXT.md Deferred Ideas `audienceRetention timeseries 정확도 개선`)
    - 401 insufficient_scope → explicit raise (Pitfall 2, silent fallback 금지)
    - Windows cp949 guard via sys.stdout.reconfigure
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


# ------------------------------------------------------------------ cp949 guard
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


KST = ZoneInfo("Asia/Seoul")


# ------------------------------------------------------------------ core

def _build_analytics_client(credentials: Any) -> Any:
    """Build the googleapiclient youtubeAnalytics v2 service.

    Isolated in a helper so tests can monkeypatch this symbol without touching
    the googleapiclient import (Plan 3 Open Q1 canonical endpoint).

    Args:
        credentials: google.oauth2.credentials.Credentials with `yt-analytics.readonly`.

    Returns:
        googleapiclient.discovery.Resource (youtubeAnalytics v2).
    """
    from googleapiclient.discovery import build
    return build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials,
        cache_discovery=False,
    )


def _parse_response(response: dict) -> dict[str, float]:
    """Parse reports().query() response into normalized metric dict.

    Response shape (YouTube Analytics v2):
        {"columnHeaders": [{name, columnType, dataType}, ...],
         "rows": [[val, val, ...], ...]}

    Empty rows → zero-metric dict (caller decides if warn+continue or raise).

    NOTE: `retention_3s` is currently mapped to `audienceWatchRatio` as a proxy;
    true 3-second retention requires the `audienceRetention` timeseries
    (dimensions=elapsedVideoTimeRatio) and is deferred to Phase 11
    (10-CONTEXT.md Deferred Ideas).
    """
    rows = response.get("rows") or []
    if not rows:
        return {
            "views": 0.0,
            "avg_view_sec": 0.0,
            "completion_rate": 0.0,
            "retention_3s": 0.0,
        }
    headers = [h["name"] for h in response.get("columnHeaders", [])]
    row = rows[0]
    row_map = dict(zip(headers, row))
    return {
        "views": float(row_map.get("views", 0) or 0),
        "avg_view_sec": float(row_map.get("averageViewDuration", 0) or 0),
        "completion_rate": float(row_map.get("audienceWatchRatio", 0) or 0),
        "retention_3s": float(row_map.get("audienceWatchRatio", 0) or 0),
    }


def fetch_daily_metrics(
    credentials: Any,
    video_ids: list[str],
    start_date: str,
    end_date: str,
) -> dict[str, dict[str, float]]:
    """Fetch KPI metrics for each video_id. Returns {video_id: metric_dict}.

    Args:
        credentials: OAuth creds with `yt-analytics.readonly` scope.
        video_ids: list of YouTube video IDs (11-char each).
        start_date: YYYY-MM-DD inclusive.
        end_date: YYYY-MM-DD inclusive.

    Returns:
        {
            "abc": {"views": 1234, "avg_view_sec": 27, "completion_rate": 0.62,
                    "retention_3s": 0.62},
            ...
        }

    Raises:
        Exception: any HttpError / auth failure — silent fallback 금지 per
            Plan 3 Pitfall 2. Caller decides whether to catch + reauth.
    """
    client = _build_analytics_client(credentials)
    out: dict[str, dict[str, float]] = {}
    for vid in video_ids:
        response = client.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,averageViewDuration,audienceWatchRatio",
            dimensions="video",
            filters=f"video=={vid}",
        ).execute()
        out[vid] = _parse_response(response)
    return out


def write_csv(
    metrics_by_video: dict[str, dict[str, float]],
    output: Path,
    scan_date: date,
) -> None:
    """Write a header + N rows CSV to `output`.

    Header: video_id, scan_date, views, avg_view_sec, completion_rate, retention_3s
    Parent directory is created if missing. UTF-8, newline='' for Windows safety.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "video_id", "scan_date", "views", "avg_view_sec",
            "completion_rate", "retention_3s",
        ])
        for vid, m in metrics_by_video.items():
            writer.writerow([
                vid,
                scan_date.isoformat(),
                m.get("views", 0.0),
                m.get("avg_view_sec", 0.0),
                m.get("completion_rate", 0.0),
                m.get("retention_3s", 0.0),
            ])


# ------------------------------------------------------------------ oauth glue

def get_credentials():
    """Late-binding import so tests can monkeypatch `fetch_kpi.get_credentials`.

    Returns OAuth Credentials with all 3 SCOPES (upload + force-ssl +
    yt-analytics.readonly). Delegates to scripts.publisher.oauth.get_credentials
    verbatim — Plan 3 does NOT duplicate the OAuth flow.
    """
    from scripts.publisher.oauth import get_credentials as _get
    return _get()


# ------------------------------------------------------------------ CLI

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts.analytics.fetch_kpi",
        description="YouTube Analytics v2 daily KPI fetch (Phase 10 KPI-01)",
    )
    parser.add_argument(
        "--video-ids",
        required=False,
        default=None,
        help="Comma-separated YouTube video IDs (Plan 3: required; "
             "channel-wide auto-enum deferred to Plan 6)",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=1,
        help="Number of days back from today (KST) for the query window",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/kpi_daily"),
        help="Directory for kpi_YYYY-MM-DD.csv output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit plan JSON to stdout, perform no OAuth or file I/O",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns exit code (0 OK, 2 bad args)."""
    args = _parse_args(argv)

    now = datetime.now(KST)
    end = now.date()
    start = end - timedelta(days=max(args.days_back, 0))

    vids = [v.strip() for v in args.video_ids.split(",")] if args.video_ids else []
    vids = [v for v in vids if v]

    if not vids:
        print(
            "[ERROR] --video-ids required in Plan 10-03 "
            "(channel-wide auto-enumeration deferred to Plan 10-06). "
            "Example: --video-ids abc123,def456",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        preview = {
            "dry_run": True,
            "video_ids": vids,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "would_write": str(args.output_dir / f"kpi_{end.isoformat()}.csv"),
            "phase": "10-03",
            "scope_required": "https://www.googleapis.com/auth/yt-analytics.readonly",
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    # Real path: OAuth + googleapiclient call. Errors propagate (Pitfall 2).
    creds = get_credentials()
    try:
        metrics = fetch_daily_metrics(
            creds,
            vids,
            start.isoformat(),
            end.isoformat(),
        )
    except Exception as exc:  # pragma: no cover — network-path branch
        msg = str(exc)
        if "401" in msg or "insufficient_scope" in msg or "403" in msg:
            print(
                f"[ERROR] OAuth scope insufficient. "
                f"Run `python -c \"from scripts.publisher.oauth import get_credentials; "
                f"get_credentials()\"` to reauth with 3 scopes "
                f"(Plan 10-03 Pitfall 2). Underlying: {msg}",
                file=sys.stderr,
            )
        raise

    out_path = args.output_dir / f"kpi_{end.isoformat()}.csv"
    write_csv(metrics, out_path, end)
    summary = {
        "written": str(out_path),
        "videos": len(metrics),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


__all__ = [
    "fetch_daily_metrics",
    "write_csv",
    "get_credentials",
    "main",
    "_build_analytics_client",  # test monkeypatch target
    "_parse_response",
    "KST",
]


if __name__ == "__main__":
    sys.exit(main())
