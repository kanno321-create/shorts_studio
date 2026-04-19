---
phase: 7
plan: 07-02
subsystem: integration-test / Wave 1 mock adapters
tags: [phase-7, wave-1, mocks, tests, D-3, D-16, D-17, D-18, D-19, D-20]
requirements: [TEST-01]
success_criteria: [SC1]
dependency_graph:
  requires: [Plan 07-01 Wave 0 fixtures + conftest]
  provides:
    - "5 deterministic mock adapter classes under tests/phase07/mocks/"
    - "Mock contract: allow_fault_injection=False default (D-3) + RuntimeError on fault (Correction 2)"
    - "MockShotstack.create_ken_burns_clip ready for Plan 07-06 Wave 3 fallback tests"
    - "MockKling + MockRunway failover pair ready for Plan 07-05 CircuitBreaker tests"
  affects:
    - "Unblocks Plans 07-03 (E2E happy path) + 07-05 (CircuitBreaker) + 07-06 (Fallback ken-burns)"
tech_stack:
  added: []
  patterns:
    - "D-3 production-safe default (allow_fault_injection=False)"
    - "RuntimeError on fault (Correction 2 — NOT CircuitBreakerTriggerError)"
    - "Duck-typed *args/**kwargs signatures (pipeline tests don't introspect arg names)"
    - "sys.path[0] insertion pattern for tests/phase07/mocks/ imports (no tests/__init__.py restructure)"
key_files:
  created:
    - tests/phase07/mocks/__init__.py
    - tests/phase07/mocks/kling_mock.py
    - tests/phase07/mocks/runway_mock.py
    - tests/phase07/mocks/typecast_mock.py
    - tests/phase07/mocks/elevenlabs_mock.py
    - tests/phase07/mocks/shotstack_mock.py
    - tests/phase07/test_mock_kling_adapter.py
    - tests/phase07/test_mock_runway_adapter.py
    - tests/phase07/test_mock_typecast_adapter.py
    - tests/phase07/test_mock_elevenlabs_adapter.py
    - tests/phase07/test_mock_shotstack_adapter.py
  modified:
    - .planning/phases/07-integration-test/07-VALIDATION.md  # rows 3-7 flipped + Wave 0 mocks/ bullet checked
decisions:
  - "D-3 enforcement: all 5 mocks default allow_fault_injection=False; fault_mode param silently ignored unless caller explicitly opts in"
  - "Correction 2 enforcement: MockKling.circuit_3x raises plain RuntimeError, NOT CircuitBreakerTriggerError (which does not exist). Plan 07-05 CircuitBreaker will emit CircuitBreakerOpenError after 3 raises."
  - "Mock signatures use *args/**kwargs to shadow real adapter duck-typing — pipeline tests never introspect parameter names"
  - "sys.path insertion in each test module (5 lines) avoids adding tests/__init__.py which would change all of phase04/05/06 test resolution"
  - "MockShotstack has all 3 real methods (render + upscale + create_ken_burns_clip) — last one is dedicated Plan 07-06 dependency"
metrics:
  duration: ~6 minutes
  completed_date: 2026-04-19
  tasks_completed: 5/5
  commits: 10  # 5 × RED + 5 × GREEN
  files_created: 11
  files_modified: 1
  lines_added: ~320
  tests_added: 32  # 7 kling + 7 runway + 5 typecast + 5 elevenlabs + 8 shotstack
  regression_baseline: "836/836 preserved (Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 W0 27)"
  full_suite: "868/868 passing (836 baseline + 32 new Wave 1 mock tests)"
---

# Phase 7 Plan 02: Wave 1 Mock Adapters Summary

One-liner: 5 deterministic mock adapter classes (Kling/Runway/Typecast/ElevenLabs/Shotstack) under tests/phase07/mocks/ with D-3 production-safe defaults + fault_mode gating; 32 new unit tests green; 868/868 full regression preserved.

---

## Objective (from PLAN)

