# Phase 10 Deferred Items

> Out-of-scope discoveries during plan execution. Each entry includes the plan
> that discovered it, the scope boundary reasoning, and the proposed owner.

## D10-01-DEF-01 — Phase 5/6 pre-existing regressions (inherited)

**Discovered during:** Plan 10-01 (skill_patch_counter) regression sweep 2026-04-20.

**Failures:**
- `tests/phase05/test_kling_adapter.py::test_runway_valid_call_returns_path` — expects `gen3_alpha_turbo`, actual adapter emits `gen4.5` (Phase 9.1 stack migration `ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)`).
- `tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator` — related stack migration artifact.
- `tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps` — adapter line-count soft cap touched by Phase 9.1 rewrites.
- `tests/phase05/test_phase05_acceptance.py::*` — acceptance wrapper inherits the above.
- `tests/phase06/test_phase06_acceptance.py::test_full_phase06_suite_green` — cascades from Phase 5 regression.
- `tests/phase06/test_phase06_acceptance.py::test_phase05_suite_still_green` — same cascade.
- `tests/phase06/test_moc_linkage.py::test_moc_frontmatter_unchanged_scaffold` — wiki frontmatter drift since Phase 6.
- `tests/phase06/test_notebooklm_wrapper.py::test_default_skill_path_is_the_2026_install` — NotebookLM skill path constant drift.

**Scope boundary:** None of these tests touch `scripts/audit/`, `tests/phase10/`, or `reports/`. They are cascades from prior Phase 9.1 stack migration (`gen4.5` rename, Kling 2.6 Pro primary, Veo 3.1 Fast fallback) + Plan 06-08 `deprecated_patterns.json` 6→8 expansion + parallel Plan 10-02 executor (drift_scan) running concurrently. Plan 10-01 changes `scripts/audit/skill_patch_counter.py` + `tests/phase10/` + `reports/.gitkeep` + `scripts/audit/__init__.py` + `tests/phase10/conftest.py` only — zero file overlap with any failing test path.

**Evidence preserved:**
- `git log --oneline -3 -- scripts/orchestrator/api/runway_i2v.py` → `ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)` is the upstream cause of gen3_alpha_turbo → gen4.5 rename.
- STATE.md Session #19 entry: "2 Phase 5 regression failures attributable to Plan 06-08 scope (deprecated_patterns.json count 6->8) — out-of-boundary, logged for 06-08 follow-up."

**Proposed owner:** Phase 9.1 follow-up ticket or a dedicated `phase-regression-cleanup` plan after Phase 10 completion. Not Plan 10-01.

**Plan 10-01 in-scope tests:** `tests/phase10/` 11/11 GREEN (3 fixture + 8 CLI behavioural). Confirmed via `pytest tests/phase10/test_skill_patch_counter.py -q`.

**Phase 4 regression:** 244/244 GREEN (clean baseline preserved — phase04 untouched by any Phase 5/6/9.1 drift).
