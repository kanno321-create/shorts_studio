---
phase: 5
slug: orchestrator-v2-write
status: passed
verified: 2026-04-19
reqs_verified: 17/17
sc_verified: 6/6
test_suite: 329/329 PASS
regression_phase04: 244/244 PASS
---

# Phase 5: Orchestrator v2 Write — Verification Report

**Phase Goal (from ROADMAP.md):**
`scripts/orchestrator/shorts_pipeline.py`를 500~800줄 state machine으로 작성하여 12 GATE DAG + CircuitBreaker + Checkpointer + 영상/음성 분리 합성 + Low-Res First 렌더 파이프라인을 완성하고, `skip_gates` 파라미터를 물리적으로 제거함으로써 shorts_naberal 5166줄 drift의 재발을 구조적으로 차단한다.

**Verified:** 2026-04-19
**Status:** passed
**Re-verification:** No — initial verification

---

## 1. Phase Goal Achievement

**Verdict: Goal delivered in full.**

The keystone artefact `scripts/orchestrator/shorts_pipeline.py` lands at **787 lines** — inside the mandatory [500, 800] structural window, *one sixth* of the shorts_naberal 5166-line drift baseline. All 12 operational GATEs (plus IDLE/COMPLETE book-ends = 15 states) are encoded as a `GateName` Python `Enum` with an explicit `GATE_DEPS` DAG declaration and a `GATE_ORDER` transition tuple.

The four structural protections ride inside this file:

1. **DAG enforcement** — `ensure_dependencies()` in `gate_guard.py` raises `GateDependencyUnsatisfied` when a successor is attempted before its predecessors dispatched.
2. **CircuitBreaker protection** — `circuit_breaker.py` implements `max_failures=3` / `cooldown_seconds=300` with CLOSED/OPEN/HALF_OPEN state transitions; each external API adapter wraps its calls in this breaker.
3. **Checkpointer** — atomic JSON round-trip to `state/{session_id}/gate_{n}.json`, enabling resume from the last-dispatched gate.
4. **Voice-first + Low-Res First rendering** — `VoiceFirstTimeline` enforces Typecast-first → audio-timestamp → video alignment; `IntegratedRenderForbidden` is raised if anyone attempts concurrent audio+video synthesis. Shotstack render defaults to `resolution="hd"` (720p) before upscale.

The keystone `skip_gates` anti-pattern is **physically absent** from the source tree (0 `grep` matches across `scripts/orchestrator/`) AND blocked at write-time by the `pre_tool_use.py` Hook consulting `.claude/deprecated_patterns.json` (regex `skip_gates\s*=`, verified by `verify_hook_blocks.py` as one of the 5 green enforcement checks).

Video stack wrapping (Kling 2.6 Pro primary → Runway Gen-3 Alpha Turbo fallback) is implemented as two sibling I2V adapters sharing the same `models.I2VRequest` contract, with `CircuitBreaker` governing the failover trigger.

---

## 2. Success Criteria Verification

| SC  | Focus                                               | Result | Evidence                                                                                                                                                                                                                       |
| --- | --------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `shorts_pipeline.py` 500~800줄 + 12 GATE enum + transitions | PASS   | `wc -l` → **787 lines**. `grep -c "class GateName" gates.py` → 1. `grep -c "_run_" shorts_pipeline.py` → 18 (13 GATE runners + helpers). `python scripts/validate/verify_line_count.py … 500 800` exits 0.             |
| 2   | `skip_gates` 0회 + Hook regex 차단                 | PASS   | `grep -r "skip_gates" scripts/orchestrator/` → **0 matches across 30 files**. `python scripts/validate/verify_hook_blocks.py` → "PASS: all 5 hook enforcement checks green" (4 deny + 1 allow).                               |
| 3   | `GateGuard.dispatch()` FAIL→raise + `verify_all_dispatched()` | PASS   | `grep -c "raise GateFailure\|raise MissingVerdict" gate_guard.py` → **2**. `grep -c "def verify_all_dispatched" gate_guard.py` → 1. `test_gate_guard.py` + `test_verify_all_dispatched.py` both green.                          |
| 4   | CircuitBreaker 3회/300초 + 재생성 3회 → Fallback   | PASS   | `circuit_breaker.py` line 93-94: `max_failures: int = 3`, `cooldown_seconds: int = 300`. `fallback.py` (141 lines) implements Ken-Burns still-image fallback. `test_fallback_shot.py` + `test_circuit_breaker_cooldown.py` green. |
| 5   | Kling→Runway failover + T2V 코드 경로 부재        | PASS   | `grep -riE "def (text_to_video\|t2v\|text2video)"` → **0 matches**. Remaining `t2v` tokens are all `T2VForbidden` sentinel class references (enforcement, not implementation). `test_kling_runway_failover.py` + `test_hook_t2v_block.py` green. `KlingI2V.generate(anchor_frame: Path \| None)` raises `T2VForbidden` when anchor is None (line 109-111). |
| 6   | 영상/음성 분리 + 720p Low-Res First               | PASS   | `grep -c "VoiceFirstTimeline\|voice_first_timeline" shorts_pipeline.py` → **6**. `grep -cE "resolution.*hd\|720p\|1280.*720"` → 4. `grep -c "IntegratedRenderForbidden" voice_first_timeline.py` → 6. `test_low_res_first.py` + `test_voice_first_timeline.py` green. |

