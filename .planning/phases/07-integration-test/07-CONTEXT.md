# Phase 7: Integration Test — Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Source:** YOLO mode direct authoring (workflow.skip_discuss=true, workflow._auto_chain_active=true — session #13/#14/#15 precedent)
**Authoring method:** Orchestrator-direct (Phase 5/6 패턴 승계; plan-checker는 researcher/planner 아웃풋 기반 검증)

<domain>
## Phase Boundary

**In-Scope (이 Phase에서 구축):**
- `tests/phase07/` 통합 테스트 스위트 전용 디렉토리 + `conftest.py` + mock fixtures 베이스
- Phase 5 `ShortsPipeline` (787줄) + `scripts/orchestrator/api/*.py` 5 adapter를 mock으로 감싸 E2E 1회 완주
- Kling / Runway / Typecast / ElevenLabs / Shotstack 5개 adapter 각각에 대한 deterministic mock adapter (실 API 호출 0건, bytes placeholder만)
- `verify_all_dispatched()` 호출 기록 검증 (12 GATE + 5 sub-gate = 17 호출 모두 기록된 후에만 COMPLETE 전이 허용됨을 실증)
- CircuitBreaker fault injection (Kling mock을 의도적으로 3회 연속 raise → 5분 cooldown 발동 + 재시도 거부 검증)
- Fallback ken-burns 렌더 실측 (재생성 루프 3회 초과 시 "정지 이미지 + 줌인" Shotstack template이 자동 삽입되어 CIRCUIT_OPEN 없이 COMPLETE 도달 증명)
- `harness-audit` 공용 스킬 실행 결과 점수 ≥ 80 달성 + A급 drift 0건 + SKILL 500줄 초과 0건 보고서
- Phase 7 07-TRACEABILITY.md (TEST-01..04 × test × SC audit trail) + 07-VALIDATION.md Nyquist flip + 07-SUMMARY.md

**Out-of-Scope (다른 Phase 이관):**
- Phase 8: GitHub Private push + YouTube Data API v3 실 발행 (실 API 호출은 Phase 8에서 처음 발생)
- Phase 8: AI disclosure 토글 자동 ON enforcement
- Phase 9: KPI 대시보드 + Taste Gate 실 운영 회로
- Phase 10: 실 30일 운영 데이터 수집 + SKILL.md.candidate 승격
- NotebookLM 채널바이블 노트북 URL 실 확보 (Phase 6에서 `TBD-url-await-user` placeholder. Phase 7은 **Tier 2 (hardcoded defaults)** 고정으로 RAG 호출 0건 — 오프라인 E2E)
- Kling/Runway adapter에 ContinuityPrefix 추가 주입 (Phase 6 Shotstack만. Phase 7에서 Kling/Runway 확장 필요성 판단 가능)

**Upstream 의존성:**
- Phase 4 agents: 32개 (17 Inspector + 14 Producer + 1 Supervisor) ✅ 존재 — 호출 가능하나 mock inspector로 대체 가능 (E2E 속도 우선)
- Phase 5 orchestrator: `scripts/orchestrator/shorts_pipeline.py` 787줄 + 5 adapters + GateName IntEnum + GATE_DEPS + CircuitBreaker + Checkpointer + GateGuard ✅ 모두 존재
- Phase 6 wiki + NotebookLM + FAILURES: `scripts/notebooklm/fallback.py` (tier 2 hardcoded defaults 고정 사용) + `scripts/orchestrator/api/models.py::ContinuityPrefix` + `scripts/orchestrator/api/shotstack.py` (filter chain continuity_prefix 주입 완료) ✅
- Phase 6 deprecated_patterns.json 8 regex + Hook enforcement 모두 ✅
- Phase 5/6 테스트 baseline: 809/809 green (Phase 4 244 + Phase 5 329 + Phase 6 236)

</domain>

<decisions>
## Implementation Decisions (Locked)

### Mock-only 원칙 (D-1~D-3)

