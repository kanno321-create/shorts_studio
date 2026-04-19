---
phase: 05-orchestrator-v2-write
plan: 05-07
subsystem: orchestrator-keystone
tags: [python, state-machine, orchestrator, checkpointer, circuit-breaker, voice-first, low-res-first, fallback, regeneration-loop]
wave: 5

# Dependency graph
dependency-graph:
  requires:
    - 05-01 (GateName + GATE_DEPS + exception hierarchy — gates.py imports)
    - 05-02 (CircuitBreaker + CircuitBreakerOpenError — 5 breaker instances)
    - 05-03 (Checkpointer + Checkpoint + make_timestamp — resume semantics)
    - 05-04 (GateGuard + Verdict — single enforcement point at dispatch)
    - 05-05 (VoiceFirstTimeline + AudioSegment + VideoCut — assembly primitive)
    - 05-06 (KlingI2VAdapter + RunwayI2VAdapter + TypecastAdapter + ElevenLabsAdapter + ShotstackAdapter — 5 API surfaces)
  provides:
    - scripts.orchestrator.shorts_pipeline.ShortsPipeline — 13-GATE state machine integrator
    - scripts.orchestrator.shorts_pipeline.GateContext — per-run data carrier
    - scripts.orchestrator.shorts_pipeline.GATE_INSPECTORS — per-gate Inspector mapping
    - scripts.orchestrator.fallback.append_failures — FAIL-01 append-only writer
    - scripts.orchestrator.fallback.insert_fallback_shot — ken-burns fallback builder
    - scripts.orchestrator.fallback.dedupe_fallback_key — per-session/gate/cut dedup key
    - scripts.orchestrator.__init__ re-exports every Wave 0-4 primitive + ShortsPipeline
  affects:
    - 05-08 (hc_checks rewrite — check_hc_10_inspector_coverage consumes GATE_INSPECTORS)
    - 05-09 (Hook extensions — D-8/D-9/D-13 physical absence verified by test meta-grep)
    - 05-10 (SC acceptance — SC1 line budget + SC2..SC5 grep acceptance all PASS)

# Tech tracking
tech-stack:
  added:
    - python dataclasses (GateContext + field(default_factory))
    - argparse CLI (--session-id / --state-root / --log-level)
    - Dependency injection pattern (producer_invoker / supervisor_invoker / asset_sourcer_invoker)
  patterns:
    - "Per-GATE method template (_run_<name>): Producer via _producer_loop, Supervisor verdict, GateGuard.dispatch — each method 8-20 lines"
    - "CircuitBreaker wrapping at adapter seam with CircuitBreakerOpenError fallthrough to backup adapter (Kling→Runway, Typecast→ElevenLabs)"
    - "Checkpointer.resume at run() entry rebuilds gate_guard._dispatched set from on-disk gate_*.json"
    - "Lambda late-binding via default-arg trick (lambda p=prompt, a=anchor, d=duration: ...) to avoid loop-variable capture in _run_assets"
    - "Module-level assert on GATE_INSPECTORS size + key equality to GateName operational set — fails import if mapping drifts"

key-files:
  created:
    - scripts/orchestrator/fallback.py (141 lines)
    - scripts/orchestrator/shorts_pipeline.py (787 lines)
    - tests/phase05/test_shorts_pipeline.py (214 lines, 11 tests)
    - tests/phase05/test_pipeline_e2e_mock.py (235 lines, 3 tests)
    - tests/phase05/test_fallback_shot.py (197 lines, 6 tests)
    - tests/phase05/test_low_res_first.py (167 lines, 4 tests)
  modified:
    - scripts/orchestrator/__init__.py (re-exports ShortsPipeline, GateContext, GATE_INSPECTORS, CircuitBreaker, CircuitState, Checkpointer, Checkpoint, sha256_file, GateGuard, Verdict, AudioSegment, VideoCut, TimelineEntry, TransitionEntry, VoiceFirstTimeline exceptions)

