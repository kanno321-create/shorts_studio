---
phase: 9
plan: 09-02
subsystem: wiki-kpi
tags: [kpi, kpi-06, sc-2, hybrid-format, youtube-analytics-v2]
requires: [09-00]
provides: [kpi-target-declaration, part-a-hybrid, part-b-monthly-tracking, youtube-analytics-v2-contract]
affects: [wiki/kpi/kpi_log.md, wiki/kpi/MOC.md]
tech-stack:
  added: []
  patterns: [hybrid-format-d06, youtube-analytics-v2-d07, moc-checkbox-flip]
key-files:
  created:
    - wiki/kpi/kpi_log.md
  modified:
    - wiki/kpi/MOC.md
decisions:
  - Hybrid format chosen (Part A Target + Part B Monthly) to satisfy SC#2 "목표 선언 + 측정 방식 명시" in single doc
  - YouTube Analytics API v2 (audienceWatchRatio + averageViewDuration) declared as template-only; real OAuth wiring deferred to Phase 10 fetch_kpi.py
  - 탐정/조수 persona (abc123..pqr678) dry-run rows used; placeholder "테스트용 쇼츠" explicitly avoided per D-10
metrics:
  duration: 00:02
  tasks: 2
  files_created: 1
  files_modified: 1
  commits: 2
  tests_passing: 5
  completed: 2026-04-20
---

# Phase 9 Plan 09-02: KPI Log Hybrid Format Summary

**One-liner:** KPI-06 3종 목표(3초 retention >60% / 완주율 >40% / 평균 시청 >25초)를 Hybrid 포맷으로 선언하고 YouTube Analytics v2 API contract를 명문화.

## Objective

SC#2 ("KPI 목표가 선언되고 측정 방식이 명시") + KPI-06 (3 target values + measurement) 동시 충족.
Phase 9는 **declarative only** — 실 API 연동은 Phase 10.

## Files Created

### `wiki/kpi/kpi_log.md` (77 lines)

**Part A: Target Declaration (KPI-06)**

| 지표 | 목표 | 임계 | 측정 | 주기 |
|------|------|-----|------|------|
| 3초 retention | > 60% | < 50% | `audienceWatchRatio[3]` | 주 1회 일요일 09:00 KST |
| 완주율 | > 40% | < 30% | `audienceWatchRatio[59]` | 주 1회 일요일 09:00 KST |
| 평균 시청 시간 | > 25초 | < 18초 | `averageViewDuration` | 주 1회 일요일 09:00 KST |

**API Contract (D-07) — literal strings present:**
- Endpoint `https://youtubeanalytics.googleapis.com/v2/reports`
- OAuth scope `https://www.googleapis.com/auth/yt-analytics.readonly`
- Metrics `audienceWatchRatio` + `averageViewDuration`
- Dimension `elapsedVideoTimeRatio`
- Shorts filter `uploaderType==SELF` + `trafficSourceType=SHORTS`
- Quota ~1 unit/report (separate from Data API v3 10k units/day)

**실패 정의:**
- 2+ 지표 FAIL → Part B 하위 3 자동 배치 → 다음 월 Taste Gate
- 단일 지표 FAIL 단발성 → 주의만, FAILURES 승격 없음 (D-13)

**Part B: Monthly Tracking**
- Schema columns: `video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes`
- 2026-04 placeholder row (Phase 10 Month 1 수집 대상)
- Dry-run 6 synthetic rows (탐정/조수 페르소나: abc123, def456, ghi789, jkl012, mno345, pqr678) per D-10

## Files Modified

### `wiki/kpi/MOC.md` (surgical edit: frontmatter + 1 line)

- Frontmatter `status: scaffold` → `status: partial` (2/5 ready: retention_3second_hook + kpi_log)
- Frontmatter `updated: 2026-04-19` → `updated: 2026-04-20`
- Replaced placeholder `- [ ] \`kpi_log_template.md\` — 월 1회 kpi_log.md 자동 생성 포맷 (KPI-02)` with `- [x] [[kpi_log]] — Hybrid format: Part A (KPI-06 targets) + Part B (Monthly Tracking) (Phase 9 ready)`
- 3 other unchecked placeholders preserved (future Phase 10 candidates)
- `retention_3second_hook.md` checked line preserved

## Acceptance Results

**test_kpi_log_schema.py: 5/5 PASS**

- `test_kpi_log_exists` PASS
- `test_target_declaration` PASS (60% / 40% / 25초 literals found)
- `test_api_contract_present` PASS (endpoint + scope + 2 metrics found)
- `test_hybrid_structure` PASS (Part A + Part B + 6 column headers)
- `test_failure_thresholds_declared` PASS (50% re-creation threshold present)

**Phase 9 collection:** 17 tests collected, 0 errors
**Phase 4-7 regression:** 986 tests collected, 0 errors (baseline preserved)
**Phase 8 collection:** 6 pre-existing ModuleNotFoundError (mocks.youtube_mock) — NOT caused by this plan (see Scope Boundary below)

## Deviations from Plan

None — plan executed exactly as written.

## Scope Boundary Notes

- Phase 8 collection shows 6 pre-existing errors (`ModuleNotFoundError: No module named 'mocks.youtube_mock'`) originating from Phase 8 Plan 08-01 scaffolding commits (5fb2d38, 501777d, b53d218). This plan only touches `wiki/kpi/` — zero production code impact. Logged here per SCOPE_BOUNDARY rule; not in scope for Plan 09-02 to fix.

## Commits

| Hash | Message |
|------|---------|
| `a20ffae` | feat(09-02): add wiki/kpi/kpi_log.md Hybrid format (KPI-06) |
| `816318d` | docs(09-02): flip MOC.md kpi_log checkbox + frontmatter partial |

## Self-Check: PASSED

**Files verified:**
- FOUND: wiki/kpi/kpi_log.md (77 lines)
- FOUND: wiki/kpi/MOC.md (modified, 3 insertions / 3 deletions)

**Commits verified:**
- FOUND: a20ffae (Task 9-02-01 kpi_log.md)
- FOUND: 816318d (Task 9-02-02 MOC.md flip)

**Tests verified:**
- 5/5 test_kpi_log_schema.py PASS (0.06s)

---

*Created: 2026-04-20 (Phase 9 Plan 09-02 execution — Wave 1 PARALLEL)*
