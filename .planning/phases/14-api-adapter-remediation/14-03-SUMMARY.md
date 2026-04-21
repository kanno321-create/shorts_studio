---
phase: 14-api-adapter-remediation
plan: 03
subsystem: testing
tags: [pytest, adapter-contract, pydantic, monkeypatch, importlib, wave2, veo-i2v, elevenlabs, shotstack]

# Dependency graph
requires:
  - phase: 14-api-adapter-remediation
    plan: 01
    provides: "pytest.ini + adapter_contract marker + tests/adapters/ package + repo_root/_fake_env fixtures + --strict-markers"
  - phase: 14-api-adapter-remediation
    plan: 02
    provides: "Wave 1 regression green (742/742 in tests/phase05+06+07) + veo_i2v.py self-doc T2V token cleanup (Wave 2 physical-absence guard 이관 완료)"
provides:
  - tests/adapters/test_veo_i2v_contract.py (ADAPT-01, 6 tests green)
  - tests/adapters/test_elevenlabs_contract.py (ADAPT-02, 7 tests green)
  - tests/adapters/test_shotstack_contract.py (ADAPT-03, 10 tests green)
  - pytest -m adapter_contract 단독 gate — 23 tests green across 3 files in 1.64s
  - importlib.util.spec_from_file_location + sys.modules 임시 등록 패턴으로 tests/phase07/mocks/ 를 load (tests/ 는 package 아님)
  - VeoI2VAdapter physical-absence guarantee 의 제 3 layer (Wave 1 module-footer assert 삭제 대체) 확립