key-decisions:
  - "shorts_pipeline.py landed at 787 lines — 13 lines of headroom under the 800 ceiling. The per-GATE method template stayed lean (8-20 lines each) by offloading regeneration to _producer_loop and Fallback to fallback.py. If future requirements add another operational GATE, the line budget would need reshaping: fallback.py absorbs another ~30 lines, or GATE_INSPECTORS moves to a dedicated constants module."
  - "Default adapter construction in __init__ (without injected instances) requires KLING_API_KEY / RUNWAY_API_KEY / TYPECAST_API_KEY / ELEVENLABS_API_KEY / SHOTSTACK_API_KEY env vars. Unit tests that do not inject adapters use a `_fake_env` fixture that sets all 5 to 'fake' via monkeypatch. Tests that DO inject MagicMock adapters do not need the fixture — the env-var requirement only triggers in the adapter constructor."
  - "CircuitBreaker catches CircuitBreakerOpenError (RuntimeError subclass from circuit_breaker.py), NOT the legacy OrchestratorError subclass CircuitOpen from gates.py. The CircuitOpen name is still exported through __init__ for any caller that wants to write-path catch OrchestratorError — but CircuitBreaker.call() actually raises CircuitBreakerOpenError. The pipeline catches the concrete type the breaker raises."
  - "_run_assets uses lambda default-arg late binding (lambda p=prompt, a=anchor, d=duration: ...) to safely pass loop-variable values into CircuitBreaker.call(). Without this, all lambdas would close over the final iteration's values. Subtle Python gotcha — fixed before any mock E2E test could trip it."
  - "Shotstack.upscale() is called UNCONDITIONALLY after Shotstack.render() inside _run_assembly. ShotstackAdapter.upscale() is a documented NOOP returning {status: skipped, ...} per RESEARCH §7 — the pipeline does NOT branch on 720p quality. Phase 8 will swap the NOOP for a real upscale decision."
  - "_producer_loop's fallback-eligibility check is hard-coded to (GateName.ASSETS, GateName.THUMBNAIL). These are the two gates whose artifact can be visually substituted by a ken-burns over a stock still. SCRIPT/VOICE/METADATA etc. have no legitimate Fallback — their artifacts are semantic, not visual. Exhaustion there MUST raise RegenerationExhausted so the pipeline stops instead of ship garbage."
  - "Meta-test (test_pipeline_source_has_no_forbidden_tokens) reads shorts_pipeline.py from disk and asserts 0 occurrences of skip_gates / text_to_video / text2video / t2v-as-word / TODO(next-session). This catches docstring regressions where a developer mentions a forbidden token in documentation (which the Hook also blocks at write time — double safety net)."

requirements-completed: [ORCH-01, ORCH-02, ORCH-04, ORCH-05, ORCH-07, ORCH-08, ORCH-09, ORCH-11, ORCH-12]

# Metrics
metrics:
  duration-minutes: 45
  tasks-completed: 3
  files-created: 6
  files-modified: 1
  tests-added: 24
  tests-passing: 24
  total-phase05-tests: 224
  lines-added: 1791
completed-date: 2026-04-19
---

# Phase 5 Plan 07: ShortsPipeline Keystone Summary

**The 787-line single-file state machine integrator that wires every Wave 0-4 primitive (GateName / GATE_DEPS / CircuitBreaker / Checkpointer / GateGuard / VoiceFirstTimeline / 5 API adapters) into `ShortsPipeline.run()` — a 13-GATE DAG executor with checkpoint resume, CircuitBreaker failover, 3-retry regeneration loop, ken-burns Fallback for ASSETS/THUMBNAIL, voice-first assembly, and Low-Res First (720p) rendering. D-1's 5166-line drift is now structurally impossible: any future edit that balloons the file past 800 lines trips `scripts/validate/verify_line_count.py` in the test suite.**

## Performance

- **Duration:** ~45 minutes
- **Tasks:** 3/3 complete (fallback.py helpers → shorts_pipeline.py keystone → 4 test files)
- **Files created:** 6 (2 source + 4 test)
- **Files modified:** 1 (scripts/orchestrator/__init__.py re-exports)
- **Tests:** 24 new (11 + 3 + 6 + 4). Full phase05 suite now 224/224 PASS (200 baseline + 24 new).
- **Commits:** 3 (one per task, feat/feat/test prefixes).

## Accomplishments

