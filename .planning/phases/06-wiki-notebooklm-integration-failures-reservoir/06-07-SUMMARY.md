---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 07
subsystem: wave-3-shotstack-continuity-injection
tags: [shotstack, d-9, d-19, d-20, wiki-02, continuity-prefix, filter-chain-first, keystone, phase06-regression]

# Dependency graph
requires:
  - phase: 06
    plan: 06
    provides: scripts/orchestrator/api/models.py::ContinuityPrefix + HexColor (D-20 pydantic schema with extra='forbid' + 7 D-10 fields), wiki/continuity_bible/prefix.json (canonical 7-field form matching schema byte-for-byte)
  - phase: 06
    plan: 02
    provides: wiki/continuity_bible/prefix.json (initial serialization with 7 D-10 fields post-normalisation in Plan 06)
  - phase: 05
    provides: scripts/orchestrator/api/shotstack.py (ShotstackAdapter render / _build_timeline_payload / _post_render public surface; D-17 FILTER_ORDER tuple; DEFAULT_RESOLUTION='hd' ORCH-11 anchor; tests/phase05/test_shotstack_adapter.py 16-test baseline), tests/phase05/test_line_count.py (400-line soft cap on shotstack.py)
  - plan: 06-PLAN metadata
    provides: CONTEXT D-9 (ShotstackAdapter direct injection, no manual copy) + D-19 (filter order canonical with continuity_prefix FIRST) + D-20 (pydantic contract) + RESEARCH §Area 5 lines 692-797 (injection template) + §Pitfall 4 lines 1275-1280 (filter reorder anti-pattern with exact-equality test)
provides:
  - scripts/orchestrator/api/shotstack.py (DEFAULT_CONTINUITY_PRESET_PATH module constant + _load_continuity_preset() lazy loader + _build_timeline_payload filter[0] injection with idempotency + ContinuityPrefix import; 369 → 397 lines, +28 under 400 soft cap)
  - tests/phase06/test_shotstack_prefix_injection.py (11 unit tests — loader contract across missing/valid/drift/invalid-HEX paths, default path shape, real prefix.json via module default, adapter injection seam, None path, idempotency, preset dump presence + None when missing)
  - tests/phase06/test_filter_order_preservation.py (6 integration tests — exact-list equality D-19 invariant, D-17 tail contiguous guard, caller-supplied tail preserved, empty filters_order safe, caller list not mutated, Phase 5 class constants still resolvable)
  - tests/phase05/test_shotstack_adapter.py::test_render_payload_carries_d17_filter_order (monkeypatched _load_continuity_preset→None to decouple Phase 5 D-17 tail assertion from wiki/continuity_bible/prefix.json presence; keeps Phase 5 contract stable)
