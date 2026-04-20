---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 03
subsystem: orchestrator
tags: [python, adapter, graceful-degrade, argparse, datetime, pipeline, circuit-breaker]

# Dependency graph
requires:
  - phase: 09.1-production-engine-wiring
    provides: shotstack/nanobanana/ken_burns graceful-degrade pattern (verbatim template for Phase 11)
  - phase: 10-sustained-operations
    provides: v1.0.1 milestone lock + D10-PIPELINE-DEF-01 defect chain identification
provides:
  - "_try_adapter helper inside ShortsPipeline.__init__ unifying 7 adapter instantiations"
  - "Kling/Runway/Typecast/ElevenLabs adapters now graceful-degrade on missing env (D-05 동일 패턴)"
  - "--session-id argparse optional with auto-timestamp default (D-16)"
  - "Line budget -2 (796 → 794) well under 800-line soft cap"
affects: [11-04-wrapper-cmd-ps1, 11-06-full-smoke-script-decision, 12-script-quality-mode]

# Tech tracking
tech-stack:
  added: ["from datetime import datetime"]
  patterns:
    - "_try_adapter(name, build, injected, hint) — uniform try/except/logger.warning/return-injected guard"
    - "args.session_id or datetime.now().strftime('%Y%m%d_%H%M%S') — argparse nullable + module-default composition"

key-files:
  created:
    - tests/phase11/test_adapter_graceful_degrade.py
    - tests/phase11/test_argparse_session_id.py
  modified:
    - scripts/orchestrator/shorts_pipeline.py

key-decisions:
  - "D-05 pipeline-site unification via inner helper (NOT adapter registry refactor — 5+ file blast radius deferred to Phase 12+)"
  - "D-06 adapter internals untouched: scripts/orchestrator/api/*.py clean; eager ValueError preserved in each adapter __init__"
  - "D-16 argparse required=False + module-level datetime default (not argparse default callable) — preserves tests' ability to patch datetime if needed"
  - "One-liner _try_adapter calls formatted as aligned column block for D-05 '동일 패턴' visual clarity"

patterns-established:
  - "Inner helper closure: define _try_adapter inside __init__ so it captures self via enclosing scope without class-level clutter"
  - "Unified exception tuple (ValueError, KenBurnsUnavailable) in single except clause — adapter family shares degrade semantics despite different raise types"
  - "Nullable argparse + module-level fallback: args.X or datetime.now()... composes cleanly vs argparse default=lambda which runs at parse-time and is harder to test"

requirements-completed: [PIPELINE-03, PIPELINE-04]

# Metrics
duration: 5min
completed: 2026-04-20
---

# Phase 11 Plan 03: Adapter Graceful Degrade Summary

**_try_adapter helper unifies 7 adapter instantiations (Kling/Runway/Typecast/ElevenLabs/Shotstack/NanoBanana/KenBurns) at pipeline-site + --session-id auto-timestamp default (D-05 + D-16 landed, net -2 lines, 794/800)**

## Performance

- **Duration:** 5min
- **Started:** 2026-04-20T17:57:14Z
- **Completed:** 2026-04-20T18:02:29Z
- **Tasks:** 2
- **Files modified:** 3 (1 modified + 2 created)

## Accomplishments