1. **ORCH-01 fulfilled — 787-line keystone file.** `scripts/orchestrator/shorts_pipeline.py` contains exactly 1 `class ShortsPipeline` + 13 `_run_<gate>` methods + `_producer_loop` + `_insert_fallback` + `_transition_to_complete` + `GATE_INSPECTORS` constant + `GateContext` dataclass + CLI `main()`. Line count 787 — 13 lines of headroom under the 800 ceiling — verified by `scripts/validate/verify_line_count.py`.

2. **ORCH-02 fulfilled — 13 operational GATE methods.** One `_run_trend` / `_run_niche` / `_run_research_nlm` / `_run_blueprint` / `_run_script` / `_run_polish` / `_run_voice` / `_run_assets` / `_run_assembly` / `_run_thumbnail` / `_run_metadata` / `_run_upload` / `_run_monitor` per operational GateName. Each method follows the same Producer-Inspector-Dispatch pattern; regeneration handled by the shared `_producer_loop` helper.

3. **ORCH-04 fulfilled — `_transition_to_complete` raises IncompleteDispatch.** The COMPLETE transition invokes `GateGuard.verify_all_dispatched()` first; if any of the 13 operational gates are missing from the dispatched set, the method raises `IncompleteDispatch` with the diagnostic list. On success, a COMPLETE checkpoint is written to `state/<session_id>/gate_14.json`.

4. **ORCH-05 fulfilled — Resume-from-checkpoint.** `ShortsPipeline.run()` calls `Checkpointer.resume(session_id)` at entry. If gate files exist, it reads `Checkpointer.dispatched_gates(session_id)` and populates `GateGuard._dispatched` with the corresponding `GateName` set. The iteration then skips every `gate in self.gate_guard.dispatched`. `test_pipeline_resume_from_checkpoint` pre-seeds gates 1-3 on disk and proves Producer invokers for TREND/NICHE/RESEARCH_NLM are never called.

5. **ORCH-06 fulfilled — 5 CircuitBreaker instances wired.** `__init__` creates `kling_breaker`, `runway_breaker`, `typecast_breaker`, `elevenlabs_breaker`, `shotstack_breaker` all at D-6 defaults (`max_failures=3`, `cooldown_seconds=300`). `_run_voice` wraps Typecast in its breaker and falls through to ElevenLabs on `CircuitBreakerOpenError`. `_run_assets` wraps Kling and falls through to Runway. `_run_assembly` wraps Shotstack.render.

6. **ORCH-07 fulfilled — DAG runtime check.** Every iteration of `run()` calls `self.gate_guard.ensure_dependencies(gate)` BEFORE invoking `_run_<gate>`. This surfaces `GateDependencyUnsatisfied` if any declared prereq is missing. ASSEMBLY (which depends on both VOICE and ASSETS per GATE_DEPS) is the canonical stress case — the pipeline order happens to visit VOICE then ASSETS before ASSEMBLY, so the check passes in happy paths, but the guard is active and tested at Plan 01 / Plan 04 level.

7. **ORCH-11 fulfilled — 720p Low-Res First.** `_run_assembly` calls `self.shotstack.render(timeline, resolution="hd", aspect_ratio="9:16")` and only THEN `self.shotstack.upscale(render_url)`. `test_shotstack_render_called_with_hd` asserts the kwargs; `test_upscale_after_render` asserts temporal ordering via side-effect recording. ShotstackAdapter.upscale() itself is a documented Phase 8 NOOP returning `{"status": "skipped"}`.

8. **ORCH-12 fulfilled — Regeneration loop + Fallback.** `_producer_loop(gate, producer_fn)` runs up to `self.max_retries` (default 3) attempts. A PASS verdict short-circuits. After all 3 FAILs: `append_failures(failures_path, session_id, gate.name, evidence, feedback)` writes to `.claude/failures/orchestrator.md` (append-only, never truncates), then for ASSETS/THUMBNAIL gates `_insert_fallback` calls `ShotstackAdapter.create_ken_burns_clip` via the injected `asset_sourcer_invoker` and adds the cut index to `ctx.fallback_indices`. For every other gate, it raises `RegenerationExhausted`.

9. **D-8 / D-9 / D-13 physical invariants.** `scripts/orchestrator/shorts_pipeline.py` contains 0 occurrences of `skip_gates`, 0 of `text_to_video` / `text2video` / isolated-`t2v`, 0 of `TODO(next-session)`, 0 of `segments[]`, 0 of `import selenium`. Verified by grep and by the meta-test `test_pipeline_source_has_no_forbidden_tokens`.