- **D-1: 실 API 호출 비용 $0** — Phase 7 전체 실행 경로에서 Kling / Runway / Typecast / ElevenLabs / Shotstack / NotebookLM RAG 실 네트워크 호출 0건. `monkeypatch`로 각 adapter의 HTTP client를 mock으로 교체. 네트워크 호출 발생 시 pytest가 명시적으로 실패하도록 `pytest-socket`이 있다면 `disable_socket` 권장(없으면 문서화만).
- **D-2: Mock asset은 결정론적 + 최소 크기** — `.mp4` placeholder 1KB (실제 유효한 MP4 atom 4 bytes `ftyp` + 최소 moov), `.wav` placeholder 1KB (44 byte RIFF header + 3초 silence PCM), JSON response는 Shotstack API schema 준수 dict literal. Fixed seed + fixed timestamps로 재실행 시 동일 결과.
- **D-3: Fault injection은 테스트 경로 전용** — `inject_fault` 파라미터는 Phase 6 `NotebookLMFallbackChain` 선행 패턴 승계. 프로덕션 경로(`CI=production` 또는 `NABERAL_ENV=prod`)에서는 fault injection 파라미터 무시. Phase 7 mock adapter도 동일 규율 — `allow_fault_injection=False` 기본값.

### E2E Pipeline 흐름 (D-4~D-6) — CORRECTED 2026-04-19 per research §Critical CONTEXT.md Corrections

- **D-4: TREND → MONITOR 13 operational gates sequence 준수** — Phase 5 `GateName IntEnum` 실제 순서 (gate_guard.py:94-96): TREND → NICHE → SCRIPT → POLISH → DIRECT → SCENE → SHOT → ASSETS → VOICE → ASSEMBLY → REVIEW → PUBLISH → MONITOR. 13 operational gates. Phase 7 테스트는 이 IntEnum 역주행/건너뛰기 시도 시 `GateOrderError` raise 증명 (실제 예외명은 `gate_guard.py` 정의 기준).
- **D-5: `verify_all_dispatched()` == 13 operational dispatches** — **Research correction**: 최초 CONTEXT가 "17 = 12 + 5 sub-gate"로 기술했으나 `gate_guard.py:169-176` 실구현은 13 operational gates (TREND..MONITOR) 전수 dispatch 기록 검증. "17"의 근거 코드 없음. "5 sub-gate"는 inspector/producer 내부 rubric이며 GateGuard dispatch table에 포함되지 않음. **TEST-02는 `dispatched_count == 13`으로 lock**. 13개 이하에서 COMPLETE 시도 시 `GateDispatchMissing` (또는 실제 예외명) raise.
- **D-6: Checkpointer atomic write 검증** — `os.replace` 기반 atomic write이 E2E 1회 완주 중 13회 발생(각 operational gate 완료 시점). `state/{session_id}/gate_NN.json` 파일 존재 + round-trip deserialize + highest gate_index resume 3-point 검증. Windows-safe `os.replace` 정상 동작 실측.

### Fault injection 시나리오 (D-7~D-9) — CORRECTED 2026-04-19