- Replaced 27-line mixed block (4 bare + 3 try/except) with 21-line `_try_adapter` helper + 7 aligned one-liner calls
- Kling/Runway/Typecast/ElevenLabs now graceful-degrade on missing API key — no longer blocks `ShortsPipeline.__init__` (D10-PIPELINE-DEF-01 errors #3 + #4 resolved)
- `--session-id` relaxed from `required=True` to optional with `YYYYMMDD_HHMMSS` auto-default — unblocks Plan 11-04 wrapper double-click UX
- 8 new tests locked (5 graceful-degrade + 3 argparse session-id), all GREEN
- Adapter internals (`scripts/orchestrator/api/*.py`) UNTOUCHED — D-06 regression protection honored

## Task Commits

Each task was committed atomically (parallel wave, --no-verify):

1. **Task 1: 8 RED tests (5 graceful-degrade + 3 argparse)** — `e78c3c5` (test)
2. **Task 2: _try_adapter helper + 7 unified calls + argparse relax** — `81ff924` (feat)

## Files Created/Modified

- `scripts/orchestrator/shorts_pipeline.py` — +1 datetime import, replaced L209-235 adapter block (27 → 21 lines), replaced argparse `--session-id` single-line + added `session_id = args.session_id or datetime.now().strftime(...)` composition. Net delta: -2 lines (796 → 794)
- `tests/phase11/test_adapter_graceful_degrade.py` — 5 tests covering missing env for kling/runway/typecast/elevenlabs individually + one all-missing integration test (new, 128 lines)
- `tests/phase11/test_argparse_session_id.py` — 3 tests: optional flag, auto-timestamp format `r'^\d{8}_\d{6}$'`, explicit override preserved (new, 66 lines)

## Line-Count Verification

```
python -c "print(sum(1 for _ in open('scripts/orchestrator/shorts_pipeline.py', encoding='utf-8')))"
→ 794
```

Within soft cap (≤ 800), target (-2) achieved exactly per §Line Budget.

## Grep Acceptance

```
grep -cn "def _try_adapter" scripts/orchestrator/shorts_pipeline.py                → 1
grep -c "_try_adapter(" scripts/orchestrator/shorts_pipeline.py                     → 8 (1 def + 7 calls)
grep -n "required=False" scripts/orchestrator/shorts_pipeline.py                    → 1 match (L744)
grep -n "args.session_id or datetime" scripts/orchestrator/shorts_pipeline.py       → 1 match (L763)
grep -n "except (ValueError, KenBurnsUnavailable)" scripts/orchestrator/shorts_pipeline.py → 1 match (L218)
git status scripts/orchestrator/api/                                                 → clean (D-06 satisfied)
```

## Test Results

- `pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -v` → **8/8 PASSED** (0.84s)
- `pytest tests/phase04/ -q` → **244/244 PASSED** (0.41s — baseline preserved)
- `pytest tests/phase05/test_line_count.py::test_shorts_pipeline_in_500_800 -v` → **PASSED** (shorts_pipeline soft-cap green)

## Decisions Made

- **Inner helper scope (not module-level):** `_try_adapter` defined inside `ShortsPipeline.__init__` to keep the helper co-located with its sole call site and avoid polluting module namespace. Zero class-attribute surface change.
- **Exception tuple unified:** Single `except (ValueError, KenBurnsUnavailable)` clause (helper body) replaces 3 separate try/except blocks (1 ValueError for shotstack, 1 for nanobanana, 1 KenBurnsUnavailable for ken_burns). Semantically identical (each adapter only raises one of the two), but expressed once.
- **Aligned column format for 7 one-liners:** Plan prose allowed single-line or multi-line; chose single-line aligned for verbal D-05 "동일 패턴" reinforcement. Each call reads as `self.X = X_adapter or _try_adapter("X", lambda: XAdapter(circuit_breaker=self.X_breaker), X_adapter, "ENV 없음")` with spaces aligning the four fields.
- **Module-level datetime composition:** `session_id = args.session_id or datetime.now().strftime(...)` instead of argparse `default=lambda: datetime.now()...` — the latter runs default at parse-time (less controllable) and doesn't compose as cleanly with `or` idiom.

## Deviations from Plan

None — plan executed exactly as written (helper + 7 calls + argparse relax per §Line Budget Pattern 3 verbatim). Tests seeded per plan prose, impl per RESEARCH §Pattern 3 lines 655-688.

## Issues Encountered

**Pre-existing Phase 5 failures (out of scope, D-06 boundary):**
- `tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps` — `elevenlabs.py` (350 > 340) + `shotstack.py` (414 > 400). Verified pre-existing by stashing Plan 11-03 changes and re-running — same failure persists. D-06 mandates adapter internals untouched; these caps predate Phase 11.
- `tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator` — pre-existing
- `tests/phase05/test_kling_adapter.py::test_runway_valid_call_returns_path` — pre-existing (`gen4.5` vs `gen3_alpha_turbo` regression from upstream adapter changes)
- `tests/phase05/test_phase05_acceptance.py::*` — 3 E2E wrappers fail transitively due to above

All failures occur identically with Plan 11-03 changes stashed. No new regression introduced.

## User Setup Required

None — no new env vars, no external service configuration. Existing adapter env vars (KLING_API_KEY, RUNWAY_API_KEY, TYPECAST_API_KEY, ELEVENLABS_API_KEY, SHOTSTACK_API_KEY, GOOGLE_API_KEY, FAL_KEY) remain the same; only their presence is now optional for construction, not for dispatch.

## Next Phase Readiness

- **Plan 11-04 wrapper (.cmd/.ps1)** — UNBLOCKED. `--session-id` is now optional so wrapper can invoke `py -3.11 -m scripts.orchestrator.shorts_pipeline` without injecting a session-id; Python will auto-generate. Wrapper still may inject explicit session-id for log-traceability (override path preserved by Test 3 `test_explicit_session_id_override`).
- **Plan 11-06 full smoke** — UNBLOCKED. `ShortsPipeline()` now constructs even with partial env; smoke can exercise whichever adapters have live keys and log warnings for the others.
- **D-05 compliance locked** — all 7 adapters share identical `_try_adapter(...)` semantics; log shape `"[pipeline] %s adapter 미초기화 (대표님 — %s): %s"` verbatim for every adapter.
- **D-06 regression protection** — zero changes to `scripts/orchestrator/api/*.py`; Phase 4/5/7 adapter unit tests unaffected.

## Self-Check: PASSED

- `tests/phase11/test_adapter_graceful_degrade.py` — FOUND
- `tests/phase11/test_argparse_session_id.py` — FOUND
- Commit `e78c3c5` (test) — FOUND in git log
- Commit `81ff924` (feat) — FOUND in git log
- `scripts/orchestrator/shorts_pipeline.py` line count = 794 ≤ 800 — VERIFIED
- `scripts/orchestrator/api/` git clean — VERIFIED (D-06)
- All 8 Phase 11 tests GREEN — VERIFIED
- 244/244 Phase 4 baseline preserved — VERIFIED

---
*Phase: 11-pipeline-real-run-activation-script-quality-mode*
*Completed: 2026-04-20*
