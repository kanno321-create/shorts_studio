# Phase 7 REQ Traceability Matrix

**Generated:** 2026-04-19 (Plan 07-08 Wave 5 phase gate)
**Coverage:** 5/5 Phase 7 requirements mapped to at least one passing test.
**Source of truth:** `.planning/REQUIREMENTS.md` §TEST (TEST-01..04) + §AUDIT
(AUDIT-02 cross-cutting) + `tests/phase07/` actual file inventory.

Every REQ ID from the Phase 7 scope appears below with at least one passing
test file and at least one acceptance SC. No orphans.

## Matrix

| REQ ID | Spec (short) | Primary Source File(s) | Primary Test File(s) | SC Acceptance |
|--------|--------------|-------------------------|----------------------|---------------|
| TEST-01 | E2E mock asset 파이프라인 1회 성공 ($0 비용) | scripts/orchestrator/shorts_pipeline.py + 5 api/*.py adapters + tests/phase07/mocks/*.py | tests/phase07/test_e2e_happy_path.py + tests/phase07/test_notebooklm_tier2_only.py | SC1 |
| TEST-02 | verify_all_dispatched() 13 operational gate lock (Correction 1 — NOT 17) | scripts/orchestrator/gate_guard.py:94-96,169-176 + scripts/orchestrator/gates.py + scripts/orchestrator/shorts_pipeline.py | tests/phase07/test_operational_gate_count_equals_13.py + test_verify_all_dispatched_13.py + test_gate_order_violation.py + test_checkpointer_atomic_writes_13.py | SC2 |
| TEST-03 | CircuitBreaker 3회 발동 + 300s cooldown (Correction 2 — CircuitBreakerOpenError, NOT *TriggerError) | scripts/orchestrator/circuit_breaker.py:57-72,108-150 | tests/phase07/test_circuit_breaker_3x_open.py + test_cooldown_300s_enforced.py | SC3 |
| TEST-04 | Fallback 정지 이미지 + 줌인 (Correction 3 — THUMBNAIL target, ken-burns standalone POST) | scripts/orchestrator/shorts_pipeline.py:576-655 + scripts/orchestrator/fallback.py:30-122 + scripts/orchestrator/api/shotstack.py:155-216 | tests/phase07/test_fallback_ken_burns_thumbnail.py + test_failures_append_on_retry_exceeded.py | SC4 |
| AUDIT-02 | harness-audit 점수 ≥ 80 + A급 drift 0 + SKILL 500줄 0 + JSON 6-key schema + agent_count + description ≤ 1024 | scripts/validate/harness_audit.py (Plan 07-01 extended with --json-out + Plan 07-07 scanner scope fix) | tests/phase07/test_harness_audit_json_schema.py + test_harness_audit_score_ge_80.py + test_skill_500_line_scan.py + test_a_rank_drift_zero.py + test_agent_count_invariant.py + test_description_1024_scan.py | SC5 |

**Coverage check:** 5/5 REQs mapped, all 5 SC covered, no orphans.

## Success Criteria -> Primary Tests

| SC  | Focus | REQs | Representative Tests |
|-----|-------|------|----------------------|
| SC1 | E2E mock $0 + NotebookLM tier 2 only | TEST-01 | test_e2e_happy_path.py (dispatched_count==13, final_gate==COMPLETE, fallback_count==0, 14 checkpoint files, Korean cp949 round-trip) + test_notebooklm_tier2_only.py (reduced chain, tier_used==0, canonical D-10 markers) |
| SC2 | verify_all_dispatched 13 operational gates | TEST-02 | test_operational_gate_count_equals_13.py (triple-lock ==13 AND !=17 AND !=12) + test_verify_all_dispatched_13.py (0/12/13 -> False/False/True, IncompleteDispatch on 12) + test_gate_order_violation.py (GateDependencyUnsatisfied) + test_checkpointer_atomic_writes_13.py (exactly 14 gate_NN.json, atomic os.replace) |
| SC3 | CircuitBreaker 5-min cooldown | TEST-03 | test_circuit_breaker_3x_open.py (3x RuntimeError -> OPEN, CircuitBreakerOpenError subclasses RuntimeError, split-literal hasattr anti-regression for Correction 2) + test_cooldown_300s_enforced.py (strict > boundary at 0/299/300/300.001, HALF_OPEN probe success/fail) |
| SC4 | Fallback ken-burns no CIRCUIT_OPEN | TEST-04 | test_fallback_ken_burns_thumbnail.py (fallback_count==1, dispatched_count==13, retry_counts[THUMBNAIL]==3, AST anchor for Correction 3) + test_failures_append_on_retry_exceeded.py (append-only format, Hook bypass-by-naming, structural fallback.py open('a')) |
| SC5 | harness-audit ≥ 80 + drift 0 + SKILL ≤ 500 lines | AUDIT-02 | 6 Plan 07-07 test files — JSON schema (D-11) + score ≥ 80 gate (3 angles) + SKILL 500-line double-entry + A-rank drift zero (post-scanner-fix) + agent_count==33 filesystem invariant + description ≤ 1024 double-entry |

All 5 SC green in `scripts/validate/phase07_acceptance.py` as of 2026-04-19.

## Research Corrections Honored

Phase 7 RESEARCH identified 3 critical falsifications in the original
07-CONTEXT.md. Each is anchored by a Phase 7 test such that silent drift
back to the incorrect form fails loudly.

| # | CONTEXT assertion | Actual code | Phase 7 test anchor | Commit |
|---|-------------------|--------------|---------------------|--------|
| Correction 1 | "17 GATE = 12 + 5 sub-gate" | `_OPERATIONAL_GATES` frozenset size == 13 (gate_guard.py:94-96) | test_operational_gate_count_equals_13.py (triple-lock ==13 AND !=17 AND !=12 + GATE_INSPECTORS cross-validation) | studio@20cdf47 |
| Correction 2 | `CircuitBreakerTriggerError` | `CircuitBreakerOpenError` (circuit_breaker.py:57-72) | test_circuit_breaker_3x_open.py::test_circuit_breaker_trigger_error_does_NOT_exist (split-literal hasattr check) | studio@36324a0 |
| Correction 3 | "ASSETS ken-burns via embedded filter" | THUMBNAIL via standalone Shotstack POST (shorts_pipeline.py:576-655 -> fallback.py:30-122 -> shotstack.py:155-216) | test_fallback_ken_burns_thumbnail.py::test_target_is_thumbnail_not_assets (AST-based anchor walking supervisor_side_effect closures) | studio@cbacaad |

## Enforcement Tests

Automation that guards this matrix from silent drift:

- `tests/phase07/test_traceability_matrix.py` — asserts every REQ in
  `PHASE7_REQS` has at least one test file whose stem matches a registered
  marker; fails if a new REQ is added without test coverage or a test file
  is renamed without updating the marker map. Also asserts the 3 Research
  Correction markers are acknowledged in this matrix.
- `tests/phase07/test_phase07_acceptance.py` — asserts
  `scripts/validate/phase07_acceptance.py` exits 0 with all 5 SC labels
  PASS; closes the SC loop.
- `tests/phase07/test_regression_809_green.py` — D-23 regression invariant:
  Phase 4 + 5 + 6 baseline (809) preserved end-to-end.

## Plan -> REQ -> Commit Audit Trail

| Plan | Wave | Primary REQs Addressed | Key Commits |
|------|------|------------------------|-------------|
| 07-01 | W0 | TEST-01 scaffold, AUDIT-02 (--json-out extension) | eca0bfe, c6044d3, 8a88cbc, 3f1fd4f |
| 07-02 | W1 | TEST-01 (5 mock adapters) | b99c89d, 5de71ad, eda1fa9, 4aaf359, f32a66e, 6a820b0, 8edc604, e6c9473, c053d6a, 9959e69 |
| 07-03 | W2a | TEST-01 (E2E + NotebookLM tier 2) | 73847dd, 405febb, 38bb829 |
| 07-04 | W2b | TEST-02 (13-gate invariant + Correction 1 anchor) | 20cdf47, 371ce1e, 85e7e2b, 496056f |
| 07-05 | W3a | TEST-03 (CircuitBreaker + Correction 2 anchor) | 36324a0, 95801cb |
| 07-06 | W3b | TEST-04 (Fallback ken-burns + Correction 3 anchor) | cbacaad, 31ccfb3 |
| 07-07 | W4 | AUDIT-02 (6-dimension gate + scanner scope fix) | ff0f8dd, 76e1d1f, cda47ab, af60939, 7a8f7f8, a738fd7, fd7a568 |
| 07-08 | W5 | Phase gate (5-REQ traceability + acceptance E2E + VALIDATION flip) | <this plan's hashes> |

## Plan Summary

| Plan | Tasks | Artifacts | Gate |
|------|-------|-----------|------|
| 07-01 | 3 | tests/phase07/ scaffold + conftest + 6 fixtures + harness_audit --json-out | Wave 0 |
| 07-02 | 5 | 5 deterministic mock adapters (Kling/Runway/Typecast/ElevenLabs/Shotstack) | Wave 1 |
| 07-03 | 2 | E2E happy path + NotebookLM tier-2-only | Wave 2a |
| 07-04 | 4 | 13-gate invariant + verify_all_dispatched + DAG + checkpointer 14 files | Wave 2b |
| 07-05 | 2 | CircuitBreaker 3× open + 300s strict > cooldown | Wave 3a |
| 07-06 | 2 | Fallback ken-burns THUMBNAIL + FAILURES append-only | Wave 3b |
| 07-07 | 6 | harness-audit 6-dimension gate (JSON, score, SKILL, drift, agents, desc) | Wave 4 |
| 07-08 | 3 | phase07_acceptance.py + 3 gate tests + 07-TRACEABILITY.md + 07-VALIDATION.md flip | Wave 5 gate |

**Totals:** 8 plans, 27 tasks, 159+3 = 162 Phase 7 tests, 3 Research Corrections anchored, 809/809 regression preserved.

Phase 7 status: shippable when all listed tests are green.

---

*Generated: 2026-04-19 (Plan 07-08 Wave 5 — Phase 7 final verification)*