Wave 1 MOCK ADAPTERS — Create 5 deterministic mock adapter classes under `tests/phase07/mocks/`, one per real adapter (Kling/Runway/Typecast/ElevenLabs/Shotstack). Each mock shadows the real adapter's public method signatures so downstream Wave 2 E2E can swap them in without code churn. Per D-3, each mock defaults `allow_fault_injection=False` so production accidentally using one of these classes fails safe.

Purpose: TEST-01 E2E happy path requires all 5 adapters as MagicMock-like instances with deterministic return values. TEST-03/04 (Waves 3) additionally need fault injection (Kling 3× RuntimeError for circuit breaker; Runway 1× then success for failover). Centralising mocks avoids copy-paste across test files.

---

## Tasks Completed

### Task 7-02-01 — MockKling (kling_mock.py + test_mock_kling_adapter.py)

- **RED commit:** `b99c89d` — `test(07-02): RED — MockKling test failing with ModuleNotFoundError` (7 tests, ModuleNotFoundError on `mocks.kling_mock`)
- **GREEN commit:** `5de71ad` — `feat(07-02): GREEN — MockKling deterministic adapter with fault_mode gating` (7/7 PASS in 0.07s)
- Files created:
  - `tests/phase07/mocks/__init__.py` (11 lines — package marker)
  - `tests/phase07/mocks/kling_mock.py` (58 lines — @dataclass with `image_to_video(*args, **kwargs) -> Path`)
  - `tests/phase07/test_mock_kling_adapter.py` (77 lines, 7 tests)
- Contract proven:
  - `test_default_success_returns_fixture_path` — returns `mock_kling.mp4` Path on success
  - `test_default_allows_fault_injection_is_false` — D-3 production-safe default
  - `test_fault_mode_ignored_when_allow_fault_injection_false` — D-3 gating
  - `test_circuit_3x_raises_runtime_error_three_times_then_succeeds` — 3 raises then success on call 4
  - `test_runway_failover_raises_once_then_succeeds` — 1 raise then success on call 2
  - `test_mock_is_NOT_circuit_breaker_trigger_error` — Correction 2 enforcement (`type(exc.value) is RuntimeError`)
  - `test_accepts_real_adapter_signature_args` — duck-typed `(prompt, anchor_frame, duration_seconds)` args accepted

### Task 7-02-02 — MockRunway (runway_mock.py + test_mock_runway_adapter.py)

- **RED commit:** `eda1fa9` — `test(07-02): RED — MockRunway test failing with ModuleNotFoundError`
- **GREEN commit:** `4aaf359` — `feat(07-02): GREEN — MockRunway deterministic adapter with fault_mode gating` (7/7 PASS in 0.07s)
- Files created:
  - `tests/phase07/mocks/runway_mock.py` (47 lines — structural sibling of kling_mock.py with `mock_runway.mp4` fixture)
  - `tests/phase07/test_mock_runway_adapter.py` (62 lines, 7 tests mirroring Kling shape)
- Contract: same as Kling. Used by Plan 07-05 failover test (Kling raises `runway_failover`, pipeline falls over to Runway which succeeds first call).

### Task 7-02-03 — MockTypecast (typecast_mock.py + test_mock_typecast_adapter.py)

- **RED commit:** `f32a66e` — `test(07-02): RED — MockTypecast test failing with ModuleNotFoundError`
- **GREEN commit:** `6a820b0` — `feat(07-02): GREEN — MockTypecast deterministic TTS adapter` (5/5 PASS in 0.06s)
- Files created:
  - `tests/phase07/mocks/typecast_mock.py` (44 lines — `generate(*args, **kwargs) -> list[dict]` with `speak_v2_url`, `duration_seconds`, `emotion_applied`)
  - `tests/phase07/test_mock_typecast_adapter.py` (45 lines, 5 tests)
- Contract proven:
  - `test_generate_returns_list_of_segments` — returns `[{"audio_path", "start_ms", "end_ms", "text", "duration_seconds", "emotion_applied", "speak_v2_url"}]`
  - `test_generate_increments_call_count` — determinism tracking
  - `test_production_safe_default` — D-3
  - `test_korean_script_roundtrip` — D-22 cp949/UTF-8 round-trip for "한국어 대본 테스트"
  - `test_fixture_path_points_to_mock_typecast_wav`

