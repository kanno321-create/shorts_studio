---
phase: 10-sustained-operations
plan: 03
subsystem: analytics
tags: [youtube-analytics, oauth, googleapiclient, kpi, csv, composite-score, idempotent-append]

requires:
  - phase: 08-publisher-youtube-oauth
    provides: scripts/publisher/oauth.py get_credentials() + InstalledAppFlow + CLIENT_SECRET_PATH/TOKEN_PATH constants
  - phase: 09-phase9-kpi-taste-gate
    provides: wiki/kpi/kpi_log.md Part A target declaration (KPI-06 baseline, byte-identical preserved)
  - phase: 10-sustained-operations
    provides: Plan 10-01 skill_patch_counter reports/ precedent + Plan 10-02 drift_scan conftest precedent
provides:
  - YouTube Analytics v2 reports().query() daily CLI (scripts/analytics/fetch_kpi.py)
  - Month-end composite-score aggregator + idempotent kpi_log.md Part B.2 appender (scripts/analytics/monthly_aggregate.py)
  - scripts.analytics namespace (__init__.py)
  - PART_B_APPEND_MARKER scaffold in wiki/kpi/kpi_log.md for downstream schedulers
  - composite_score shared helper (0.5*retention + 0.3*completion + 0.2*(view/60)) — re-exported for Plan 10-06 research_loop
  - OAuth SCOPES lockstep test (tests/phase08/test_oauth_installed_flow.py: _two → _three_in_order)
affects: [10-04-scheduler-hybrid, 10-06-research-loop-notebooklm, 10-07-ypp-trajectory, 11-candidate-audienceRetention-timeseries]

tech-stack:
  added: [googleapiclient.discovery.build("youtubeAnalytics", "v2"), zoneinfo.ZoneInfo("Asia/Seoul") KST]
  patterns:
    - "late-binding get_credentials() wrapper to enable test monkeypatch without touching scripts.publisher.oauth directly"
    - "MagicMock chain for googleapiclient (client → reports() → query() → execute())"
    - "stdlib-only monthly aggregation via collections.defaultdict + csv.DictReader (pandas rejected per Plan 3 Open Q4)"
    - "idempotent markdown append via regex search below PART_B_APPEND_MARKER + single-shot text.replace(..., 1)"
    - "explicit RuntimeError on missing marker — Pitfall 2 analogue, silent fallback 금지"
    - "composite_score shared-helper export for cross-plan reuse (Plan 10-06 monthly_context)"

key-files:
  created:
    - scripts/analytics/__init__.py
    - scripts/analytics/fetch_kpi.py (291 lines)
    - scripts/analytics/monthly_aggregate.py (295 lines)
    - tests/phase10/test_fetch_kpi.py (10 tests)
    - tests/phase10/test_monthly_aggregate.py (10 tests)
  modified:
    - wiki/kpi/kpi_log.md (Part B.2 section + PART_B_APPEND_MARKER added; Part A byte-identical)
    - tests/phase08/test_oauth_installed_flow.py (SCOPES assertion _two → _three_in_order)
    - .planning/phases/10-sustained-operations/deferred-items.md (D10-03-DEF-01/02 entries)

key-decisions:
  - "retention_3s ← audienceWatchRatio proxy (v1). audienceRetention timeseries 정확도 개선은 Phase 11 candidate (10-CONTEXT.md Deferred Ideas)"
  - "Plan frontmatter 의 wiki/shorts/kpi/kpi_log.md 는 존재하지 않음 — 실 경로는 wiki/kpi/kpi_log.md (Phase 9 Plan 09-02 생성 위치). Plan 3 는 실 경로를 따름 (Rule 1 deviation, 데이터 손실 금지)"
  - "Part A (KPI-06 Target Declaration) 는 byte-identical 보존. Part B.1 video-level synthetic sample 도 보존. 새 Part B.2 aggregate section 을 Part B 하위 subsection 으로 추가 (Plan prose 의 단순 header overwrite 방식보다 안전)"
  - "Task 1 에서 SCOPES 는 이미 Wave 0 commit 2fda554f 에서 확장됨 — Task 1 은 검증만 (재수정 금지). 단, Phase 8 test_oauth_installed_flow.py 의 낡은 _two_in_order 단언을 Plan 3 직접 후폭풍으로 _three_in_order 로 업데이트 (Rule 1)"
  - "composite_score 를 monthly_aggregate.py 에서 export — Plan 10-06 research_loop 가 동일 함수를 import 재사용하도록 계약 수립"

