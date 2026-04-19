---
phase: 7
plan: 07-06
subsystem: integration-test
tags: [TEST-04, SC4, fallback, ken-burns, THUMBNAIL, append-only, correction-3]
requires: [07-01, 07-02, 07-03, 07-04]
provides: [TEST-04 coverage, SC4 proof, Correction 3 anchor, Hook bypass-by-naming doctrine]
affects: [tests/phase07/, .planning/phases/07-integration-test/07-VALIDATION.md]
tech-stack:
  added: []
  patterns: [TDD integration test, AST-based anchor guard, Hook bypass-by-naming]
key-files:
  created:
    - tests/phase07/test_fallback_ken_burns_thumbnail.py
    - tests/phase07/test_failures_append_on_retry_exceeded.py
  modified:
    - .planning/phases/07-integration-test/07-VALIDATION.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
decisions:
  - "Anchor test uses AST parsing (not text grep) to detect GateName.THUMBNAIL/ASSETS inside supervisor_side_effect closures — immune to docstring/comment false-positives"
  - "Hook bypass-by-naming: tests deliberately use lowercase 'failures.md' (tmp_path basename) because check_failures_append_only fires only on exact basename 'FAILURES.md'"
  - "Fallback chain anchor locks the standalone-POST contract: ken-burns fires via shotstack.create_ken_burns_clip (not embedded in main render.render)"
metrics:
  duration_minutes: 6
  tasks_completed: 2
  new_tests: 16
  new_lines: 528
  commits: 2
  completed_date: 2026-04-19
---

# Phase 7 Plan 06: Fallback ken-burns THUMBNAIL + FAILURES.md append Summary

TEST-04 locked: THUMBNAIL gate 3×FAIL → append_failures + ken-burns Fallback → COMPLETE without CircuitBreakerOpenError. RESEARCH Correction 3 permanently anchored via AST-based drift guard. FAILURES.md append-only regime proven structurally at both pipeline-run and fallback.py-source levels. Hook bypass-by-naming contract documented and tested.

---

## Deliverables

### 1. `tests/phase07/test_fallback_ken_burns_thumbnail.py` (276 lines, 8 tests)

Proves the ORCH-12 Fallback lane for the THUMBNAIL gate end-to-end:

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_thumbnail_3x_fail_triggers_ken_burns_fallback` | `final_gate == "COMPLETE"`, `dispatched_count == 13`, `fallback_count == 1`, supervisor invoked ≥ 3× on THUMBNAIL |
| 2 | `test_create_ken_burns_clip_called_once` | `ShotstackMock.ken_burns_call_count == 1` |
| 3 | `test_create_ken_burns_clip_duration_positive` | `last_ken_burns_args.duration_s > 0`, `image_path == still_image.jpg` |
| 4 | `test_no_circuit_breaker_open_error_raised` | `CircuitBreakerOpenError` NOT raised (SC4 proof — Fallback lane bypasses breakers) |
| 5 | `test_retry_counts_thumbnail_equals_3` | `pipeline.ctx.retry_counts[GateName.THUMBNAIL] == 3` |
| 6 | `test_fallback_indices_contains_cut_index` | `pipeline.ctx.fallback_indices == [0]` |
| 7 | `test_target_is_thumbnail_not_assets` | **Anchor (AST)**: `GateName.THUMBNAIL in targets`, `GateName.ASSETS not in targets` (inside supervisor closures only) |
| 8 | `test_fallback_chain_reaches_shotstack_create_ken_burns_clip` | standalone-POST contract: `create_ken_burns_clip` called once; `render` called ≥ 1 (independent path) |

### 2. `tests/phase07/test_failures_append_on_retry_exceeded.py` (252 lines, 8 tests)

Proves FAILURES.md append-only format + Hook compatibility:

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_failures_file_exists_after_retry_exhaustion` | `failures_path.exists()` after 3×FAIL |
| 2 | `test_failures_contains_thumbnail_exhausted_marker` | `"THUMBNAIL FAIL after regeneration exhausted"` heading present |
| 3 | `test_failures_contains_session_marker_comment` | `<!-- session:<sid> gate:THUMBNAIL ts:... -->` regex matches |
| 4 | `test_failures_contains_evidence_summary` | `"Evidence (first 3):"` + `"thumbnail_hook_weak"` + `"no face, no caption"` |
| 5 | `test_failures_contains_semantic_feedback` | `"Semantic feedback:"` + `"face + caption missing"` |
| 6 | `test_failures_file_basename_is_lowercase_hook_bypass` | `fp.name == "failures.md"` (NOT `"FAILURES.md"`) — Hook bypass contract |
| 7 | `test_failures_write_is_append_only` | second run's content starts with first run's content, both session ids present |
| 8 | `test_failures_write_mode_is_append_grep_proof` | **Structural**: `fallback.py` source contains `.open("a"` AND zero `.open("w"` patterns |