**Top-level E2E acceptance:** `python scripts/validate/phase05_acceptance.py` → exit 0, all 6 SC reporting PASS.

---

## 3. Requirements Traceability (17/17)

| REQ ID  | Spec                                              | Covering Plan(s) | Source File(s)                                                              | Test Status | REQUIREMENTS.md |
| ------- | ------------------------------------------------- | ---------------- | --------------------------------------------------------------------------- | ----------- | --------------- |
| ORCH-01 | 500~800줄 state machine                           | 05-07, 05-08    | `shorts_pipeline.py` (787L), `hc_checks.py` (1176L)                        | green       | [x]             |
| ORCH-02 | 12 GATE enum + canonical transitions              | 05-01, 05-07, 05-10 | `gates.py`, `shorts_pipeline.py`                                            | green       | [x]             |
| ORCH-03 | GateGuard.dispatch raises on FAIL                 | 05-01, 05-04    | `gate_guard.py`, `gates.py` exceptions                                     | green       | [x]             |
| ORCH-04 | verify_all_dispatched → COMPLETE                  | 05-04           | `gate_guard.py`, `shorts_pipeline.py`                                      | green       | [x]             |
| ORCH-05 | Checkpointer atomic JSON round-trip                | 05-03           | `checkpointer.py`                                                           | green       | [x]             |
| ORCH-06 | CircuitBreaker 3/300s                              | 05-02           | `circuit_breaker.py`                                                        | green       | [x]             |
| ORCH-07 | DAG depends_on + ensure_dependencies               | 05-01, 05-04, 05-07 | `gates.py`, `gate_guard.py`                                                | green       | [x]             |
| ORCH-08 | skip_gates physical removal + Hook regex block    | 05-01, 05-09    | `deprecated_patterns.json`, `scripts/orchestrator/**`                       | green       | [x]             |
| ORCH-09 | TODO(next-session) Hook block                      | 05-01, 05-09    | `deprecated_patterns.json`, source tree                                    | green       | [x]             |
| ORCH-10 | Voice-first timeline (Typecast → video align)      | 05-05, 05-06    | `voice_first_timeline.py`, `api/typecast.py`, `api/elevenlabs.py`          | green       | [x]             |
| ORCH-11 | Low-Res First 720p → upscale                       | 05-06, 05-07    | `api/shotstack.py`, `shorts_pipeline.py`                                    | green       | [x]             |
| ORCH-12 | Regen 3 → Fallback shot + FAILURES append          | 05-07           | `shorts_pipeline.py`, `fallback.py`                                        | green       | [x]             |
| VIDEO-01| T2V absent; I2V + Anchor Frame only                | 05-06, 05-09    | `api/kling_i2v.py`, `api/runway_i2v.py`, `api/models.py`                   | green       | [x]             |
| VIDEO-02| 4~8s clips + 1 Move Rule                           | 05-05, 05-06    | `api/models.py`, `voice_first_timeline.py`                                 | green       | [x]             |
| VIDEO-03| Transition Shots (close-up/silhouette/bg)          | 05-05           | `voice_first_timeline.py`                                                  | green       | [x]             |
| VIDEO-04| Kling primary, Runway backup                       | 05-06           | `api/kling_i2v.py`, `api/runway_i2v.py`                                    | green       | [x]             |
| VIDEO-05| Shotstack color grade → saturation → grain         | 05-06           | `api/shotstack.py`                                                          | green       | [x]             |

**Orphan check:** REQUIREMENTS.md Phase 5 row claims 17 REQs (ORCH-01..12 + VIDEO-01..05). All 17 appear in at least one plan's `requirements_addressed` frontmatter. No orphans. All rows marked `[x]` in REQUIREMENTS.md (verified via grep).

**Traceability document:** `.planning/phases/05-orchestrator-v2-write/05-TRACEABILITY.md` exists with the full REQ → source → test mapping plus plan → commit audit trail.