- **D-7: CircuitBreaker 3× failure → OPEN → cooldown** — **Research correction**: Kling mock이 `MagicMock.side_effect = [RuntimeError, RuntimeError, RuntimeError, ...]` 3회 연속 raise하여 breaker OPEN 전이 유도. 4번째 호출에서 `CircuitBreakerOpenError` (circuit_breaker.py:57-72 실제 클래스명; 최초 CONTEXT의 `CircuitBreakerTriggerError`는 오류) raise + `cooldown_remaining_seconds > 0` (Phase 5 precedent: strict `>`) 확인. 300s cooldown math는 `unittest.mock.patch("scripts.orchestrator.circuit_breaker.time.monotonic")` stdlib 패턴으로 결정론 확보 (pytest-socket / freezegun 도입 금지 — 미설치 dep). Runway 자동 failover 경로는 별도 plan.
- **D-8: Fallback ken-burns는 standalone Shotstack POST** — **Research correction**: `_build_ken_burns_fallback_timeline` 같은 메서드는 존재하지 않음. 실제 체인 (`shotstack.py:155-216` + `shorts_pipeline.py:576-627` + `fallback.py:30-67`): `shorts_pipeline._producer_loop → append_failures(FAILURES.md append) → _insert_fallback → fallback.insert_fallback_shot → shotstack.create_ken_burns_clip`. Ken-burns는 **main render filter chain에 embedded 아님** — 독립 Shotstack POST로 `{asset: still_image, effect: zoom_in, duration: 3.0}` 타임라인 생성. D-19 filter order 계약은 main render에만 적용, ken-burns는 standalone이므로 위반 대상 아님.
- **D-9: 재생성 루프 3회 초과 → FAILURES.md append + ken-burns 삽입 (THUMBNAIL 대상)** — **Research correction**: `_producer_loop`는 10 gates에서 invoke되나 Fallback-eligible gate 교집합(`shorts_pipeline.py:621` 필터)은 **THUMBNAIL only** (ASSETS는 CircuitBreaker + Runway failover 경로 — Fallback 레인 아님). Producer/Inspector 재시도 3회 후에도 inspector FAIL 지속 시 THUMBNAIL gate에서 `FAILURES.md` append + ken-burns 독립 Shotstack POST 호출되어 CIRCUIT_OPEN 없이 COMPLETE 도달. Phase 6 `check_failures_append_only` Hook과 충돌 없음 증명 (append-only 규율 준수). 보조 테스트 (선택): `test_assets_both_providers_fail.py` — ASSETS gate가 ken-burns Fallback 경로에 도달 불가함을 설계적으로 기록.

### Harness-audit 기준 (D-10~D-12)

- **D-10: harness-audit 스킬 실행 경로** — Phase 1에서 `../../harness/.claude/skills/harness-audit/SKILL.md` 상속 확인. Phase 7은 `studios/shorts` 루트에서 `harness-audit` 스킬 호출 (또는 skill wrapper script 직접 실행) → JSON 보고서 출력 → 점수 ≥ 80 검증. 스킬이 없거나 호출 실패 시 Phase 7 직접 `scripts/audit/run_harness_audit.py` CLI 작성 fallback 허용.
- **D-11: harness-audit 출력 JSON schema 고정** — 최소 필수 키: `score: int (0-100)`, `a_rank_drift_count: int`, `skill_over_500_lines: list[str]`, `agent_count: int`, `description_over_1024: list[str]`, `deprecated_pattern_matches: dict[str, int]`. Phase 7 테스트는 이 6 키 존재 + 타입 + 값 범위 검증.
- **D-12: A급 drift 0건 정의** — `.claude/deprecated_patterns.json` 8개 regex 전수 스캔 대상: `scripts/**/*.py` + `.claude/agents/**/*.md` + `tests/**/*.py` + `wiki/**/*.md` 전부. 매치 0건이어야 A급 drift 0건. canonical I2V 등 allow-list 예외는 Phase 5 test_six_patterns 패턴 승계.

### Tests infrastructure (D-13~D-15)

- **D-13: tests/phase07/ 독립 디렉토리** — `tests/phase07/__init__.py` + `conftest.py` 신규 작성 (Phase 5/6 conftest 복사 금지 — Phase별 fixture 독립 원칙). 공통 fixture는 pytest plugin 혹은 상위 `tests/conftest.py` 승격 여부는 planner 판단.
- **D-14: 전체 suite 809/809 무회귀 + Phase 7 신규 추가만** — Phase 4 (244) + Phase 5 (329) + Phase 6 (236) 기존 테스트 수정 0건. Phase 7 신규 테스트는 `tests/phase07/test_*.py` 추가만. `pytest tests/phase04 tests/phase05 tests/phase06` 회귀 sweep 3 phase green 확인.
- **D-15: NotebookLM tier 2 고정 (offline E2E)** — `NotebookLMFallbackChain`을 `RAGBackend=None` + `GrepWikiBackend=None` + `HardcodedDefaultsBackend=only` 구성으로 instantiate. Phase 7 E2E 전 구간에서 tier 0/1 호출 0건. tier_used == 2 검증. 실 RAG 호출은 Phase 8 이후 온라인 시 활성화.