affects:
  - 06-08..11-PLAN (Shotstack render pipeline now carries Continuity Bible; downstream wave-4 harness audits can assume visual DNA injection is a hard contract)
  - Phase 7 integration/E2E harness (render-time D-19 invariant is test-asserted; any future ken-burns fallback or new filter will be guarded by test_filter_order_preservation.py)
  - Phase 5 shotstack_adapter regression (one test's assertion isolated via monkeypatch; semantic meaning preserved — test now explicitly targets the pre-injection D-17 tail rather than the post-injection canonical)

# Tech tracking
tech-stack:
  added: []  # pure pydantic v2 + stdlib Path; no new runtime deps
  patterns:
    - "Lazy filesystem-sensitive preset loader returning None on file absence: _load_continuity_preset(path=None) with path override kwarg. Default resolves against cwd so CI runners and dev boxes both work; tests override with tmp_path to avoid cwd coupling. The Optional[ContinuityPrefix] return type + no-raise-on-missing contract is the clean decoupler for Phase 7 env matrix variance (prefix.json may or may not be on disk in a given smoke check)."
    - "Filter-chain injection via list prepend NOT mutation: filters_order = ['continuity_prefix', *filters_order]. Never mutates the caller's list; test_injection_without_mutating_caller_list specifically guards this. Idempotency check (if filters_order[0] != 'continuity_prefix') so caller pre-injection is a no-op, not a double-prepend."
    - "D-19 invariant asserted by exact list equality, not set membership or substring: payload['timeline']['filters'] == ['continuity_prefix', 'color_grade', 'saturation', 'film_grain']. This is the Pitfall 4 defence — re-ordering ('continuity_prefix' → middle) fails the exact-equality check immediately, while a set comparison would hide a reorder."
    - "Phase 5 regression isolation via monkeypatch: test_render_payload_carries_d17_filter_order now stubs _load_continuity_preset to None. This lets the Phase 5 test assert pure D-17 tail semantics (independent of wiki/continuity_bible/prefix.json filesystem state) while Phase 6 tests own the post-injection D-19 canonical. Cleaner than either deleting the test (loses Phase 5 meaning) or coupling to wiki/ files (fragile)."
    - "shotstack.py line-count management: initial implementation pushed file to 432 lines (cap 400 per tests/phase05/test_line_count.py). Rule 1 auto-fix compacted 3 docstrings + 1 inline comment block to 397 lines (3-line headroom). Pattern mirrors Plan 06-06's models.py 181 → 164 compaction: single-line Field()-style descriptors preserved information while shaving line count."

key-files:
  created:
    - tests/phase06/test_shotstack_prefix_injection.py (226 lines, 11 tests)
    - tests/phase06/test_filter_order_preservation.py (152 lines, 6 tests)
  modified:
    - scripts/orchestrator/api/shotstack.py (369 → 397 lines, +28. Added `ContinuityPrefix` to existing `.models` import; DEFAULT_CONTINUITY_PRESET_PATH module constant; _load_continuity_preset() lazy loader; injection block + continuity_preset dump at top of _build_timeline_payload; zero existing-line deletions.)
    - tests/phase05/test_shotstack_adapter.py (195 → 214 lines, +19. test_render_payload_carries_d17_filter_order now monkeypatches _load_continuity_preset→None + documents Phase 6 Plan 07 interaction in its docstring. 15 other tests byte-identical.)
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-07-01 + 6-07-02 flipped "❌ W0 / ⬜ pending" → "✅ on disk / ✅ green")

key-decisions:
  - "Phase 5 test isolation (monkeypatch, not deletion). test_render_payload_carries_d17_filter_order was failing after GREEN because it calls adapter.render() against the real filesystem (which has wiki/continuity_bible/prefix.json courtesy Plan 02 + Plan 06), so the 3-element D-17 tail assertion became ['continuity_prefix', 'color_grade', 'saturation', 'film_grain']. Three options: (a) delete the Phase 5 test (loses its regression meaning for the non-injected case), (b) update it to 4-element form (conflates Phase 5 D-17 with Phase 6 D-19 — two different invariants on one test), (c) monkeypatch _load_continuity_preset to None so the test asserts the PRE-injection D-17 tail in isolation. Picked (c). This mirrors the cleanest separation: Phase 5 owns 'when no preset is present, D-17 tail is exactly these 3 filters in this order'; Phase 6 owns 'when a preset IS present, D-19 prepends continuity_prefix at index 0'. Both contracts survive independently. The 19-line delta is entirely docstring + monkeypatch setup — assertion semantics unchanged."
  - "Docstring compaction to respect tests/phase05/test_line_count soft cap 400 on shotstack.py. Initial implementation added ~63 lines (helper docstring with Parameters section + injection-method docstring with 10-line explanation + 5-line continuity_preset inline comment), pushing the file to 432 lines. Rule 1 auto-fix: compacted to terse single-line + 1-sentence docstrings referencing Plan 07 / D-9 / D-19 / D-20 numerals. Information preserved in PLAN.md, RESEARCH.md §Area 5, and this SUMMARY. Net: 397 lines (3-line headroom). No behaviour change — all 17 new tests still green, Phase 5 329/329 still green."
  - "RED→GREEN commit split per Plan 07 Task 1 tdd='true' contract. Tests shipped in RED commit (b20ba21: 16 of 17 tests failing with AttributeError on _load_continuity_preset / DEFAULT_CONTINUITY_PRESET_PATH; 1 passing = the Phase 5 class-constant regression guard). Implementation shipped in GREEN commit (20cdeed: shotstack.py injection + Phase 5 test monkeypatch). Bisect can pinpoint (a) the exact commit that introduced the D-19 contract (20cdeed) and (b) the exact commit that introduced the test invariant (b20ba21); both are now git-archaeology anchors for future regressions."
  - "Idempotency guard (filters_order[0] != 'continuity_prefix') over silent pass-through. Chose explicit check that the first element is already 'continuity_prefix' rather than implicit de-duplication later. Reason: if a future caller passes ['continuity_prefix', 'color_grade', ...] intentionally (testing the invariant, or a pre-composed request builder), the adapter does the right thing without double-prepending. Test test_adapter_idempotent_against_caller_prepend pins this contract."

