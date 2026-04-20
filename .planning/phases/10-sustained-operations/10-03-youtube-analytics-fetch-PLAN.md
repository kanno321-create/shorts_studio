---
phase: 10-sustained-operations
plan: 03
type: execute
wave: 2
depends_on: [10-01-skill-patch-counter, 10-02-drift-scan-phase-lock]
files_modified:
  - scripts/analytics/__init__.py
  - scripts/analytics/fetch_kpi.py
  - scripts/analytics/monthly_aggregate.py
  - scripts/publisher/oauth.py
  - tests/phase10/test_fetch_kpi.py
  - tests/phase10/test_monthly_aggregate.py
  - wiki/shorts/kpi/kpi_log.md
autonomous: true
requirements: [KPI-01, KPI-02]
must_haves:
  truths:
    - "scripts/analytics/fetch_kpi.py 가 YouTube Analytics v2 `reports().query()` 호출로 channel videos 의 retention/CTR/avg_view_duration 을 수집한다"
    - "scripts/publisher/oauth.py SCOPES 에 `yt-analytics.readonly` 가 추가되며 Wave 0 smoke 에서 대표님 로컬 브라우저 1회 재인증 후 config/youtube_token.json 이 갱신된다"
    - "scripts/analytics/monthly_aggregate.py 가 일별 CSV 를 읽어 월별 composite score 기준 집계 후 wiki/shorts/kpi/kpi_log.md Part B 에 row 를 append 한다"
    - "두 스크립트 모두 --dry-run 지원 + Windows cp949 reconfigure 가드 + stdlib csv (pandas 금지)"
  artifacts:
    - path: scripts/analytics/fetch_kpi.py
      provides: "YouTube Analytics v2 daily KPI fetch CLI — KPI-01"
      min_lines: 150
    - path: scripts/analytics/monthly_aggregate.py
      provides: "Month-end aggregator — KPI-02, appends row to kpi_log.md Part B"
      min_lines: 120
    - path: scripts/publisher/oauth.py
      provides: "SCOPES list +1 entry: yt-analytics.readonly"
      contains: "yt-analytics.readonly"
    - path: tests/phase10/test_fetch_kpi.py
      provides: "KPI-01 unit — googleapiclient build() + reports.query() mocked"
      min_lines: 80
    - path: tests/phase10/test_monthly_aggregate.py
      provides: "KPI-02 unit — CSV parse + markdown append"
      min_lines: 80
    - path: wiki/shorts/kpi/kpi_log.md
      provides: "Part B 월별 table (Phase 9 scaffold — 이번에는 header 만 확장, 실 데이터는 scheduler 가 append)"
      contains: "Part B"
  key_links:
    - from: scripts/analytics/fetch_kpi.py
      to: scripts/publisher/oauth.py
      via: "from scripts.publisher.oauth import get_credentials"
      pattern: "from scripts\\.publisher\\.oauth import"
    - from: scripts/analytics/fetch_kpi.py
      to: googleapiclient
      via: "build('youtubeAnalytics', 'v2', credentials=creds).reports().query(...)"
      pattern: "youtubeAnalytics.*v2"
    - from: scripts/analytics/monthly_aggregate.py
      to: wiki/shorts/kpi/kpi_log.md
      via: "Path.read_text() → append row below Part B table marker → Path.write_text()"
      pattern: "kpi_log\\.md"
---

<objective>
YouTube Analytics API v2 일일 수집 cron (KPI-01) + 월 1회 `wiki/shorts/kpi/kpi_log.md` 자동 집계 (KPI-02) 를 구축한다. 기존 Phase 8 `scripts/publisher/oauth.py` 의 SCOPES 에 `yt-analytics.readonly` 1개를 추가하고, 대표님이 로컬 브라우저에서 `get_credentials()` 1회 호출로 재인증하여 `config/youtube_token.json` 을 재발급한다 (Wave 0 smoke). 월간 aggregate 은 stdlib csv + collections.defaultdict 로 일별 CSV 를 읽어 composite score 기준 row 를 kpi_log.md Part B 에 append 한다.