---

## Chain Exercised (Correction 3 + Pitfall 2)

```
_producer_loop(THUMBNAIL)                           # shorts_pipeline.py:576-625
  retry 1/3 -> supervisor FAIL
  retry 2/3 -> supervisor FAIL
  retry 3/3 -> supervisor FAIL
  exhausted:
    append_failures(tmp_path/failures.md, ...)       # fallback.py:30-64 (open 'a')
    _insert_fallback(THUMBNAIL, last_output)         # shorts_pipeline.py:627-655
      insert_fallback_shot(shotstack, asset_sourcer, prompt, 5.0)
                                                     # fallback.py:67-122
        still_image = asset_sourcer_invoker(prompt)  # tmp_path/still_image.jpg
        fallback_clip = shotstack.create_ken_burns_clip(
            image_path=still_image,
            duration_s=5.0,
            scale_from=1.0, scale_to=1.15,
            pan_direction="left_to_right",
        )                                            # shotstack.py:155-216 (mock returns Path)
      ctx.fallback_indices.append(0)                 # shorts_pipeline.py:649
      return fallback dict (is_fallback=True)

back in _run_thumbnail:                              # shorts_pipeline.py:508-521
  verdict = supervisor_invoker(THUMBNAIL, fallback_dict)   # 4th call -> PASS
  gate_guard.dispatch(THUMBNAIL, PASS)

... METADATA/UPLOAD/MONITOR proceed normally ...
_transition_to_complete() -> all 13 gates verified -> COMPLETE
```

---

## Pipeline Result (from E2E run)

```python
result = pipeline.run()
# result == {
#     "session_id": "sid_fb_1",
#     "final_gate": "COMPLETE",
#     "dispatched_count": 13,
#     "fallback_count": 1,
# }
pipeline.ctx.retry_counts[GateName.THUMBNAIL] == 3
pipeline.ctx.fallback_indices == [0]
shotstack.ken_burns_call_count == 1
shotstack.last_ken_burns_args == {
    "image_path": tmp_path / "still_image.jpg",
    "duration_s": 5.0,
    "scale_from": 1.0,
    "scale_to": 1.15,
    "pan_direction": "left_to_right",
}
```

---

## failures.md Actual Sample (from real test run)

```markdown

<!-- session:sid_fa_2 gate:THUMBNAIL ts:2026-04-19T18:27:34.128456+00:00 -->
## sid_fa_2 THUMBNAIL FAIL after regeneration exhausted

- **Timestamp:** 2026-04-19T18:27:34.128456+00:00
- **Evidence (first 3):** thumbnail_hook_weak: no face, no caption
- **Semantic feedback:** face + caption missing
```

---

## RESEARCH Correction 3 — Permanently Anchored

**Claim:** ken-burns Fallback targets the THUMBNAIL gate, NOT ASSETS.

**Reason:**
- `_producer_loop` is invoked by 10 of 13 gates; `_run_assets` has its own Kling→Runway failover path.
- The `if gate in (GateName.ASSETS, GateName.THUMBNAIL)` filter at `shorts_pipeline.py:621` gates Fallback eligibility.
- **Intersection**: {THUMBNAIL} only.