patterns-established:
  - "Pattern: wiki artefact → pydantic model → adapter injection trilogy. WIKI-02 is now wired end-to-end: (a) wiki/continuity_bible/channel_identity.md narrative, (b) wiki/continuity_bible/prefix.json JSON artefact, (c) scripts/orchestrator/api/models.py::ContinuityPrefix schema, (d) scripts/orchestrator/api/shotstack.py::_load_continuity_preset + _build_timeline_payload injection. The flow (a→b→c→d) means a single edit to channel_identity.md's canonical HEX palette propagates through prefix.json validation to every future render call. Future wiki nodes consumed by API adapters should follow this same 4-step pattern."
  - "Pattern: Optional-return lazy loader decouples wiki-filesystem presence from adapter construction. _load_continuity_preset(path=None) → ContinuityPrefix | None. The ShotstackAdapter.__init__ never reads filesystem; the loader is called only inside _build_timeline_payload (render time). This is the cleanest way to stay lazy: adapter construction is cheap and testable without wiki/ present, and the filesystem read happens exactly when needed (per render). Future API adapters consuming wiki artefacts should mirror this (loader separate from __init__; None-return on missing file)."
  - "Pattern: Phase-boundary test isolation via monkeypatch. When Phase N introduces a new invariant that the Phase N-1 test did not anticipate, the cleanest fix is monkeypatching the new contract's seam to the Phase N-1 value within the Phase N-1 test. Preserves the Phase N-1 contract as an independent assertion. Alternatives (deleting, upgrading to 4-element form, wrapping with version checks) all lose information or couple contracts. This pattern will repeat in Phase 7 (harness audits introducing new filter guards) and Phase 8 (upscale pipeline adding a post-D-17 filter)."

requirements-completed: [WIKI-02]

# Metrics
duration: ~6m
completed: 2026-04-19
---

# Phase 6 Plan 07: Shotstack Continuity Prefix Injection Summary

**KEYSTONE wave-3 wiring: ShotstackAdapter now auto-prepends "continuity_prefix" at filters_order[0] whenever wiki/continuity_bible/prefix.json exists, making every Shotstack render automatically carry the channel's visual DNA (color palette, camera lens, Korean-senior audience profile, BGM mood). D-17 Phase 5 tail (color_grade → saturation → film_grain) preserved byte-identical. 17 new tests (11 unit + 6 integration) lock the D-19 canonical invariant by exact list equality; Phase 5 329/329 regression green via monkeypatch-based test isolation; models.py + prefix.json trilogy from Plan 06 now fully consumed at runtime.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-04-19T08:09:14Z
- **Completed:** 2026-04-19T08:15:36Z
- **Tasks:** 2 / 2 complete (Task 1 TDD RED + GREEN; Task 2 test files shipped in RED commit)
- **Files created:** 2 (both test files)
- **Files modified:** 3 (shotstack.py, tests/phase05/test_shotstack_adapter.py, 06-VALIDATION.md)
- **Tests added:** 17 (11 unit + 6 integration)
- **Phase 5 regression:** 329/329 PASS (16/16 shotstack_adapter, 1 Phase 5 test updated via monkeypatch isolation)
- **Phase 6 full suite:** 140/140 PASS (123 prior + 17 new)
- **Full repo suite:** 713/713 PASS
- **shotstack.py line delta:** +28 (369 → 397 lines, 3-line headroom under 400 soft cap)

## Accomplishments

### Task 1 — Shotstack Adapter Preset Injection (GREEN)