### Task 7-02-04 — MockElevenLabs (elevenlabs_mock.py + test_mock_elevenlabs_adapter.py)

- **RED commit:** `8edc604` — `test(07-02): RED — MockElevenLabs test failing with ModuleNotFoundError`
- **GREEN commit:** `e6c9473` — `feat(07-02): GREEN — MockElevenLabs deterministic TTS fallback adapter` (5/5 PASS in 0.06s)
- Files created:
  - `tests/phase07/mocks/elevenlabs_mock.py` (50 lines — `generate_with_timestamps(*args, **kwargs) -> list[dict]` with `word`, `start_s`, `end_s`, `voice_id="rachel_mock"`)
  - `tests/phase07/test_mock_elevenlabs_adapter.py` (44 lines, 5 tests)
- Contract: Typecast fallback proof path. Word-level timestamp segments compatible with VoiceFirstTimeline alignment expectations (which is additionally patched in E2E).

### Task 7-02-05 — MockShotstack (shotstack_mock.py + test_mock_shotstack_adapter.py)

- **RED commit:** `c053d6a` — `test(07-02): RED — MockShotstack test failing with ModuleNotFoundError`
- **GREEN commit:** `9959e69` — `feat(07-02): GREEN — MockShotstack with render/upscale/create_ken_burns_clip` (8/8 PASS in 0.07s)
- Files created:
  - `tests/phase07/mocks/shotstack_mock.py` (82 lines — richest mock with 3 methods)
  - `tests/phase07/test_mock_shotstack_adapter.py` (76 lines, 8 tests)
- Contract proven:
  - `test_render_returns_v2_envelope` — `{"response": {"id", "url", "message"}, "success": True, "status": "done"}`
  - `test_render_call_count_increments` — deterministic id generation (`mock_shotstack_001`, `_002`, ...)
  - `test_render_payload_captured` — `last_render_payload` spy
  - `test_upscale_is_noop` — `{"status": "skipped", "reason": "mock upscale NOOP"}`
  - `test_create_ken_burns_clip_returns_path` — Plan 07-06 Wave 3 fallback dependency
  - `test_create_ken_burns_clip_captures_args` — `last_ken_burns_args` spy (duration_s, scale_to, pan_direction)
  - `test_production_safe_default`
  - `test_render_accepts_timeline_list_signature` — real signature `render(timeline: list, ...)` accepted

---

## Mock Signature Verification (real-adapter compatibility)

| Mock | Real adapter | Mock method | Real method signature | Duck-typed compatibility |
|------|--------------|-------------|----------------------|---------------------------|
| KlingMock | KlingI2VAdapter (kling_i2v.py:93-132) | `image_to_video(*args, **kwargs) -> Path` | `image_to_video(prompt, anchor_frame, duration_seconds=5) -> Path` | ✅ test_accepts_real_adapter_signature_args |
| RunwayMock | RunwayI2VAdapter (runway_i2v.py:83-116) | `image_to_video(*args, **kwargs) -> Path` | `image_to_video(prompt, anchor_frame, duration_seconds=5) -> Path` | ✅ test_accepts_real_adapter_signature_args |
| TypecastMock | TypecastAdapter (typecast.py:71-129) | `generate(*args, **kwargs) -> list[dict]` | `generate(scenes: list[dict]) -> list[AudioSegment]` | ✅ shape matches D-18; pipeline patches VoiceFirstTimeline.align |
| ElevenLabsMock | ElevenLabsAdapter (elevenlabs.py:169-219) | `generate_with_timestamps(*args, **kwargs) -> list[dict]` | `generate_with_timestamps(scenes: list[dict]) -> list[AudioSegment]` | ✅ word-level timestamp dicts match D-19 |
| ShotstackMock | ShotstackAdapter (shotstack.py:102-216) | `render(payload, *args, **kwargs) -> dict` + `upscale(...) -> dict` + `create_ken_burns_clip(image_path, duration_s, ...) -> Path` | same 3 methods | ✅ v2 envelope D-20; ken-burns standalone per RESEARCH Correction 3 |