Purpose: D-2 Lock 기간 중 데이터 축적이 유일한 학습 경로. 수동 조회는 규율을 깬다. cron 만이 continuous pass 를 증명한다.
Output: fetch_kpi.py + monthly_aggregate.py + oauth.py scope 확장 + kpi_log.md Part B header.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/STATE.md
@.planning/phases/10-sustained-operations/10-CONTEXT.md
@.planning/phases/10-sustained-operations/10-RESEARCH.md
@.planning/phases/10-sustained-operations/10-VALIDATION.md
@scripts/publisher/oauth.py
@scripts/failures/aggregate_patterns.py
@wiki/shorts/kpi/kpi_log.md
@CLAUDE.md

<interfaces>
<!-- YouTube Analytics API v2 + Phase 8 oauth 재사용 계약 -->

From `scripts/publisher/oauth.py` (기존, Phase 8 PUB-03) — Plan 3 가 확장:
```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    # Plan 3 신규:
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
CLIENT_SECRET_PATH = Path("config/client_secret.json")
TOKEN_PATH = Path("config/youtube_token.json")

def get_credentials() -> google.oauth2.credentials.Credentials:
    """Returns auth'd Credentials. Loads from TOKEN_PATH, refreshes if expired,
    or runs InstalledAppFlow.run_local_server(port=0) for first-time auth."""
```

From RESEARCH.md §Plan 3 Open Q1 — YouTube Analytics v2 endpoint (공식 확정):
```python
from googleapiclient.discovery import build
yta = build("youtubeAnalytics", "v2", credentials=creds)
response = yta.reports().query(
    ids="channel==MINE",
    startDate="2026-04-01",
    endDate="2026-04-30",
    metrics="views,averageViewDuration,audienceWatchRatio",
    dimensions="video",
    filters=f"video=={video_id}",
).execute()
# response 구조: {"columnHeaders": [{name, columnType, dataType}, ...], "rows": [[val, ...], ...]}
```

From RESEARCH.md §Plan 3 Open Q4 — stdlib csv + defaultdict 집계:
```python
import csv
from collections import defaultdict
from pathlib import Path

def aggregate_month(daily_csv_dir: Path, year_month: str) -> dict[str, dict]:
    monthly = defaultdict(list)
    for daily in daily_csv_dir.glob(f"kpi_{year_month}-*.csv"):
        with daily.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                monthly[row["video_id"]].append({
                    "retention_3s": float(row["retention_3s"]),
                    "completion_rate": float(row["completion_rate"]),
                    "avg_view_sec": float(row["avg_view_sec"]),
                })
    return {vid: mean_metrics(samples) for vid, samples in monthly.items()}
```

From RESEARCH.md §Plan 6 Open Q2 — Composite score (Plan 6 와 공유 헬퍼, Plan 3 에서 정의하여 export):
```python
def composite_score(metrics: dict) -> float:
    return (
        0.5 * metrics["retention_3s"]       # 3초 hook
        + 0.3 * metrics["completion_rate"]  # 완주율
        + 0.2 * (metrics["avg_view_sec"] / 60)  # 정규화
    )
```

