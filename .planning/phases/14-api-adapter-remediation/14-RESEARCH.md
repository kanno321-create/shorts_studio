# Phase 14: API Adapter Remediation — Research

**Researched:** 2026-04-21
**Domain:** Brownfield adapter test remediation + contract hardening + drift prevention
**Confidence:** HIGH (direct pytest evidence of all 15 failures + adapter files inspected)

---

## Summary

15 pre-existing pytest failures across `tests/phase05` / `tests/phase06` / `tests/phase07` were frozen out-of-scope at the Phase 9.1 gate (per `09.1-VERIFICATION.md` Bucket A 3 + Bucket B 9 + 3 cascade). Phase 12 also deferred. Phase 14's job is to (a) transition all 15 failures → green, (b) introduce a **structural contract-test layer** under `tests/adapters/` that codifies schema + retry + fault-injection + fallback regulations for 7 adapters, (c) register a **`@pytest.mark.adapter_contract`** marker in a root-level `pytest.ini` (currently absent) so the contract suite can be run in isolation, and (d) document everything in `wiki/render/adapter_contracts.md` (wiki/render/ already exists and hosts `remotion_kling_stack.md` + `i2v_prompt_engineering.md` — natural home).

The good news: 13 of 15 failures are trivially mechanical (5 pre-existing Phase 6 drift + 5 transitive aggregator cascades + 3 Phase 9.1 evolution). Only 1 adapter code change is required (the Runway model rename `gen4.5` vs legacy `gen3_alpha_turbo` already landed; the Phase 5 test is the thing that drifted). The "cleanup" work is mostly **test-to-code synchronization**, not adapter rewriting. Fault injection rails already exist in `tests/phase07/mocks/` — contract tests reuse them.

**Primary recommendation:** Remediate in a **single Wave** ordered as (1) non-cascade atoms first (test_blacklist_grep, test_runway, test_line_count, test_moc_linkage, test_notebooklm_wrapper), (2) then run the 5 aggregators green by construction, (3) then introduce `tests/adapters/` with contract tests reusing existing Mocks, (4) register marker + optional Hook, (5) author `wiki/render/adapter_contracts.md`. No new agents. No adapter code rewrite beyond 1-2 docstring/assertion tweaks on `veo_i2v.py` T2V-pattern self-reference.

---

## User Constraints (from Phase 14 scope + CLAUDE.md)

### Locked Decisions (from ROADMAP Phase 14 + REQUIREMENTS ADAPT-01~06 + session #27 multiSelect)
- **D-1**: Adapter contract tests live at `tests/adapters/test_{adapter}_contract.py` (new directory — not `tests/phase14/`). Reason: contract tests span all phases, not phase-owned; matches ADAPT-05 wiki/docs placement cross-cutting rationale.
- **D-2**: `wiki/render/adapter_contracts.md` (NOT `docs/adapter_contracts.md`) — wiki/render/ is the active render-stack documentation home (already hosts `remotion_kling_stack.md`, `i2v_prompt_engineering.md`, `MOC.md`). `docs/` is not yet used for this purpose in this project.
- **D-3**: 7 adapters covered: kling, runway, veo_i2v, typecast, elevenlabs, shotstack, whisperx. `whisperx` has no module in `scripts/orchestrator/api/` (current subtitle alignment path uses elevenlabs `convert_with_timestamps` + D-10 `_chars_to_words`) — treat whisperx row as **"deferred / not yet implemented" documentation stub** rather than demanding a contract test against non-existent code.
- **D-4**: Pytest marker `@pytest.mark.adapter_contract` registered in new root-level `pytest.ini` (the repo currently has no `pytest.ini`, `pyproject.toml`, or `setup.cfg` — marker registration must create one, minimally).
- **D-5**: Fault injection contract is **reusable from `tests/phase07/mocks/`** — mocks already ship `allow_fault_injection=False` default (D-3 Phase 7) + `circuit_3x` / `runway_failover` modes. Contract tests must verify the `allow_fault_injection=False` production-safe default as INVARIANT.
- **D-6**: No real API calls in contract tests — httpx/SDK seams are monkey-patched exactly as Phase 5 `test_shotstack_adapter.py` / `test_elevenlabs_adapter.py` already do.
- **D-7**: CLAUDE.md forbid #4 — **no T2V / text_to_video / t2v**. `veo_i2v.py` already enforces via T2VForbidden; contract tests must re-verify I2V-only.
- **D-8**: CLAUDE.md forbid #3 — no silent try/except fallbacks. Adapters already use explicit raise; contract tests verify error paths.
- **D-9**: CLAUDE.md forbid #9 — no new agents (32 agent cap). Phase 14 is testing/docs only, no agent changes.

### Claude's Discretion
- **Hook extension for adapter file edits** (ADAPT-06c "optional"): recommendation = **defer to Phase 15 / deferred-items.md** unless trivial. Current `pre_tool_use.py` checks deprecated_patterns.json regexes; extending it to require a corresponding `tests/adapters/test_*_contract.py` test on every adapter edit is a strictly additive Hook, but rules out quick adapter docstring fixes without updating tests. Safer recommendation: add a **soft warning** (not deny) when an adapter file is edited without a contract test touch — or defer entirely to Phase 15.
- **Line-count cap adjustment strategy** for `elevenlabs.py` (350 > 340) and `shotstack.py` (414 > 400): two options — (a) raise soft caps to 360 / 420 respectively with RESEARCH-cited rationale (Phase 9.1 D-11 + D-13 intentional growth), (b) split files into submodules. Option (a) recommended — splitting creates import churn for zero safety gain.
- **Contract schema format**: pydantic BaseModel (reuses existing `scripts/orchestrator/api/models.py` infrastructure with `I2VRequest`, `ShotstackRenderRequest`, `ContinuityPrefix`) vs `typing.TypedDict` vs `jsonschema`. Recommend pydantic v2 — already in use, fail-fast ValidationError, same pattern as existing Phase 6 `ContinuityPrefix` (Plan 06-06).