---

## 4. Must-Haves Verification (aggregate across 10 plans)

Each plan's `requirements_addressed` frontmatter maps to concrete source files that were independently verified:

| Plan    | Wave | Must-Have                                           | Source Exists?                                                                      | Tests Green? |
| ------- | ---- | --------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------ |
| 05-01   | W1   | GateName enum, GATE_DEPS, exceptions, patterns JSON | `gates.py`, `.claude/deprecated_patterns.json` (6 regex)                           | 18 tests     |
| 05-02   | W2   | CircuitBreaker class + cooldown                     | `circuit_breaker.py` (215L)                                                         | 20 tests     |
| 05-03   | W2   | Checkpointer atomic JSON                            | `checkpointer.py` (233L)                                                            | 19 tests     |
| 05-04   | W2   | GateGuard.dispatch + verify_all_dispatched          | `gate_guard.py` (197L)                                                              | 23 tests     |
| 05-05   | W3   | VoiceFirstTimeline + transition shots               | `voice_first_timeline.py` (283L)                                                    | 33 tests     |
| 05-06   | W4   | 5 API adapters + models.py                          | `api/models.py` (122L), `kling_i2v.py` (212L), `runway_i2v.py` (196L), `typecast.py` (365L), `elevenlabs.py` (311L), `shotstack.py` (369L) | 87 tests     |
| 05-07   | W5   | shorts_pipeline.py keystone + fallback.py           | `shorts_pipeline.py` (787L), `fallback.py` (141L)                                   | 24 tests     |
| 05-08   | W6   | hc_checks rewrite (13+ signatures preserved)        | `scripts/hc_checks/hc_checks.py` (1176L)                                            | 41 tests     |
| 05-09   | W6   | Hook regression coverage (5 test files)             | Hook test suite under `tests/phase05/test_hook_*.py`                               | 31 tests     |
| 05-10   | W7   | SC 1-6 acceptance + TRACEABILITY + VALIDATION flip | `scripts/validate/phase05_acceptance.py`, `05-TRACEABILITY.md`, VALIDATION status=complete / nyquist_compliant=true | 33 tests     |

All 10 SUMMARY.md files exist. All 10 plans' claimed artefacts exist on disk with line counts matching the SUMMARY claims exactly.

---

## 5. Test Suite Health

**Phase 5 test results:** `python -m pytest tests/phase05/ -q --no-cov`
```
329 passed in 17.42s
```

Distribution across plan waves (as reported by SUMMARY aggregates + VALIDATION.md):
- Wave 1 (Plan 01 infra): 18 tests
- Wave 2 (Plans 02/03/04 parallel): 20 + 19 + 23 = 62 tests
- Wave 3 (Plan 05 voice-first): 33 tests
- Wave 4 (Plan 06 adapters): 87 tests
- Wave 5 (Plan 07 pipeline): 24 tests
- Wave 6 (Plans 08/09 parallel): 41 + 31 = 72 tests
- Wave 7 (Plan 10 verification): 33 tests
- **Total: 328 expected, 329 actual — +1 consistent with VALIDATION.md note of Wave 5 baseline 224 → adjusting for additional fixture/helper tests.**

**Regression gate:**
- Phase 4 (244 tests): `python -m pytest tests/phase04/ -q` → **244 passed in 0.39s** (no cross-phase regressions)
- Phase 3: no test directory found (Phase 3 was Harvest, no Python tests expected)

**Spot-check critical tests:**
Ran SC-critical subset (9 files, 78 tests): all green in 0.56s. Included `test_fallback_shot.py`, `test_kling_runway_failover.py`, `test_hook_t2v_block.py`, `test_verify_all_dispatched.py`, `test_gate_guard.py`, `test_low_res_first.py`, `test_voice_first_timeline.py`, `test_line_count.py`, `test_blacklist_grep.py`.

**Acceptance CLIs:**
- `python scripts/validate/verify_line_count.py scripts/orchestrator/shorts_pipeline.py 500 800` → exit 0 ("787 lines")
- `python scripts/validate/verify_hook_blocks.py` → exit 0 ("PASS: all 5 hook enforcement checks green")
- `python scripts/validate/phase05_acceptance.py` → exit 0, all 6 SC PASS

---

## 6. Structural Drift Check (the original Phase 5 mandate)

Phase 5's founding purpose is structural prevention of the shorts_naberal 5166-line `orchestrate.py` drift pattern. The following mechanisms are now in place:

| Defence Layer              | Mechanism                                                                 | Verified |
| -------------------------- | ------------------------------------------------------------------------- | -------- |
| **Line budget ceiling**    | `test_line_count.py` asserts `shorts_pipeline.py ∈ [500, 800]`            | 787 ✓    |
| **Line budget floor**      | Same test rejects pipelines under 500 lines (prevents over-extraction)    | 787 ≥ 500 ✓ |
| **skip_gates keyword**     | `grep -r "skip_gates" scripts/orchestrator/` = **0 matches**              | ✓        |
| **skip_gates write-block** | `pre_tool_use.py` → `deprecated_patterns.json` regex `skip_gates\s*=`     | ✓ (Hook verifier) |
| **TODO(next-session)**     | grep = 0 in `scripts/orchestrator/`, Hook regex blocks further writes    | ✓        |
| **T2V code path**          | No `def text_to_video` / `def t2v` / `def text2video` — only `T2VForbidden` sentinel | ✓        |
| **selenium imports**       | Hook regex `\bimport\s+selenium\b`; test_hook_selenium_block.py green    | ✓        |
| **segments[] legacy**      | Hook regex `segments\s*\[\s*\]`; not found in orchestrator               | ✓        |
| **try-except silence**     | Hook regex `try\s*:[^\n]*\n\s+pass\s*$` catches empty-pass silencers      | ✓        |

**Agent harness separation** (`shorts_studio/CLAUDE.md` mandate):
`shorts_pipeline.py` does NOT reimplement Inspector or Producer logic. Dependency injection pattern confirmed — the `ShortsPipeline` constructor takes `producer_invoker`, `supervisor_invoker`, `asset_sourcer_invoker` callables (lines 152-224). Production wiring (Task tool → Agent harness) is separate from pipeline logic. grep count for `producer_invoker|supervisor_invoker|asset_sourcer_invoker` patterns → 35 occurrences = heavy DI contact surface, no direct agent reimplementation.

---

## 7. Open Items (deferred, not blocking)

The following are documented in `deferred-items.md` as pre-existing gaps or out-of-scope discoveries:

1. **AF-8 selenium submodule regex gap** — Current regex catches `import selenium` and `from selenium import ...` but misses `from selenium.webdriver import Chrome`. Pinned by `test_hook_selenium_block.py::test_from_selenium_submodule_allowed`. Proposed tightened regex documented. Owner: Future Phase 5+ maintenance. Does NOT affect Phase 5 SCs — selenium imports into shorts_pipeline have been verified zero.

2. **720p → AI upscale visual quality** (ORCH-11 Manual-Only) — Shotstack upscale scope moved to Phase 8. Phase 5 verifies the code path (720p default render + upscale hook) but not the upscaled output quality.

3. **Real Kling 2.6 Pro API calls** (VIDEO-04 Manual-Only) — Requires live API keys + credits; deferred to Phase 7 (integration) + Phase 8 (production).

4. **Real Shotstack composite output** (ORCH-10 Manual-Only) — Large binary outputs; Phase 7 mock-asset E2E then Phase 8 live.

None of these block Phase 5 completion or compromise the structural guarantees just validated.

---

## 8. Non-Source Artefact Verification

- ✓ `05-TRACEABILITY.md` exists, all 17 REQs listed with at least one test file each
- ✓ `05-VALIDATION.md` frontmatter has `status: complete`, `nyquist_compliant: true`
- ✓ 10 SUMMARY.md files present (05-01 through 05-10)
- ✓ 10 PLAN.md files present with `requirements_addressed` frontmatter each
- ✓ `.claude/deprecated_patterns.json` contains 6 regex entries (skip_gates, TODO(next-session), T2V, segments[], selenium, try-except silence)
- ✓ `scripts/validate/` contains all 3 acceptance CLIs (verify_line_count.py, verify_hook_blocks.py, phase05_acceptance.py)
- ✓ Traceability enforcement tests (`test_traceability_matrix.py`, `test_phase05_acceptance.py`) exist inside `tests/phase05/` to guard the matrix from silent drift

---

## 9. Verdict

**Phase 5 goal is delivered.** The 5166-line drift pattern is structurally blocked at three layers — line budget contract test, write-time Hook regex block, and the physical absence of the `skip_gates` keyword/T2V code path. The 12 GATE DAG runs through `gate_guard.py` dispatch enforcement, CircuitBreaker wraps every external API, Checkpointer persists atomic JSON state, and VoiceFirstTimeline serialises Typecast → video alignment before Shotstack 720p render → upscale. Kling→Runway failover is encoded in sibling adapters sharing a Pydantic I2VRequest contract.

All 6 Success Criteria pass, all 17 REQs covered with green tests, 329 Phase 5 tests pass in 17s, 244 Phase 4 regression tests still green. No blocking gaps.

---

## VERIFICATION PASSED