10. **Dependency injection for testability.** `ShortsPipeline.__init__` takes 8 injectables: 5 adapters + 3 invokers (producer / supervisor / asset_sourcer). Production code passes real adapter instances + Phase 4 harness spawn calls; every test in Plan 07 injects `MagicMock`. Zero real API traffic during the 224-test phase05 run.

11. **Helper extraction — fallback.py.** 141-line helper module carrying `append_failures` (FAIL-01 append-only writer with parent-dir mkdir and first-3-evidence truncation), `insert_fallback_shot` (wraps `ShotstackAdapter.create_ken_burns_clip` via dependency injection), and `dedupe_fallback_key` (deterministic per-session/gate/cut key per RESEARCH line 862). Extracting these kept shorts_pipeline.py under the 800-line ceiling.

## Task Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | fallback.py — append_failures + insert_fallback_shot + dedupe_fallback_key (141 lines) | `5849ee1` |
| 2 | shorts_pipeline.py (787 lines) + __init__.py re-exports — ShortsPipeline state machine | `031c4ba` |
| 3 | 4 test files (test_shorts_pipeline + test_pipeline_e2e_mock + test_fallback_shot + test_low_res_first) — 24 tests green | `7653492` |

## Files Created

### Source (`scripts/orchestrator/`)
| File | Lines | Contents |
|------|------:|----------|
| `fallback.py` | 141 | `append_failures(failures_path, session_id, gate, evidence, semantic_feedback)` with append-only `open("a", encoding="utf-8")`; `insert_fallback_shot(shotstack_adapter, asset_sourcer_invoker, prompt, duration_s, scale_from, scale_to, pan_direction)` calling `shotstack_adapter.create_ken_burns_clip(...)`; `dedupe_fallback_key(session_id, gate, cut_index)` returning `"{session}:{gate}:{cut}"` |
| `shorts_pipeline.py` | 787 | `GATE_INSPECTORS` (13-key dict) + `GateContext` dataclass + `ShortsPipeline` class (init wires 5 CircuitBreakers + 5 adapters + GateGuard + Checkpointer + VoiceFirstTimeline + 3 default invokers) + `run()` top-level + 13 `_run_<gate>` methods + `_producer_loop` + `_insert_fallback` + `_transition_to_complete` + CLI `main()` + module-level assert on GATE_INSPECTORS size/keys |

### Tests (`tests/phase05/`)
| File | Lines | Tests | Coverage |
|------|------:|------:|----------|
| `test_shorts_pipeline.py` | 214 | 11 | 13 `_run_<gate>` method presence; GATE_INSPECTORS size + key equality; 5 breakers at D-6 defaults; max_retries=3; IncompleteDispatch raised on empty dispatched; 3 default invokers raise NotImplementedError; forbidden tokens absent; GateContext initial state; line count 500≤N≤800 |
| `test_pipeline_e2e_mock.py` | 235 | 3 | Full 13-gate end-to-end mock run with dispatched_count=13 + 13+ gate_*.json files; pre-seeded gates 1-3 skip Producer invocation; summary dict surfaces fallback_count |
| `test_fallback_shot.py` | 197 | 6 | ASSETS 3 retries → Fallback + FAILURES append + fallback_indices updated; SCRIPT 3 retries → RegenerationExhausted; PASS first try → no FAILURES file; append_failures preserves existing content; evidence summary truncated to 3; dedupe_fallback_key deterministic |
| `test_low_res_first.py` | 167 | 4 | Shotstack.render kwargs resolution="hd" + aspect_ratio="9:16"; render() before upscale() temporal ordering; ShotstackAdapter.upscale() NOOP returns `{"status": "skipped"}` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Module docstring contained forbidden tokens**
- **Found during:** Task 2 post-write grep verification
- **Issue:** My initial `shorts_pipeline.py` module docstring mentioned the forbidden patterns (`skip_gates`, `TODO(next-session)`, `t2v`, `text_to_video`) explicitly while explaining the D-8/D-9/D-13 invariants. The acceptance criteria at PLAN line 797-799 require these patterns to have 0 occurrences ANYWHERE in the file, including docstrings.
- **Fix:** Rewrote the module docstring to reference the CONTEXT file for the forbidden-token list instead of spelling them out inline. The invariants are still documented — just via link rather than self-reference.
- **Files modified:** `scripts/orchestrator/shorts_pipeline.py` (module docstring only, no code changes)
- **Commit:** folded into `031c4ba` (caught before Task 2 finalised)