### Mock fixtures 스펙 (D-16~D-20)

- **D-16: KlingI2V mock** — `respond_with={"task_id": "mock_kling_001", "status": "succeed", "video_url": "file://tests/phase07/fixtures/mock_kling.mp4"}`. `inject_fault` 옵션: `None` | `"circuit_3x"` (3회 연속 예외) | `"runway_failover"` (1회 예외 후 성공).
- **D-17: RunwayI2V mock** — `respond_with={"task_id": "mock_runway_001", "status": "SUCCEEDED", "output": ["file://tests/phase07/fixtures/mock_runway.mp4"]}`. `inject_fault` 옵션 동일.
- **D-18: Typecast TTS mock** — `respond_with={"speak_v2_url": "file://tests/phase07/fixtures/mock_typecast.wav", "duration_seconds": 3.0, "emotion_applied": true}`. 타임스탬프 자동 생성(audio-first video cuts driver 역할 유지).
- **D-19: ElevenLabs TTS mock** — `respond_with={"audio_url": "file://tests/phase07/fixtures/mock_elevenlabs.wav", "voice_id": "rachel_mock", "duration_seconds": 3.0}`. Typecast fallback 경로 증명 전용.
- **D-20: Shotstack render mock** — `respond_with={"response": {"message": "Created", "id": "mock_shotstack_001", "url": "file://tests/phase07/fixtures/mock_shotstack.mp4"}, "success": true, "status": "done"}`. ken-burns fallback 경로는 `template="ken_burns"` 파라미터 감지 후 별도 응답 분기.

### Determinism + 회귀 (D-21~D-23)

- **D-21: Fixed seed + fixed timestamps** — 모든 mock은 `freezegun`(있다면) 또는 직접 monkeypatch로 `datetime.now() = 2026-04-19T00:00:00Z` 고정. UUID는 `uuid.UUID("00000000-0000-0000-0000-000000000001")` 시작 incremental. 재실행 시 bytes-identical 출력.
- **D-22: Windows cp949 + UTF-8 round-trip** — 모든 Phase 7 테스트 subprocess 호출은 Phase 6 패턴 승계: `sys.stdout.reconfigure(encoding="utf-8")` + subprocess `encoding="utf-8"` + `errors="replace"`. 한국어 fixture (예: trend keyword, continuity prefix) round-trip 검증 1건 이상.
- **D-23: Phase 4/5/6 기존 testsuite 809/809 무회귀** — Phase 7 execute-phase 중 매 Wave 완료 시 `pytest tests/phase04 tests/phase05 tests/phase06` 회귀 sweep 실행. 실패 0건 유지. Phase 7 신규 테스트 증가는 허용되나 기존 테스트 수정은 Rule 1 deviation으로 명시 기록.

### Claude's Discretion (명시적 위임)