---

## Fault-Injection Semantics Covered

| fault_mode | `allow_fault_injection=False` | `allow_fault_injection=True` |
|------------|-------------------------------|------------------------------|
| `None` (default) | Deterministic success | Deterministic success |
| `"circuit_3x"` | Deterministic success (fault ignored per D-3) | Calls 1-3 raise `RuntimeError("mock Kling circuit_3x failure #N")`; call 4+ succeeds |
| `"runway_failover"` | Deterministic success (fault ignored) | Call 1 raises `RuntimeError("mock Kling runway_failover #1")`; call 2+ succeeds |

**Correction 2 enforcement:** All fault raises are `type(exc) is RuntimeError` — the non-existent `CircuitBreakerTriggerError` is NOT used. Plan 07-05 CircuitBreaker catches the RuntimeError and transitions to OPEN state, emitting `CircuitBreakerOpenError` on subsequent calls (the only legitimate breaker exception per `scripts/orchestrator/circuit_breaker.py:57-72`).

---

## Regression Sweep Result

```bash
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov
# 868 passed in 76.06s (0:01:16)
```

Baseline before Plan 07-02: **836/836** (Phase 4: 244 + Phase 5: 329 + Phase 6: 236 + Phase 7 W0: 27).  
After Plan 07-02: **868/868** — +32 new Wave 1 tests, zero regressions.

Per-task breakdown:
- tests/phase07/test_mock_kling_adapter.py: 7/7 PASS
- tests/phase07/test_mock_runway_adapter.py: 7/7 PASS
- tests/phase07/test_mock_typecast_adapter.py: 5/5 PASS
- tests/phase07/test_mock_elevenlabs_adapter.py: 5/5 PASS
- tests/phase07/test_mock_shotstack_adapter.py: 8/8 PASS

---

## Verification

### Acceptance criteria evaluation

| # | Plan acceptance criterion | Result |
|---|---------------------------|--------|
| 1 | `test -f tests/phase07/mocks/__init__.py` | ✅ PASS |
| 2 | `grep -c "class KlingMock" tests/phase07/mocks/kling_mock.py` == 1 | ✅ PASS |
| 3 | `grep -c "class RunwayMock" tests/phase07/mocks/runway_mock.py` == 1 | ✅ PASS |
| 4 | `grep -c "class TypecastMock" tests/phase07/mocks/typecast_mock.py` == 1 | ✅ PASS |
| 5 | `grep -c "class ElevenLabsMock" tests/phase07/mocks/elevenlabs_mock.py` == 1 | ✅ PASS |
| 6 | `grep -c "class ShotstackMock" tests/phase07/mocks/shotstack_mock.py` == 1 | ✅ PASS |
| 7 | `grep -c "allow_fault_injection: bool = False"` across all 5 mocks | ✅ PASS (5/5) |
| 8 | `! grep -q "CircuitBreakerTriggerError"` across all 5 mocks | ✅ PASS (zero hits) |
| 9 | `grep -cE "def render\\(\|def upscale\\(\|def create_ken_burns_clip\\("` shotstack_mock.py == 3 | ✅ PASS |
| 10 | All 5 per-mock pytest files exit 0 | ✅ PASS (32/32) |
| 11 | Regression sweep `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q` exit 0 | ✅ PASS (868/868) |

### VALIDATION.md rows flipped

- Row 3 (7-02-01 kling) ⬜ pending → ✅ green ; File Exists ❌ W0 → ✅
- Row 4 (7-02-02 runway) ⬜ pending → ✅ green ; ❌ W0 → ✅
- Row 5 (7-02-03 typecast) ⬜ pending → ✅ green ; ❌ W0 → ✅
- Row 6 (7-02-04 elevenlabs) ⬜ pending → ✅ green ; ❌ W0 → ✅
- Row 7 (7-02-05 shotstack) ⬜ pending → ✅ green ; ❌ W0 → ✅
- Wave 0 Requirements `tests/phase07/mocks/` bullet: [ ] → [x]