**2. [Rule 3 — Blocking] Initial 3 unit tests tripped adapter env-var requirement**
- **Found during:** Task 3 first pytest run — `test_default_{producer,supervisor,asset_sourcer}_invoker_raises_not_implemented` FAILED
- **Issue:** These tests construct `ShortsPipeline` WITHOUT injecting adapter MagicMocks, to exercise the default paths. But the default adapter constructors (`KlingI2VAdapter()`, etc.) read their API keys from env and raise `ValueError` when absent. The 3 tests hit the env-var check before reaching the default invoker logic.
- **Fix:** Added a module-level `_fake_env` fixture using `monkeypatch.setenv` for all 5 API env vars, then injected it into the 3 failing tests. The rest of the test file's tests use injected `MagicMock` adapters and do not need the fixture.
- **Files modified:** `tests/phase05/test_shorts_pipeline.py`
- **Commit:** folded into `7653492` (caught before Task 3 finalised)

No Rule 4 (architectural) decisions needed. No auth gates encountered.

## Authentication Gates

None encountered during Plan 07 implementation. All 24 new tests use mocked adapters and mocked producer/supervisor invokers — zero real API traffic, zero real keys needed. Production runs will require the 5 API keys (KLING/RUNWAY/TYPECAST/ELEVENLABS/SHOTSTACK) set in the environment; Plan 07 does not wire env-var loading (that lands in Phase 8 config).

## Known Stubs

1. **Default invokers raise NotImplementedError.** `_default_producer_invoker`, `_default_supervisor_invoker`, and `_default_asset_sourcer` are documented stubs — they exist so `ShortsPipeline(session_id=...)` without kwargs fails loudly at the first operational method call (not silently swallowing the gate). Production wires the Phase 4 harness; tests inject MagicMock.
2. **`_run_research_nlm` calls the generic producer_invoker.** Phase 6 WIKI-03 will swap this for a NotebookLM RAG client call. The current placeholder (`producer_invoker("researcher", "RESEARCH_NLM", {...})`) unblocks the 13-gate walk without prejudice.
3. **`_run_upload` calls the generic producer_invoker.** Phase 8 PUB-01 will wire YouTube API v3. For now the placeholder routes through the generic producer path.
4. **`ShotstackAdapter.upscale()` returns `{"status": "skipped"}`.** Documented Phase 8 NOOP per RESEARCH §7 — included here for completeness (the stub ships as a callable so `_run_assembly` does not need to special-case upscale absence).

None of these stubs affect the plan's goal of dispatching all 13 operational GATEs and reaching COMPLETE; they are intentional deferrals per the PLAN's explicit exclusions ("Phase 5 does not touch NotebookLM RAG integration / YouTube API v3 / real-cost upscale" — CONTEXT lines 23-27).

## Verification Evidence

### Task 1 — fallback.py
```
$ python scripts/validate/verify_line_count.py scripts/orchestrator/fallback.py 60 180
PASS: scripts\orchestrator\fallback.py has 141 lines (range [60, 180])
$ python -c "from scripts.orchestrator.fallback import append_failures, insert_fallback_shot, dedupe_fallback_key"
(exit 0)
```