- tests/phase07/ 내 테스트 파일 개수 및 네이밍 (Phase 5/6 패턴 참고하되 planner가 Phase 7 Wave 구조에 맞게 분할)
- mock adapter 구현 위치: `tests/phase07/mocks/` vs `tests/phase07/fixtures/adapters/` — planner 판단
- harness-audit 스킬 호출 방식: Skill tool 직접 호출 vs wrapper CLI (`scripts/audit/run_harness_audit.py`) — 스킬 상속 확인 후 planner 판단
- ken-burns fallback Shotstack POST 세부 구조: 3초 줌인 + 정지 이미지 경로는 고정, 나머지 detail planner 판단 (`shotstack.create_ken_burns_clip:155-216` 실 시그니처 기반)
- harness-audit JSON 확장 방식: `scripts/validate/harness_audit.py` 기존 90점 출력기에 `--json-out` 플래그 추가 (backward-compatible — 기존 text 출력 보존)
- 보조 테스트 필요성 판단: (a) `test_operational_gate_count_equals_13.py` (CONTEXT "17→13" 오류 재발 차단 앵커), (b) `test_assets_both_providers_fail.py` (ASSETS ken-burns 경로 불가 설계 기록) — planner 재량

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 규율 & 정체성
- `.planning/ROADMAP.md §Phase 7` — goal + 5 SC + TEST-01..04 REQ IDs
- `.planning/REQUIREMENTS.md §TEST` — 4 REQ 상세 (TEST-01 E2E mock / TEST-02 verify_all_dispatched / TEST-03 CircuitBreaker / TEST-04 Fallback ken-burns)
- `.planning/STATE.md §Phase Completion` — Phase 4/5/6 산출물 전체 목록