affects: [14-04, 14-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contract test schema+seam 2축 검증: pydantic model_fields drift 감지 + monkeypatch private seam (_submit_and_poll / _invoke_tts / _post_render / httpx.Client)"
    - "Phase 7 mock load via importlib.util.spec_from_file_location + sys.modules 고유 prefix 등록 + try/finally cleanup — tests/ 가 Python package 가 아닐 때의 D-3 invariant 검증 패턴"
    - "DeprecationWarning 캡처 패턴: with warnings.catch_warnings(record=True) + warnings.simplefilter('always') + _post_render seam patch.object side_effect=RuntimeError 로 network 차단 후 pytest.raises 내부 캡처"
    - "@pytest.mark.adapter_contract 모듈-level pytestmark 선언 (함수별 반복 회피)"

key-files:
  created:
    - tests/adapters/test_veo_i2v_contract.py
    - tests/adapters/test_elevenlabs_contract.py
    - tests/adapters/test_shotstack_contract.py
    - .planning/phases/14-api-adapter-remediation/14-03-SUMMARY.md
  modified: []

key-decisions:
  - "Private attribute _api_key — 3 adapter 모두 constructor 가 self._api_key (underscore) 저장. Plan 본문 'getattr(a, \"api_key\", None)' reference 는 source 재확인 후 '_api_key' 로 조정 (deviation Rule 1)."
  - "tests/phase07/mocks/ load via importlib.util — tests/__init__.py 부재 (Phase 7 Plan 07-03 D-13) 때문에 'from tests.phase07...' 불가. @dataclass 의 cls.__module__ resolution 을 위해 sys.modules[mod_name] 임시 등록 + try/finally cleanup 필수 (첫 naive import 후 ModuleNotFoundError → spec_from_file_location → AttributeError 체인 후 확정)."
  - "ken_burns DeprecationWarning 캡처는 _post_render seam 을 RuntimeError side_effect 로 차단 — warnings.warn 은 method 서두에서 발생하므로 network 도달 전 경고가 record 된다. pytest.raises(RuntimeError) 안쪽 with warnings.catch_warnings 로 이중 캡처."
  - "render() contract test 에서 VALID_RATIOS_BY_MODEL 우회: 실제 TimelineEntry dataclass 의존 최소화 위해 dict placeholder 를 timeline 으로 전달 — shotstack._serialise_timeline_entries 는 dict 를 verbatim 수용."
  - "Test 개수 Wave 2 예산 초과 허용: plan 은 veo 6 + el 7 + ss 7 = 20 을 요구했으나 실 구현은 6+7+10 = 23. shotstack 10 은 _api_key resolution + render httpx seam 2 tests 추가 — drift-control 강화 목적."

patterns-established:
  - "Contract test 의 네트워크 차단 2층 방어: (1) @pytest.mark.adapter_contract 로 CI 격리, (2) 각 test 내부 seam monkeypatch + httpx.Client MagicMock + _post_render patch.object — 어느 하나만 실패해도 real API 안 탐."
  - "VeoI2VAdapter physical-absence 3중 layer 완성: (a) tests/phase05/test_blacklist_grep.py 의 repo-wide grep, (b) .claude/hooks/pre_tool_use.py deprecated_patterns.json, (c) tests/adapters/test_veo_i2v_contract.py::test_no_text_only_method — Wave 1 에서 module-footer assert 삭제로 source 오염 0 달성 + Wave 2 contract test 가 physical-absence + source blacklist 재검증."
  - "Wave 1→Wave 2 invariant 승계 방식: Wave 1 이 삭제한 assert 의 guarantee 를 Wave 2 contract test 가 inspect.getsource + blacklist regex 로 재획득 — source 에는 금기 토큰 0 / class 에는 text-only method 부재."

requirements-completed: [ADAPT-01, ADAPT-02, ADAPT-03]

# Metrics
duration: 17m
completed: 2026-04-21
---

# Phase 14 Plan 03: Wave 2 Adapter Contract Tests Summary

**3 개 adapter contract 테스트 파일 신설 (veo_i2v 6 + elevenlabs 7 + shotstack 10 = 23 tests) 전수 green + `pytest -m adapter_contract` 단독 gate 23/23 in 1.64s + Wave 1 regression 742/742 preserved — ADAPT-01/02/03 충족.**

## Performance

- **Duration:** 16m 8s (968 seconds), final SUMMARY 포함 17m
- **Started:** 2026-04-21T10:31:22Z
- **Completed (code+tests committed):** 2026-04-21T10:47:30Z
- **Tasks:** 3/3 completed (14-03-01 / 14-03-02 / 14-03-03)
- **Files created:** 3 (1 per task, disjoint)
- **Files modified:** 0 (pure Wave 2 contract-test addition — no production/test-baseline touch)

## Accomplishments

- **23 contract tests green across 3 files** — plan budget 20 초과 (`+15%`). 파일별: veo_i2v 6, elevenlabs 7, shotstack 10. 전수 `@pytest.mark.adapter_contract` 마킹.
- **`pytest -m adapter_contract -v --no-cov` → 23 passed in 1.64s** (1458 deselected) — Wave 4 phase-gate 가 요구하는 ≥20 threshold 달성 + Wave 4 단독 gate readiness 확보.
- **VeoI2VAdapter physical-absence 3중 layer 완성** — Wave 1 에서 삭제된 module-footer assert 의 guarantee 를 `test_no_text_only_method` 가 `inspect.getsource` + blacklist regex 로 승계. source 토큰 0 + class attribute 부재 동시 검증.
- **Wave 1 regression 742/742 보존** — `pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov` → 742 passed, 2 warnings in 629.71s (0:10:29). Pre-Wave-1 baseline 과 exact 동일.
- **Network 차단 2층 방어 pattern 확립** — (1) marker-level CI 격리 + (2) seam monkeypatch (_submit_and_poll / _invoke_tts / _post_render / httpx.Client). 3 파일 × 평균 2 seam = 6 monkeypatch, 실 API 호출 0 회.

## Task Commits

Each task committed atomically (per-file commit_discipline):

1. **Task 14-03-01: test_veo_i2v_contract.py (ADAPT-01, 6 tests)** — `1958eee` (test)
2. **Task 14-03-02: test_elevenlabs_contract.py (ADAPT-02, 7 tests)** — `b0367d6` (test)
3. **Task 14-03-03: test_shotstack_contract.py (ADAPT-03, 10 tests)** — `8c43c64` (test)

## Files Created/Modified

### Created (3)

- `tests/adapters/test_veo_i2v_contract.py` — 163 lines, 6 tests, module `pytestmark = pytest.mark.adapter_contract`. Verifies: physical-absence guard (inspect.getsource + T2V_BLACKLIST regex) + I2VRequest schema (prompt min_length + duration 4-8) + anchor_frame=None → T2VForbidden + API-key 3-tier (kwarg > VEO_API_KEY > FAL_KEY > ValueError) + image_to_video 반환 Path + fault_injection 속성 부재. Imports: `VeoI2VAdapter`, `I2VRequest`, `T2VForbidden` (from `..gates`).
- `tests/adapters/test_elevenlabs_contract.py` — 234 lines, 7 tests. Verifies: generate() list[AudioSegment] + generate_with_timestamps() words_by_scene dict + _chars_to_words D-10 determinism (한국어 포함) + dual env alias (ELEVENLABS_API_KEY / ELEVEN_API_KEY) + default_voice_id 3-tier constructor snapshot (tier 1+2) + empty text → ValueError + Phase 7 ElevenLabsMock().allow_fault_injection is False (importlib load). Imports: `ElevenLabsAdapter`, `_chars_to_words`, `AudioSegment`.
- `tests/adapters/test_shotstack_contract.py` — 273 lines, 10 tests. Verifies: ShotstackRenderRequest schema drift + DEFAULT_RESOLUTION=='hd' (ORCH-11) + DEFAULT_ASPECT=='9:16' (TS-1) + FILTER_ORDER tuple (D-17) + continuity_prefix anchor == filter[0] (D-19) + upscale() NOOP + create_ken_burns_clip DeprecationWarning (D-11) + API-key 2-tier (kwarg > env > ValueError) + ShotstackMock().allow_fault_injection is False + render() httpx.Client MagicMock seam (output hd + 9:16 반영). Imports: `ShotstackAdapter`, `ShotstackRenderRequest`.

### Modified (0)

Pure Wave 2 addition — production adapter source (veo_i2v.py / elevenlabs.py / shotstack.py) + Wave 1 test baseline (test_kling_adapter.py / test_line_count.py / test_moc_linkage.py / test_notebooklm_wrapper.py) 전혀 건드리지 않음.

## D-3 / D-11 / D-17 / D-19 Invariant 검증 매핑 표

| Invariant | Source | Test file :: name | Assertion |
| --------- | ------ | ----------------- | --------- |
| **D-3** (Phase 7 mock fault_injection=False default) | tests/phase07/mocks/elevenlabs_mock.py:21 | `test_elevenlabs_contract.py::test_elevenlabs_mock_fault_injection_disabled_by_default` | `ElevenLabsMock().allow_fault_injection is False` |
| **D-3** (Phase 7 mock fault_injection=False default) | tests/phase07/mocks/shotstack_mock.py:34 | `test_shotstack_contract.py::test_shotstack_mock_fault_injection_disabled_by_default` | `ShotstackMock().allow_fault_injection is False` |
| **D-3** (production adapter 은 toggle 없음) | scripts/orchestrator/api/veo_i2v.py | `test_veo_i2v_contract.py::test_production_adapter_has_no_fault_injection_attr` | `not hasattr(adapter, "allow_fault_injection")` |
| **D-11** (ken_burns DeprecationWarning, physical removal Phase 10) | scripts/orchestrator/api/shotstack.py:182-189 | `test_shotstack_contract.py::test_create_ken_burns_clip_emits_deprecation_warning` | `any(issubclass(w.category, DeprecationWarning) for w in warning_list)` |
| **D-13** (T2VForbidden anchor_frame REQUIRED) | scripts/orchestrator/api/veo_i2v.py:101-106 | `test_veo_i2v_contract.py::test_missing_anchor_raises_t2v_forbidden` | `with pytest.raises(T2VForbidden)` |
| **D-13** (physical absence of T2V in source) | scripts/orchestrator/api/veo_i2v.py (Wave 1 cleanup) | `test_veo_i2v_contract.py::test_no_text_only_method` | `T2V_BLACKLIST.search(inspect.getsource(VeoI2VAdapter)) is None` |
| **D-14** (duration 4-8) | scripts/orchestrator/api/models.py:59-63 | `test_veo_i2v_contract.py::test_i2v_request_schema_compliance` | `with pytest.raises(ValidationError): I2VRequest(..., duration_seconds=10)` |
| **D-17** (color_grade → saturation → film_grain) | scripts/orchestrator/api/shotstack.py:77 | `test_shotstack_contract.py::test_filter_order_d17` | `FILTER_ORDER == ('color_grade', 'saturation', 'film_grain')` |
| **D-19** (continuity_prefix at filter[0]) | scripts/orchestrator/api/shotstack.py:294-297 | `test_shotstack_contract.py::test_continuity_prefix_anchor_is_filter_zero` | `FILTER_ORDER[0] == 'color_grade'` (anchor lock) |
| **ORCH-11** (720p first-pass) | scripts/orchestrator/api/shotstack.py:71 | `test_shotstack_contract.py::test_default_resolution_hd_orch11` + `::test_render_uses_httpx_client_seam` | `DEFAULT_RESOLUTION == 'hd'` + POST payload output.resolution=='hd' |
| **TS-1** (Shorts 9:16 vertical) | scripts/orchestrator/api/shotstack.py:72 | `test_shotstack_contract.py::test_default_aspect_9_16` + `::test_render_uses_httpx_client_seam` | `DEFAULT_ASPECT == '9:16'` + POST payload output.aspectRatio=='9:16' |
| **금기 #3** (침묵 폴백 금지, 명시적 raise) | 3 adapters 공통 | 3 파일 × `test_api_key_*` + `test_empty_text_raises_value_error` + `test_missing_anchor_raises_t2v_forbidden` | `with pytest.raises(ValueError/T2VForbidden)` |
| **금기 #4** (T2V / text_to_video 부재) | scripts/orchestrator/api/veo_i2v.py | `test_veo_i2v_contract.py::test_no_text_only_method` | `T2V_BLACKLIST.search(...) is None` + `not hasattr(VeoI2VAdapter, "text_to_video")` |

## Decisions Made

1. **_api_key private 속성 명시 (Plan → source 재확인)**: 3 adapter 모두 constructor 가 `self._api_key = resolved` (underscore prefix) 로 저장. Plan 본문의 `getattr(a, "api_key", None)` references 는 source 재확인 단계에서 발견 → `_api_key` 로 조정. (Rule 1 deviation.)
2. **Phase 7 mock load via `importlib.util` + `sys.modules` 임시 등록**: `tests/` 가 Python package 가 아니므로 (Phase 7 Plan 07-03 D-13) `from tests.phase07.mocks import ...` 불가. naive `from tests.phase07...` → `ModuleNotFoundError` → `importlib.util.spec_from_file_location` → `@dataclass` 의 `cls.__module__.None.__dict__` `AttributeError` → `sys.modules[mod_name] = module` 등록 후 `exec_module` + `try/finally pop` 로 확정. 고유 prefix `_phase07_{mock_name}_mock_contract` 로 pollution 최소화.
3. **ken_burns DeprecationWarning 캡처 전략**: `warnings.warn(..., DeprecationWarning, stacklevel=2)` 는 method 서두에서 발생 → `_post_render` seam 을 `patch.object(..., side_effect=RuntimeError)` 로 차단하면 실 network 안 타고도 warning 은 record 된다. `pytest.raises(RuntimeError)` 내부 `with warnings.catch_warnings(record=True): warnings.simplefilter("always")` 로 이중 캡처.
4. **Test 개수 shotstack 10 (plan 요구 ≥7)**: plan 은 veo 6 + elevenlabs 7 + shotstack 7 = 20 을 요구했으나 실 구현은 6+7+10 = 23 (+15%). shotstack 에 `test_api_key_resolution_and_value_error` (금기 #3 재검증) + `test_render_uses_httpx_client_seam` (payload output 필드 drift 감지) 2 tests 추가 — drift-control 강화 목적. 단독 검증 대상 확장이며 production code 수정 없음.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug: stale attribute reference in plan text] `api_key` → `_api_key` 조정**

- **Found during:** Task 14-03-01 (test_api_key_3tier_resolution 작성 중 source 확인)
- **Issue:** 14-03-PLAN.md `<action>` 블록 내 test 코드가 `getattr(adapter, "api_key", None)` 로 assertion 을 작성하도록 명시. VeoI2VAdapter source 확인 (`scripts/orchestrator/api/veo_i2v.py:81`) 결과 실 저장 속성은 `self._api_key` (private/underscore). Plan 을 그대로 따르면 모든 tier assertion 이 `None == "kwarg-key"` 로 fail 했을 것.
- **Fix:** 3 파일 전부 `getattr(adapter, "_api_key", None)` 로 통일. 추가로 elevenlabs 의 `_default_voice_id` (plan 의 `default_voice`) + shotstack 동일 pattern 적용.
- **Files modified:** tests/adapters/test_veo_i2v_contract.py, test_elevenlabs_contract.py, test_shotstack_contract.py (신규 작성 시점에 반영, 별도 edit 아님)
- **Verification:** 3 파일 전수 green — 1958eee / b0367d6 / 8c43c64 + 전수 `pytest -m adapter_contract` 23/23.
- **Committed in:** 각 task commit 에 해당 수정이 포함.

**2. [Rule 3 — Blocking: tests/ is not a Python package] Phase 7 mock load 전략 변경**

- **Found during:** Task 14-03-02 첫 실행 (6 passed, 1 failed with `ModuleNotFoundError: No module named 'tests.phase07'`)
- **Issue:** Plan `<action>` 에 명시된 `from tests.phase07.mocks.elevenlabs_mock import ElevenLabsMock` 은 `tests/__init__.py` 가 존재할 때만 동작. Phase 7 Plan 07-03 D-13 에 의해 `tests/__init__.py` 는 의도적으로 부재 (Phase 4/5/6 import resolution 호환성 유지).
- **Fix:** `importlib.util.spec_from_file_location` 경유 direct load 로 전환. 추가 blocker: `@dataclass` 가 `sys.modules.get(cls.__module__).__dict__` 조회 → `None.__dict__ AttributeError` 발생. 해결: `sys.modules[mod_name] = module` 를 `exec_module` 전에 등록 + `try/finally sys.modules.pop(mod_name, None)` cleanup. 고유 prefix (`_phase07_elevenlabs_mock_contract`, `_phase07_shotstack_mock_contract`) 사용하여 pollution 최소화.
- **Files modified:** tests/adapters/test_elevenlabs_contract.py + test_shotstack_contract.py (동일 pattern 적용)
- **Verification:** 2 파일 전수 green — pytest `test_elevenlabs_mock_fault_injection_disabled_by_default` + `test_shotstack_mock_fault_injection_disabled_by_default` PASS.
- **Committed in:** b0367d6 (elevenlabs — 이중 naive import 시도 → importlib 전환 → sys.modules 등록 3-step evolution 가 동일 file 내 landed), 8c43c64 (shotstack — elevenlabs pattern 을 처음부터 재사용).

**3. [Rule 2 — Missing critical: plan 요구 test 개수 초과 달성] shotstack 7 → 10 tests**

- **Found during:** Task 14-03-03 (plan 요구 ≥7 tests, 8 behavior bullets in `<behavior>` 블록)
- **Issue:** Plan `<behavior>` 에 8 개 test case 명시 (`test_shotstack_render_request_schema` + ... + `test_shotstack_mock_fault_injection_disabled_by_default`), 그러나 plan acceptance criteria 는 `≥7` 로 설정. Strict 7 만 작성 시 API-key resolution (금기 #3 필수사항) + httpx seam (payload drift 감지) 두 cross-cutting invariant 가 빠짐.
- **Fix:** `test_api_key_resolution_and_value_error` (금기 #3) + `test_render_uses_httpx_client_seam` (payload output 필드 drift 감지) 2 개 추가. 10 tests 전수 green.
- **Files modified:** tests/adapters/test_shotstack_contract.py
- **Verification:** 10/10 passed in 0.81s (`pytest tests/adapters/test_shotstack_contract.py -v --no-cov`).
- **Committed in:** 8c43c64

---

**Total deviations:** 3 auto-fixed (1 Rule 1 plan-bug, 1 Rule 3 blocking-issue, 1 Rule 2 missing-critical cross-cutting guard)
**Impact on plan:** 0 scope creep — 전부 Wave 2 ADAPT-01/02/03 scope 내부. Plan 의 test case 5+ 요구 + acceptance criteria `≥6/≥7/≥7` 전수 상회. Production code 수정 0.

## Evidence Blocks (CLAUDE.md 필수사항 #8)

### 1. 파일별 개별 pytest

```
$ py -3.11 -m pytest tests/adapters/test_veo_i2v_contract.py -v --no-cov
... 6 passed in 0.81s

$ py -3.11 -m pytest tests/adapters/test_elevenlabs_contract.py -v --no-cov
... 7 passed in 0.85s

$ py -3.11 -m pytest tests/adapters/test_shotstack_contract.py -v --no-cov
... 10 passed in 0.81s
```

### 2. `pytest -m adapter_contract` 전수 gate

```
$ py -3.11 -m pytest -m adapter_contract -v --no-cov
collected 1481 items / 1458 deselected / 23 selected

tests/adapters/test_elevenlabs_contract.py::test_generate_returns_audio_segment_list PASSED
tests/adapters/test_elevenlabs_contract.py::test_generate_with_timestamps_populates_words_by_scene PASSED
tests/adapters/test_elevenlabs_contract.py::test_chars_to_words_round_trip PASSED
tests/adapters/test_elevenlabs_contract.py::test_api_key_dual_env_alias PASSED
tests/adapters/test_elevenlabs_contract.py::test_default_voice_3tier_resolution PASSED
tests/adapters/test_elevenlabs_contract.py::test_empty_text_raises_value_error PASSED
tests/adapters/test_elevenlabs_contract.py::test_elevenlabs_mock_fault_injection_disabled_by_default PASSED
tests/adapters/test_shotstack_contract.py::test_shotstack_render_request_schema PASSED
tests/adapters/test_shotstack_contract.py::test_default_resolution_hd_orch11 PASSED
tests/adapters/test_shotstack_contract.py::test_default_aspect_9_16 PASSED
tests/adapters/test_shotstack_contract.py::test_filter_order_d17 PASSED
tests/adapters/test_shotstack_contract.py::test_continuity_prefix_anchor_is_filter_zero PASSED
tests/adapters/test_shotstack_contract.py::test_upscale_is_noop PASSED
tests/adapters/test_shotstack_contract.py::test_create_ken_burns_clip_emits_deprecation_warning PASSED
tests/adapters/test_shotstack_contract.py::test_api_key_resolution_and_value_error PASSED
tests/adapters/test_shotstack_contract.py::test_shotstack_mock_fault_injection_disabled_by_default PASSED
tests/adapters/test_shotstack_contract.py::test_render_uses_httpx_client_seam PASSED
tests/adapters/test_veo_i2v_contract.py::test_no_text_only_method PASSED
tests/adapters/test_veo_i2v_contract.py::test_i2v_request_schema_compliance PASSED
tests/adapters/test_veo_i2v_contract.py::test_missing_anchor_raises_t2v_forbidden PASSED
tests/adapters/test_veo_i2v_contract.py::test_api_key_3tier_resolution PASSED
tests/adapters/test_veo_i2v_contract.py::test_output_is_path PASSED
tests/adapters/test_veo_i2v_contract.py::test_production_adapter_has_no_fault_injection_attr PASSED

===================== 23 passed, 1458 deselected in 1.64s =====================
```

### 3. Wave 1 regression preservation

```
$ py -3.11 -m pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov
... (previous output)
742 passed, 2 warnings in 629.71s (0:10:29)
```

Pre-Wave-1 baseline (14-02-wave1-sweep.log): `742 passed, 2 warnings in 633.34s`. Delta: -3.63s (-0.6%). **zero regression introduced by Wave 2**.

### 4. grep verification (acceptance criteria)

```
$ grep -c "pytest.mark.adapter_contract" tests/adapters/test_veo_i2v_contract.py
1
$ grep -c "pytest.mark.adapter_contract" tests/adapters/test_elevenlabs_contract.py
1
$ grep -c "pytest.mark.adapter_contract" tests/adapters/test_shotstack_contract.py
1

$ grep -cE "^def test_" tests/adapters/test_veo_i2v_contract.py
6
$ grep -cE "^def test_" tests/adapters/test_elevenlabs_contract.py
7
$ grep -cE "^def test_" tests/adapters/test_shotstack_contract.py
10

$ grep -rc "TODO" tests/adapters/test_veo_i2v_contract.py tests/adapters/test_elevenlabs_contract.py tests/adapters/test_shotstack_contract.py
tests/adapters/test_veo_i2v_contract.py:0
tests/adapters/test_elevenlabs_contract.py:0
tests/adapters/test_shotstack_contract.py:0
```

## Production Source Import Map

| Adapter | Production source | Contract test file | Seam(s) monkeypatched |
| ------- | ----------------- | ------------------ | --------------------- |
| veo_i2v | `scripts.orchestrator.api.veo_i2v::VeoI2VAdapter` + `scripts.orchestrator.api.models::I2VRequest` + `scripts.orchestrator.gates::T2VForbidden` | `tests/adapters/test_veo_i2v_contract.py` | `VeoI2VAdapter._submit_and_poll` |
| elevenlabs | `scripts.orchestrator.api.elevenlabs::{ElevenLabsAdapter, _chars_to_words}` + `scripts.orchestrator.voice_first_timeline::AudioSegment` | `tests/adapters/test_elevenlabs_contract.py` | `ElevenLabsAdapter._invoke_tts` + `ElevenLabsAdapter._invoke_tts_with_timestamps` + `ElevenLabsAdapter._get_audio_duration` |
| shotstack | `scripts.orchestrator.api.shotstack::ShotstackAdapter` + `scripts.orchestrator.api.models::ShotstackRenderRequest` | `tests/adapters/test_shotstack_contract.py` | `scripts.orchestrator.api.shotstack.httpx.Client` + `ShotstackAdapter._post_render` |

## CLAUDE.md Compliance Check

| Rule | Applied in Task | Evidence |
| ---- | ---------------- | -------- |
| 금기 #2 (TODO 금지) | All 3 tasks | `grep -rc "TODO" tests/adapters/test_*_contract.py` → 0 hits |
| 금기 #3 (try-except 침묵 폴백 금지) | All 3 tasks | 6 `pytest.raises()` 명시 (ValueError + T2VForbidden + ValidationError + RuntimeError); try-except blocks 없음 (importlib 의 try/finally 는 sys.modules cleanup 전용이며 silent fallback 아님 — raise 는 그대로 propagate) |
| 금기 #4 (T2V 금지) | Task 14-03-01 | `test_no_text_only_method` 이 inspect.getsource + blacklist regex 로 veo_i2v 소스 + class attribute 물리적 부재 검증 |
| 금기 #9 (32 agent 초과 금지) | — | Phase 14 는 test/docs only; 신규 agent 0 |
| 필수 #4 (FAILURES.md append-only) | — | 본 plan 에서 신규 failure pattern 0 — 편집 없음 |
| 필수 #5 (STRUCTURE Whitelist) | All 3 tasks | 신규 파일 전부 `tests/adapters/` 아래 — Wave 0 에서 이미 whitelisted |
| 필수 #8 (증거 기반 보고) | This SUMMARY + commit bodies | 각 task commit body 에 pytest 출력 + grep count 인용; 본 SUMMARY Evidence Blocks §1-4 에 전수 재확인 |

## Issues Encountered

1. **Initial `from tests.phase07.mocks...` ModuleNotFoundError** — Phase 7 Plan 07-03 D-13 에 의해 `tests/__init__.py` 부재. 해결: `importlib.util.spec_from_file_location` 경유 direct load.
2. **`@dataclass` + `spec_from_file_location` 의 `None.__dict__ AttributeError`** — dataclass field 의 forward-reference resolution 이 `sys.modules[cls.__module__]` 를 조회하므로 module 이 sys.modules 에 없으면 fail. 해결: `exec_module` 전에 `sys.modules[mod_name] = module` 등록 + try/finally pop cleanup.
3. **Plan 의 `api_key` attribute reference 가 실 adapter source 와 drift** — 3 adapter 모두 `_api_key` (private). 해결: source 재확인 후 test 작성 시점에 반영 (별도 commit 불필요).
4. **shotstack `test_create_ken_burns_clip_emits_deprecation_warning` 에서 warning 캡처 위치 설계** — warnings.warn 은 method 서두 → network 도달 전 발생. `_post_render` 를 RuntimeError side_effect 로 차단해도 warning 은 record 된다. 설계: `pytest.raises(RuntimeError)` outer + `with warnings.catch_warnings(record=True)` inner 이중 컨텍스트.

## Next Phase Readiness

- **Wave 3 (Plan 14-04) unblocked** — `wiki/render/adapter_contracts.md` 작성 (ADAPT-05) + `tests/adapters/test_adapter_contracts_doc.py` structural validator (ADAPT-05) + MOC.md TOC entry flip + optional hook (ADAPT-06c) 진입 가능. Wave 2 에서 확립한 `pytest -m adapter_contract -v` 23/23 floor 를 Wave 3 validator 가 확장 (+1~6 docs validator tests 예상 → Wave 4 phase-gate 는 ≥24 tests 기준).
- **Wave 4 phase-gate (Plan 14-05) readiness** — 14-VALIDATION.md row 14-05-02 `pytest -m adapter_contract -v --no-cov` ≥20 tests threshold 이미 초과 달성 (23/23). Wave 1 regression baseline 742 도 그대로 — Wave 4 의 full regression floor 는 742 + adapter_contract 23 = 765 이 될 것.
- **ADAPT-01/02/03 Success Criteria 전수 충족** — Wave 2 완결. 잔여 Phase 14 REQ: ADAPT-04 (Wave 1 완결, 742/742), ADAPT-05 (Wave 3 예정), ADAPT-06 (Wave 0 + Wave 3 optional hook 완결 예정).
- **No blockers** for Plan 14-04 (Wave 3 docs + validator) 실행.

## Self-Check: PASSED

- [x] `tests/adapters/test_veo_i2v_contract.py` exists — FOUND (163 lines)
- [x] `tests/adapters/test_elevenlabs_contract.py` exists — FOUND (234 lines)
- [x] `tests/adapters/test_shotstack_contract.py` exists — FOUND (273 lines)
- [x] Commit `1958eee` exists (Task 14-03-01) — FOUND (`test(14-03): veo_i2v adapter contract`)
- [x] Commit `b0367d6` exists (Task 14-03-02) — FOUND (`test(14-03): elevenlabs adapter contract`)
- [x] Commit `8c43c64` exists (Task 14-03-03) — FOUND (`test(14-03): shotstack adapter contract`)
- [x] `pytest tests/adapters/test_veo_i2v_contract.py -v --no-cov` — 6 passed in 0.81s
- [x] `pytest tests/adapters/test_elevenlabs_contract.py -v --no-cov` — 7 passed in 0.85s
- [x] `pytest tests/adapters/test_shotstack_contract.py -v --no-cov` — 10 passed in 0.81s
- [x] `pytest -m adapter_contract -v --no-cov` — 23 passed, 1458 deselected in 1.64s
- [x] `pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov` — 742 passed, 0 failed in 629.71s
- [x] `grep -c "pytest.mark.adapter_contract"` → 1 per file
- [x] `grep -cE "^def test_"` → 6 / 7 / 10 (≥5 threshold + ≥ plan target 6/7/7)
- [x] `grep -rc "TODO" tests/adapters/test_*_contract.py` → 0 hits total
- [x] `grep -c "test_no_text_only_method"` in veo file → 1
- [x] `grep -c "test_missing_anchor_raises_t2v_forbidden"` in veo file → 1
- [x] `grep -c "test_api_key_3tier_resolution"` in veo file → 1
- [x] `grep -c "test_chars_to_words_round_trip"` in elevenlabs file → 1
- [x] `grep -c "test_api_key_dual_env_alias"` in elevenlabs file → 1
- [x] `grep -c "test_elevenlabs_mock_fault_injection_disabled_by_default"` in elevenlabs file → 1
- [x] `grep -c "FILTER_ORDER"` in shotstack file → 11
- [x] `grep -c "DEFAULT_RESOLUTION"` in shotstack file → 2
- [x] `grep -c "DeprecationWarning"` in shotstack file → 5
- [x] `grep -c "allow_fault_injection"` in shotstack file → 4
- [x] Zero `skip_gates` in any new file (금기 #1)
- [x] Zero `TODO` in any new file (금기 #2)
- [x] Zero silent try-except (금기 #3) — 모든 expected error 는 pytest.raises()
- [x] Zero T2V tokens in new test sources (금기 #4) — T2V_BLACKLIST 는 regex literal 으로 검증 대상 표현
- [x] No production source modification — git diff scripts/ → empty
- [x] Phase 7 mock load via importlib — sys.modules pollution bounded by try/finally

---
*Phase: 14-api-adapter-remediation*
*Plan: 03 (Wave 2 Adapter Contract Tests)*
*Completed: 2026-04-21*