### Task 2 — shorts_pipeline.py
```
$ python scripts/validate/verify_line_count.py scripts/orchestrator/shorts_pipeline.py 500 800
PASS: scripts\orchestrator\shorts_pipeline.py has 787 lines (range [500, 800])

$ grep -c "class ShortsPipeline" scripts/orchestrator/shorts_pipeline.py
1
$ grep -cE "def _run_" scripts/orchestrator/shorts_pipeline.py
13
$ grep -c "def _producer_loop" scripts/orchestrator/shorts_pipeline.py
1
$ grep -c "def _insert_fallback" scripts/orchestrator/shorts_pipeline.py
1
$ grep -c "def _transition_to_complete" scripts/orchestrator/shorts_pipeline.py
1

# Forbidden tokens (grep exit=1 means 'not present')
$ grep -q "skip_gates" scripts/orchestrator/shorts_pipeline.py; echo $?
1
$ grep -qiE "t2v|text_to_video|text2video" scripts/orchestrator/shorts_pipeline.py; echo $?
1
$ grep -q "TODO(next-session)" scripts/orchestrator/shorts_pipeline.py; echo $?
1

# Positive patterns
$ grep -c 'resolution="hd"' scripts/orchestrator/shorts_pipeline.py
2
$ grep -c "verify_all_dispatched" scripts/orchestrator/shorts_pipeline.py
3
$ grep -c "ensure_dependencies" scripts/orchestrator/shorts_pipeline.py
2
```

### Task 3 — 4 test files green
```
$ python -m pytest tests/phase05/test_shorts_pipeline.py tests/phase05/test_pipeline_e2e_mock.py tests/phase05/test_fallback_shot.py tests/phase05/test_low_res_first.py -q --no-cov
24 passed in 0.17s

$ grep -cE "^def test_" tests/phase05/test_shorts_pipeline.py
11
$ grep -cE "^def test_" tests/phase05/test_pipeline_e2e_mock.py
3
$ grep -cE "^def test_" tests/phase05/test_fallback_shot.py
6
$ grep -cE "^def test_" tests/phase05/test_low_res_first.py
4
```

### Full phase05 suite after Wave 5
```
$ python -m pytest tests/phase05/ -q --no-cov
224 passed in 0.50s
```

200 baseline (Plans 01-06) + 24 new Plan 07. No regressions; every sibling plan still green.

### Sentinel grep across scripts/orchestrator/ (after clearing __pycache__)
```
$ rm -rf scripts/orchestrator/**/__pycache__
$ grep -r "skip_gates" scripts/orchestrator/; echo exit=$?
exit=1
$ grep -rE "t2v|text_to_video|text2video" scripts/orchestrator/; echo exit=$?
exit=1
$ grep -r "TODO(next-session)" scripts/orchestrator/; echo exit=$?
exit=1
```
All three sentinel greps exit 1 (no match) — D-8 / D-9 / D-13 physical invariants hold across the entire orchestrator package.

## Self-Check: PASSED

### Files exist
- `scripts/orchestrator/fallback.py` — **FOUND** (141 lines)
- `scripts/orchestrator/shorts_pipeline.py` — **FOUND** (787 lines)
- `scripts/orchestrator/__init__.py` — **FOUND** (modified; re-exports Wave 0-5 primitives)
- `tests/phase05/test_shorts_pipeline.py` — **FOUND** (214 lines, 11 tests)
- `tests/phase05/test_pipeline_e2e_mock.py` — **FOUND** (235 lines, 3 tests)
- `tests/phase05/test_fallback_shot.py` — **FOUND** (197 lines, 6 tests)
- `tests/phase05/test_low_res_first.py` — **FOUND** (167 lines, 4 tests)

### Commits in git log
- `5849ee1` (Task 1 — fallback.py helpers) — **FOUND**
- `031c4ba` (Task 2 — shorts_pipeline.py + __init__.py) — **FOUND**
- `7653492` (Task 3 — 4 test files) — **FOUND**

### Runtime checks
- `python -c "from scripts.orchestrator import ShortsPipeline, GateContext, GATE_INSPECTORS, CircuitBreaker, Checkpointer, GateGuard, Verdict"` → exit 0
- `python -m pytest tests/phase05/ -q --no-cov` → **224 passed**
- `python scripts/validate/verify_line_count.py scripts/orchestrator/shorts_pipeline.py 500 800` → **PASS (787 lines)**
- `python scripts/validate/verify_line_count.py scripts/orchestrator/fallback.py 60 180` → **PASS (141 lines)**
- Recursive grep on `scripts/orchestrator/` for skip_gates / t2v / text_to_video / text2video / TODO(next-session) → **0 matches** (after clearing `__pycache__`)

Ready for Plan 05-08 (hc_checks rewrite — consumes `GATE_INSPECTORS` re-export for `check_hc_10_inspector_coverage`).