### Deferred Ideas (OUT OF SCOPE — do not research)
- whisperx module creation (stub row in contract doc only; implementation = separate phase).
- Real API smoke runs against ElevenLabs/Shotstack/Veo (that's Phase 13's scope — SMOKE-01~06).
- Runway adapter removal (deferred-items.md §2.1 — Phase 10 batch window, but no work in Phase 14).
- Kling NEG_PROMPT hardcode review (deferred-items.md §2.2 — deferred).
- Shotstack.create_ken_burns_clip removal (deferred-items.md §2.7 — deprecated via DeprecationWarning, physical removal deferred).

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **ADAPT-01** | veo_i2v adapter drift cleanup + `tests/adapters/test_veo_i2v_contract.py` | Current failures do not include a veo-specific test file failure — the T2V-blacklist `test_blacklist_grep.py::test_no_t2v_in_orchestrator` trips on veo_i2v.py lines 180/182/183 **self-documentation** that uses `t2v` / `text_to_video` tokens in code comments + assert message. Fix = rewrite comments/assertion to use ANSI-safe hyphens (`"text-only"` or PascalCase `T2VForbidden`) so the word-boundary regex stops matching. Contract test asserts `I2VRequest` schema + API-key 3-tier resolution + `T2VForbidden` raise on None anchor_frame. |
| **ADAPT-02** | elevenlabs adapter cleanup + `tests/adapters/test_elevenlabs_contract.py` | Contract test asserts `_chars_to_words()` round-trip + `generate()` / `generate_with_timestamps()` mock contract (existing Phase 5 tests provide template) + 3-tier voice_id resolution (D-13) + `ELEVENLABS_API_KEY` / `ELEVEN_API_KEY` alias ValueError behavior. `elevenlabs.py` line count 350 > 340 soft cap → raise cap to 360. |
| **ADAPT-03** | shotstack adapter cleanup + `tests/adapters/test_shotstack_contract.py` | Contract test asserts `ShotstackRenderRequest` schema + `DEFAULT_RESOLUTION="hd"` (ORCH-11) + `FILTER_ORDER = (color_grade, saturation, film_grain)` (D-17) + continuity_prefix injection at filter[0] (D-19) + `upscale()` NOOP contract + `create_ken_burns_clip` DeprecationWarning (D-11). Line count 414 > 400 soft cap → raise cap to 420. |
| **ADAPT-04** | Full `pytest tests/phase05 tests/phase06 tests/phase07` = 0 failures | **Measured baseline 2026-04-21: 15 failed, 727 passed** (660s wall). Target: 742 passed, 0 failed. Of the 15, only 2-3 require any adapter / code change; 12-13 require test-to-code synchronization. |
| **ADAPT-05** | `wiki/render/adapter_contracts.md` — 7 adapter × 5 columns | Structure documented in §"adapter_contracts.md schema" below. |
| **ADAPT-06** | `@pytest.mark.adapter_contract` + isolated `pytest -m adapter_contract` + optional Hook | Marker registration = new `pytest.ini`. Isolated run = default pytest behavior once marker registered. Hook = recommend **deferred** or **warn-only** (see Claude's Discretion §Hook extension). |

---

## Current State — 15 Failures Inventory (measured 2026-04-21, pytest --tb=short)

### Bucket A — Phase 9.1 direct cascade (3 failures — ROOT-CAUSE fixes)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| A-1 | `tests/phase05/test_kling_adapter.py::test_runway_valid_call_returns_path` | `assert 'gen4.5' == 'gen3_alpha_turbo'` | Phase 9.1 D-12 renamed model to `gen4.5` (Runway Gen-3a Turbo failed complex-limb-motion in 세션 #24). Test still pins legacy string. | `tests/phase05/test_kling_adapter.py:205` — change expected to `"gen4.5"` + ratio to `"720:1280"` (already at 206) — ratio already matches. Only model assertion needs flip. |
| A-2 | `tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps` | `elevenlabs.py: 350 lines (soft cap 340)` + `shotstack.py: 414 lines (soft cap 400)` | Phase 9.1 D-11 Shotstack DeprecationWarning + D-13 ElevenLabs 3-tier voice_id intentionally grew files. | `tests/phase05/test_line_count.py:63-70` — raise caps: `elevenlabs.py: 340 → 360`, `shotstack.py: 400 → 420`. Comment references this research as authority. |
| A-3 | `tests/phase05/test_phase05_acceptance.py::test_pytest_phase05_sweep_green` | Aggregation — green when A-1 + A-2 fixed. | Cascade. | Zero additional code. |

### Bucket A2 — Phase 9.1 self-documentation collateral (1 failure)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| A-4 | `tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator` | Regex `(^|[^A-Za-z_])t2v([^A-Za-z_]|$)\|text_to_video\|text2video` matches `scripts/orchestrator/api/veo_i2v.py` lines 180 (comment), 182 (assertion target `text_to_video`), 183 (assertion message Korean comment). | `veo_i2v.py` T2V-guard comments use literal banned tokens in **self-documentation** — i.e. the module's own comment uses the word it's trying to ban. Classic self-reference paradox. | `scripts/orchestrator/api/veo_i2v.py:180-185` — rewrite comments to use `"text-only"` (hyphenated) + rewrite assertion target via PascalCase identifier. Options: (a) delete lines 182-185 (the `assert not hasattr(VeoI2VAdapter, "text_to_video")` is defense-in-depth already covered by the class definition having no such method — the grep guard is the authority), (b) move assertion into a `tests/adapters/test_veo_i2v_contract.py::test_no_text_only_method` **inside tests/** which the blacklist grep scopes to `scripts/orchestrator/`. Option (b) preferred — contract test adopts the guard. |

### Bucket A3 — Phase 5 acceptance aggregators (2 failures)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| A-5 | `tests/phase05/test_phase05_acceptance.py::test_acceptance_e2e_exit_zero` | phase05_acceptance.py exit non-zero | Aggregator — green when A-1..A-4 fixed. | Zero additional code. |
| A-6 | `tests/phase05/test_phase05_acceptance.py::test_acceptance_output_reports_all_pass` | Output table missing ALL_PASS | Aggregator. | Zero additional code. |

### Bucket B — Phase 6 pre-existing D09-DEF-02 drift (2 failures)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| B-1 | `tests/phase06/test_moc_linkage.py::test_moc_frontmatter_unchanged_scaffold` | `wiki/render/MOC.md: assert 'status: scaffold' in text` — actual is `status: partial` | Phase 9.1 / prior session flipped MOC status to `partial` to reflect real-world maturation but test pins original `scaffold` value. D-17 "MOC-as-TOC" doctrine says status should stay `scaffold`, BUT production-bible-driven updates legitimately promoted state. | Two options: (a) revert MOC.md back to `status: scaffold` (preserves D-17 invariant, reverses Phase 9.1 progression), (b) update `MOC_CHECK_EXPECTATIONS` to accept `status: scaffold OR partial`. Research recommends **(b)** — `partial` is informational, the D-17 invariant was "no MOC promotes to ready"; `scaffold → partial` is within spirit. Update test assertion to `assert re.search(r"status:\s*(scaffold|partial)", text)`. |
| B-2 | `tests/phase06/test_notebooklm_wrapper.py::test_default_skill_path_is_the_2026_install` | `assert 'C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm' == 'C:/Users/PC/Desktop/secondjob_naberal/.claude/skills/notebooklm'` | `scripts/notebooklm/query.py:44` DEFAULT_SKILL_PATH migrated from `shorts_naberal` → `secondjob_naberal` (Phase 9 D09-DEF-02 / 5-notebook registry consolidation). Test pins legacy path. | `tests/phase06/test_notebooklm_wrapper.py:51` — update expected string to `"C:/Users/PC/Desktop/secondjob_naberal/.claude/skills/notebooklm"`. Add cited comment referencing `__init__.py` line 7-10 which documents the migration rationale. |

### Bucket B2 — Phase 6 acceptance aggregators (2 failures)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| B-3 | `tests/phase06/test_phase06_acceptance.py::test_full_phase06_suite_green` | Aggregation | Cascade of B-1 + B-2. | Zero additional code. |
| B-4 | `tests/phase06/test_phase06_acceptance.py::test_phase05_suite_still_green` | Aggregation | Cascade of all Phase 5 failures. | Zero additional code. |

### Bucket C — Phase 7 regression aggregators (5 failures)

| # | Test file :: name | Actual error | Root cause | Fix location |
|---|-------------------|--------------|------------|--------------|
| C-1 | `tests/phase07/test_phase07_acceptance.py::test_full_phase07_suite_green_excluding_wrapper` | Cascade | Depends on all phase07 green. | Zero additional code. |
| C-2 | `tests/phase07/test_phase07_acceptance.py::test_phase_4_5_6_still_green` | Cascade | Depends on Phase 4 + 5 + 6 green. | Zero additional code. |
| C-3 | `tests/phase07/test_regression_809_green.py::test_phase05_green` | subprocess pytest tests/phase05 rc!=0 | Cascade of A-1..A-6. | Zero additional code. |
| C-4 | `tests/phase07/test_regression_809_green.py::test_phase06_green` | subprocess pytest tests/phase06 rc!=0 | Cascade of B-1..B-4. | Zero additional code. |
| C-5 | `tests/phase07/test_regression_809_green.py::test_combined_baseline_passes` | combined subprocess rc!=0 | Cascade of all above. | Zero additional code. |

### Summary count
- **Atomic fixes (code/test edits):** 6 tests — A-1, A-2, A-4, B-1, B-2 + 1 adapter self-doc edit (veo_i2v.py lines 180-185)
- **Automatic green via cascade:** 9 tests — A-3, A-5, A-6, B-3, B-4, C-1, C-2, C-3, C-4, C-5
- **Production adapter code changes:** 1 — veo_i2v.py comment/assertion rewrite (lines 180-185)
- **No changes required:** kling_i2v.py, runway_i2v.py, elevenlabs.py, shotstack.py, typecast.py, ken_burns.py, nanobanana.py, models.py

---

## Adapter File Locations + Import Structure

### Current adapters (all in `scripts/orchestrator/api/`)

| File | Lines | Purpose | Invokers.py / pipeline touch |
|------|-------|---------|-----------------------------|
| `models.py` | 164 | pydantic v2 schemas: `I2VRequest`, `ShotstackRenderRequest`, `ContinuityPrefix`, `HexColor` | Imported by every adapter |
| `kling_i2v.py` | 220 | Primary I2V (Kling 2.6 Pro via fal.ai, 세션 #24 final) | `shorts_pipeline.py` |
| `runway_i2v.py` | 237 | Backup I2V (Runway Gen-4.5, HELD / not on production path) | `shorts_pipeline.py` (dead path currently) |
| `veo_i2v.py` | 185 | Fallback I2V (Veo 3.1 Fast via fal.ai, for Kling failure on precision motion) | `shorts_pipeline.py` (via `--use-veo` smoke flag) |
| `typecast.py` | 365 | Primary TTS (Korean, shorts_naberal 승계 경로) | `shorts_pipeline.py` |
| `elevenlabs.py` | 350 | Fallback TTS + word-level timestamps (D-10 `_chars_to_words`) | `shorts_pipeline.py` |
| `shotstack.py` | 414 | Assembly/render + (deprecated) ken-burns + continuity_prefix injection | `shorts_pipeline.py` ASSEMBLY gate |
| `ken_burns.py` | 192 | Local FFmpeg Ken-Burns fallback (replaces deprecated Shotstack path per Phase 9.1 D-11) | `shorts_pipeline.py` THUMBNAIL gate fallback |
| `nanobanana.py` | 200 | T2I hero image generation (Phase 9.1 REQ-091-02) | `shorts_pipeline.py` ASSETS gate |

### Harvest origin (`.preserved/harvested/api_wrappers_raw/`)
- Per Phase 3 Plan 03-06, harvested API wrappers are read-only (chmod -w). Phase 5 rewrote from scratch using harvested as reference. Phase 14 DOES NOT touch harvest (CLAUDE.md forbid #6).

### Phase 7 mocks (`tests/phase07/mocks/`)
All 5 mocks exist and are contract-compatible:
- `kling_mock.py` (55 lines) — `image_to_video(*args, **kwargs) → Path`, fault_mode=`circuit_3x|runway_failover`, `allow_fault_injection=False` default (D-3)
- `runway_mock.py` (~46 lines) — mirrors kling
- `typecast_mock.py` (~47 lines) — `generate(*args, **kwargs) → list[dict]`
- `elevenlabs_mock.py` (~50 lines) — `generate_with_timestamps(*args, **kwargs) → list[dict]` (word-level)
- `shotstack_mock.py` (82 lines) — `render(payload) → dict`, `upscale(*args) → dict`, `create_ken_burns_clip(image, duration, scale, pan) → Path`

### Production-safe defaults (D-3 Phase 7)
All mocks default `allow_fault_injection=False`. Contract tests MUST verify this invariant per adapter — covered by `tests/adapters/test_*_contract.py::test_production_safe_default_disables_fault_injection`.

---

## Technical Approach — ADAPT-01~06 Concrete Solutions

### ADAPT-01 — veo_i2v contract test + self-doc cleanup

**Code edits:**
1. `scripts/orchestrator/api/veo_i2v.py` lines 180-185 — rewrite comments/assertion:
   ```python
   # (before) # 이 모듈에 image_to_video 만 존재하고 text_to_video/t2v 는 절대 정의되지 않음을
   # (after)  # This module exposes only image_to_video; the T2VForbidden sentinel class
   #          # name is Pascal-cased so the repo blacklist grep does not flag self-doc.
   # (before) assert not hasattr(VeoI2VAdapter, "text_to_video"), (
   # (after)  # Move this physical-absence assertion to tests/adapters/test_veo_i2v_contract.py
   #          # so the production module contains zero banned tokens.
   ```
   → Delete or rewrite the bottom-of-module `assert not hasattr(...)` block.

**New file:** `tests/adapters/test_veo_i2v_contract.py`
- `@pytest.mark.adapter_contract`
- `test_no_text_only_method` — `assert not hasattr(VeoI2VAdapter, "image_to_video_text_only")` + blacklist-regex scan on `inspect.getsource(VeoI2VAdapter)` (moved from module)
- `test_i2v_request_schema_compliance` — monkeypatch `_submit_and_poll` + verify pydantic `I2VRequest` validates
- `test_missing_anchor_raises_t2v_forbidden`
- `test_api_key_3tier_resolution` — `api_key=` kwarg > `VEO_API_KEY` env > `FAL_KEY` env > ValueError
- `test_output_is_path` — mock returns Path
- `test_production_safe_default_has_no_fault_injection_toggle` — real adapter has no `allow_fault_injection` attr (that's mock-only)

### ADAPT-02 — elevenlabs contract test

**Code edits:**
1. `tests/phase05/test_line_count.py:68` — raise `"elevenlabs.py": 340 → 360`

**New file:** `tests/adapters/test_elevenlabs_contract.py`
- `@pytest.mark.adapter_contract`
- `test_generate_returns_audio_segment_list` — reuse Phase 5 test pattern with `_invoke_tts` patch
- `test_generate_with_timestamps_populates_words_by_scene` — word-level alignment contract
- `test_chars_to_words_round_trip` — `_chars_to_words` determinism
- `test_api_key_dual_env_alias` — `ELEVENLABS_API_KEY` / `ELEVEN_API_KEY` both accepted
- `test_default_voice_3tier_resolution` — constructor kwarg > env > module cache > API discovery (mocked)
- `test_empty_text_raises_value_error`
- `test_ffprobe_fallback_when_pydub_missing`
- `test_elevenlabs_mock_fault_injection_disabled_by_default` — assert `ElevenLabsMock().allow_fault_injection is False`

### ADAPT-03 — shotstack contract test

**Code edits:**
1. `tests/phase05/test_line_count.py:69` — raise `"shotstack.py": 400 → 420`

**New file:** `tests/adapters/test_shotstack_contract.py`
- `@pytest.mark.adapter_contract`
- `test_shotstack_render_request_schema` — pydantic `ShotstackRenderRequest` validation
- `test_default_resolution_hd_orch11` — `DEFAULT_RESOLUTION == "hd"` (ORCH-11)
- `test_default_aspect_9_16`
- `test_filter_order_d17` — `FILTER_ORDER == ("color_grade", "saturation", "film_grain")`
- `test_continuity_prefix_injected_at_filter_zero` — D-19 invariant
- `test_upscale_is_noop` — Phase 5 RESEARCH §7 stub
- `test_create_ken_burns_clip_emits_deprecation_warning` — D-11 deprecation visible
- `test_shotstack_mock_fault_injection_disabled_by_default`

### ADAPT-04 — Full phase05/06/07 regression = 0 failures

**Concrete fix list:**
1. `tests/phase05/test_kling_adapter.py:205` — `"gen3_alpha_turbo"` → `"gen4.5"`
2. `tests/phase05/test_line_count.py:68-69` — caps 340→360 + 400→420
3. `scripts/orchestrator/api/veo_i2v.py:180-185` — self-doc rewrite (+ contract test absorbs guard)
4. `tests/phase06/test_moc_linkage.py:46` — accept `scaffold` OR `partial`
5. `tests/phase06/test_notebooklm_wrapper.py:51-53` — `shorts_naberal` → `secondjob_naberal`

After (1)-(5) lands, 10 aggregator tests go green by construction. Verify with full sweep.

### ADAPT-05 — `wiki/render/adapter_contracts.md`

**Structure** (7 rows × 5 columns + mock↔real delta):

```markdown
---
category: render
status: ready
tags: [contract, adapter, phase14]
updated: 2026-04-21
---

# Adapter Contracts — Phase 14 Baseline

## Adapter Registry

| Adapter | Purpose | Input Schema | Output Schema | Retry/Fallback | Fault Injection |
|---------|---------|-------------|--------------|----------------|-----------------|
| kling_i2v | Primary I2V (Kling 2.6 Pro via fal.ai) | `I2VRequest` (prompt, anchor_frame REQUIRED, duration_seconds) | `Path` to MP4 | CircuitBreaker 3/300s → Veo fallback | `KlingMock(fault_mode="circuit_3x"\|"runway_failover")` |
| runway_i2v | HELD backup I2V (Gen-4.5, off production path) | `I2VRequest` | `Path` | — (not on production path; see deferred-items.md) | `RunwayMock` same shape as Kling |
| veo_i2v | Fallback I2V (Veo 3.1 Fast, precision motion failover) | `I2VRequest` | `Path` | Called when Kling CircuitBreaker OPEN | No dedicated mock (Phase 7 omitted — Phase 15 add) |
| typecast | Primary TTS (Korean) | scenes `list[dict]` (scene_id, text, voice_id, emotion) | `list[AudioSegment]` | ElevenLabs fallback on failure | `TypecastMock(allow_fault_injection=False)` |
| elevenlabs | Fallback TTS + word-level timestamps | scenes `list[dict]` | `list[AudioSegment]` + `words_by_scene` | Tier-3 fallback = EdgeTTS (not yet implemented) | `ElevenLabsMock(allow_fault_injection=False)` |
| shotstack | Assembly + 720p render + continuity_prefix | `ShotstackRenderRequest` | `dict` with `response.url` | KenBurnsLocal fallback for THUMBNAIL gate | `ShotstackMock(allow_fault_injection=False)` |
| whisperx | Subtitle alignment (NOT YET IMPLEMENTED — stub) | audio_path + text | word-level timings | Current path = ElevenLabs `_chars_to_words` D-10 | — |

## Mock↔Real Contract Deltas

| Adapter | Real signature | Mock signature | Delta rationale |
|---------|---------------|----------------|-----------------|
| kling_i2v | `image_to_video(prompt: str, anchor_frame: Path\|None, duration_seconds: int=5) → Path` | `image_to_video(*args, **kwargs) → Path` | Mock tolerates any calling convention (pipeline uses kwargs, legacy tests use positional) |
| typecast | `generate(scenes: list[dict]) → list[AudioSegment]` | `generate(*args, **kwargs) → list[dict]` | Mock returns list[dict] per D-18 Phase 7 unit contract; pipeline patches `VoiceFirstTimeline.align → []` |
| elevenlabs | `generate_with_timestamps(scenes) → list[AudioSegment] + words_by_scene attr` | `generate_with_timestamps(*args, **kwargs) → list[dict]` (word dicts) | Mock simplifies attr-on-class pattern |
| shotstack | `render(timeline, resolution, aspect_ratio) → dict` | `render(payload=None, *args, **kwargs) → dict` | Mock absorbs v1/v2 envelope shape |

## Retry / Fallback Rails

Details refer to Phase 7 RESEARCH Correction 3 (fallback ken-burns TH­UMBNAIL-only) + D-5 Phase 6 (NotebookLM 3-tier fallback).

1. **I2V chain**: kling_i2v → (CircuitBreaker 3/300s OPEN) → veo_i2v. Runway held off-path.
2. **TTS chain**: typecast → elevenlabs (on explicit raise or empty output). Tier-3 EdgeTTS not yet implemented.
3. **Render chain**: shotstack → (DeprecationWarning-guarded path) → ken_burns_local. THUMBNAIL-only gate-scoped fallback per Correction 3.

## Production-Safe Defaults (D-3 Invariant)

All mocks ship `allow_fault_injection=False` by default. Tests explicitly set True to trigger faults.
Real adapters do NOT have this attribute — production code has no fault-injection toggle.

## Sample Contract Test (reference)

{link to tests/adapters/test_shotstack_contract.py}
```

### ADAPT-06 — Marker + isolated gate + optional Hook

**1. Create `pytest.ini` at repo root:**
```ini
[pytest]
markers =
    adapter_contract: Phase 14 adapter contract tests — run with -m adapter_contract
testpaths = tests
addopts = --strict-markers
```

**2. Mark every contract test with `@pytest.mark.adapter_contract`** at the module or function level.

**3. Isolated run verification:**
```bash
pytest -m adapter_contract  # runs only tests/adapters/
```
Research verified: pytest markers work out of the box once registered in `pytest.ini`. The `--strict-markers` flag causes unregistered markers to error, which is the drift-prevention lever (future typos get caught at collection time).

**4. Optional Hook extension** (recommendation = defer or warn-only):

Option A (defer): Add a line-item to `deferred-items.md` — "Hook extension for adapter_contract requirement on adapter edits — Phase 15 scope."

Option B (warn-only): Extend `.claude/hooks/pre_tool_use.py` so that when a `scripts/orchestrator/api/*.py` file is edited, the Hook **prints a warning** (does NOT deny) reminding the dev to update the corresponding `tests/adapters/test_*_contract.py`. This is non-blocking and preserves quick docstring fixes.

Recommendation: **Option B** (warn-only) because it's cheap to implement (15 lines Python) and catches the drift class without blocking work.

---

## Risks & Unknowns

### R1: pytest.ini introduction side effects
**Risk:** Adding a root `pytest.ini` with `testpaths = tests` + `--strict-markers` may retroactively break existing tests that use informal markers (e.g. `@pytest.mark.asyncio`).
**Evidence:** Grep for `pytest.mark` across `tests/` — multiple informal markers may exist.
**Mitigation:** Before adding `--strict-markers`, grep-scan for all markers in tests/ and register them in pytest.ini. If `asyncio` / `slow` / other markers used, include them in the registry.
**Verification step:** Plan must include a Wave 0 task that runs `pytest --collect-only 2>&1 | grep -i "unknown.*mark"` and resolves all orphaned markers before `--strict-markers` goes live.

### R2: MOC.md `status: scaffold` → `partial` philosophical question
**Risk:** B-1 fix (accept `scaffold` OR `partial`) may mask future MOC drift.
**Evidence:** D-17 invariant says MOC-as-TOC stays scaffold. Phase 9.1 allowed progression to `partial` empirically.
**Mitigation:** Document in contract test that the invariant is "MOC never goes `ready`" (two allowed states: `scaffold`, `partial`) — tighten regex to exclude `ready|complete`.

### R3: Runway adapter is held but still imported
**Risk:** `scripts/orchestrator/api/runway_i2v.py` is imported by tests/phase05/test_kling_adapter.py + active in `invokers.py` symbol table even though production doesn't call it.
**Evidence:** `deferred-items.md §2.1` explicitly says Runway is held, Phase 10 batch window removes it.
**Mitigation:** Phase 14 does NOT remove Runway — contract test treats it as existing-but-held. Document as "held" in adapter_contracts.md.

### R4: whisperx adapter stub
**Risk:** ADAPT-05 says 7 adapters including whisperx, but `scripts/orchestrator/api/whisperx.py` does not exist.
**Evidence:** `find scripts -name whisperx*` = 0 matches. Current subtitle alignment = ElevenLabs `_chars_to_words` D-10.
**Mitigation:** Document whisperx row as "NOT YET IMPLEMENTED — see §whisperx deferred" in adapter_contracts.md. No contract test file required (adapter file doesn't exist — would ModuleNotFoundError).

### R5: Windows cp949 encoding in test output
**Risk:** Background pytest run emitted `?? ??? image_to_video ? ????` — Korean strings became mojibake in CI output.
**Evidence:** pytest output line 15 — `scripts\orchestrator\api\veo_i2v.py:180: # �� ��⿡ image_to_video` (cp949 misdecode).
**Mitigation:** Contract tests must use `encoding="utf-8", errors="replace"` on every subprocess.run (STATE.md §28 precedent).

### R6: Contract tests might mask failing adapter code
**Risk:** If a contract test mocks `_submit_and_poll`, real API regressions won't be caught.
**Evidence:** Phase 7 already mocks everything; Phase 13 smoke tests are the real-API layer.
**Mitigation:** Accept this boundary — contract tests verify SCHEMA + SIGNATURE + RETRY LOGIC, not real API. Phase 13 smoke covers real-API. Document this split explicitly in `wiki/render/adapter_contracts.md`.

### Open unknown: Hook extension ROI
**Question:** Does warn-only Hook actually prevent drift, or does it generate noise?
**Decision lever:** Plan-phase should ask — if user-approved, implement Option B; if not, defer via Option A.

---

## Validation Architecture

> Note: `.planning/config.json::workflow.nyquist_validation = true` — this section is authoritative.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 + pluggy 1.6.0 (Python 3.11.9) |
| Config file | **None currently** — Phase 14 Wave 0 creates `pytest.ini` |
| Quick run command | `pytest tests/adapters -m adapter_contract -q --no-cov` |
| Full suite command | `pytest tests/phase05 tests/phase06 tests/phase07 tests/adapters -q --no-cov` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| ADAPT-01 | veo_i2v contract test exists + passes | unit | `pytest tests/adapters/test_veo_i2v_contract.py -m adapter_contract -x` | ❌ Wave 0 create |
| ADAPT-02 | elevenlabs contract test exists + passes | unit | `pytest tests/adapters/test_elevenlabs_contract.py -m adapter_contract -x` | ❌ Wave 0 create |
| ADAPT-03 | shotstack contract test exists + passes | unit | `pytest tests/adapters/test_shotstack_contract.py -m adapter_contract -x` | ❌ Wave 0 create |
| ADAPT-04 | phase05/06/07 sweep green | integration | `pytest tests/phase05 tests/phase06 tests/phase07 --tb=no -q` | ✅ all exist (currently 15 red) |
| ADAPT-05 | wiki/render/adapter_contracts.md exists + frontmatter valid | structural | `pytest tests/adapters/test_adapter_contracts_doc.py` (verifies file + frontmatter + 7-row table) | ❌ Wave 0 create |
| ADAPT-06 | marker registered + isolated run works | integration | `pytest -m adapter_contract --collect-only 2>&1 \| grep -c "test session"` | ❌ pytest.ini absent |

### Nyquist Sampling — 15 → 0 Regression

**Sampling strategy**: the pytest sweep `tests/phase05 tests/phase06 tests/phase07` is the authoritative 15→0 oracle. Three sampling rates:

- **Per task commit (inner loop ~ 1-3s)**: `pytest <touched_test_files> -x --no-cov` — test-to-code correspondence for that specific fix.
- **Per wave merge (mid loop ~ 11m wall measured 2026-04-21)**: `pytest tests/phase05 tests/phase06 tests/phase07 --tb=no -q` — confirms 0 failures after the wave lands.
- **Phase gate (outer loop ~ 11m+ wall)**: `pytest tests/phase05 tests/phase06 tests/phase07 tests/adapters -q --no-cov` + `pytest -m adapter_contract -v` — full regression sweep + isolated contract gate + asserting 742 → 742+adapter_contract_count (estimated ≥ 25 new tests).

**Contract gate Nyquist** (ADAPT-06 isolation):
```bash
pytest -m adapter_contract -q  # must exit 0 + report N tests where N >= 15 (5+ per adapter × 3 adapters)
```

### Sampling Rate
- **Per task commit:** `pytest <file> -x` or `pytest -m adapter_contract tests/adapters/test_<name>_contract.py`
- **Per wave merge:** `pytest tests/phase05 tests/phase06 tests/phase07 -q --no-cov` (full 11m sweep, exit 0)
- **Phase gate:** Full 11m sweep + `pytest -m adapter_contract -v` + `python scripts/validate/phase14_acceptance.py` (Wave 0 creates this)

### Wave 0 Gaps

- [ ] `pytest.ini` at repo root — registers `adapter_contract` marker + `testpaths = tests`
- [ ] `tests/adapters/__init__.py` — package marker (empty)
- [ ] `tests/adapters/conftest.py` — reuse Phase 5/7 fixture patterns (`repo_root`, `_fake_env`)
- [ ] `tests/adapters/test_veo_i2v_contract.py` — ADAPT-01
- [ ] `tests/adapters/test_elevenlabs_contract.py` — ADAPT-02
- [ ] `tests/adapters/test_shotstack_contract.py` — ADAPT-03
- [ ] `tests/adapters/test_adapter_contracts_doc.py` — ADAPT-05 (doc existence + frontmatter + 7-row table validator)
- [ ] `wiki/render/adapter_contracts.md` — ADAPT-05 (7-row matrix + mock↔real delta + retry rails)
- [ ] `scripts/validate/phase14_acceptance.py` — phase-gate aggregator (mirrors `phase07_acceptance.py` pattern)
- [ ] `tests/phase14/test_phase14_acceptance.py` — E2E wrapper (mirrors `tests/phase07/test_phase07_acceptance.py` pattern)

---

## Build Order (recommended Wave structure)

### Wave 0 — Foundation (blocks everything)
1. Create `pytest.ini` with adapter_contract marker + strict-markers (after grepping for existing markers in tests/)
2. Create `tests/adapters/` package (empty `__init__.py` + conftest.py reusing Phase 5/7 fixtures)
3. Verify `pytest --collect-only -m adapter_contract` returns 0 items without error (marker registration works)

### Wave 1 — Root-cause fixes (parallel-safe, 5 atoms)
All 5 edits are in disjoint files, so all can land in parallel:
- **1a**: `tests/phase05/test_kling_adapter.py:205` — `"gen3_alpha_turbo"` → `"gen4.5"`
- **1b**: `tests/phase05/test_line_count.py:68-69` — caps 340→360 + 400→420
- **1c**: `scripts/orchestrator/api/veo_i2v.py:180-185` — self-doc cleanup (delete or rewrite)
- **1d**: `tests/phase06/test_moc_linkage.py:46` — accept `scaffold|partial`
- **1e**: `tests/phase06/test_notebooklm_wrapper.py:51-53` — `shorts_naberal` → `secondjob_naberal`

After Wave 1: expected 6 failures remaining are all aggregators that go green by construction. Run `pytest tests/phase05 tests/phase06 tests/phase07 -q` and confirm 0 failures (15 → 0).

### Wave 2 — Contract tests (parallel-safe, 3 atoms)
- **2a**: `tests/adapters/test_veo_i2v_contract.py` (ADAPT-01) — absorbs the veo_i2v physical-absence assertion removed from module
- **2b**: `tests/adapters/test_elevenlabs_contract.py` (ADAPT-02)
- **2c**: `tests/adapters/test_shotstack_contract.py` (ADAPT-03)

All 3 carry `@pytest.mark.adapter_contract`. Verify isolated run: `pytest -m adapter_contract -v` shows ≥ 15 tests green.

### Wave 3 — Documentation + optional Hook (parallel-safe)
- **3a**: `wiki/render/adapter_contracts.md` (ADAPT-05) + `wiki/render/MOC.md` checkbox flip
- **3b**: `tests/adapters/test_adapter_contracts_doc.py` — structural validator for the doc
- **3c** (optional): Extend `pre_tool_use.py` with warn-only check (ADAPT-06c) — DEFER if user says no

### Wave 4 — Phase gate
- `scripts/validate/phase14_acceptance.py` — aggregator
- `tests/phase14/test_phase14_acceptance.py` — E2E wrapper
- `.planning/phases/14-api-adapter-remediation/14-TRACEABILITY.md` — REQ/SC matrix
- `.planning/phases/14-api-adapter-remediation/14-VALIDATION.md` — frontmatter flip

### Parallelization benefit
Wave 1 (5 atoms) + Wave 2 (3 atoms) + Wave 3 (3 atoms) = 11 parallel tasks. Sequential = 11 × ~3min = 33min. Parallel = 3 Waves × ~6min = 18min (assuming Wave 2 depends on Wave 1 green, Wave 3 on Wave 2). ROI = ~45% wall reduction.

---

## Project Constraints (from CLAUDE.md)

### 금기사항 (Forbidden) — enforce during implementation
1. **금기 #1** `skip_gates=True` — not applicable (no orchestrator changes)
2. **금기 #2** `TODO(next-session)` — absolutely no TODO comments in any new test file
3. **금기 #3** try-except 침묵 폴백 — contract tests MUST verify adapters raise explicitly (no silent catch)
4. **금기 #4** T2V / text_to_video / t2v — contract tests verify I2V-only for kling/runway/veo; veo_i2v.py self-doc cleanup removes this class of false-positive for the grep guard
5. **금기 #6** `shorts_naberal` 원본 수정 — not touched (harvest read-only)
6. **금기 #9** 32 에이전트 초과 — no new agents (Phase 14 is tests/docs only)

### 필수사항 (Must-do)
1. **필수 #1** Hook 3종 활성 — do not disable; warn-only Hook extension (ADAPT-06c) opt-in only
2. **필수 #2** SKILL.md ≤ 500줄 — not applicable (no skill changes)
3. **필수 #3** 오케스트레이터 500~800줄 — `shorts_pipeline.py` stays at 792 (no changes)
4. **필수 #4** FAILURES.md append-only — if Phase 14 discovers a new failure pattern, append there
5. **필수 #5** STRUCTURE.md Whitelist — `tests/adapters/` is under `tests/` which is whitelisted; `wiki/render/adapter_contracts.md` is under `wiki/render/` which is whitelisted. `pytest.ini` is at repo root — verify Whitelist permits top-level config files.
6. **필수 #7** 한국어 존댓말 baseline — not applicable to test code
7. **필수 #8** 증거 기반 보고 — every failure fix documented with pytest output evidence (this RESEARCH.md carries it)

---

## Runtime State Inventory (rename/refactor category)

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — adapter tests are stateless | None |
| Live service config | None — no API state changes | None |
| OS-registered state | None — no pm2/task-scheduler/systemd touches | None |
| Secrets/env vars | None — env var names (ELEVENLABS_API_KEY, SHOTSTACK_API_KEY, VEO_API_KEY/FAL_KEY, RUNWAY_API_KEY) unchanged. Contract tests use `monkeypatch.setenv` pattern. | None |
| Build artifacts / installed packages | `__pycache__/` for existing phase05/06/07 tests — cleared automatically on rerun. No egg-info, no compiled binaries. | None |

**Nothing found in category:** All 5 categories verified empty — this phase is pure test/doc work, no runtime state mutation.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All tests | ✓ | 8.4.2 | — |
| pydantic v2 | models.py contract assertions | ✓ | (in use, models.py Phase 5) | — |
| Python 3.11 | Runtime | ✓ | 3.11.9 | — |
| httpx | shotstack/veo network mock | ✓ | (installed, Phase 5 usage) | — |
| fal_client | kling/veo submit_and_poll | ✓ (lazy import — mocked away in contract tests) | — | monkeypatch skips real import |
| elevenlabs SDK | elevenlabs contract test mock | ✓ (lazy import) | — | monkeypatch |
| Real API keys | Contract tests | **NOT REQUIRED** | — | `monkeypatch.setenv(..., "fake")` per Phase 5 pattern |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

---

## Code Examples

### Contract test template (verified pattern from `tests/phase05/test_shotstack_adapter.py`)
```python
# tests/adapters/test_shotstack_contract.py
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.orchestrator.api.shotstack import ShotstackAdapter
from scripts.orchestrator.api.models import ShotstackRenderRequest

pytestmark = pytest.mark.adapter_contract


def test_default_resolution_hd_orch11():
    """ORCH-11 invariant: first-pass render is 720p."""
    assert ShotstackAdapter.DEFAULT_RESOLUTION == "hd"


def test_filter_order_d17():
    """D-17 invariant: color_grade → saturation → film_grain."""
    assert ShotstackAdapter.FILTER_ORDER == ("color_grade", "saturation", "film_grain")


def test_shotstack_mock_fault_injection_disabled_by_default():
    """D-3 Phase 7 production-safe default: fault injection OFF."""
    from tests.phase07.mocks.shotstack_mock import ShotstackMock
    assert ShotstackMock().allow_fault_injection is False


def test_api_key_value_error_when_missing(monkeypatch):
    monkeypatch.delenv("SHOTSTACK_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ShotstackAdapter(api_key=None)


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_schema_compliance(mock_client_class, tmp_path):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": {"id": "r_001", "url": "file:///tmp/out.mp4"}, "success": True}
    mock_response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = lambda *a: None
    mock_client_class.return_value = mock_client
    
    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    # ... full payload assertion
```

### pytest.ini template (verified against pytest 8.4.2 docs)
```ini
[pytest]
markers =
    adapter_contract: Phase 14 adapter contract tests (tests/adapters/)

testpaths = tests

addopts = --strict-markers
```

---

## Open Questions (plan-phase decisions needed)

1. **Hook extension scope** — ADAPT-06c explicitly says "optional". Plan-phase should ask user: warn-only Hook (Option B) or defer entirely (Option A)? Recommendation = B because cheap; but user preference wins.

2. **whisperx row in contract doc** — include as "NOT YET IMPLEMENTED" stub (recommended) or remove from the 7-adapter list? Plan-phase decides. ADAPT-05 spec says 7 adapters including whisperx.

3. **Line-count cap strategy** — raise caps (recommended 360/420) or split files? Plan-phase decides. Splitting costs ~200 LOC import refactor for zero safety gain; raising is 2-line test edit.

4. **MOC.md status invariant reconciliation** — accept `scaffold|partial` (recommended) or revert MOC.md to `scaffold`? Plan-phase decides. Reverting reverses Phase 9.1 legitimate progression.

5. **pytest.ini vs pyproject.toml** — pytest config can live in either. Recommend `pytest.ini` (minimal surface, no Python-package-manager commitments). Plan-phase decides.

6. **Test count estimation** — plan should budget ≥ 25 new contract tests (5-8 per adapter × 3 adapters + doc validator). Exact count set at plan time.

---

## Sources

### Primary (HIGH confidence)
- `tests/phase05/test_blacklist_grep.py` (lines 60-89) + direct pytest 2026-04-21 output showing `scripts\orchestrator\api\veo_i2v.py:180,182,183` T2V-regex matches.
- `tests/phase05/test_kling_adapter.py:195-207` — direct source showing `gen3_alpha_turbo` expectation.
- `tests/phase05/test_line_count.py:58-79` — direct source showing soft caps 340 + 400.
- `tests/phase06/test_moc_linkage.py:41-46` — direct source showing `scaffold` assertion.
- `tests/phase06/test_notebooklm_wrapper.py:49-53` — direct source showing `shorts_naberal` pin.
- `scripts/orchestrator/api/veo_i2v.py:179-185` — T2V-guard self-documentation.
- `scripts/orchestrator/api/elevenlabs.py` — 350 lines, 3-tier voice_id logic (Phase 9.1 D-13).
- `scripts/orchestrator/api/shotstack.py` — 414 lines, continuity_prefix injection (Phase 6 D-19) + ken_burns DeprecationWarning (Phase 9.1 D-11).
- `scripts/orchestrator/api/runway_i2v.py:40-56` — DEFAULT_MODEL = "gen4.5", Phase 9.1 D-12 evolution.
- `.planning/phases/09.1-production-engine-wiring/09.1-VERIFICATION.md` lines 124-158 — Bucket A + B + C 12-failure diagnosis (3 direct cascade evolution + 9 pre-existing, consistent with current 15).
- `.planning/phases/09.1-production-engine-wiring/deferred-items.md` — official Phase 10 deferrals (Runway removal, Kling NEG_PROMPT, Shotstack ken-burns physical removal).
- `tests/phase07/mocks/{kling,runway,typecast,elevenlabs,shotstack}_mock.py` — 5 deterministic mocks with `allow_fault_injection=False` D-3 invariant.
- `tests/phase07/conftest.py` + `tests/phase05/conftest.py` — fixture templates (`repo_root`, `_fake_env`, `phase07_fixtures`).
- pytest 8.4.2 full-sweep measurement 2026-04-21: 15 failed, 727 passed, 660.60s wall.

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` ADAPT-01~06 (direct specification).
- `.planning/ROADMAP.md` Phase 14 section (lines 360-373).
- `CLAUDE.md` (금기사항 9 + 필수사항 8).
- `wiki/render/MOC.md`, `wiki/render/remotion_kling_stack.md`, `wiki/render/i2v_prompt_engineering.md` — existing wiki/render/ ecosystem.

### Tertiary (LOW confidence)
- Hook extension ROI — inferred from precedent (pre_tool_use.py deprecated_patterns.json) + no empirical data on adapter-contract-absent-edit drift frequency.

---

## Metadata

**Confidence breakdown:**
- Current state / 15 failures: HIGH — direct pytest output + direct source reading for all tests.
- Fix strategy: HIGH — 13 of 15 are mechanical, 2 require 5-line edits.
- Contract schema format: HIGH — pydantic v2 already the project standard (models.py).
- Adapter inventory: HIGH — all 9 files inspected, line counts measured.
- Validation architecture: HIGH — nyquist_validation=true confirmed, existing acceptance pattern copied from Phase 7.
- Hook extension ROI: LOW — no empirical signal; recommended Option B (warn-only) or deferral.
- whisperx row handling: MEDIUM — spec says 7 adapters but no module exists; recommendation is stub row but plan must decide.

**Research date:** 2026-04-21
**Valid until:** 2026-05-21 (30 days — stable brownfield domain, adapter files evolve only at phase boundaries)
**Research duration:** ~18 min (full 11m pytest sweep + ~7m file inspection)