### Phase 5 orchestrator 산출물 (E2E 대상)
- `scripts/orchestrator/shorts_pipeline.py` — 787줄 ShortsPipeline 클래스 (TREND → COMPLETE main 진입점)
- `scripts/orchestrator/gate_guard.py` — GateName IntEnum + GATE_DEPS + verify_all_dispatched() + dispatch() + DAG
- `scripts/orchestrator/circuit_breaker.py` — 3×300s state machine (CLOSED/OPEN/HALF_OPEN) + CircuitBreakerTriggerError / CircuitBreakerOpenError
- `scripts/orchestrator/checkpointer.py` — state/{session_id}/gate_NN.json atomic write + resume
- `scripts/orchestrator/api/kling_i2v.py` — Kling I2V adapter (mock 대상 #1)
- `scripts/orchestrator/api/runway_i2v.py` — Runway Gen-3 Alpha Turbo adapter (Kling 실패 시 failover 대상)
- `scripts/orchestrator/api/typecast.py` — Typecast TTS adapter (video cuts driver)
- `scripts/orchestrator/api/elevenlabs.py` — ElevenLabs TTS adapter (Typecast 백업)
- `scripts/orchestrator/api/shotstack.py` — Shotstack render adapter (continuity_prefix injection 완료 + ken-burns fallback 지점)
- `scripts/orchestrator/api/models.py` — ContinuityPrefix pydantic v2 + 기타 DTO
- `scripts/hc_checks/hc_checks.py` — 1176줄 hc_checks 재작성본 (13+ 시그니처 byte-preservation)

### Phase 6 integration 산출물
- `scripts/notebooklm/fallback.py` — NotebookLMFallbackChain tier 0/1/2 (Phase 7은 tier 2 only 고정)
- `wiki/continuity_bible/prefix.json` — ContinuityPrefix D-10 7-field serialization (Shotstack adapter auto-load)
- `.claude/deprecated_patterns.json` — 8 regex (Phase 5 core 6 + Phase 6 audit 2)
- `.claude/hooks/pre_tool_use.py` — FAILURES append-only + SKILL_HISTORY backup enforcement
- `.claude/failures/FAILURES.md` + `FAILURES_INDEX.md` — append-only 대상 (Phase 7 D-9 재생성 루프 3회 초과 시 실 append 발생)

### 공용 스킬 (harness 상속)
- `../../harness/.claude/skills/harness-audit/SKILL.md` — 점수 rubric + 출력 JSON schema (D-10/D-11)
- `../../harness/.claude/skills/drift-detection/SKILL.md` — drift 정의 + 스캔 범위
- `../../harness/.claude/skills/progressive-disclosure/SKILL.md` — SKILL 500줄 제약 근거
- `../../harness/.claude/skills/gate-dispatcher/SKILL.md` — dispatch() 규격
- `../../harness/.claude/skills/context-compressor/SKILL.md` — context 압축 규율

### 이전 Phase의 VERIFICATION + TRACEABILITY (format 승계 대상)
- `.planning/phases/05-orchestrator-v2-write/05-TRACEABILITY.md` — 17 REQ × test 매트릭스 format
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-TRACEABILITY.md` — 9 REQ × test 매트릭스 format
- `.planning/phases/05-orchestrator-v2-write/05-VALIDATION.md` — Nyquist flip 완료 예시
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md` — Nyquist flip 완료 예시
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-SUMMARY.md` — Phase 완료 요약 format

### 메모리 규칙 (C:/Users/PC/.claude/projects/.../memory/)
- `feedback_yolo_no_questions.md` — YOLO 기조 승계 (CONTEXT 직접 작성 근거)
- `feedback_no_background_publish.md` — 백그라운드 실행 금지 (테스트 subprocess는 foreground only)
- `feedback_quality_first.md` — 속도보다 품질 우선 (무회귀 809/809 유지)

### 운영 문서
- `CLAUDE.md` (studios/shorts 루트) — 프로젝트 규율
- `.planning/STATE.md` — 현재 Phase position + 세션 #19 말미 기록

</canonical_refs>

<specifics>
## Specific Ideas

### Phase 7 Wave 구성 가이드 (planner 참고)

| Wave | 목적 | 병렬 가능성 |
|------|------|-------------|
| 0 | Foundation — tests/phase07/ scaffold + conftest.py + mock fixtures base | N/A |
| 1 | Mock adapters — 5 adapter mocks (Kling/Runway/Typecast/ElevenLabs/Shotstack) | parallel 가능 (독립 파일) |
| 2 | E2E happy path — TREND → COMPLETE 1회 완주 + verify_all_dispatched 17 GATE | sequential (dependency on Wave 1) |
| 3 | Fault injection — CircuitBreaker 3×300 + Fallback ken-burns | parallel 가능 (서로 독립 시나리오) |
| 4 | harness-audit 스킬 실행 + score ≥ 80 + A급 drift 0 + SKILL 500줄 0 | sequential (Wave 3 완료 후) |
| 5 | Phase gate — 07-TRACEABILITY + 07-VALIDATION flip + 07-SUMMARY + acceptance E2E wrapper | sequential (최종) |

### Mock adapter 시그니처 예시 (D-16 기반)

```python
# tests/phase07/mocks/kling_i2v_mock.py
from dataclasses import dataclass, field
from typing import Literal, Optional

@dataclass
class MockKlingI2V:
    fault_mode: Optional[Literal["circuit_3x", "runway_failover"]] = None
    call_count: int = 0
    allow_fault_injection: bool = False  # D-3: 프로덕션 차단

    def generate(self, image_bytes: bytes, prompt: str) -> dict:
        if self.allow_fault_injection and self.fault_mode == "circuit_3x":
            self.call_count += 1
            if self.call_count <= 3:
                raise CircuitBreakerTriggerError(f"mock Kling failure #{self.call_count}")
        # deterministic response
        return {
            "task_id": f"mock_kling_{self.call_count:03d}",
            "status": "succeed",
            "video_url": "file://tests/phase07/fixtures/mock_kling.mp4",
        }
```

### 13 operational gate dispatch 검증 패턴 예시 (D-5 corrected 기반)

```python
# tests/phase07/test_verify_all_dispatched.py
def test_complete_transition_requires_13_operational_dispatches(pipeline_with_mocks):
    pipeline = pipeline_with_mocks
    # 12 dispatches — COMPLETE 시도 시 GateDispatchMissing
    for gate_name in FIRST_12_GATE_NAMES:  # TREND..PUBLISH (or actual 12 names from GateName IntEnum)
        pipeline.gate_guard.dispatch(gate_name)
    with pytest.raises(GateDispatchMissing) as exc:  # actual class name TBD by planner read-first
        pipeline.transition_to_complete()
    assert exc.value.missing_count == 1

    # 13th dispatch (MONITOR) → transition allowed
    pipeline.gate_guard.dispatch(GateName.MONITOR)
    pipeline.transition_to_complete()  # no raise
```

### harness-audit 출력 schema 예시 (D-11)

```json
{
  "score": 95,
  "a_rank_drift_count": 0,
  "skill_over_500_lines": [],
  "agent_count": 32,
  "description_over_1024": [],
  "deprecated_pattern_matches": {
    "selenium": 0,
    "T2V": 0,
    "skip_gates": 0,
    "segments": 0,
    "TODO_gate": 0,
    "background_publish": 0,
    "FAILURES_removed": 0,
    "SKILL_direct_edit": 0
  },
  "phase": 7,
  "timestamp": "2026-04-19T00:00:00Z"
}
```

### 07-TRACEABILITY.md 예상 구조 (Phase 6 format 승계)

```markdown
# Phase 7 Traceability Matrix

| REQ-ID | Description | Source file(s) | Test file(s) | SC ref | Plan(s) | Commit(s) |
|--------|-------------|----------------|--------------|--------|---------|-----------|
| TEST-01 | E2E mock asset 1회 성공 | scripts/orchestrator/shorts_pipeline.py | tests/phase07/test_e2e_happy_path.py | SC1 | 07-02, 07-03 | studio@... |
| TEST-02 | verify_all_dispatched 17 GATE | scripts/orchestrator/gate_guard.py | tests/phase07/test_verify_all_dispatched.py | SC2 | 07-04 | studio@... |
| TEST-03 | CircuitBreaker 3회 발동 | scripts/orchestrator/circuit_breaker.py | tests/phase07/test_circuit_breaker_3x.py | SC3 | 07-05 | studio@... |
| TEST-04 | Fallback ken-burns | scripts/orchestrator/api/shotstack.py | tests/phase07/test_fallback_ken_burns.py | SC4 | 07-06 | studio@... |
```

</specifics>

<deferred>
## Deferred Ideas

- **NotebookLM 채널바이블 노트북 URL 실 확보**: Phase 6 `TBD-url-await-user` placeholder 그대로. Phase 7은 tier 2 (hardcoded defaults) 고정이므로 blocking 아님. Phase 8 이후 온라인 활성화 시 필요.
- **Kling/Runway adapter ContinuityPrefix 주입 확장**: Phase 6 Shotstack만. Phase 7 E2E에서 Kling/Runway 영상 생성 요청에도 ContinuityPrefix 전달 필요성 관찰 가능 → Phase 8 개선 대상으로 deferred-items.md 기록.
- **실 API 호출 smoke test (1건 per adapter)**: Phase 7은 100% mock. Phase 8에서 실 API 키 + credit 투입 후 최소 1건 smoke test (비용 < $1 목표).
- **harness-audit 자동 월 1회 cron**: Phase 7은 1회 실행 증명까지. 월 1회 cron 설치는 Phase 10 `AUDIT-02`.
- **drift_scan.py 주 1회 cron**: Phase 7은 harness-audit 내장 drift 검사만. 독립 `scripts/audit/drift_scan.py` + weekly cron은 Phase 10 `AUDIT-03`.
- **session_start.py 매 세션 감사 점수 출력**: Phase 10 `AUDIT-01` deferred.
- **Playwright E2E (실 브라우저 통한 YouTube 발행)**: Phase 7은 mock only. 실 브라우저 자동화는 Phase 8 publisher agent 담당.
- **pytest-socket `disable_socket` 도입**: Phase 7에서 실 네트워크 호출 0건을 강제로 증명하고 싶다면 `pytest-socket` 도입 고려. 현재는 monkeypatch + 문서화로 우회 (dependency 추가 보류).

</deferred>

---

*Phase: 07-integration-test*
*Context gathered: 2026-04-19 via YOLO orchestrator-direct authoring (skip_discuss=true)*
*Session: #20*