patterns-established:
  - "Analytics CLI: argparse --video-ids / --days-back / --output-dir / --dry-run. Windows cp949 stdout+stderr reconfigure guard. KST-anchored datetime.now() → date().isoformat() CSV filename"
  - "stdlib-only month-end aggregate: defaultdict[video_id → list of samples] → per-video mean → composite rank → top-N summary"
  - "idempotent markdown append: read_text → detect existing month row below MARKER via regex → skip if present else replace(MARKER, MARKER+\\n+row, 1) → write_text"
  - "401/403/insufficient_scope scope re-auth hint — stderr + explicit raise (never silent)"

requirements-completed: [KPI-01, KPI-02]

duration: 18min
completed: 2026-04-20
---

# Phase 10 Plan 03: YouTube Analytics Fetch Summary

**Stdlib-only YouTube Analytics v2 daily fetch CLI + month-end composite-score aggregator idempotently appending to `wiki/kpi/kpi_log.md` Part B.2 via PART_B_APPEND_MARKER — KPI-01/02 infrastructure shipped.**

## Performance

- **Duration:** ~18 min (Task 1 + Task 2 RED→GREEN)
- **Started:** 2026-04-20T12:40:00Z (approximately)
- **Completed:** 2026-04-20T12:58:00Z (approximately)
- **Tasks:** 2 (1 scaffold + 1 TDD RED→GREEN implementation)
- **Files created:** 5 (2 production Python, 2 pytest modules, 1 namespace `__init__.py`)
- **Files modified:** 3 (kpi_log.md Part B.2 append, phase08 scope test rename, deferred-items.md 2 entries)

## Accomplishments

- `scripts/analytics/fetch_kpi.py` — YouTube Analytics v2 `reports().query()` daily CLI with per-video filter, CSV output, explicit 401 re-auth hint, `--dry-run` stdout-only mode (291 lines, 150+ requirement exceeded).
- `scripts/analytics/monthly_aggregate.py` — stdlib `collections.defaultdict + csv` month-end aggregator with shared `composite_score` export and idempotent markdown append to kpi_log.md Part B.2 below `<!-- PART_B_APPEND_MARKER -->` (295 lines, 120+ requirement exceeded).
- 19/19 Task 2 tests GREEN (10 fetch_kpi + 10 monthly_aggregate; plan minimum 12+ exceeded).
- `wiki/kpi/kpi_log.md` Part B.2 section + PART_B_APPEND_MARKER scaffold installed (Phase 9 Part A/B.1 byte-identical preserved).
- OAuth SCOPES lockstep test updated to reflect Wave 0 `yt-analytics.readonly` addition (phase08 6/6 GREEN post-fix).
- `composite_score` contract established for Plan 10-06 cross-plan re-use.

## Task Commits

1. **Task 1: scripts/analytics/ scaffold + kpi_log.md Part B.2 marker + oauth test lockstep** — `230b0e1` (feat)
2. **Task 2 RED: fetch_kpi + monthly_aggregate 19 failing tests** — `60907dc` (test)
3. **Task 2 GREEN: fetch_kpi.py + monthly_aggregate.py implementation** — `69c83df` (feat)

_Plan metadata commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS flip) follows at end of execution._

## Files Created/Modified

- `scripts/analytics/__init__.py` — Phase 10 analytics namespace marker (7 lines).
- `scripts/analytics/fetch_kpi.py` — daily KPI fetch CLI (YouTube Analytics v2 `reports().query()`).
- `scripts/analytics/monthly_aggregate.py` — month-end aggregator + kpi_log.md appender.
- `tests/phase10/test_fetch_kpi.py` — 10 behavioral + anchor tests (MagicMock-chained googleapiclient; zero real OAuth).
- `tests/phase10/test_monthly_aggregate.py` — 10 behavioral + anchor tests (tmp kpi_log.md fixture; real wiki/kpi/kpi_log.md untouched).
- `wiki/kpi/kpi_log.md` — Part B.2 "Month-level Aggregate" subsection with composite_score formula documentation + PART_B_APPEND_MARKER placeholder.
- `tests/phase08/test_oauth_installed_flow.py` — `test_scopes_are_exactly_two_in_order` renamed to `_three_in_order` with post-Plan-10-03 invariant (3-entry list assertion).
- `.planning/phases/10-sustained-operations/deferred-items.md` — D10-03-DEF-01 (drift_scan STATE.md assertion, Plan 10-02 scope) + D10-03-DEF-02 (regression_986 cascade, inherited D10-01-DEF-01).

## Decisions Made