`scripts/orchestrator/api/shotstack.py` now contains:

1. **Import extension** — `from .models import ContinuityPrefix, ShotstackRenderRequest` (extended, not duplicated)
2. **Module constant** — `DEFAULT_CONTINUITY_PRESET_PATH = Path("wiki/continuity_bible/prefix.json")` (near DEFAULT_OUTPUT_DIR per CONTEXT D-9 placement)
3. **Lazy loader** — `_load_continuity_preset(path: Path | None = None) -> ContinuityPrefix | None`
   - Returns `None` when file absent (graceful degradation)
   - Raises `pydantic.ValidationError` on schema drift / out-of-range / malformed HEX (D-20 Pitfall 5 fail-fast)
   - `path` override for unit tests
4. **Injection seam inside `_build_timeline_payload`** — prepends `"continuity_prefix"` to `filters_order` when preset is loaded, with idempotency guard (`filters_order[0] != "continuity_prefix"`) so caller pre-injection is a no-op. The caller's list is NOT mutated in place.
5. **Payload emits `continuity_preset`** — `timeline.continuity_preset = preset.model_dump()` (or `None` when preset missing) so downstream Shotstack consumers can introspect the applied DNA.

### Task 2 — D-19 Invariant Tests

**`tests/phase06/test_shotstack_prefix_injection.py`** (11 tests):

1. `test_load_preset_returns_none_when_missing` — graceful degradation
2. `test_load_preset_returns_model_when_valid` — parsed model shape
3. `test_load_preset_raises_on_schema_drift` — extra='forbid' Pitfall 5 guard
4. `test_load_preset_raises_on_invalid_hex` — HexColor regex guard
5. `test_default_path_points_at_wiki_continuity_bible` — D-9 location anchor
6. `test_real_prefix_json_loads_via_default` — end-to-end wiki/continuity_bible/prefix.json resolution via module default
7. `test_adapter_injects_prefix_at_position_zero` — D-19 filter[0] assertion
8. `test_adapter_no_injection_when_preset_missing` — None path preserves caller's order
9. `test_adapter_idempotent_against_caller_prepend` — no double-prepend
10. `test_timeline_payload_includes_continuity_preset_dump` — model_dump presence
11. `test_timeline_payload_continuity_preset_none_when_missing` — explicit None on missing preset

**`tests/phase06/test_filter_order_preservation.py`** (6 tests):

1. `test_d19_filter_order_exact_equality` — `filters == ['continuity_prefix','color_grade','saturation','film_grain']` asserted by EXACT list equality (Pitfall 4 defence)
2. `test_d17_tail_contiguous_after_injection` — indices verify `saturation == color_grade+1` and `film_grain == saturation+1`
3. `test_caller_supplied_order_prepended_not_replaced` — caller's tail (even non-standard like `[..., 'vignette']`) is preserved; prefix is PREPENDED not SUBSTITUTED
4. `test_no_injection_does_not_break_empty_filters_order` — edge case: empty filters_order + no preset → still empty, no crash
5. `test_injection_without_mutating_caller_list` — caller's list object is not mutated
6. `test_phase5_shotstack_adapter_still_imports` — regression: Phase 5 class-level constants (`FILTER_ORDER`, `DEFAULT_RESOLUTION`, `DEFAULT_ASPECT`) unchanged

## Filter Order Before/After Demonstration

**Before Plan 07 (Phase 5 baseline):**

```python
# adapter.render(timeline) with default args
payload["timeline"]["filters"] == ["color_grade", "saturation", "film_grain"]  # D-17 only
```

**After Plan 07 (Phase 6 WIKI-02 wired):**

```python
# adapter.render(timeline) with default args AND wiki/continuity_bible/prefix.json on disk
payload["timeline"]["filters"] == ["continuity_prefix", "color_grade", "saturation", "film_grain"]  # D-19
payload["timeline"]["continuity_preset"] == {
    "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
    "warmth": 0.2,
    "focal_length_mm": 35,
    "aperture_f": 2.8,
    "visual_style": "cinematic",
    "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
    "bgm_mood": "ambient",
}

# adapter.render(timeline) when prefix.json absent (graceful degradation)
payload["timeline"]["filters"] == ["color_grade", "saturation", "film_grain"]  # D-17 tail unchanged
payload["timeline"]["continuity_preset"] is None
```