---

## Deviations from Plan

None — plan executed exactly as written.

Minor implementation note: the plan's import pattern `from tests.phase07.mocks.kling_mock import KlingMock` does not resolve because `tests/` has no `__init__.py` (adding one would alter Phase 4/5/6 test resolution — out of scope). Used a 5-line `sys.path.insert(0, str(_PHASE07_ROOT))` prelude in each test module to make `from mocks.kling_mock import KlingMock` work without restructuring the tests/ package hierarchy. This is strictly additive (Rule 3 fix for a plan-assumed but unstated precondition) and does not affect mock contracts or behavior. The conftest.py inherited from Wave 0 already adds repo-root to sys.path; our insertion adds `tests/phase07/` to make `mocks` directly importable.

---

## Known Stubs

None. All 5 mock classes are fully wired with deterministic return values, `allow_fault_injection` gating, and call-count tracking. Fixture paths point to the 0-byte placeholder files created in Plan 07-01 (intentional per D-2 Don't Hand-Roll — pipeline tests never `read_bytes` these paths).

---

## Commit Hashes (shorts repo)

| Order | Hash    | Message |
|-------|---------|---------|
| 1     | b99c89d | test(07-02): RED — MockKling test failing with ModuleNotFoundError |
| 2     | 5de71ad | feat(07-02): GREEN — MockKling deterministic adapter with fault_mode gating |
| 3     | eda1fa9 | test(07-02): RED — MockRunway test failing with ModuleNotFoundError |
| 4     | 4aaf359 | feat(07-02): GREEN — MockRunway deterministic adapter with fault_mode gating |
| 5     | f32a66e | test(07-02): RED — MockTypecast test failing with ModuleNotFoundError |
| 6     | 6a820b0 | feat(07-02): GREEN — MockTypecast deterministic TTS adapter |
| 7     | 8edc604 | test(07-02): RED — MockElevenLabs test failing with ModuleNotFoundError |
| 8     | e6c9473 | feat(07-02): GREEN — MockElevenLabs deterministic TTS fallback adapter |
| 9     | c053d6a | test(07-02): RED — MockShotstack test failing with ModuleNotFoundError |
| 10    | 9959e69 | feat(07-02): GREEN — MockShotstack with render/upscale/create_ken_burns_clip |

Final metadata commit (SUMMARY + VALIDATION flip + STATE + ROADMAP) will be recorded immediately after self-check.

---

## Self-Check: PASSED

Verification commands (all ran successfully):
- `test -f tests/phase07/mocks/__init__.py` → FOUND
- `test -f tests/phase07/mocks/kling_mock.py` → FOUND
- `test -f tests/phase07/mocks/runway_mock.py` → FOUND
- `test -f tests/phase07/mocks/typecast_mock.py` → FOUND
- `test -f tests/phase07/mocks/elevenlabs_mock.py` → FOUND
- `test -f tests/phase07/mocks/shotstack_mock.py` → FOUND
- `test -f tests/phase07/test_mock_kling_adapter.py` → FOUND
- `test -f tests/phase07/test_mock_runway_adapter.py` → FOUND
- `test -f tests/phase07/test_mock_typecast_adapter.py` → FOUND
- `test -f tests/phase07/test_mock_elevenlabs_adapter.py` → FOUND
- `test -f tests/phase07/test_mock_shotstack_adapter.py` → FOUND
- `git log` shows all 10 commit hashes (b99c89d → 9959e69) → FOUND
- pytest sweep Phase 4+5+6+7 → 868/868 PASS
- No `CircuitBreakerTriggerError` references in any mock source → verified

No missing items. Plan 07-02 is Wave 1 complete. Plans 07-03 (E2E happy path), 07-05 (CircuitBreaker), 07-06 (Fallback ken-burns) are unblocked.
