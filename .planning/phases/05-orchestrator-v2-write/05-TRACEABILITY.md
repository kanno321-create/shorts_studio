# Phase 5 REQ Traceability Matrix

**Generated:** 2026-04-19 (Plan 05-10 Wave 7 final verification)
**Coverage:** 17/17 Phase 5 requirements mapped to at least one passing test.
**Source of truth:** `.planning/REQUIREMENTS.md` Phase 5 section + `tests/phase05/` actual file inventory.

Every REQ ID from REQUIREMENTS.md Phase 5 section appears in at least one row with a passing test file. No orphans.

## REQ -> Source + Test Mapping

| REQ ID | Spec (short) | Source File(s) | Test File(s) | Acceptance |
|--------|--------------|-----------------|---------------|------------|
| ORCH-01 | 500-800 line state machine | scripts/orchestrator/shorts_pipeline.py | tests/phase05/test_line_count.py, tests/phase05/test_shorts_pipeline.py | SC 1 |
| ORCH-02 | 12 GATE enum + transitions | scripts/orchestrator/gates.py, scripts/orchestrator/shorts_pipeline.py | tests/phase05/test_gate_enum.py, tests/phase05/test_dag_declaration.py, tests/phase05/test_shorts_pipeline.py | SC 1 partial |
| ORCH-03 | GateGuard.dispatch raises on FAIL | scripts/orchestrator/gate_guard.py, scripts/orchestrator/gates.py (exceptions) | tests/phase05/test_gate_guard.py, tests/phase05/test_exceptions.py | SC 3 |
| ORCH-04 | verify_all_dispatched = COMPLETE gate | scripts/orchestrator/gate_guard.py, scripts/orchestrator/shorts_pipeline.py | tests/phase05/test_verify_all_dispatched.py, tests/phase05/test_shorts_pipeline.py | SC 3 |
| ORCH-05 | Checkpointer atomic JSON round-trip | scripts/orchestrator/checkpointer.py | tests/phase05/test_checkpointer_roundtrip.py, tests/phase05/test_checkpointer_resume.py | SC 3 adjacent |
| ORCH-06 | CircuitBreaker 3 failures / 300s cooldown | scripts/orchestrator/circuit_breaker.py | tests/phase05/test_circuit_breaker.py, tests/phase05/test_circuit_breaker_cooldown.py | SC 4 |
| ORCH-07 | DAG depends_on + ensure_dependencies | scripts/orchestrator/gates.py, scripts/orchestrator/gate_guard.py | tests/phase05/test_dag_declaration.py, tests/phase05/test_gate_guard.py | SC 1 partial |
| ORCH-08 | skip_gates regex block + physical absence | .claude/deprecated_patterns.json, scripts/orchestrator/** | tests/phase05/test_deprecated_patterns_json.py, tests/phase05/test_hook_skip_gates_block.py, tests/phase05/test_blacklist_grep.py | SC 2 |
| ORCH-09 | TODO(next-session) regex block | .claude/deprecated_patterns.json | tests/phase05/test_deprecated_patterns_json.py, tests/phase05/test_hook_todo_next_session_block.py, tests/phase05/test_blacklist_grep.py | SC 2 adjacent |
| ORCH-10 | Voice-first timeline (Typecast -> video align) | scripts/orchestrator/voice_first_timeline.py, scripts/orchestrator/shorts_pipeline.py, scripts/orchestrator/api/typecast.py, scripts/orchestrator/api/elevenlabs.py | tests/phase05/test_voice_first_timeline.py, tests/phase05/test_shorts_pipeline.py, tests/phase05/test_typecast_adapter.py, tests/phase05/test_elevenlabs_adapter.py | SC 6 |
| ORCH-11 | Low-Res First 720p -> AI upscale | scripts/orchestrator/api/shotstack.py, scripts/orchestrator/shorts_pipeline.py | tests/phase05/test_low_res_first.py, tests/phase05/test_shotstack_adapter.py, tests/phase05/test_shorts_pipeline.py | SC 6 |
| ORCH-12 | Regen 3 -> Fallback shot + FAILURES append | scripts/orchestrator/shorts_pipeline.py, scripts/orchestrator/fallback.py | tests/phase05/test_fallback_shot.py, tests/phase05/test_shorts_pipeline.py | SC 4 |
| VIDEO-01 | T2V absent; I2V + Anchor Frame only | scripts/orchestrator/api/kling_i2v.py, scripts/orchestrator/api/runway_i2v.py, scripts/orchestrator/api/models.py | tests/phase05/test_kling_adapter.py, tests/phase05/test_hook_t2v_block.py, tests/phase05/test_blacklist_grep.py, tests/phase05/test_hook_allows_i2v.py | SC 5 |
| VIDEO-02 | 4-8s clips + 1 Move Rule | scripts/orchestrator/api/models.py, scripts/orchestrator/voice_first_timeline.py | tests/phase05/test_i2v_request_schema.py, tests/phase05/test_voice_first_timeline.py | SC 5 partial |
| VIDEO-03 | Transition shots (close-up / silhouette / bg) | scripts/orchestrator/voice_first_timeline.py | tests/phase05/test_transition_shots.py, tests/phase05/test_voice_first_timeline.py | SC 6 partial |
| VIDEO-04 | Kling 2.6 Pro primary, Runway Gen-3 backup | scripts/orchestrator/api/kling_i2v.py, scripts/orchestrator/api/runway_i2v.py | tests/phase05/test_kling_runway_failover.py, tests/phase05/test_kling_adapter.py | SC 5 |
| VIDEO-05 | Shotstack color grade + filter order (grade -> sat -> grain) | scripts/orchestrator/api/shotstack.py | tests/phase05/test_shotstack_adapter.py | SC 6 partial |

**Coverage check:** 17 / 17 REQs mapped with at least one dedicated test file each. No orphans.

## Success Criteria -> REQ -> Test Aggregation

| SC  | Focus | REQs | Representative Tests |
|-----|-------|------|----------------------|
| SC 1 | 500-800 lines + 12 GATE enum | ORCH-01, ORCH-02, ORCH-07 | tests/phase05/test_line_count.py, test_gate_enum.py, test_dag_declaration.py |
| SC 2 | skip_gates 0 + Hook block | ORCH-08, ORCH-09 | tests/phase05/test_blacklist_grep.py, test_hook_skip_gates_block.py, test_hook_todo_next_session_block.py |
| SC 3 | GateGuard.dispatch + verify_all_dispatched | ORCH-03, ORCH-04, ORCH-05 | tests/phase05/test_gate_guard.py, test_verify_all_dispatched.py, test_checkpointer_roundtrip.py |
| SC 4 | CircuitBreaker + regen + Fallback | ORCH-06, ORCH-12 | tests/phase05/test_circuit_breaker.py, test_circuit_breaker_cooldown.py, test_fallback_shot.py |
| SC 5 | Kling -> Runway + no T2V | VIDEO-01, VIDEO-04 | tests/phase05/test_kling_runway_failover.py, test_blacklist_grep.py, test_hook_t2v_block.py |
| SC 6 | Voice-first + 720p Low-Res First | ORCH-10, ORCH-11 | tests/phase05/test_voice_first_timeline.py, test_low_res_first.py, test_shotstack_adapter.py |

All 6 SC green in `scripts/validate/phase05_acceptance.py` as of 2026-04-19.

## Enforcement Tests

Automation that guards this matrix from silent drift:

- `tests/phase05/test_traceability_matrix.py` — asserts every REQ in `PHASE5_REQS` list has at least one test file whose stem matches a registered marker; fails if a new REQ is added without test coverage or a test file is renamed without updating the marker map.
- `tests/phase05/test_phase05_acceptance.py` — asserts `scripts/validate/phase05_acceptance.py` exits 0 with all 6 SC labels PASS; closes the SC loop.
- `tests/phase05/test_blacklist_grep.py` + `test_line_count.py` — contract tests covering SC 1 / 2 / 5 at the source level (no interpretation — direct filesystem assertions).

## Plan -> REQ -> Commit Audit Trail

| Plan | Wave | Primary REQs Addressed | Key Commits |
|------|------|------------------------|-------------|
| 05-01 | W1 | ORCH-02, ORCH-03, ORCH-07, ORCH-08, ORCH-09 | a3e9476, 8c19c23, cf9874d, 2fea858, eebfe32 |
| 05-02 | W2 | ORCH-06 | 8fd0dce, 3c73cdc, f2b42b1, c13c219, 5ee9c19 |
| 05-03 | W2 | ORCH-05 | 1ea14f9, cd9e861, 2135745 |
| 05-04 | W2 | ORCH-03, ORCH-04, ORCH-07 | 3c74d40, b3454e7, 8380421 |
| 05-05 | W3 | ORCH-10, VIDEO-02, VIDEO-03 | 5d9ab61, 7375d8c, 2a4cd49 |
| 05-06 | W4 | VIDEO-01, VIDEO-02, VIDEO-04, VIDEO-05, ORCH-10, ORCH-11 | 2169c4c, d1deecc, 51eb449, bf9f728, ce8f4fe |
| 05-07 | W5 | ORCH-01, ORCH-02, ORCH-11, ORCH-12 | 5849ee1, 031c4ba, 7653492, 16303f4 |
| 05-08 | W6 | ORCH-01 (regression) | 92b2b33, d4ad6f8, 6b3f744 |
| 05-09 | W6 | ORCH-08, ORCH-09, VIDEO-01 (Hook regression) | df4dac3, a9b313d, 0636120, 690a58a, 259c5d1, 9c7d266 |
| 05-10 | W7 | all 17 REQs (verification) | see Plan 10 SUMMARY |

## Phase 5 Status

- **Plans completed:** 10 / 10 (01..10)
- **Source files created:** scripts/orchestrator/ package (shorts_pipeline.py 787 lines + 6 support modules: gates, circuit_breaker, checkpointer, gate_guard, voice_first_timeline, fallback + api/ subpackage of 6 adapters: models, kling_i2v, runway_i2v, typecast, elevenlabs, shotstack) + scripts/hc_checks/ rewrite (1176 lines, 13 public signatures preserved) + .claude/deprecated_patterns.json (6 regex entries) + 3 scripts/validate/ CLIs (verify_line_count, verify_hook_blocks, phase05_acceptance)
- **Tests green:** 313+ in tests/phase05/ as of Plan 10 completion (Wave 5 baseline 224 + Plan 08 regression 41 + Plan 09 Hook 31 + Plan 10 verification 33 = 329 expected)
- **SC 1-6:** All PASS (`python scripts/validate/phase05_acceptance.py` exits 0)
- **REQ coverage:** 17 / 17 marked complete in REQUIREMENTS.md

## Out-of-Scope Deferred Items

Logged in `deferred-items.md` in this phase directory. Does not block Phase 5 completion:

- **AF-8 submodule selenium regex gap** (Plan 09) — `from selenium.webdriver import Chrome` currently allowed by Hook. Pinned in `tests/phase05/test_hook_selenium_block.py::test_from_selenium_submodule_allowed`. Proposed future-tightening regex documented. Out of Plan 05-09 scope (plan forbade deprecated_patterns.json edits).

## Closing Statement

Phase 5 converts the Phase 4 agent catalog + Phase 3 harvested assets into a runnable Python state machine. By Plan 10 Wave 7 completion:

- The 5166-line drift baseline of shorts_naberal is structurally prevented (SC 1 enforces 500-800 lines + Hook blocks forbidden keywords)
- The "skip_gates escape hatch" antipattern is physically absent from the codebase and rejected by the Hook before it can land
- The T2V temptation is blocked at three layers: source grep, runtime sentinel class (`T2VForbidden`), and Hook regex
- Every GATE dispatch is tested, every Circuit breaker state transition is tested, every API adapter has unit tests, and every regeneration-loop fallback path is tested

**Phase 5 is shippable.** Next: `/gsd:verify-work 05` then `/gsd:plan-phase 6` (Wiki + NotebookLM + FAILURES Reservoir).