## Live Runtime Verification

```
$ python -c "from scripts.orchestrator.api.shotstack import ShotstackAdapter, _load_continuity_preset
  preset = _load_continuity_preset(); print('preset loaded:', preset is not None)
  a = ShotstackAdapter(api_key='test')
  p = a._build_timeline_payload(
      serialised_entries=[{'kind':'clip','start':0,'end':1,'clip_path':'/x','speed':1.0,'audio_path':'/a'}],
      resolution='hd', aspect_ratio='9:16',
      filters_order=['color_grade','saturation','film_grain'])
  print('filter order:', p['timeline']['filters'])
  print('continuity_preset.visual_style:', p['timeline']['continuity_preset']['visual_style'])"
preset loaded: True
filter order: ['continuity_prefix', 'color_grade', 'saturation', 'film_grain']
continuity_preset.visual_style: cinematic
```

D-19 canonical invariant confirmed live against the real wiki/continuity_bible/prefix.json.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Phase 5 `test_render_payload_carries_d17_filter_order` regression after GREEN**

- **Found during:** Task 1 GREEN verification (Phase 5 regression run)
- **Issue:** The Phase 5 test `test_render_payload_carries_d17_filter_order` calls `adapter.render(timeline)` which exercises the real filesystem (where `wiki/continuity_bible/prefix.json` exists after Plan 02 + Plan 06). Post-GREEN, the filter chain became `['continuity_prefix', 'color_grade', 'saturation', 'film_grain']` (correct per D-19), but the test asserted the 3-element D-17 tail. 1/16 Phase 5 shotstack_adapter tests failed.
- **Fix:** Added `monkeypatch.setattr(_shotstack_mod, "_load_continuity_preset", lambda path=None: None)` to the Phase 5 test so it asserts the PRE-injection D-17 tail in isolation. Documented the Phase 6 Plan 07 interaction in the test's docstring. Assertion semantics preserved — the test still asserts `filters == ["color_grade", "saturation", "film_grain"]` in the "no preset" state. Phase 6 Plan 07 owns the post-injection D-19 canonical in its own test file.
- **Files modified:** `tests/phase05/test_shotstack_adapter.py`
- **Commit:** `20cdeed`
- **Rationale:** Alternatives considered: (a) delete the test (loses Phase 5 regression meaning), (b) update it to 4-element form (couples Phase 5 and Phase 6 contracts onto one test). Monkeypatch isolation keeps both contracts independent and clearly attributable.

**2. [Rule 1 - Bug] shotstack.py 400-line soft cap breach**

- **Found during:** Task 1 GREEN verification (`tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps` failed)
- **Issue:** Initial verbose docstrings for `_load_continuity_preset` (Parameters section) + `_build_timeline_payload` (multi-paragraph) + inline `continuity_preset` comment pushed shotstack.py to 432 lines. Soft cap = 400.
- **Fix:** Compacted docstrings to single-sentence form with D-9/D-19/D-20 numeric anchors; inlined comment block. Final: 397 lines (3-line headroom). Behaviour unchanged; all 17 new tests still green.
- **Files modified:** `scripts/orchestrator/api/shotstack.py`
- **Commit:** `20cdeed` (same GREEN commit)

### Rule 4 Checkpoints

None — all deviations inline-fixable per Rules 1/2/3.

## Regression / Test Status

| Scope | Tests | Status |
|-------|-------|--------|
| tests/phase06/test_shotstack_prefix_injection.py | 11 | ✅ |
| tests/phase06/test_filter_order_preservation.py | 6 | ✅ |
| tests/phase06/ (full) | 140 | ✅ (123 prior + 17 new) |
| tests/phase05/test_shotstack_adapter.py | 16 | ✅ (1 test updated via monkeypatch; semantics preserved) |
| tests/phase05/ (full) | 329 | ✅ |
| tests/ (full repo) | 713 | ✅ |
| python import smoke test | `from scripts.orchestrator.api.shotstack import _load_continuity_preset, DEFAULT_CONTINUITY_PRESET_PATH, ShotstackAdapter` | ✅ |
| shotstack.py line count | 397 / 400 soft cap | ✅ (3-line headroom) |