- **retention_3s proxy:** v1 maps `retention_3s ← audienceWatchRatio` because the true 3-second retention requires `audienceRetention` timeseries (`dimensions=elapsedVideoTimeRatio`) and per-video pagination. Documented in source docstring + Phase 10 CONTEXT Deferred Ideas. Phase 11 candidate after ≥1 month real-data calibration.
- **kpi_log.md path reconciliation:** Plan frontmatter declared `wiki/shorts/kpi/kpi_log.md` but Phase 9 Plan 09-02 shipped the real file at `wiki/kpi/kpi_log.md`. Followed disk truth (no `wiki/shorts/` directory exists). Data preserved byte-identical.
- **Part B section topology:** Extended rather than replaced. Phase 9 video-level synthetic sample (6 rows) preserved as Part B.1; new `Part B.2: Month-level Aggregate` subsection added with the marker. This maintains Phase 9 Taste Gate UX evidence while enabling Plan 3 monthly rows.
- **composite_score shared export:** Exposed via `scripts.analytics.monthly_aggregate.composite_score` so Plan 10-06 research_loop imports the exact same formula (documented in `__all__`). Prevents formula drift across plans.
- **argparse `--video-ids` required (no channel enum):** Channel-wide auto-enumeration of recent uploads is Plan 10-06 scope. Plan 10-03 exits 2 with stderr hint when `--video-ids` is absent.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] kpi_log.md real path differs from Plan frontmatter**
- **Found during:** Task 1 (kpi_log.md edit)
- **Issue:** Plan frontmatter specified `wiki/shorts/kpi/kpi_log.md`, but `wiki/shorts/` does not exist. Phase 9 Plan 09-02 created `wiki/kpi/kpi_log.md` (commit 2026-04-20 Phase 9) with Part A target declaration + Part B.1 video-level samples.
- **Fix:** Followed disk truth — edited `wiki/kpi/kpi_log.md`. Updated `scripts/analytics/monthly_aggregate.py` default `--kpi-log` to `wiki/kpi/kpi_log.md`. Updated tests/phase10/test_monthly_aggregate.py to assert against `wiki/kpi/kpi_log.md`.
- **Files modified:** wiki/kpi/kpi_log.md + scripts/analytics/monthly_aggregate.py (_parse_args default) + tests/phase10/test_monthly_aggregate.py (marker constant check).
- **Verification:** `grep -c "PART_B_APPEND_MARKER" wiki/kpi/kpi_log.md` returns 2 (one marker + one reference in extended footer note); `test_monthly_aggregate_marker_constant_matches_kpi_log` GREEN against real disk file.
- **Committed in:** 230b0e1 (Task 1).

**2. [Rule 1 - Bug] Phase 8 test_oauth_installed_flow.py asserted 2 scopes, actual is 3**
- **Found during:** Task 1 regression verification (`pytest tests/phase08/test_oauth_installed_flow.py`).
- **Issue:** Wave 0 commit `2fda554f` expanded `scripts/publisher/oauth.py::SCOPES` to include `yt-analytics.readonly` (3 entries), but `tests/phase08/test_oauth_installed_flow.py::test_scopes_are_exactly_two_in_order` still asserted the old 2-entry list. Direct regression caused by Plan 3's OAuth scope expansion prerequisite — in-scope to fix.
- **Fix:** Renamed function to `test_scopes_are_exactly_three_in_order` + updated asserted list + added docstring anchoring Plan 10-03 as the source of the 3rd scope + future-change guidance.
- **Files modified:** tests/phase08/test_oauth_installed_flow.py.
- **Verification:** `pytest tests/phase08/test_oauth_installed_flow.py -q` 6/6 GREEN.
- **Committed in:** 230b0e1 (Task 1).

**3. [Rule 2 - Missing Critical] Plan Part B topology replacement would delete Phase 9 Taste Gate evidence**
- **Found during:** Task 1 (kpi_log.md edit planning).
- **Issue:** Plan action step 3 said "extend Part B header columns" but existing header is video-level (video_id|title|upload_date|3sec_retention|…) which is not the same schema as the month-level aggregate header in Plan prose (Month|Videos|Avg 3s|…). Straight overwrite would (a) delete Phase 9 synthetic samples used for Taste Gate UX validation, (b) break the KPI-06 Part A scaffold reference structure.
- **Fix:** Preserved Part A + Part B (renamed logically to Part B.1 video-level) byte-identical. Added new `### Part B.2: Month-level Aggregate` subsection with the Plan prose header + formula documentation + PART_B_APPEND_MARKER. Adjusted `aggregate` row format to match Plan prose exactly (7 columns: Month | Videos | Avg 3s Retention | Avg Completion | Avg View (s) | Top Composite | Notes).
- **Files modified:** wiki/kpi/kpi_log.md (added lines, zero deletes).
- **Verification:** Part A "3초 retention: > 60%" text byte-identical (grep confirmation). `test_monthly_aggregate_appends_kpi_log_row` GREEN (demonstrates row lands exactly after MARKER).
- **Committed in:** 230b0e1 (Task 1).

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 2 critical data-preservation).
**Impact on plan:** All fixes necessary for correctness and Phase 9 data preservation. Zero scope creep. Net artefact count and module line-count requirements met with margin (291 / ≥150 and 295 / ≥120). Tests exceeded plan target (19 vs 12+ minimum).