From `wiki/shorts/kpi/kpi_log.md` (Phase 9 스캐폴드 — Part A 목표 + Part B header):
```markdown
# KPI Log — naberal-shorts-studio

## Part A: Target Declaration
- 3초 retention: > 60%
- 완주율: > 40%
- 평균 시청: > 25초

## Part B: Monthly Tracking (Plan 3 이후 append)
| Month | Videos | Avg 3s Retention | Avg Completion | Avg View (s) | Top Composite | Notes |
|-------|--------|------------------|----------------|--------------|---------------|-------|
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Wave 0 smoke — oauth.py SCOPES 확장 + youtube_token.json 재발급 지침 + scripts/analytics/ 스캐폴드</name>
  <files>
    scripts/publisher/oauth.py,
    scripts/analytics/__init__.py,
    wiki/shorts/kpi/kpi_log.md
  </files>
  <read_first>
    - `scripts/publisher/oauth.py` 전체 (SCOPES 현재 2 entries, get_credentials() 구현)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 3 Open Q2 (Pitfall 2) — scope 변경 시 token 무효화 경고
    - `wiki/shorts/kpi/kpi_log.md` 현재 (Phase 9 Plan 02 scaffold)
    - `.planning/phases/10-sustained-operations/10-VALIDATION.md` §Manual-Only Verifications (OAuth 재인증 manual)
  </read_first>
  <action>
    1. `scripts/publisher/oauth.py` 수정 — SCOPES 리스트에 1 entry 추가 (정확히 이 위치, 기존 2 entries 는 byte-identical 유지):
       ```python
       SCOPES = [
           "https://www.googleapis.com/auth/youtube.upload",
           "https://www.googleapis.com/auth/youtube.force-ssl",
           "https://www.googleapis.com/auth/yt-analytics.readonly",   # Plan 10-03 신규 (KPI-01)
       ]
       ```
       - 기존 함수 시그니처 (`get_credentials()`, `refresh()`, `revoke()`) 건드리지 않음 (Phase 8 regression 보호)
    2. `scripts/analytics/__init__.py` 작성 (7-line 네임스페이스 — `scripts/audit/__init__.py` 스타일과 동일):
       ```python
       """scripts.analytics — YouTube Analytics v2 + 월간 집계. Phase 10 신규 (KPI-01/02)."""
       from __future__ import annotations
       __all__ = []
       ```
    3. `wiki/shorts/kpi/kpi_log.md` Part B 확장 — 기존 Phase 9 header 에 Plan 3 필드 추가 (기존 Part A 는 수정 금지):
       - 기존 Part B table header 에 `Top 3 Video IDs`, `Fetch Status`, `Data Source` 컬럼 추가
       - `<!-- PART_B_APPEND_MARKER --> ` HTML comment 추가 (monthly_aggregate.py 가 이 marker 직후에 row append)
       - Part A 는 **byte-identical 유지** (KPI-06 는 이미 Phase 9 에서 [x])
    4. Wave 0 smoke 실행 지침 (대표님 manual step):
       - 대표님 컴퓨터에서 `python scripts/publisher/oauth.py --reauth` 또는 `python -c "from scripts.publisher.oauth import get_credentials; get_credentials(); print('OK')"` 실행
       - 브라우저가 열리면 kanno3@naver.com 계정으로 로그인 + 3 scope 승인
       - 새 `config/youtube_token.json` 저장 확인 (size != 0, `grep -c "yt-analytics" config/youtube_token.json` ≥ 1 기대 — token 이 scope 명을 literal 로 포함하지는 않지만 `scope` 필드 JSON 확인)
       - Plan 4 Scheduler 에서 GH secret 으로 업로드 예정 — 본 task 는 로컬 token 갱신까지만
       - **실패 시 FAILURES.md append (F-KPI-01)** + Plan 3 중단
    5. Plan 3 에서는 단순 smoke: `python -c "from scripts.publisher.oauth import SCOPES; assert 'https://www.googleapis.com/auth/yt-analytics.readonly' in SCOPES; print(f'SCOPES count: {len(SCOPES)}')"` → `SCOPES count: 3` 출력
  </action>
  <acceptance_criteria>
    - `grep -c "yt-analytics.readonly" scripts/publisher/oauth.py` == 1
    - `python -c "from scripts.publisher.oauth import SCOPES; print(len(SCOPES))"` prints `3`
    - 기존 2 scope 가 byte-identical 유지: `grep -c "auth/youtube.upload" scripts/publisher/oauth.py` == 1 AND `grep -c "auth/youtube.force-ssl" scripts/publisher/oauth.py` == 1
    - `ls scripts/analytics/__init__.py` 존재
    - `grep -c "PART_B_APPEND_MARKER\\|Part B" wiki/shorts/kpi/kpi_log.md` ≥ 2
    - Phase 8 regression 보존: `pytest tests/phase08 -q --tb=no` exit 0
    - OAuth 재인증 manual step 기록: `.planning/phases/10-sustained-operations/10-CONTEXT.md` 의 Manual-Only Verifications 에 이미 있음 — 추가 문서화 불필요
  </acceptance_criteria>
  <verify>
    <automated>python -c "from scripts.publisher.oauth import SCOPES; assert len(SCOPES) == 3 and 'yt-analytics.readonly' in SCOPES[2]; print('OK')" && pytest tests/phase08 -q --tb=no</automated>
  </verify>
  <done>SCOPES 3 entries 완비, scripts/analytics/ 네임스페이스 준비, kpi_log.md Part B marker 삽입, Phase 8 regression 보존. 대표님 재인증 manual step 은 Plan 4 scheduler 실행 전까지 dispatch.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: fetch_kpi.py (일일 수집) + monthly_aggregate.py (월 1회 kpi_log.md append) 구현</name>
  <files>
    scripts/analytics/fetch_kpi.py,
    scripts/analytics/monthly_aggregate.py,
    tests/phase10/test_fetch_kpi.py,
    tests/phase10/test_monthly_aggregate.py
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 3 Open Q1-Q4 + §Code Examples `Plan 3 YouTube Analytics fetch` (line 1044-1067)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 6 Open Q2 (composite_score 공유 정의)
    - `scripts/publisher/oauth.py` (Task 1 수정본)
    - `scripts/failures/aggregate_patterns.py` (stdlib CLI pattern 재사용 — argparse + sys.stdout.reconfigure)
    - `wiki/shorts/kpi/kpi_log.md` (Task 1 PART_B_APPEND_MARKER 위치)
  </read_first>
  <behavior>
    - Test fetch-1 (test_fetch_parses_youtube_analytics_response): monkeypatched `build()` → `.reports().query().execute()` 가 `{"columnHeaders": [...], "rows": [[...]]}` 반환 → `fetch_daily_metrics()` 가 dict[video_id, metrics] 반환
    - Test fetch-2 (test_fetch_writes_csv_with_isoformat_timestamp): `--output-dir` 에 `kpi_YYYY-MM-DD.csv` 생성 (CSV header + N rows)
    - Test fetch-3 (test_fetch_dry_run_no_file_io): `--dry-run` 시 파일 미생성 + stdout JSON 만
    - Test fetch-4 (test_fetch_handles_empty_rows): response `{"rows": []}` → 빈 CSV (header only) + exit 0 + stderr WARN
    - Test fetch-5 (test_fetch_raises_on_401_insufficient_scope): `HttpError` 401 + "insufficient_scope" → explicit raise (Plan 3 Pitfall 2 — scope 재인증 요구)
    - Test fetch-6 (test_fetch_cli_video_ids_accepts_multiple): `--video-ids abc,def,ghi` argparse → 3 호출 (per-video filter)
    - Test agg-1 (test_monthly_aggregate_reads_daily_csvs): tmp dir 에 3 daily CSV 생성 → `aggregate_month()` → dict[video_id, mean_metrics] 반환
    - Test agg-2 (test_monthly_aggregate_composite_score_correct): sample metrics → composite_score = 0.5*retention + 0.3*completion + 0.2*(avg_view/60) 검증
    - Test agg-3 (test_monthly_aggregate_appends_kpi_log_row): tmp kpi_log.md 복사본 → aggregate 실행 → PART_B_APPEND_MARKER 직후에 새 row 삽입
    - Test agg-4 (test_monthly_aggregate_idempotent_month): 같은 month 재실행 → row 중복 추가 안함 (기존 row 있으면 skip 또는 replace, 구현 결정)
    - Test agg-5 (test_monthly_aggregate_dry_run): `--dry-run` → kpi_log.md 미수정 + stdout JSON
    - Test agg-6 (test_monthly_aggregate_handles_empty_daily_dir): daily CSV 0개 → exit 0 + `{"videos_aggregated": 0}` + FAILURES append (F-KPI-02) optional
  </behavior>
  <action>
    1. `scripts/analytics/fetch_kpi.py` 작성 (≥150 lines):
       ```python
       """YouTube Analytics v2 daily KPI fetch — KPI-01 / SC#2.

       Usage:
         python -m scripts.analytics.fetch_kpi --video-ids abc,def --output-dir data/kpi_daily/
         python -m scripts.analytics.fetch_kpi --dry-run

       Called by:
         .github/workflows/analytics-daily.yml (Plan 4) — GH secret 주입 후 호출.
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

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")

       def _build_analytics_client(credentials: Any) -> Any:
           from googleapiclient.discovery import build
           return build("youtubeAnalytics", "v2", credentials=credentials,
                        cache_discovery=False)

       def fetch_daily_metrics(
           credentials: Any, video_ids: list[str], start_date: str, end_date: str,
       ) -> dict[str, dict[str, float]]:
           """Fetch metrics for each video_id. Returns {video_id: {retention_3s, completion_rate, avg_view_sec}}."""
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

       def _parse_response(response: dict) -> dict[str, float]:
           rows = response.get("rows") or []
           if not rows:
               return {"retention_3s": 0.0, "completion_rate": 0.0, "avg_view_sec": 0.0, "views": 0.0}
           headers = [h["name"] for h in response.get("columnHeaders", [])]
           row = rows[0]
           row_map = dict(zip(headers, row))
           # audienceWatchRatio: watch time as fraction; retention_3s 추정 — 실 데이터는 audienceWatchRatio timeseries 필요
           return {
               "views": float(row_map.get("views", 0)),
               "avg_view_sec": float(row_map.get("averageViewDuration", 0)),
               "completion_rate": float(row_map.get("audienceWatchRatio", 0)),
               # retention_3s 는 별도 metric 없음. fetch_kpi v1 은 audienceWatchRatio 를 proxy 로 사용
               # NOTE: audienceWatchRatio 를 retention_3s proxy 로 사용. audienceRetention timeseries
               # 호출로 정확도 개선은 Phase 11 candidate. 현재 설계는 RESEARCH.md Plan 3 Open Q1 의
               # 공식 endpoint 에 충실. (10-CONTEXT.md Deferred Ideas 에 기록)
               "retention_3s": float(row_map.get("audienceWatchRatio", 0)),
           }

       def write_csv(metrics_by_video: dict[str, dict], output: Path, scan_date: date) -> None:
           output.parent.mkdir(parents=True, exist_ok=True)
           with output.open("w", encoding="utf-8", newline="") as f:
               w = csv.writer(f)
               w.writerow(["video_id", "scan_date", "views", "avg_view_sec",
                           "completion_rate", "retention_3s"])
               for vid, m in metrics_by_video.items():
                   w.writerow([vid, scan_date.isoformat(), m["views"], m["avg_view_sec"],
                               m["completion_rate"], m["retention_3s"]])

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="YouTube Analytics v2 daily KPI fetch")
           parser.add_argument("--video-ids", required=False,
                               help="Comma-separated YouTube video IDs (default: read from channel)")
           parser.add_argument("--days-back", type=int, default=1)
           parser.add_argument("--output-dir", type=Path, default=Path("data/kpi_daily"))
           parser.add_argument("--dry-run", action="store_true")
           args = parser.parse_args(argv)

           now = datetime.now(KST)
           end = now.date()
           start = end - timedelta(days=args.days_back)

           vids = args.video_ids.split(",") if args.video_ids else []
           if not vids:
               # TODO: Plan 6 에서 최근 N개 영상 ID 자동 조회 로직 추가. Plan 3 에서는 명시 요구.
               print("[ERROR] --video-ids required in Plan 3 (channel-wide auto-enumeration deferred to Plan 6)",
                     file=sys.stderr)
               return 2

           if args.dry_run:
               print(json.dumps({
                   "dry_run": True,
                   "video_ids": vids,
                   "start_date": start.isoformat(),
                   "end_date": end.isoformat(),
                   "would_write": str(args.output_dir / f"kpi_{end}.csv"),
               }, ensure_ascii=False, indent=2))
               return 0

           from scripts.publisher.oauth import get_credentials
           creds = get_credentials()
           try:
               metrics = fetch_daily_metrics(creds, vids, start.isoformat(), end.isoformat())
           except Exception as exc:
               msg = str(exc)
               if "401" in msg or "insufficient_scope" in msg:
                   print(f"[ERROR] OAuth scope insufficient — run `python scripts/publisher/oauth.py --reauth` (Plan 3 Pitfall 2): {msg}",
                         file=sys.stderr)
               raise   # Project Rule 3: silent fallback 금지

           out_path = args.output_dir / f"kpi_{end.isoformat()}.csv"
           write_csv(metrics, out_path, end)
           print(json.dumps({"written": str(out_path), "videos": len(metrics)}, ensure_ascii=False))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    2. `scripts/analytics/monthly_aggregate.py` 작성 (≥120 lines):
       ```python
       """Month-end aggregator — KPI-02 / SC#2.

       Reads data/kpi_daily/kpi_YYYY-MM-*.csv, computes per-video means + composite,
       appends 1 row to wiki/shorts/kpi/kpi_log.md Part B table.
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

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       PART_B_MARKER = "<!-- PART_B_APPEND_MARKER -->"

       def composite_score(metrics: dict) -> float:
           """Composite (shared with Plan 6 research_loop)."""
           return (
               0.5 * metrics.get("retention_3s", 0.0)
               + 0.3 * metrics.get("completion_rate", 0.0)
               + 0.2 * (metrics.get("avg_view_sec", 0.0) / 60.0)
           )

       def aggregate_month(daily_csv_dir: Path, year_month: str) -> dict[str, dict]:
           monthly: dict[str, list[dict]] = defaultdict(list)
           for daily in sorted(daily_csv_dir.glob(f"kpi_{year_month}-*.csv")):
               with daily.open(encoding="utf-8") as f:
                   for row in csv.DictReader(f):
                       monthly[row["video_id"]].append({
                           "retention_3s": float(row["retention_3s"]),
                           "completion_rate": float(row["completion_rate"]),
                           "avg_view_sec": float(row["avg_view_sec"]),
                           "views": float(row.get("views", 0)),
                       })
           out: dict[str, dict] = {}
           for vid, samples in monthly.items():
               n = len(samples)
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

       def append_kpi_log_row(
           kpi_log: Path, year_month: str, videos: dict[str, dict], top_n: int = 3
       ) -> bool:
           """Append 1 row to Part B. Returns True if appended, False if duplicate month exists."""
           text = kpi_log.read_text(encoding="utf-8")
           if PART_B_MARKER not in text:
               raise RuntimeError(f"PART_B_APPEND_MARKER missing in {kpi_log}")
           # Idempotent: skip if month already has a row below marker
           post_marker = text.split(PART_B_MARKER, 1)[1]
           if re.search(rf"^\|\s*{re.escape(year_month)}\s*\|", post_marker, re.MULTILINE):
               return False
           if not videos:
               new_row = f"| {year_month} | 0 | n/a | n/a | n/a | n/a | no data |"
           else:
               top = sorted(videos.items(), key=lambda kv: kv[1]["composite"], reverse=True)[:top_n]
               top_ids = ", ".join(vid for vid, _ in top)
               avg_ret = sum(v["retention_3s"] for v in videos.values()) / len(videos)
               avg_comp = sum(v["completion_rate"] for v in videos.values()) / len(videos)
               avg_view = sum(v["avg_view_sec"] for v in videos.values()) / len(videos)
               top_composite = top[0][1]["composite"] if top else 0.0
               new_row = (
                   f"| {year_month} | {len(videos)} | {avg_ret:.3f} | {avg_comp:.3f} "
                   f"| {avg_view:.1f} | {top_composite:.3f} | top: {top_ids} |"
               )
           # Insert after marker line
           new_text = text.replace(PART_B_MARKER, f"{PART_B_MARKER}\n{new_row}")
           kpi_log.write_text(new_text, encoding="utf-8")
           return True

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="Monthly KPI aggregate — KPI-02")
           parser.add_argument("--year-month", default=None,
                               help="YYYY-MM (default: previous month KST)")
           parser.add_argument("--daily-dir", type=Path, default=Path("data/kpi_daily"))
           parser.add_argument("--kpi-log", type=Path,
                               default=Path("wiki/shorts/kpi/kpi_log.md"))
           parser.add_argument("--dry-run", action="store_true")
           args = parser.parse_args(argv)

           if args.year_month is None:
               now = datetime.now(KST)
               ym = f"{now.year}-{now.month - 1 if now.month > 1 else 12:02d}"
               if now.month == 1:
                   ym = f"{now.year - 1}-12"
           else:
               ym = args.year_month

           videos = aggregate_month(args.daily_dir, ym)
           summary = {"year_month": ym, "videos_aggregated": len(videos),
                      "top_composite": max((v["composite"] for v in videos.values()), default=0.0)}

           if args.dry_run:
               summary["dry_run"] = True
               summary["videos_preview"] = {k: {kk: round(vv, 3) for kk, vv in v.items() if isinstance(vv, float)}
                                            for k, v in list(videos.items())[:3]}
               print(json.dumps(summary, ensure_ascii=False, indent=2))
               return 0

           appended = append_kpi_log_row(args.kpi_log, ym, videos)
           summary["appended"] = appended
           print(json.dumps(summary, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    3. `tests/phase10/test_fetch_kpi.py` 작성 (≥80 lines) — 6 tests 에 나열된 behavior 구현:
       - `monkeypatch` 로 `scripts.analytics.fetch_kpi._build_analytics_client` 를 MockClient 반환하게
       - MockClient.reports().query().execute() 가 fixture response 반환
       - `fetch_daily_metrics()` + CLI `main()` 두 레이어 테스트
    4. `tests/phase10/test_monthly_aggregate.py` 작성 (≥80 lines) — 6 tests agg-1 ~ agg-6:
       - tmp_path 에 synthetic daily CSV 3개 생성 → `aggregate_month()` 검증
       - tmp_path 에 Part A + Part B + marker 포함 kpi_log.md 복사본 → `append_kpi_log_row()` 검증
       - composite_score 공식 fixture 로 검증
    5. 실행: `pytest tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -xvs` — 12+ tests GREEN
    6. 수동 실증: `python -m scripts.analytics.fetch_kpi --dry-run --video-ids dummy123` — exit 0 + stdout `"dry_run": true` 확인
    7. 수동 실증: `python -m scripts.analytics.monthly_aggregate --dry-run --year-month 2026-04 --daily-dir /tmp/empty_does_not_exist` — exit 0 + `"videos_aggregated": 0`
  </action>
  <acceptance_criteria>
    - `pytest tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -q` 12+ tests GREEN
    - `python -m scripts.analytics.fetch_kpi --dry-run --video-ids test123` exit 0 + stdout JSON 에 `"dry_run": true` + `"video_ids": ["test123"]`
    - `python -m scripts.analytics.monthly_aggregate --dry-run --year-month 2026-04` exit 0 + stdout JSON 에 `"year_month": "2026-04"`
    - `grep -c "youtubeAnalytics.*v2" scripts/analytics/fetch_kpi.py` == 1
    - `grep -c "get_credentials" scripts/analytics/fetch_kpi.py` == 1
    - `grep -c "composite_score" scripts/analytics/monthly_aggregate.py` ≥ 2 (def + call)
    - `grep -c "PART_B_APPEND_MARKER\\|PART_B_MARKER" scripts/analytics/monthly_aggregate.py` ≥ 2
    - `grep -c "sys.stdout.reconfigure" scripts/analytics/fetch_kpi.py` == 1
    - `grep -c "sys.stdout.reconfigure" scripts/analytics/monthly_aggregate.py` == 1
    - `wc -l scripts/analytics/fetch_kpi.py` ≥ 150 lines
    - `wc -l scripts/analytics/monthly_aggregate.py` ≥ 120 lines
    - Phase 8 regression 보존: `pytest tests/phase08 -q --tb=no` exit 0
    - Phase 10 Plan 1/2 regression 보존: `pytest tests/phase10/test_skill_patch_counter.py tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -q` GREEN
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -q && python -m scripts.analytics.fetch_kpi --dry-run --video-ids demo123 && python -m scripts.analytics.monthly_aggregate --dry-run --year-month 2026-04</automated>
  </verify>
  <done>fetch_kpi.py + monthly_aggregate.py 완비, composite_score 공유 정의 export, Phase 10 Plan 1/2 + Phase 8 regression 보존, 12+ tests GREEN</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -v` 12+ tests PASS
- CLI `python -m scripts.analytics.fetch_kpi --dry-run --video-ids demo123` exit 0
- CLI `python -m scripts.analytics.monthly_aggregate --dry-run` exit 0
- `scripts/publisher/oauth.py` SCOPES == 3 entries (yt-analytics.readonly 추가)
- `wiki/shorts/kpi/kpi_log.md` `PART_B_APPEND_MARKER` 삽입 + Part A 무변경
- Phase 8 regression (scripts/publisher/* 건드렸으므로) `pytest tests/phase08 -q --tb=no` exit 0
- Phase 10 Plan 1/2 regression `pytest tests/phase10 -q --tb=no` exit 0
</verification>

<success_criteria>
1. `scripts/analytics/fetch_kpi.py` — 150+ lines, YouTube Analytics v2 `reports().query()` 호출, stdlib csv, --dry-run / --video-ids / --output-dir CLI
2. `scripts/analytics/monthly_aggregate.py` — 120+ lines, composite_score export (0.5r + 0.3c + 0.2v/60), kpi_log.md idempotent append
3. `scripts/publisher/oauth.py` SCOPES 3 entries (yt-analytics.readonly 추가, 기존 2 byte-identical)
4. `wiki/shorts/kpi/kpi_log.md` Part B 에 `PART_B_APPEND_MARKER` 삽입 (Plan 4 scheduler 가 monthly_aggregate 실행 시 이 marker 활용)
5. 12+ tests GREEN (fetch-1..6, agg-1..6)
6. Phase 8 regression 전수 보존 (Plan 3 의 oauth.py 수정이 유일한 shared file)
7. 대표님 OAuth 재인증 manual step 필요성 VALIDATION.md 에 명시 (Plan 4 scheduler 활성화 전 1회)
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-03-SUMMARY.md` with:
- Commits: (oauth scope 확장 + analytics 모듈 2종 + tests)
- Reusable assets used: scripts/publisher/oauth.py (scope 확장), stdlib csv/collections
- Deferred to Phase 11: audienceRetention timeseries 정확도 개선 (WARNING #3 — 현 v1 은 audienceWatchRatio proxy 사용, 10-CONTEXT.md Deferred Ideas 에 명시 기록)
- Next: Plan 4 (Scheduler) — analytics-daily.yml + skill-patch-count-monthly.yml + drift-scan-weekly.yml 가 scripts/analytics + scripts/audit 을 호출
- OAuth 재인증 manual step 대표님 dispatch 필요 (Plan 4 실행 전)
</output>
