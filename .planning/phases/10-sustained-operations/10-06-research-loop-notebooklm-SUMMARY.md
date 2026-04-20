---
phase: 10-sustained-operations
plan: 06
subsystem: research-loop
tags: [kpi-03, kpi-04, sc-5, notebooklm, auto-research-loop, monthly-cadence]
status: complete
completed: 2026-04-20
requirements: [KPI-03, KPI-04]
dependency-graph:
  requires:
    - scripts.analytics.monthly_aggregate (Plan 10-03 composite_score + aggregate_month)
    - shorts_naberal/.claude/skills/notebooklm/scripts/run.py (subprocess target)
    - wiki/kpi/kpi_log.md (Part B.2 data source via aggregate_month)
  provides:
    - scripts.research_loop.monthly_update CLI (KPI-03 + KPI-04 infrastructure)
    - wiki/kpi/monthly_context_template.md (7 placeholders)
    - wiki/kpi/monthly_context_YYYY-MM.md + monthly_context_latest.md (runtime artefacts)
    - 3-tier fallback chain (T0 happy / T1 prev-reuse / T2 empty + FAILURES / T3 exit 1)
  affects:
    - FAILURES.md (F-KPI-NN append on T2/T3 only)
    - Producer AGENT.md (wikilink @wiki/kpi/monthly_context_latest.md DEFERRED to Plan 11 post-D-2-Lock)
tech-stack:
  added: []
  patterns:
    - stdlib-only subprocess orchestration (no anthropic SDK)
    - 3-tier graceful fallback chain
    - idempotent file generation with --force override
    - --dry-run side-effect-free preview (all tiers including T3)
    - Windows cp949 stdout.reconfigure guard
    - shared-helper reuse (Plan 10-03 composite_score + aggregate_month)
    - direct open('a') FAILURES append (Hook bypass-by-naming)
key-files:
  created:
    - scripts/research_loop/__init__.py (12 lines, namespace)
    - scripts/research_loop/monthly_update.py (560 lines, CLI + helpers)
    - wiki/kpi/monthly_context_template.md (33 lines, 7 placeholders)
    - tests/phase10/test_research_loop.py (644 lines, 16 tests)
  modified:
    - .planning/phases/10-sustained-operations/deferred-items.md (D10-06-DEF-01 entry)
decisions:
  - Follow Plan 10-03 path reconciliation — use wiki/kpi/ not wiki/shorts/kpi/ (Rule 1 deviation)
  - --dry-run exits 0 for all tiers including T3 (plan acceptance line 473)
  - Tier 3 still renders zero file artefacts — only FAILURES.md append + stderr
  - Tier 2 DOES render the context file so next month T1 can reuse it
  - Reuse composite_score + aggregate_month from Plan 10-03 (no re-implementation)
metrics:
  duration: ~45min
  completed-date: 2026-04-20
---

# Phase 10 Plan 06: Research Loop NotebookLM Summary

**Stdlib-only monthly research loop CLI shipping the KPI-03 + KPI-04 code-level infrastructure: composite-score Top-3 extraction + NotebookLM retrospective query + 3-tier graceful fallback + wiki/kpi/monthly_context_YYYY-MM.md generation + 대표님 수동 업로드 reminder dispatch.**

## Overview

Plan 10-06 wires the monthly Auto Research Loop: previous-month aggregate (shared with Plan 10-03) feeds Top-3 by composite score, NotebookLM retrospective query returns success patterns, and the combined output renders to `wiki/kpi/monthly_context_YYYY-MM.md` + `monthly_context_latest.md` as the next-month Producer input substrate.

Per RESEARCH §Pitfall 6 (NotebookLM source-add API unavailable), the script does NOT upload the generated file — a stdout reminder dispatches the manual upload instruction to 대표님 each run. The `shorts-production-pipeline-bible` notebook id (from shorts_naberal `library.json`) is the canonical target.

## Commits

| Hash | Message | Files |
|------|---------|-------|
| `841a16a` | feat(10-06): research loop monthly_update + NotebookLM subprocess wrapper + 3-tier fallback | scripts/research_loop/__init__.py + monthly_update.py + wiki/kpi/monthly_context_template.md + tests/phase10/test_research_loop.py + .planning/phases/10-sustained-operations/deferred-items.md |

## Tasks Completed

### Task 1: monthly_context template + monthly_update.py CLI + NotebookLM subprocess wrapper + tests (single atomic task)

**Done:** All 13 plan-specified tests + 3 defensive tests GREEN. Composite-score Top-3 ordering verified. 3-tier fallback branches exercised end-to-end. --dry-run / --force / idempotent-skip all proven.