## Issues Encountered

- **Pre-existing Phase 5/6/7 regression cascade** (D10-01-DEF-01 + D10-03-DEF-02): phase08 `test_regression_986_green.py` fails on `test_phase05_green` / `test_phase06_green` / `test_phase07_green` / `test_combined_986_green` due to Phase 9.1 stack migration (`gen3_alpha_turbo → gen4.5`, Kling 2.6 Pro primary). Zero file overlap with Plan 10-03 — logged to deferred-items.md. Proposed owner: dedicated `phase-regression-cleanup` plan after Phase 10 completion.
- **Plan 10-02 drift_scan assertion drift** (D10-03-DEF-01): `tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default` expects literal `phase_lock: false` substring but current STATE.md omits the key when default-false. Plan 10-02 scope; harden test or teach gsd-tools explicit write. Plan 10-03 verifies: `tests/phase10/test_fetch_kpi.py` + `tests/phase10/test_monthly_aggregate.py` 19/19 GREEN in isolation.

## Authentication Gates

- **OAuth re-authentication (대표님 manual step, Wave 0 already executed):** SCOPES expansion from 2 → 3 entries (adding `yt-analytics.readonly`) invalidates the existing `config/youtube_token.json` refresh_token. Dispatch pending for Plan 10-04 scheduler activation: 대표님 executes `python -c "from scripts.publisher.oauth import get_credentials; get_credentials()"` locally, browser opens for `kanno3@naver.com`, 3-scope consent, new token saved. Plan 10-03 implementation is contract-complete without this step (all tests mock oauth).

## Known Stubs

- **retention_3s as audienceWatchRatio proxy** (fetch_kpi.py `_parse_response`): documented in source docstring + 10-CONTEXT.md Deferred Ideas. Phase 11 candidate — once real data accumulates (≥1 month), proxy error vs. true `audienceRetention` timeseries can be calibrated. Plan 10-06 research loop will use `composite_score` which depends on this proxy; proxy accuracy improvement would transparently improve downstream scoring.

## Next Phase Readiness

- **Plan 10-04 (Scheduler)** already shipped (prior session). `analytics-daily.yml` GH Actions workflow can now invoke `python -m scripts.analytics.fetch_kpi --video-ids $VIDS --output-dir data/kpi_daily/` once `YOUTUBE_CLIENT_SECRET` + `YOUTUBE_TOKEN_JSON` GH secrets are populated (대표님 re-auth required first).
- **Plan 10-06 (research_loop)** can `from scripts.analytics.monthly_aggregate import composite_score, aggregate_month` verbatim — contract established.
- **Plan 10-07 (YPP trajectory)** will consume `wiki/kpi/kpi_log.md` Part B.2 rows as monthly input.
- **Pending dispatch:** 대표님 local browser re-auth before Plan 10-04 GH secret upload. Without this, daily cron will emit 401 insufficient_scope (explicit raise + stderr hint — no silent failure).

## Self-Check: PASSED

- `scripts/analytics/__init__.py` — FOUND.
- `scripts/analytics/fetch_kpi.py` — FOUND (291 lines).
- `scripts/analytics/monthly_aggregate.py` — FOUND (295 lines).
- `tests/phase10/test_fetch_kpi.py` — FOUND (10 tests GREEN).
- `tests/phase10/test_monthly_aggregate.py` — FOUND (10 tests GREEN).
- `wiki/kpi/kpi_log.md` — MODIFIED (PART_B_APPEND_MARKER present, Part A byte-identical).
- Commit `230b0e1` — FOUND (Task 1 scaffold + oauth test lockstep + kpi_log.md extend).
- Commit `60907dc` — FOUND (Task 2 RED, 19 failing tests).
- Commit `69c83df` — FOUND (Task 2 GREEN, 19 passing tests + implementation).
- Phase 8 oauth regression — 6/6 GREEN (`pytest tests/phase08/test_oauth_installed_flow.py -q`).
- Phase 10 Plan 10-03 tests — 19/19 GREEN (`pytest tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -q`).

---
*Phase: 10-sustained-operations*
*Completed: 2026-04-20*
