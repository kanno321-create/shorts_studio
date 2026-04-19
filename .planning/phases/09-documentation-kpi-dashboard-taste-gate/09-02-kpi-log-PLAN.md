---
plan: 09-02
phase: 9
wave: 1
depends_on: [09-00]
files_modified:
  - wiki/kpi/kpi_log.md
  - wiki/kpi/MOC.md
files_read_first:
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
  - tests/phase09/test_kpi_log_schema.py
  - wiki/kpi/MOC.md
  - wiki/kpi/retention_3second_hook.md
  - .planning/REQUIREMENTS.md
autonomous: true
requirements: [KPI-06]
tasks_addressed: [9-02-01, 9-02-02]
success_criteria: [SC#2]
estimated_commits: 2
parallel_boundary: parallel with 09-01 and 09-03 (disjoint files — docs/ARCHITECTURE.md vs wiki/kpi/kpi_log.md vs wiki/kpi/taste_gate_*.md)

must_haves:
  truths:
    - "wiki/kpi/kpi_log.md exists with frontmatter (category/status/tags/updated)"
    - "Part A Target Declaration section present with 3 KPI target rows (3초 retention > 60% / 완주율 > 40% / 평균 시청 > 25초)"
    - "API Contract sub-section declares YouTube Analytics v2 endpoint + OAuth scope + metric names"
    - "Part B Monthly Tracking section present with column headers video_id / title / 3sec_retention / completion_rate / avg_view_sec / taste_gate_rank"
    - "wiki/kpi/MOC.md checkbox for kpi_log_template.md flipped to kpi_log.md with [x]"
    - "pytest tests/phase09/test_kpi_log_schema.py exits 0"
  artifacts:
    - path: "wiki/kpi/kpi_log.md"
      provides: "Hybrid format KPI declaration — Part A (KPI-06 targets) + Part B (Monthly Tracking template + dry-run row)"
      min_lines: 80
      contains: "audienceWatchRatio"
    - path: "wiki/kpi/MOC.md"
      provides: "MOC checkbox update — kpi_log_template.md → kpi_log.md [x]"
  key_links:
    - from: "wiki/kpi/kpi_log.md"
      to: "tests/phase09/test_kpi_log_schema.py"
      via: "Test asserts API contract literals (youtubeanalytics.googleapis.com/v2/reports, yt-analytics.readonly, audienceWatchRatio, averageViewDuration) + Part A/B headers + column names"
      pattern: "audienceWatchRatio|averageViewDuration|yt-analytics.readonly|Part A|Part B"
    - from: "wiki/kpi/MOC.md"
      to: "wiki/kpi/kpi_log.md"
      via: "Checkbox flip + markdown link"
      pattern: "\\[x\\].*kpi_log\\.md"
    - from: "wiki/kpi/kpi_log.md"
      to: "wiki/kpi/retention_3second_hook.md"
      via: "Reference link — measurement basis for 3-sec retention"
      pattern: "retention_3second_hook"
---

<objective>
Write `wiki/kpi/kpi_log.md` in Hybrid format (D-06): Part A Target Declaration locking KPI-06 three targets (3초 retention > 60% / 완주율 > 40% / 평균 시청 > 25초) with measurement method per D-07 (YouTube Analytics API v2 `audienceWatchRatio` + `averageViewDuration`, OAuth scope `yt-analytics.readonly`, weekly Sunday KST cadence). Part B Monthly Tracking template with column headers `video_id / title / 3sec_retention / completion_rate / avg_view_sec / taste_gate_rank`. Flip `wiki/kpi/MOC.md` checkbox from `kpi_log_template.md` placeholder to `kpi_log.md` [x].

Purpose: Target SC#2 — "KPI 목표가 선언되고 측정 방식이 명시" — and KPI-06 (3 target values + measurement). Phase 9 declares the API contract without wiring (wiring lives in Phase 10 `scripts/analytics/fetch_kpi.py`).

Output: wiki/kpi/kpi_log.md (~80-150 lines) + wiki/kpi/MOC.md edited with checkbox flip + updated timestamp. test_kpi_log_schema.py green.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
@tests/phase09/test_kpi_log_schema.py
@wiki/kpi/MOC.md
@wiki/kpi/retention_3second_hook.md
@.planning/REQUIREMENTS.md

<interfaces>
## Target kpi_log.md Hybrid structure (verbatim from 09-RESEARCH.md §Pattern 6)

```markdown
---
category: kpi
status: ready
tags: [kpi, monthly-tracking, retention, completion, avg-watch]
updated: 2026-04-20
---

# KPI Log — 월별 추적 + 목표 선언

> 지표 목표 선언(Part A)과 월간 실적 추적(Part B)을 하나의 문서로 통합.
> Phase 10 `scripts/analytics/fetch_kpi.py`가 Part B를 주 1회 갱신 예정.

## Part A: Target Declaration (KPI-06)

| 지표 | 목표 | 임계 (재제작 trigger) | 측정 방식 | 측정 주기 |
|------|------|----------------------|-----------|-----------|
| 3초 retention | **> 60%** | < 50% | YouTube Analytics v2 `audienceWatchRatio[3]` | 업로드 7일 후 + 주 1회 일요일 KST |
| 완주율 (Completion Rate) | **> 40%** | < 30% | `audienceWatchRatio[59]` (60초 Shorts 기준) | 업로드 7일 후 + 주 1회 일요일 KST |
| 평균 시청 시간 | **> 25초** | < 18초 | `averageViewDuration` (초 단위) | 업로드 7일 후 + 주 1회 일요일 KST |

### API Contract (Phase 10 실연동 대상)

- **Endpoint:** `GET https://youtubeanalytics.googleapis.com/v2/reports`
- **OAuth scope:** `https://www.googleapis.com/auth/yt-analytics.readonly`
- **Required params:**
  - `ids=channel==MINE`
  - `startDate` / `endDate` (YYYY-MM-DD)
  - `metrics=audienceWatchRatio,averageViewDuration`
  - `dimensions=elapsedVideoTimeRatio` (for 3-sec point)
  - `filters=video==<videoId>`
- **Quota:** ~1 unit per report (Analytics API separate quota from Data API v3's 10,000 units/day)
- **Shorts filter:** `filters=video==<id>;uploaderType==SELF` (Shorts shelf 트래픽은 `trafficSourceType=SHORTS`로 별도 집계)

### 실패 정의

- 3종 지표 중 **2개 이상 FAIL** → 해당 에피소드 Part B 하위 3 자동 배치 → 다음 월 Taste Gate 검토 대상
- 단일 지표 < 임계 + 단발성 → kpi_log.md 주의 표시만, FAILURES.md 승격 없음

## Part B: Monthly Tracking

### 2026-04 (첫 실 데이터는 Phase 10)

| video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes |
|----------|-------|-------------|---------------:|----------------:|-------------:|:---------------:|-------|
| _ | _ | _ | _ | _ | _ | _ | Phase 10 Month 1 수집 대상 |

### Dry-run 2026-04 (synthetic sample — D-10 참조)

> 실 데이터 도입 전 대표님 Taste Gate UX 검증용 placeholder. [[taste_gate_2026-04]] 참조.

| video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes |
|----------|-------|-------------|---------------:|----------------:|-------------:|:---------------:|-------|
| abc123 | "탐정이 조수에게 묻다: 23살 범인의 진짜 동기?" | 2026-04-05 | 68% | 42% | 27 | 1 (상위) | synthetic — Phase 9 dry-run |
| def456 | "100억 갑부가 딱 한 번 울었던 순간" | 2026-04-08 | 64% | 41% | 26 | 2 (상위) | synthetic |
| ghi789 | "3번째 편지의 의미를 아시나요?" | 2026-04-11 | 61% | 40% | 25 | 3 (상위) | synthetic |
| jkl012 | "조수가 놓친 단서" | 2026-04-14 | 48% | 28% | 19 | 4 (하위) | synthetic — hook 약함 |
| mno345 | "5번 방문한 이유" | 2026-04-17 | 45% | 25% | 17 | 5 (하위) | synthetic — 지루함 |
| pqr678 | "범인의 마지막 말" | 2026-04-20 | 42% | 24% | 16 | 6 (하위) | synthetic — 결말 처참 |

## Related

- [[retention_3second_hook]] — 3초 hook 측정 기반 이론
- [[taste_gate_protocol]] — 월 1회 대표님 평가 회로
- [[MOC]] — KPI 카테고리 노드 맵

---

*Created: 2026-04-20 (Phase 9 Plan 09-02)*
*Next update: Phase 10 Month 1 (first real data collection, Sunday KST cron trigger)*
```

## wiki/kpi/MOC.md current Planned Nodes section (lines 17-25)

```markdown
## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [ ] `three_second_hook_target.md` — retention > 60% (SUMMARY §9 Korean specifics)
- [ ] `completion_rate_target.md` — 완주율 > 40%
- [ ] `avg_watch_duration_target.md` — > 25초
- [ ] `kpi_log_template.md` — 월 1회 `kpi_log.md` 자동 생성 포맷 (KPI-02)
- [x] `retention_3second_hook.md` — 3초 retention >60% 목표 + YouTube Analytics 측정 (Phase 6 ready)
```

## MOC.md replacement required (flip kpi_log_template.md checkbox + timestamp update)

- Replace `- [ ] kpi_log_template.md — 월 1회 kpi_log.md 자동 생성 포맷 (KPI-02)` with `- [x] [[kpi_log]] — Hybrid format: Part A (KPI-06 targets) + Part B (Monthly Tracking) (Phase 9 ready)`
- Keep other 3 unchecked placeholders untouched (they remain Phase 10 future work)
- Update `updated: 2026-04-19` to `updated: 2026-04-20`
- Update status from `scaffold` to `partial` (reflects 2/5 nodes now ready: retention_3second_hook + kpi_log)
</interfaces>
</context>

<tasks>

<task id="9-02-01">
  <action>
Create `wiki/kpi/kpi_log.md` with EXACTLY the content shown in the `<interfaces>` block above (the full Hybrid format markdown). Literal requirements:

1. **Frontmatter** — `category: kpi`, `status: ready`, `tags: [kpi, monthly-tracking, retention, completion, avg-watch]`, `updated: 2026-04-20`
2. **Part A heading** — `## Part A: Target Declaration (KPI-06)` exactly
3. **3 target rows** — 3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초 — all three thresholds literal
4. **Re-creation trigger thresholds** — 50% / 30% / 18 in column 3
5. **API Contract sub-section** — MUST contain these literal strings:
   - `https://youtubeanalytics.googleapis.com/v2/reports`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - `audienceWatchRatio`
   - `averageViewDuration`
   - `elapsedVideoTimeRatio`
   - `uploaderType==SELF`
   - `trafficSourceType=SHORTS`
6. **실패 정의 sub-section** — reference to "2개 이상 FAIL" + "FAILURES.md 승격"
7. **Part B heading** — `## Part B: Monthly Tracking` exactly
8. **Monthly Tracking table columns** — exact header row: `| video_id | title | upload_date | 3sec_retention | completion_rate | avg_view_sec | taste_gate_rank | notes |`
9. **2026-04 placeholder row** — single row with `_` placeholders + "Phase 10 Month 1 수집 대상" note
10. **Dry-run sub-section** — 6 synthetic rows matching the 탐정/조수 페르소나 video_ids (abc123/def456/ghi789/jkl012/mno345/pqr678) and titles exactly as in `<interfaces>`. NO placeholder like "테스트용 쇼츠".
11. **Related links section** — `[[retention_3second_hook]]`, `[[taste_gate_protocol]]`, `[[MOC]]`
12. **Trailing metadata** — `*Created: 2026-04-20 (Phase 9 Plan 09-02)*`

Write in UTF-8. Do NOT include `skip_gates` or `TODO(next-session)` anywhere (Hook 3종 차단).
  </action>
  <read_first>
    - tests/phase09/test_kpi_log_schema.py (the 5 tests this file must satisfy: target_declaration / api_contract_present / hybrid_structure / failure_thresholds / kpi_log_exists)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Pattern 6 (full Hybrid format body verbatim)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md §D-05, §D-06, §D-07 (Hybrid format contract)
    - wiki/kpi/retention_3second_hook.md (existing sibling node frontmatter convention)
    - .planning/REQUIREMENTS.md line 147 (KPI-06 exact text)
  </read_first>
  <acceptance_criteria>
    - `test -f wiki/kpi/kpi_log.md` exits 0
    - `wc -l < wiki/kpi/kpi_log.md` outputs a number >= 80
    - `grep -q '^category: kpi$' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '^status: ready$' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '## Part A' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '## Part B' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'Target Declaration' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'Monthly Tracking' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '60%' wiki/kpi/kpi_log.md && grep -q '3초 retention' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '40%' wiki/kpi/kpi_log.md && grep -q '완주율' wiki/kpi/kpi_log.md` exits 0
    - `grep -qE '(> ?25초|> ?25)' wiki/kpi/kpi_log.md && grep -q '평균 시청' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'youtubeanalytics.googleapis.com/v2/reports' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'yt-analytics.readonly' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'audienceWatchRatio' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'averageViewDuration' wiki/kpi/kpi_log.md` exits 0
    - `grep -q 'elapsedVideoTimeRatio' wiki/kpi/kpi_log.md` exits 0
    - `grep -qE 'video_id.*title.*3sec_retention.*completion_rate.*avg_view_sec.*taste_gate_rank' wiki/kpi/kpi_log.md` exits 0
    - `grep -q '50%' wiki/kpi/kpi_log.md` exits 0 (3-sec re-creation threshold)
    - `grep -c 'abc123\|def456\|ghi789\|jkl012\|mno345\|pqr678' wiki/kpi/kpi_log.md` outputs `>= 6`
    - `grep -q '테스트용 쇼츠' wiki/kpi/kpi_log.md` must be FALSE (forbidden placeholder)
    - `grep -q 'skip_gates' wiki/kpi/kpi_log.md` must be FALSE
    - `grep -q 'TODO(next-session)' wiki/kpi/kpi_log.md` must be FALSE
    - `python -m pytest tests/phase09/test_kpi_log_schema.py -x --no-cov` exits 0
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/test_kpi_log_schema.py -x --no-cov</automated>
  <task_type>impl</task_type>
</task>

<task id="9-02-02">
  <action>
Edit `wiki/kpi/MOC.md` to flip the `kpi_log_template.md` checkbox. Target literal replacement per `<interfaces>`:

Before (existing line):
```
- [ ] `kpi_log_template.md` — 월 1회 `kpi_log.md` 자동 생성 포맷 (KPI-02)
```

After:
```
- [x] [[kpi_log]] — Hybrid format: Part A (KPI-06 targets) + Part B (Monthly Tracking) (Phase 9 ready)
```

Also update frontmatter:
- `status: scaffold` → `status: partial`
- `updated: 2026-04-19` → `updated: 2026-04-20`

Keep the 3 other unchecked placeholders (three_second_hook_target.md, completion_rate_target.md, avg_watch_duration_target.md) UNTOUCHED — they remain Phase 10 future candidates. The `retention_3second_hook.md` checked line stays as-is.

Do NOT delete or rewrite unrelated sections (Scope / Related / Source References / footer metadata). This is a surgical edit.

Run collection + full Phase 9 sweep to confirm parallel plans 09-01 and 09-03 still collect cleanly:

```
python -m pytest tests/phase09/ --collect-only -q --no-cov
python -m pytest tests/phase09/test_kpi_log_schema.py -q --no-cov
```

Both MUST exit 0.

Run Phase 4-8 collection sweep:

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov
```

MUST exit 0 (986+ collection preserved — wiki-only changes should not affect any test).
  </action>
  <read_first>
    - wiki/kpi/MOC.md (read current line 17-25 for exact existing text)
    - wiki/kpi/kpi_log.md (just-written companion file)
    - tests/phase09/test_kpi_log_schema.py
  </read_first>
  <acceptance_criteria>
    - `grep -c '^- \[x\].*kpi_log' wiki/kpi/MOC.md` outputs `>= 1`
    - `grep -q 'kpi_log_template.md' wiki/kpi/MOC.md` must be FALSE (old placeholder removed) — if still present as literal filename this check fails
    - `grep -q '\[\[kpi_log\]\]' wiki/kpi/MOC.md` exits 0 (Obsidian-style link added)
    - `grep -q '^status: partial$' wiki/kpi/MOC.md` exits 0 (frontmatter status updated)
    - `grep -q '^updated: 2026-04-20$' wiki/kpi/MOC.md` exits 0
    - `grep -c '^- \[ \] `[^`]*\.md`' wiki/kpi/MOC.md` outputs `3` (3 unchecked future placeholders preserved)
    - `grep -q 'retention_3second_hook' wiki/kpi/MOC.md` exits 0 (existing checked line preserved)
    - `python -m pytest tests/phase09/ --collect-only -q --no-cov` exits 0
    - `python -m pytest tests/phase09/test_kpi_log_schema.py -q --no-cov` exits 0
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov` exits 0
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/test_kpi_log_schema.py -q --no-cov</automated>
  <task_type>impl</task_type>
</task>

</tasks>

<verification>
1. `wiki/kpi/kpi_log.md` exists with Hybrid format (Part A + Part B).
2. Part A declares 3 KPI-06 targets + API Contract (endpoint + scope + 2 metrics) + 실패 정의.
3. Part B has Monthly Tracking table + Dry-run 6 synthetic rows (탐정/조수 personas).
4. `wiki/kpi/MOC.md` checkbox flipped from `kpi_log_template.md` → `[[kpi_log]]` [x]; frontmatter status=partial / updated=2026-04-20.
5. All 5 `test_kpi_log_schema.py` tests pass.
6. Phase 4-8 986+ collection preserved.
7. No placeholder "테스트용 쇼츠", no skip_gates, no TODO(next-session).
</verification>

<success_criteria>
Plan 09-02 is COMPLETE when:
- `wiki/kpi/kpi_log.md` ships with Hybrid format Part A + Part B, all 3 KPI-06 targets declared with measurement method, API Contract with literal endpoint + OAuth scope + metric names.
- `wiki/kpi/MOC.md` checkbox flipped to `[[kpi_log]]` [x] with frontmatter update.
- `test_kpi_log_schema.py` all 5 tests PASS.
- Phase 4-8 986+ collection preserved (wiki-only change, zero production impact).
- SC#2 (KPI 목표 선언 + 측정 방식 명시) and KPI-06 (3 target values) both textually satisfied and grep-verifiable.
</success_criteria>

<output>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-02-SUMMARY.md` documenting:
- Files created (wiki/kpi/kpi_log.md with line count)
- Files modified (wiki/kpi/MOC.md — 1 checkbox flip + frontmatter update)
- 3 KPI-06 targets declared (3초 retention > 60% / 완주율 > 40% / 평균 시청 > 25초)
- API Contract literals present (endpoint, scope, 2 metrics)
- test_kpi_log_schema.py result (5/5 PASS expected)
- Phase 4-8 regression collection result
- Commit hash
</output>