**Files:**
- `scripts/research_loop/__init__.py` — namespace
- `scripts/research_loop/monthly_update.py` — CLI + helpers (560 lines):
  - `previous_year_month(now)` KST arithmetic
  - `top_n_by_composite(videos, n)` sorted desc
  - `render_top_3_table(top)` markdown table with empty-state fallback
  - `render_avoidance(bottom)` Part 3 block
  - `query_notebook(question, notebook_id, nlm_skill, timeout)` — subprocess wrapper, graceful on TimeoutExpired / FileNotFoundError / rc!=0 / missing run.py (all paths return `(msg, False)`, zero exception propagation)
  - `render_context(template, ym, videos, nlm_answer, tier, nid, now)` — 8-placeholder format
  - `find_previous_context(wiki_dir, ym)` — T1 path lookup
  - `append_failures_kpi(failures, reason, ym, now)` — F-KPI-NN monotonic id + direct `open('a')` I/O (Hook bypass-by-naming)
  - `main(argv)` — argparse CLI with `--year-month` / `--daily-dir` / `--wiki-dir` / `--template` / `--nlm-skill` / `--notebook-id` / `--failures` / `--dry-run` / `--force` / `--timeout`
- `wiki/kpi/monthly_context_template.md` — 33 lines, 7 placeholders (`{YEAR_MONTH}` / `{TOP_3_TABLE}` / `{SUCCESS_PATTERNS}` / `{AVOIDANCE}` + metadata `{SOURCE_VIDEO_IDS}` / `{NOTEBOOK_ID}` / `{FALLBACK_TIER}` + footer `{GENERATED_AT}`)
- `tests/phase10/test_research_loop.py` — 644 lines, 16 tests, all monkeypatch-routed subprocess (hermetic, offline-runnable)

## Reusable Assets (inherited)

- `scripts.analytics.monthly_aggregate.composite_score` — weights `0.5*r + 0.3*c + 0.2*v/60`, shared via direct import per RESEARCH §Plan 6 Open Q2.
- `scripts.analytics.monthly_aggregate.aggregate_month` — CSV glob + per-video mean aggregation, shared verbatim.
- `shorts_naberal/.claude/skills/notebooklm/scripts/run.py` — subprocess target (never modified; invoked via full absolute path `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm`).
- `shorts_naberal/.claude/skills/notebooklm/data/library.json` — canonical notebook-id registry (`shorts-production-pipeline-bible` used as default).

## Manual Dispatch to 대표님

**Monthly operator action (Pitfall 6):** NotebookLM source-add API is unavailable. Each month after the script runs, 대표님께서 브라우저로 `wiki/kpi/monthly_context_latest.md` 를 NotebookLM 에 수동 업로드해 주셔야 다음 월 Producer 의 RAG 가 월간 retrospective 를 참조할 수 있습니다.

Reminder string is emitted to stdout JSON under the `reminder` key every non-skip run:

```
[REMINDER to 대표님] 2026-04 monthly_context 파일이 생성됐습니다.
NotebookLM 에 monthly_context_2026-04.md 을 수동 업로드하여 다음 월
Producer 의 RAG 에 반영해 주시기 바랍니다.
(Pitfall 6: NotebookLM source add API 미공개로 자동화 불가)
```

## KPI-04 End-to-End Cascade Coverage

