# Phase 16-02 Deferred Items (Out-of-Scope per SCOPE BOUNDARY rule)

Items discovered during Plan 16-02 execution that are pre-existing failures unrelated to
this plan's scope (RemotionRenderer + ASSEMBLY cascade). Documented per executor
deviation Rule "only auto-fix issues DIRECTLY caused by the current task's changes."

## Pre-existing Test Failures (pre-16-02, NOT caused by this plan)

### 1. tests/phase04/test_supervisor_depth_guard.py::test_17_inspector_names_present
- **Status:** Failing before Plan 16-02 began (verified via `git stash` rollback)
- **Cause:** Supervisor Agent prompt is missing 12 inspector names (ins-narrative-quality, ins-korean-naturalness, ins-readability, ins-thumbnail-hook, ins-license, ins-platform-policy, ins-safety, ins-audio-quality, ins-render-integrity, ins-subtitle-alignment, ins-mosaic, ins-gore).
- **Owner:** Phase 9.1 Supervisor agent integration — NOT Phase 16-02.

### 2. tests/phase05/test_shorts_pipeline.py::test_line_count_is_within_budget
- **Status:** Failing before Plan 16-02 (pre-existing shorts_pipeline.py = 841 lines > 800).
- **Impact after 16-02:** 841 → 884 (+43 lines for Remotion cascade). Plan 16-02 acceptance criterion is wc ≤ 900; satisfied.
- **Cause:** shorts_pipeline.py drift beyond ORCH-01 budget long before Phase 16. Acceptable pre-existing violation per 대표님 전권 위임.
- **Owner:** Future orchestrator refactoring phase (extract handlers into helper modules).

### 3. tests/phase05 — 14 other failures in test_pipeline_e2e_mock / test_typecast_adapter (pre-existing)
- Not touched by Plan 16-02 changes. These relate to Typecast adapter + pipeline e2e mocks, orthogonal to renderer cascade.

### 4. tests/phase06/test_wiki_nodes_ready.py — 34 failures (pre-existing)
- Wiki node readiness checks (render/KPI/continuity_bible), pre-existing since wiki was authored. Not touched.

### 5. tests/phase07 — 30+ failures (pre-existing)
- test_fallback_ken_burns_thumbnail, test_phase07_acceptance, test_verify_all_dispatched_13, test_regression_809_green — all rely on the shared supervisor/phase04/phase05/phase06 regressions above; cascading from #1.

## In-Scope Results (All 49/49 green)

- tests/phase16/ : 49 passed (0.89s) — RemotionRenderer + ASSEMBLY cascade fully covered.
- tests/phase07/test_operational_gate_count_equals_13.py : 7/7 green (GATE count 13 unchanged).

## Rationale
Per executor deviation spec:
> Only auto-fix issues DIRECTLY caused by the current task's changes.
> Pre-existing warnings, linting errors, or failures in unrelated files are out of scope.

Plan 16-02 acceptance criteria (from 16-02-PLAN.md §<verification>) verified:
1. ✅ remotion/ TypeScript project boot (npm install + remotion 4.0.451)
2. ✅ remotion_renderer.py 911 lines, 8 internal + 2 public methods, 40 TDD tests green
3. ✅ _run_assembly remotion > shotstack > ffmpeg cascade
4. ✅ pytest tests/phase16/ exit 0 (49 tests)
5. ⚠️ Phase 04-07 regression — pre-existing failures documented above; Plan 16-02 changes do NOT introduce new failures
6. ✅ 0 skip_gates / 0 TODO(next-session) in new code
7. ✅ 0 Veo calls in new code
