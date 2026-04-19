---
phase: 7
plan: 07-04
subsystem: integration-test / Wave 2b — 13-gate invariant lock
tags: [phase-7, wave-2, verify-all-dispatched, gate-deps, checkpointer, correction-1, D-4, D-5, D-6]
requirements: [TEST-02]
success_criteria: [SC2]
dependency_graph:
  requires:
    - "Plan 07-01 (Wave 0 conftest + _fake_env fixture)"
    - "Plan 07-02 (5 mock adapters under tests/phase07/mocks/)"
  provides:
    - "Anchor test against '17 GATE' misconception reappearing (RESEARCH Open Q2)"
    - "GateGuard.verify_all_dispatched 12→False / 13→True contract lock"
    - "_transition_to_complete IncompleteDispatch raise on 12 dispatches"
    - "GATE_DEPS DAG enforcement proof (ASSEMBLY, UPLOAD multi-parent edges)"
    - "Checkpointer 14-file atomic write invariant (13 operational + COMPLETE)"
  affects:
    - "Locks the 13-gate Correction 1 truth against future CONTEXT.md drift"
    - "Unblocks Plan 07-07 harness-audit + Plan 07-08 Phase 7 acceptance wrapper"
tech_stack:
  added: []
  patterns:
    - "Unit + integration split: GateGuard exercised directly AND via full ShortsPipeline.run()"
    - "AudioSegment-shape patch at pipeline.typecast.generate for E2E VOICE gate"
    - "sys.path insertion for tests/phase07/mocks/ imports (Wave 1 precedent)"
    - "Triple-lock anchor: == 13 AND != 17 AND != 12 in one test (anti-drift in both directions)"
key_files:
  created:
    - tests/phase07/test_operational_gate_count_equals_13.py
    - tests/phase07/test_verify_all_dispatched_13.py
    - tests/phase07/test_gate_order_violation.py
    - tests/phase07/test_checkpointer_atomic_writes_13.py
  modified:
    - .planning/phases/07-integration-test/07-VALIDATION.md  # rows 10-13 flipped
decisions:
  - "Correction 1 triple-lock: test_operational_gate_count_equals_13.py asserts == 13 AND != 17 AND != 12 in one test method, so a future drift in either direction trips loudly."
  - "Canonical exception name: GateDependencyUnsatisfied (gates.py:150), NOT GateOrderError (which was a plan prose label). Research Correction 2 anchored."
  - "Checkpoint file count contract: exactly 14 files (13 operational + COMPLETE written by _transition_to_complete at shorts_pipeline.py:674-688). Not 13. SUMMARY documents this for Plan 07-03 cross-check."
  - "E2E tests patch pipeline.typecast.generate with AudioSegment dataclass return (the Wave-1 TypecastMock returns dicts; the pipeline's _run_voice requires the dataclass shape). Plan 07-04 scope is the dispatch-count invariant, not audio plumbing."
  - "_OPERATIONAL_GATES frozenset is the primary canonical set; GATE_INSPECTORS is a redundant source-of-truth (13 keys). test_operational_gates_frozenset_matches_gate_inspectors pins the agreement so drifting one without the other is a loud failure."
metrics:
  duration: ~8 minutes
  completed_date: 2026-04-19
  tasks_completed: 4/4
  commits: 4
  files_created: 4
  test_count_added: 31  # 7 + 7 + 9 + 8
  regression_sweep: 911/911  # 809 baseline + 102 Phase 7 (01+02+04)
---

# Phase 7 Plan 07-04: 13-Gate Invariant Lock Summary

**One-liner:** Locks the "13 operational gates" truth (Correction 1) with a triple-assertion anchor test (`== 13` AND `!= 17` AND `!= 12`), proves `verify_all_dispatched()` is the COMPLETE precondition via unit + integration coverage, enforces `GATE_DEPS` DAG at dispatch time, and confirms exactly 14 atomic checkpoint files land on disk during an end-to-end mock run.