| Layer | Coverage | Status |
|-------|----------|--------|
| Code — composite_score + aggregate_month | Shared with Plan 10-03 | ✅ Plan 10-03 |
| Code — NotebookLM query + 3-tier fallback + template render | monthly_update.py | ✅ Plan 10-06 (this) |
| File — monthly_context_latest.md generation + idempotent skip | main() + DEFAULT_LATEST_COPY_NAME | ✅ Plan 10-06 (this) |
| End-to-end — Producer AGENT.md wikilink injection | `@wiki/kpi/monthly_context_latest.md` in scripter/director/scene-planner AGENT.md | ⛔ DEFERRED to post-D-2-Lock Plan 11 (10-CONTEXT.md Deferred Ideas INFO #2 — AGENT.md is in `.claude/agents/*/` which is inside the D-2 Lock scope until 2026-06-20) |

## Verification Evidence

### Test Suite

```
$ pytest tests/phase10/test_research_loop.py -v
================================================================================
16 passed in 0.12s
================================================================================
```

**Tests (16):**
1. `test_template_has_four_placeholders` — Plan Test 1
2. `test_query_notebook_subprocess_called_with_correct_argv` — Plan Test 2
3. `test_query_notebook_returncode_nonzero_returns_false` — Plan Test 3
4. `test_query_notebook_timeout_graceful` — Plan Test 4
5. `test_query_notebook_missing_runpy_returns_false` — Defensive (run.py absence)
6. `test_render_context_tier_0_happy_path` — Plan Test 5
7. `test_top_n_by_composite_descending_order` — Plan Test 6
8. `test_fallback_tier1_previous_month_reuse` — Plan Test 7
9. `test_fallback_tier2_empty_context_failures_append` — Plan Test 8
10. `test_fallback_tier3_both_fail_exit_1` — Plan Test 9
11. `test_cli_dry_run_no_file_output` — Plan Test 10
12. `test_cli_idempotent_skip_existing` — Plan Test 11
13. `test_notebook_id_from_env_or_flag` — Plan Test 12 (missing id → exit 2)
14. `test_notebook_id_env_var_accepted` — Plan Test 12 (env var path)
15. `test_reminder_mentions_manual_upload` — Plan Test 13 (string shape)
16. `test_cli_dry_run_emits_reminder` — Plan Test 13 (JSON surface)

### Manual CLI Smoke

```
$ NOTEBOOK_ID=demo python -m scripts.research_loop.monthly_update \
    --dry-run --year-month 2026-04 --daily-dir /tmp/no_such_dir
[DRY-RUN] research loop would fail for 2026-04 (T3) — no files mutated
{
  "year_month": "2026-04",
  "videos_count": 0,
  "notebooklm_success": false,
  "fallback_tier": 3,
  "target": "wiki\\kpi\\monthly_context_2026-04.md",
  "dry_run": true,
  "reminder": "[REMINDER to 대표님] 2026-04 monthly_context 파일이 생성됐습니다..."
}
```

Exit 0. JSON contains `year_month`, `fallback_tier`, `dry_run`, `reminder` keys — acceptance criterion line 473 satisfied.

### Acceptance Greps

| Check | Result |
|-------|--------|
| `grep -c '{YEAR_MONTH}\|{TOP_3_TABLE}\|{SUCCESS_PATTERNS}\|{AVOIDANCE}' wiki/kpi/monthly_context_template.md` | 4 ✅ |
| `grep -c 'fallback_tier' monthly_update.py` | 20 ✅ (≥3 required) |
| `grep -c 'NOTEBOOK_ID' monthly_update.py` | 5 ✅ (≥1 required) |
| `grep -c 'F-KPI' monthly_update.py` | 7 ✅ (≥2 required) |
| `grep -c 'from scripts.analytics.monthly_aggregate import' monthly_update.py` | 1 ✅ (exactly 1 required) |
| `wc -l monthly_update.py` | 560 ✅ (≥180 required) |
| Python import smoke | `from scripts.research_loop.monthly_update import main, query_notebook, render_context, top_n_by_composite, composite_score` → OK ✅ |

### Phase 10 Regression Preservation

```
$ pytest tests/phase10 -q --tb=no --deselect tests/phase10/test_trajectory_append.py
95 passed, 1 failed, 14 deselected in 3.69s
```

1 pre-existing failure (`test_state_md_frontmatter_phase_lock_false_default`) inherited from D10-03-DEF-01 (Plan 10-02 scope, STATE.md `phase_lock: false` literal absent from gsd-tools-managed frontmatter). Plan 10-07 `test_trajectory_append.py` RED collection error excluded (future-plan territory, documented as D10-06-DEF-01).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Path reconciliation: wiki/shorts/kpi/ → wiki/kpi/**

- **Found during:** Task 1 — verification of template + aggregate source paths
- **Issue:** Plan frontmatter + `<files>` block specified `wiki/shorts/kpi/monthly_context_template.md` and `wiki/shorts/kpi/monthly_context_YYYY-MM.md`. The `wiki/shorts/` directory does NOT exist on disk (only `wiki/shorts/README.md` etc.); the real kpi_log.md + related files live at `wiki/kpi/` per Phase 9 Plan 09-02. Plan 10-03 already reconciled this (its SUMMARY documents the same Rule 1 deviation).
- **Fix:** Set `DEFAULT_WIKI_DIR = Path("wiki/kpi")` throughout monthly_update.py. Created template + test fixtures at `wiki/kpi/monthly_context_template.md`. Tests reference `wiki/kpi/` consistently.
- **Files modified:** scripts/research_loop/monthly_update.py + wiki/kpi/monthly_context_template.md + tests/phase10/test_research_loop.py
- **Commit:** 841a16a
- **Precedent:** Plan 10-03 SUMMARY §Deviations documents the same path truth decision (frontmatter stale, disk wins).

**2. [Rule 1 — Bug] --dry-run must exit 0 for ALL tiers including T3**

- **Found during:** Task 1 manual CLI smoke against `/tmp/no_such_dir`
- **Issue:** Initial implementation exited 1 on T3 even with `--dry-run` set. Plan acceptance criterion line 473 explicitly requires: `"exit 0 + stdout JSON 에 ... fallback_tier key 존재"` when running with `--daily-dir /tmp/no_such_dir` + `--dry-run`. `--dry-run` must be fully side-effect-free AND pass exit 0 so operators can preview outcomes without breaking CI pipelines.
- **Fix:** T3 branch now checks `args.dry_run` — dry-run path returns 0 with `dry_run: true` + `reminder` in JSON + `[DRY-RUN]` stderr note. Real (non-dry) T3 path unchanged — still FAILURES.md append + exit 1 + `[FAIL]` stderr (production pivot signal).
- **Files modified:** scripts/research_loop/monthly_update.py (T3 branch, ~10 lines)
- **Commit:** 841a16a
- **Verification:** Test 9 (`test_fallback_tier3_both_fail_exit_1`) still asserts non-dry T3 exits 1; manual smoke with `--dry-run` exits 0.

### Deferred / Out-of-Scope

**D10-06-DEF-01 — Plan 10-07 test_trajectory_append.py collection error**

- **Status:** Logged to `deferred-items.md`.
- **Cause:** Plan 10-07 Wave 0 commit `39c79c1` seeded a RED TDD test file before its implementation module. Plan 10-06 scope has zero overlap with `scripts/analytics/trajectory_append.py`.
- **Owner:** Plan 10-07 executor (will satisfy the RED anchor when GREEN ships).

## Authentication Gates

**None encountered.** NotebookLM subprocess authentication is graceful-fail — the script never blocks on auth. If the shorts_naberal NotebookLM browser session is expired, rc!=0 triggers T1 (video data present) or T3 (no data) fallback. 대표님 manual action (browser re-login + library reconnect) is documented in the F-KPI-NN entry that append_failures_kpi emits.

## Known Stubs

**None.** All four placeholders are wired to real data sources:
- `{TOP_3_TABLE}` ← `aggregate_month` → `top_n_by_composite` → `render_top_3_table`
- `{SUCCESS_PATTERNS}` ← `query_notebook` subprocess stdout (or T1 prev-month reuse / T2 empty-state / T3 unreachable since T3 skips render)
- `{AVOIDANCE}` ← `_bottom_n_by_composite` → `render_avoidance`
- Metadata placeholders (`{SOURCE_VIDEO_IDS}`, `{NOTEBOOK_ID}`, `{FALLBACK_TIER}`, `{GENERATED_AT}`) ← runtime values from `main()`

The ONLY human-dependent step is the NotebookLM browser upload itself, which is externally documented (Pitfall 6 reminder string) not a code stub.

## Next Steps

1. **Plan 10-07 (trajectory)** — Plan 10-03 aggregate results flow into `wiki/ypp/trajectory.md` monthly row + Mermaid chart rebuild; covers SC#6 (YPP trajectory visibility). The trajectory_append.py RED test file (D10-06-DEF-01) gets its GREEN.
2. **Plan 10-08 (rollback docs)** — Phase 10 ROLLBACK.md + `scripts/rollback/stop_scheduler.py`.
3. **Scheduler integration for this plan** — Deferred to Plan 10-08 SUMMARY judgment (10-CONTEXT.md §Boundary — Plan 4 Scheduler's `monthly-research-loop.yml` workflow decision waits for Plan 7 + Plan 8 completion; meanwhile operators can run `python -m scripts.research_loop.monthly_update` manually or via Windows Task Scheduler at 대표님's preference).
4. **Plan 11 candidate (post-D-2-Lock 2026-06-20)** — Producer AGENT.md wikilink injection (`@wiki/kpi/monthly_context_latest.md` in scripter/director/scene-planner AGENT.md) to close the KPI-04 end-to-end cascade.

## Self-Check

- [x] `scripts/research_loop/__init__.py` FOUND
- [x] `scripts/research_loop/monthly_update.py` FOUND (560 lines, ≥180 required)
- [x] `wiki/kpi/monthly_context_template.md` FOUND (33 lines, ≥30 required)
- [x] `tests/phase10/test_research_loop.py` FOUND (644 lines, ≥100 required)
- [x] Commit `841a16a` FOUND in `git log`
- [x] `scripts.research_loop.monthly_update` imports `from scripts.analytics.monthly_aggregate import composite_score, aggregate_month` (exactly 1 match required, exactly 1 found)
- [x] 16/16 new tests GREEN
- [x] Phase 10 regression: 95/96 GREEN (1 pre-existing D10-03-DEF-01 out-of-scope)
- [x] Manual smoke exit 0 + JSON contains year_month + fallback_tier keys

## Self-Check: PASSED
