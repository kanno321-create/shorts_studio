---
category: kpi
status: ready
tags: [kpi, monthly-tracking, retention, completion, avg-watch]
updated: 2026-04-20
---

# KPI Log — 월별 추적 + 목표 선언

> 지표 목표 선언(Part A)과 월간 실적 추적(Part B)을 하나의 문서로 통합.
> Phase 10 `scripts/analytics/fetch_kpi.py`가 Part B를 주 1회 (매주 일요일 09:00 KST) 갱신 예정.

## Part A: Target Declaration (KPI-06)

KPI-06 3종 목표 — 3초 retention / 완주율 / 평균 시청 시간. ROADMAP §219-229 SC#2 "KPI 목표가 선언되고 측정 방식이 명시" 충족 기준.

| 지표 | 목표 | 임계 (재제작 trigger) | 측정 방식 | 측정 주기 |
|------|------|----------------------|-----------|-----------|
| 3초 retention | **> 60%** | < 50% | YouTube Analytics v2 `audienceWatchRatio[3]` | 업로드 7일 후 + 매주 일요일 09:00 KST |
| 완주율 (Completion Rate) | **> 40%** | < 30% | `audienceWatchRatio[59]` (60초 Shorts 기준) | 업로드 7일 후 + 매주 일요일 09:00 KST |
| 평균 시청 시간 | **> 25초** | < 18초 | `averageViewDuration` (초 단위) | 업로드 7일 후 + 매주 일요일 09:00 KST |

### API Contract (Phase 10 실연동 대상)

Phase 9는 API endpoint + 필드명 + 스코프 + 주기만 선언. 실 OAuth 연동·cron 등록은 Phase 10 `scripts/analytics/fetch_kpi.py`.

- **Endpoint:** `GET https://youtubeanalytics.googleapis.com/v2/reports`
- **OAuth scope:** `https://www.googleapis.com/auth/yt-analytics.readonly`
- **Required params:**
  - `ids=channel==MINE`
  - `startDate` / `endDate` (YYYY-MM-DD)
  - `metrics=audienceWatchRatio,averageViewDuration`
  - `dimensions=elapsedVideoTimeRatio` (3초 시점 retention 추출용)
  - `filters=video==<videoId>`
- **Quota:** Analytics API 약 1 unit / report (Data API v3의 10,000 units/day와 별도 쿼터)
- **Shorts filter:** `filters=video==<id>;uploaderType==SELF`. Shorts shelf 트래픽은 `trafficSourceType=SHORTS`로 별도 집계.
- **Update cadence:** 매주 일요일 09:00 KST (Phase 10 cron 등록 대상)

### 실패 정의

- 3종 지표 중 **2개 이상 FAIL** → 해당 에피소드 Part B 하위 3 자동 배치 → 다음 월 Taste Gate 검토 대상.
- 단일 지표 < 임계 + 단발성 → `kpi_log.md` 주의 표시만, `FAILURES.md` 승격 없음.
- 재제작 여부 판정 근거는 `taste_gate_YYYY-MM.md` 대표님 평가와 교차 참조. 자동 재제작 금지 (D-13).

## Part B: Monthly Tracking

### 2026-04 (첫 실 데이터는 Phase 10)

실제 월별 수집은 Phase 10 Month 1부터. Phase 9는 스키마와 포맷만 확정.

| video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes |
|----------|-------|-------------|---------------:|----------------:|-------------:|:---------------:|-------|
| _ | _ | _ | _ | _ | _ | _ | Phase 10 Month 1 수집 대상 |

### Dry-run 2026-04 (synthetic sample — D-10 참조)

> 실 데이터 도입 전 대표님 Taste Gate UX 검증용 placeholder. 탐정/조수 페르소나(CONTENT-02) 기반. [[taste_gate_2026-04]] 참조.

| video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes |
|----------|-------|-------------|---------------:|----------------:|-------------:|:---------------:|-------|
| abc123 | "탐정이 조수에게 묻다: 23살 범인의 진짜 동기?" | 2026-04-05 | 68% | 42% | 27 | 1 (상위) | synthetic — Phase 9 dry-run |
| def456 | "100억 갑부가 딱 한 번 울었던 순간" | 2026-04-08 | 64% | 41% | 26 | 2 (상위) | synthetic |
| ghi789 | "3번째 편지의 의미를 아시나요?" | 2026-04-11 | 61% | 40% | 25 | 3 (상위) | synthetic |
| jkl012 | "조수가 놓친 단서" | 2026-04-14 | 48% | 28% | 19 | 4 (하위) | synthetic — hook 약함 |
| mno345 | "5번 방문한 이유" | 2026-04-17 | 45% | 25% | 17 | 5 (하위) | synthetic — 지루함 |
| pqr678 | "범인의 마지막 말" | 2026-04-20 | 42% | 24% | 16 | 6 (하위) | synthetic — 결말 처참 |

### Part B.2: Month-level Aggregate (Plan 10-03 monthly_aggregate.py append 대상)

Phase 10 `scripts/analytics/monthly_aggregate.py` 가 월말에 `data/kpi_daily/kpi_YYYY-MM-*.csv` 를 읽어 composite score (`0.5 * retention_3s + 0.3 * completion_rate + 0.2 * (avg_view_sec / 60)`) 기준으로 아래 marker 직후 1 row append. Idempotent — 동일 month 재실행 시 중복 추가 안함.

| Month | Videos | Avg 3s Retention | Avg Completion | Avg View (s) | Top Composite | Notes |
|-------|--------|------------------|----------------|--------------|---------------|-------|
<!-- PART_B_APPEND_MARKER -->

## Related

- [[retention_3second_hook]] — 3초 hook 측정 기반 이론 (KPI-06 목표 근거)
- [[taste_gate_protocol]] — 월 1회 대표님 평가 회로 (KPI-05)
- [[MOC]] — KPI 카테고리 노드 맵

---

*Created: 2026-04-20 (Phase 9 Plan 09-02)*
*Extended: 2026-04-20 (Phase 10 Plan 10-03 — Part B.2 aggregate section + PART_B_APPEND_MARKER)*
*Next update: Phase 10 Month 1 (첫 실 데이터 수집, Sunday KST cron trigger)*