## Scope

Plan 07-04 is TEST-02 / SC2's critical anti-regression harness. It exists because the original 07-CONTEXT.md D-5 claimed "17 = 12 + 5 sub-gate" but the actual source (`scripts/orchestrator/gate_guard.py:94-96`) enforces **exactly 13** operational gates (`TREND..MONITOR`). RESEARCH §Critical CONTEXT.md Corrections #1 falsified the 17-number, and RESEARCH §Open Q2 recommended an explicit anchor test. Plan 07-04 delivers that anchor plus three supporting contract tests.

## Tasks Completed (4/4)

| Task      | Test file                                             | Tests | Commit    |
|-----------|-------------------------------------------------------|-------|-----------|
| 7-04-01   | `tests/phase07/test_operational_gate_count_equals_13.py` | 7     | `20cdf47` |
| 7-04-02   | `tests/phase07/test_verify_all_dispatched_13.py`      | 7     | `371ce1e` |
| 7-04-03   | `tests/phase07/test_gate_order_violation.py`          | 9     | `85e7e2b` |
| 7-04-04   | `tests/phase07/test_checkpointer_atomic_writes_13.py` | 8     | `496056f` |

**Total tests added:** 31. **All green.**

## Evidence

### Correction 1 Anchor (Task 7-04-01)

```text
$ python -c "from scripts.orchestrator.gate_guard import _OPERATIONAL_GATES; print(len(_OPERATIONAL_GATES))"
13

$ python -m pytest tests/phase07/test_operational_gate_count_equals_13.py -q --no-cov
7 passed in 0.12s
```

Canonical 13 gate names (IntEnum order): `TREND, NICHE, RESEARCH_NLM, BLUEPRINT, SCRIPT, POLISH, VOICE, ASSETS, ASSEMBLY, THUMBNAIL, METADATA, UPLOAD, MONITOR`.

### verify_all_dispatched Contract (Task 7-04-02)

Unit-level: 0 dispatches → False; 12 dispatches → False; 13 dispatches → True. MONITOR-only missing specifically also False. Integration-level: full `ShortsPipeline.run()` lands `dispatched_count == 13` + `final_gate == "COMPLETE"`. `_transition_to_complete` with 12 gates raises `IncompleteDispatch`.

### DAG Order Enforcement (Task 7-04-03)

`ASSEMBLY` without `VOICE` → `GateDependencyUnsatisfied`. Same for missing `ASSETS`. `UPLOAD` without `METADATA` or `THUMBNAIL` → same raise. Happy path (both parents dispatched) → no raise. `TREND` on an empty graph → no raise (IDLE is treated as satisfied by `gate_guard.py:188`).

Note on exception name: the plan prose used "GateOrderError" informally, but the canonical class is `GateDependencyUnsatisfied` (`gates.py:150`). Research Correction 2 already anchored this; Plan 07-04 follows the canonical name.

### Checkpointer Atomic Writes (Task 7-04-04)

```text
$ python -m pytest tests/phase07/test_checkpointer_atomic_writes_13.py -q --no-cov
8 passed in 0.26s
```

E2E produces **exactly 14 `gate_NN.json` files** (13 operational + COMPLETE written by `_transition_to_complete` at `shorts_pipeline.py:674-688`). Filenames are zero-padded (`gate_01.json..gate_14.json`). Every checkpoint carries the canonical D-5 schema (`_schema=1, session_id, gate, gate_index, timestamp, verdict, artifacts`). Timestamps are ISO-8601 UTC. No `.tmp` residue post-run (`os.replace` atomic guarantee held). `Checkpointer.resume()` returns 14 on clean finish. `dispatched_gates()` reconstructs the 13 operational names + `COMPLETE` from disk. Round-trip `json.loads/dumps` is stable.

## Regression Sweep

```text
$ python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov
911 passed in 71.74s
```