**Guard (test #7 above):** `test_target_is_thumbnail_not_assets` AST-parses this test file and inspects every function whose name starts with `supervisor` (i.e., all `supervisor_side_effect` closures). Asserts:
- `"THUMBNAIL" in target_gate_names`
- `"ASSETS" not in target_gate_names`

If a future developer flips the target from THUMBNAIL to ASSETS, the anchor test fails immediately — guarding Correction 3 against silent drift.

---

## Hook Bypass-by-Naming Contract

**Hook:** `.claude/hooks/pre_tool_use.py::check_failures_append_only`
**Trigger:** basename exactly equals `"FAILURES.md"` (case-sensitive, line 184)
**Phase 7 tests:** use `tmp_path / "failures.md"` (lowercase `f`) — basename is `"failures.md"`, NOT `"FAILURES.md"` — Hook does NOT fire during test runs.

**Tested explicitly:** `test_failures_file_basename_is_lowercase_hook_bypass` asserts:
- `fp.name == "failures.md"`
- `fp.name != "FAILURES.md"`
- `tmp_path in fp.parents` (no bleed into real `.claude/failures/`)

---

## Regression Sweep

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov
============================= 941 passed in 75.52s ==============================
```

Baseline (STATE session #20) was 911 before this wave. Wave 3b added:
- Plan 07-05 (parallel, CircuitBreaker): +14 tests
- Plan 07-06 (this plan, Fallback ken-burns): +16 tests
- **Total Wave 3b delta:** +30 tests, 911 → 941

---

## Commits

- `cbacaad` test(07-06): GREEN — THUMBNAIL 3x retry → ken-burns → COMPLETE (Task 1)
- `31ccfb3` test(07-06): GREEN — append-only FAILURES.md respected + Hook bypass-by-naming (Task 2)

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] AST-based anchor replaced text grep for Correction 3 guard**

- **Found during:** Task 1 initial run
- **Issue:** Plan proposed `assert "GateName.ASSETS\"" not in src.replace(...)` (text-level grep) but the anchor test's own docstring mentions `GateName.ASSETS` as a forbidden example, causing the test to FAIL on its own text.
- **Fix:** Switched to `ast.parse()` + walk the tree, collecting `GateName.<NAME>` attribute accesses inside functions whose names start with `supervisor` (i.e., `supervisor_side_effect` closures — the actual structural lever). This is stricter AND correctly ignores narrative text.
- **Files modified:** `tests/phase07/test_fallback_ken_burns_thumbnail.py` (test_target_is_thumbnail_not_assets)
- **Commit:** cbacaad (landed as part of Task 1 GREEN)

**2. [Rule 3 - Blocking] Plan-sample used dotted import for self-source read; tests/ has no package marker**

- **Found during:** Task 1 initial run
- **Issue:** Plan wrote `import tests.phase07.test_fallback_ken_burns_thumbnail as self_module` but `tests/` has no `__init__.py` (Plan 07-03 precedent — intentional, to avoid altering Phase 4/5/6 resolution).
- **Fix:** Read self-source via `Path(__file__).read_text(encoding="utf-8")` then `ast.parse()`. Identical semantics, zero package-layout side effects.
- **Files modified:** `tests/phase07/test_fallback_ken_burns_thumbnail.py`
- **Commit:** cbacaad

**3. [Rule 2 - Missing Critical Functionality] Wave-1 TTS mocks return list[dict] but pipeline._run_voice iterates AudioSegment.path**

- **Found during:** Task 1 scaffolding (carried over from Plan 07-03/07-04 precedent)
- **Issue:** `TypecastMock.generate` / `ElevenLabsMock.generate_with_timestamps` return `list[dict]` per D-18/D-19 unit contracts, but `ShortsPipeline._run_voice` iterates `seg.path` which is an `AudioSegment` attribute.
- **Fix:** Per-test override `typecast.generate = lambda *a, **kw: []` + same for elevenlabs — mirrors Plan 07-03 E2E precedent. Keeps Wave-1 mocks honest at their unit contracts AND allows E2E pipeline walks.
- **Files modified:** `tests/phase07/test_fallback_ken_burns_thumbnail.py`, `tests/phase07/test_failures_append_on_retry_exceeded.py`
- **Commit:** cbacaad + 31ccfb3

### None else

Plan 07-06 executed substantially as written. 8 tests per file ≥ the 6 required per acceptance criteria; AST anchor replaces text grep but preserves the Correction 3 guarantee.

---

## Authentication Gates Encountered

None.

---

## Known Stubs

None. All tests wire real ShortsPipeline + real Wave-1 mock adapters via dependency injection; no placeholder data flows through to assertions. The `still_image.jpg` path is a real 0-byte fixture on disk (Don't Hand-Roll D-2), and the mock `ShotstackMock.ken_burns_path` returns a real Path object.

---

## Self-Check: PASSED

**Verified deliverables:**
- ✅ `tests/phase07/test_fallback_ken_burns_thumbnail.py` exists (276 lines, 8 tests, all green)
- ✅ `tests/phase07/test_failures_append_on_retry_exceeded.py` exists (252 lines, 8 tests, all green)
- ✅ Commit `cbacaad` present in `git log`
- ✅ Commit `31ccfb3` present in `git log`
- ✅ Regression 941/941 green (Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 132)
- ✅ Acceptance criteria grep checks all pass (≥ threshold on every pattern)
- ✅ Parallel boundary respected: zero file overlap with Plan 07-05 (07-05 owned test_circuit_breaker_3x_open.py + test_cooldown_300s_enforced.py; 07-06 owned test_fallback_ken_burns_thumbnail.py + test_failures_append_on_retry_exceeded.py)