## Commits

- `b20ba21` — `test(06-07): add failing tests for Shotstack Continuity Prefix injection (RED)` — 2 files / +378 lines / 16 failing tests + 1 Phase 5-constant guard passing
- `20cdeed` — `feat(06-07): inject Continuity Prefix at Shotstack filter[0] (D-9 / D-19 GREEN)` — 2 files / +50/-3 lines / 17 new tests green + Phase 5 329/329 preserved

## Acceptance Criteria

### Task 1 (shotstack.py injection)

- [x] `python -c "from scripts.orchestrator.api.shotstack import _load_continuity_preset, DEFAULT_CONTINUITY_PRESET_PATH; print('OK')"` exits 0
- [x] `grep -c "_load_continuity_preset" scripts/orchestrator/api/shotstack.py` = 2 (≥2)
- [x] `grep -c "ContinuityPrefix" scripts/orchestrator/api/shotstack.py` = 5 (≥2)
- [x] `grep -c "continuity_prefix" scripts/orchestrator/api/shotstack.py` = 3 (≥1)
- [x] `grep -c "DEFAULT_CONTINUITY_PRESET_PATH" scripts/orchestrator/api/shotstack.py` = 2 (≥2)
- [x] `grep -c "continuity_preset" scripts/orchestrator/api/shotstack.py` = 3 (≥1)
- [x] `grep -c "class ShotstackAdapter" scripts/orchestrator/api/shotstack.py` = 1 (exactly)
- [x] Phase 5 `tests/phase05/test_shotstack_adapter.py` 16/16 green

### Task 2 (tests)

- [x] `python -m pytest tests/phase06/test_shotstack_prefix_injection.py -q --no-cov` = 11 passed
- [x] `python -m pytest tests/phase06/test_filter_order_preservation.py -q --no-cov` = 6 passed
- [x] `grep -cE "^def test_" tests/phase06/test_shotstack_prefix_injection.py` = 11 (≥10)
- [x] `grep -cE "^def test_" tests/phase06/test_filter_order_preservation.py` = 6 (≥5)
- [x] `grep -c 'continuity_prefix' tests/phase06/test_filter_order_preservation.py` = 5 (≥2)
- [x] `grep -c 'color_grade.*saturation.*film_grain' tests/phase06/test_filter_order_preservation.py` = 8 (≥1)
- [x] Phase 5 regression: `python -m pytest tests/phase05/ -q --no-cov` = 329 passed

## Known Stubs

None. WIKI-02 is now fully wired end-to-end:

- `wiki/continuity_bible/channel_identity.md` (narrative source of truth)
- `wiki/continuity_bible/prefix.json` (canonical 7-field D-20 serialization)
- `scripts/orchestrator/api/models.py::ContinuityPrefix` (pydantic v2 contract)
- `scripts/orchestrator/api/shotstack.py::_load_continuity_preset + _build_timeline_payload` (runtime injection at filter[0])

Every Shotstack render call now automatically carries the channel's visual DNA unless `prefix.json` is physically absent (in which case graceful degradation).

## Self-Check: PASSED

- [x] `scripts/orchestrator/api/shotstack.py` exists and contains `_load_continuity_preset`, `DEFAULT_CONTINUITY_PRESET_PATH`, injection block (FOUND)
- [x] `tests/phase06/test_shotstack_prefix_injection.py` created, 226 lines, 11 tests, all green (FOUND)
- [x] `tests/phase06/test_filter_order_preservation.py` created, 152 lines, 6 tests, all green (FOUND)
- [x] Commit `b20ba21` (RED) in git log (FOUND)
- [x] Commit `20cdeed` (GREEN) in git log (FOUND)
- [x] Phase 5 329/329 tests still green (FOUND)
- [x] shotstack.py 397 lines under 400 cap (FOUND)
- [x] D-19 filter order exact equality asserted (FOUND)
- [x] Deviation Rule 1 auto-fixes documented (Phase 5 test isolation + docstring compaction)