Baseline Phase 4 (244) + Phase 5 (329) + Phase 6 (236) = 809 preserved. Phase 7: 71 + 31 = 102 (Plan 07-01 Wave 0 + Plan 07-02 Wave 1 + Plan 07-04 Wave 2b).

## Deviations from Plan

### Rule 1 — Bug/correction: exception class name

**Found during:** Task 7-04-03 planning read-first of `gates.py`.
**Issue:** Plan 07-04 prose + CONTEXT D-4 said `GateOrderError`, but there is no such class. The canonical exception is `GateDependencyUnsatisfied` (already documented in Research Correction 2).
**Fix:** Wrote tests against `GateDependencyUnsatisfied` instead. This is the same decision Plan 07-04's own `<interfaces>` block made ("Exception names (verbatim — NOT CircuitBreakerTriggerError)"), so it was in-scope.
**Files modified:** `tests/phase07/test_gate_order_violation.py`.
**Commit:** `85e7e2b`.

### Rule 1 — Bug: TypecastMock output shape mismatch

**Found during:** First attempt at Task 7-04-02's `test_e2e_complete_transition_allowed_exactly_at_13`.
**Issue:** Wave-1 `TypecastMock.generate` returns `list[dict]`, but the real pipeline's `_run_voice` (shorts_pipeline.py:427-429) iterates the result expecting `AudioSegment` dataclass instances with a `.path` attribute (`seg.path.as_posix()`). The mismatch manifested as `AttributeError: 'dict' object has no attribute 'path'` on the first E2E run.
**Fix:** Patched `pipeline.typecast.generate` inside the E2E test to return a single real `AudioSegment` (`scripts.orchestrator.AudioSegment`). Plan 07-04's scope is dispatch count; 07-03 owns audio/video plumbing.
**Alternatives considered:** (a) update `TypecastMock` to return `AudioSegment` objects — would affect Plan 07-03 + Plan 07-05 shared fixture. Deferred as a cross-plan decision. (b) Skip E2E entirely — rejected because TEST-02 demands the integration-level proof.
**Files modified:** `tests/phase07/test_verify_all_dispatched_13.py` (added `AudioSegment` import + `patch.object` context); same approach in `tests/phase07/test_checkpointer_atomic_writes_13.py`.
**No deferred-items.md entry** — the Wave-1 mock is fine for its own standalone adapter tests; the pipeline-level shape mismatch is a test-author concern handled inline.

## VALIDATION.md updates

Rows 10-13 flipped ❌ W0 → ✅ (+ pending → ✅ green):

- Row 10 (7-04-01): test_operational_gate_count_equals_13.py
- Row 11 (7-04-02): test_verify_all_dispatched_13.py
- Row 12 (7-04-03): test_gate_order_violation.py
- Row 13 (7-04-04): test_checkpointer_atomic_writes_13.py

## Known Stubs

None. All tests execute real code paths against real (non-mocked-away) orchestrator primitives. The five external API adapters are mocked per plan scope (D-1/D-2 zero-network requirement), and `VoiceFirstTimeline.align/insert_transition_shots` + `pipeline.typecast.generate` are patched to AudioSegment-returning stubs for the two pipeline E2E scenarios — these patches are scoped to 07-04 tests and do not leak.

## Self-Check: PASSED

- `tests/phase07/test_operational_gate_count_equals_13.py` — FOUND
- `tests/phase07/test_verify_all_dispatched_13.py` — FOUND
- `tests/phase07/test_gate_order_violation.py` — FOUND
- `tests/phase07/test_checkpointer_atomic_writes_13.py` — FOUND
- Commit `20cdf47` — FOUND
- Commit `371ce1e` — FOUND
- Commit `85e7e2b` — FOUND
- Commit `496056f` — FOUND
- Regression 911/911 — PASSED

---

*Plan 07-04 complete. Ready for Plan 07-05 (CircuitBreaker 3× fault injection) + Plan 07-06 (Fallback ken-burns) in Wave 3.*
