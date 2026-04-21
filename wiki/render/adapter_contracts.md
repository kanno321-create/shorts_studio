---
category: render
status: ready
tags: [contract, adapter, phase14]
updated: 2026-04-21
owner: Phase 14 API Adapter Remediation
---

# Adapter Contracts — Phase 14 Baseline

> naberal-shorts-studio 의 모든 외부 API adapter (`scripts/orchestrator/api/*.py`) 의
> 입력 schema + 출력 schema + retry/fallback 규칙 + fault injection 지원 여부 +
> mock↔real 계약 차이를 단일 지점에 anchoring 합니다. Phase 5/6/7 integration
> 테스트와 Phase 14 contract 테스트 (`tests/adapters/test_*_contract.py`) 의
> 상위 개념 문서이며, 향후 adapter 변경 시 본 문서가 sync 를 강제하는
> single-source-of-truth 역할을 수행합니다.

## Adapter Registry

| Adapter | Purpose | Input Schema | Output Schema | Retry/Fallback | Fault Injection |
|---------|---------|--------------|---------------|----------------|-----------------|
| **kling_i2v** | Primary I2V (Kling 2.6 Pro via fal.ai `kling-video/v2.6/pro/image-to-video`) | `I2VRequest(prompt: str, anchor_frame: Path REQUIRED, duration_seconds: int = 5 [4~8])` | `Path` (local MP4 in `outputs/kling/`) | CircuitBreaker 3회/300s OPEN → `veo_i2v` fallback | `KlingMock(fault_mode="circuit_3x"\|"runway_failover")`, `allow_fault_injection=False` default |
| **runway_i2v** | HELD backup I2V (Gen-4.5, off production path — `deferred-items.md §2.1`) | `I2VRequest` (same shape as Kling) | `Path` (local MP4 in `outputs/runway/`) | — (off-path; Phase 10 batch removal 예정) | `RunwayMock`, `allow_fault_injection=False` default |
| **veo_i2v** | Fallback I2V (Veo 3.1 Fast via fal.ai `veo3.1/fast/image-to-video`, 정밀 motion failover) | `I2VRequest` (`anchor_frame=None` → `T2VForbidden` raise; duration 4~8) | `Path` (local MP4 in `outputs/veo/`) | Called when Kling CircuitBreaker OPEN | No dedicated Phase 7 mock (Phase 15+ add 예정) |
| **typecast** | Primary TTS (Korean, D-10 voice-first) | `scenes: list[dict]` (`scene_id: int`, `text: str`, `voice_id: str\|None`, `emotion_style: str\|None`) | `list[AudioSegment]` with monotonic `(start, end, duration, path)` | ElevenLabs fallback on explicit raise / empty output | `TypecastMock(generate → list[dict])`, `allow_fault_injection=False` default |
| **elevenlabs** | Fallback TTS + word-level timestamps (D-10 `_chars_to_words`) | `scenes: list[dict]` (same shape) | `list[AudioSegment]` + parallel `words_by_scene` (word-level `{word, start, end}` dicts) | Tier-3 EdgeTTS (NOT YET IMPLEMENTED — 금기 #3 명시 raise) | `ElevenLabsMock(generate_with_timestamps → list[dict])`, `allow_fault_injection=False` default |
| **shotstack** | Assembly + 720p render + `continuity_prefix` (D-19) | `ShotstackRenderRequest(timeline_entries, resolution="hd", aspect_ratio="9:16", filters_order=FILTER_ORDER)` | `dict` with `response.url` (remote MP4 URL) | KenBurnsLocal fallback for THUMBNAIL gate only (Phase 7 RESEARCH Correction 3) | `ShotstackMock(render → dict, upscale, create_ken_burns_clip)`, `allow_fault_injection=False` default |
| **whisperx** | Subtitle alignment — **NOT YET IMPLEMENTED (Phase 15+ stub)** | audio_path + text (설계 예정) | word-level timings (설계 예정) | 현재 경로 = ElevenLabs `_chars_to_words` D-10 | — (모듈 부재, Phase 7 mock 없음) |

## Mock ↔ Real Contract Deltas

| Adapter | Real signature | Mock signature (Phase 7 `tests/phase07/mocks/`) | Delta rationale |
|---------|----------------|--------------------------------------------------|-----------------|
| **kling_i2v** | `image_to_video(prompt: str, anchor_frame: Path\|None, duration_seconds: int = 5) → Path` | `image_to_video(*args, **kwargs) → Path` | Mock 은 호출 convention 불문 수용 — pipeline kwargs + legacy positional 양쪽 흡수 (D-3 Phase 7 Correction 2). |
| **runway_i2v** | `image_to_video(prompt, anchor_frame, duration_seconds)` + `DEFAULT_MODEL = "gen4.5"` | `image_to_video(*args, **kwargs) → Path` | Kling mock 과 동일 패턴. RunwayMock 은 `circuit_3x`/`runway_failover` fault_mode 지원 (fault injection 전용). |
| **typecast** | `generate(scenes: list[dict]) → list[AudioSegment]` | `generate(*args, **kwargs) → list[dict]` | Mock 은 D-18 Phase 7 unit contract 에 따라 `list[dict]` 반환; pipeline integration 단계에서 `VoiceFirstTimeline.align → []` 로 patch (Phase 7 Plan 07-03 E2E precedent). |
| **elevenlabs** | `generate_with_timestamps(scenes) → list[AudioSegment]` + `words_by_scene` attr | `generate_with_timestamps(*args, **kwargs) → list[dict]` (word dicts) | Mock 은 attr-on-class 패턴을 dict-of-dicts 로 단순화 (D-10 chars→words alignment 는 real adapter 에서만 검증). |
| **shotstack** | `render(timeline: list, resolution: str, aspect_ratio: str) → dict` | `render(payload=None, *args, **kwargs) → dict` | Mock 은 v1/v2 envelope shape 양쪽 흡수; real adapter 는 httpx.Client seam 경유 (`_post_render`) 로 테스트 격리. |

## Retry / Fallback Rails

1. **I2V chain**: `kling_i2v` → (CircuitBreaker 3회/300s OPEN) → `veo_i2v`. `runway_i2v` 는 off-path (deferred-items.md §2.1, Phase 10 batch 제거 예정).
2. **TTS chain**: `typecast` → `elevenlabs` (명시적 raise 또는 empty output 시). Tier-3 EdgeTTS 는 아직 미구현 — 현재 2-tier 구조.
3. **Render chain**: `shotstack` → (DeprecationWarning-guarded `create_ken_burns_clip` path) → `ken_burns_local`. **THUMBNAIL gate 전용** (Phase 7 RESEARCH Correction 3 — ASSETS gate 는 fallback 대상 아님).
4. **Subtitle alignment chain**: 현재 `elevenlabs._chars_to_words` (D-10) 단독. `whisperx` 도입 시 Tier-0 primary + elevenlabs Tier-1 fallback 으로 재설계 예정 (Phase 15+).

## Production-Safe Defaults (D-3 Phase 7 Invariant)

- 모든 Phase 7 Mock 은 `allow_fault_injection=False` 로 **기본값** 선언 (`tests/phase07/mocks/{kling,runway,typecast,elevenlabs,shotstack}_mock.py`).
- **Real adapter 는 `allow_fault_injection` 속성을 가지지 않음** — production 코드에는 fault-injection toggle 이 존재하지 않는다.
- Contract 테스트 전수 검증:
  - `tests/adapters/test_elevenlabs_contract.py::test_elevenlabs_mock_fault_injection_disabled_by_default`
  - `tests/adapters/test_shotstack_contract.py::test_shotstack_mock_fault_injection_disabled_by_default`
  - `tests/adapters/test_veo_i2v_contract.py::test_production_adapter_has_no_fault_injection_attr`

## CLAUDE.md 금기사항 강제

- **금기 #4** T2V / text_to_video / t2v 금지: `kling_i2v`/`runway_i2v`/`veo_i2v` 3 종 I2V adapter 는 모두 `anchor_frame` 필수. `veo_i2v` 는 `anchor_frame=None` 입력 시 `T2VForbidden` raise (D-13 VIDEO-01 invariant). `scripts/orchestrator/api/veo_i2v.py` source 는 banned token (t2v / text_to_video / text2video) 0 hits 유지 — Phase 14 Wave 1 에서 module-footer assert 가 3 외부 layer (repo blacklist grep + `pre_tool_use.py` deprecated_patterns.json + Wave 2 contract test) 로 이관 완료.
- **금기 #3** try-except 침묵 폴백 금지: 모든 adapter 는 실패 시 명시적 `raise`; retry 는 CircuitBreaker 레이어에서만 허용. Contract 테스트는 `pytest.raises(ValueError/T2VForbidden/ValidationError/RuntimeError)` 로 명시 검증.
- **금기 #5** Selenium 업로드 금지: `shotstack` / `publisher` 는 YouTube Data API v3 공식 경로만 사용 (Phase 8 Plan 05 ANCHOR C AST-level 검증).

## Contract 테스트 Cross-Reference

| Adapter | Contract 테스트 파일 | Phase | Test 개수 |
|---------|----------------------|-------|----------|
| veo_i2v | `tests/adapters/test_veo_i2v_contract.py` | 14 (Plan 03 Task 14-03-01) | 6 tests green |
| elevenlabs | `tests/adapters/test_elevenlabs_contract.py` | 14 (Plan 03 Task 14-03-02) | 7 tests green |
| shotstack | `tests/adapters/test_shotstack_contract.py` | 14 (Plan 03 Task 14-03-03) | 10 tests green |
| kling_i2v | (Phase 5 `tests/phase05/test_kling_adapter.py` — unit) + 추후 contract 이관 후보 | 5 / Phase 15 후보 | n/a |
| runway_i2v | (Phase 5 `tests/phase05/test_kling_adapter.py::test_runway_*`) + deferred-items.md §2.1 제거 후 정리 | 5 / Phase 10 batch | n/a |
| typecast | (Phase 5 unit + Phase 7 mock) + 추후 contract 이관 후보 | 5 / Phase 15 후보 | n/a |
| whisperx | **NOT YET IMPLEMENTED** — 모듈 부재 | — | — |

## Phase 13 Smoke (real API) 경계

- 본 문서의 contract 테스트는 **schema + signature + retry 로직** 만 mock 기반으로 검증 (Phase 14 RESEARCH §R6).
- **실 API 회귀** (network error, 429 rate limit, 실 payload 파싱, 실 과금) 는 Phase 13 SMOKE-01~06 범위.
- 두 layer 는 상호 보완 — contract 은 빠르고 저렴 (~1.64s for 23 tests), smoke 는 느리고 비용 발생 (실 API, budget cap $5).
- 어느 하나만 green 이어서는 안 되며, adapter 변경 시 두 layer 모두 재실행 필요.

## 갱신 기록

- **2026-04-21** Phase 14 Plan 04 Task 14-04-01 신설 — 7 adapter × 5 column 매트릭스 + mock↔real delta + retry/fallback rails + production-safe defaults + 금기사항 강제 + contract 테스트 cross-reference + Phase 13 boundary 문서화.
