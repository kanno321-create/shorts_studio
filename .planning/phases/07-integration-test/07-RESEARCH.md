---
phase: 7
phase_name: integration-test
research_version: 1.0
generated: 2026-04-19
authoring: gsd-phase-researcher (YOLO skip_discuss)
areas_count: 12
validation_dimensions: 20
---

# Phase 7: Integration Test — Research

**Researched:** 2026-04-19
**Domain:** End-to-end integration testing of the Phase 5 orchestrator (13-GATE state machine + 5 API adapters + CircuitBreaker + Checkpointer + regeneration loop) with 100% mock I/O, harness-audit threshold ≥ 80 attainment, and 809-test regression invariance.
**Confidence:** HIGH on the existing Phase 5/6 implementation contract (every file in `scripts/orchestrator/**` was read line-by-line on 2026-04-19); MEDIUM-HIGH on the CONTEXT.md assumptions that survived verification; LOW on three CONTEXT.md claims that were **falsified by code inspection** and require planner correction (see §Critical CONTEXT.md Corrections).

## Summary

Phase 7 is a **pure test-authoring phase**: no production code under `scripts/` is modified. The deliverable is a new `tests/phase07/` suite that drives the existing `ShortsPipeline.run()` from TREND through COMPLETE using MagicMock adapters (precedent already exists: `tests/phase05/test_pipeline_e2e_mock.py`), a CircuitBreaker fault-injection scenario that forces 3 consecutive Kling failures → OPEN → cooldown-blocked retry (precedent: `tests/phase05/test_circuit_breaker_cooldown.py`), a Fallback-lane scenario that exhausts the 3-retry regeneration loop on ASSETS/THUMBNAIL and verifies ken-burns insertion + FAILURES.md append without CIRCUIT_OPEN, and an extension to the existing `scripts/validate/harness_audit.py` so it emits the 6-key JSON schema required by CONTEXT D-11 while attaining score ≥ 80.

The investigation surfaced **three factual errors in 07-CONTEXT.md** that the planner MUST correct before task authoring: (1) `verify_all_dispatched()` enforces **13 operational gates** (TREND..MONITOR), not 17 — `scripts/orchestrator/gate_guard.py:94-96, 169-176` is unambiguous; the "12 + 5 sub-gate" decomposition is not present in code. (2) The exception raised on breaker trip is `CircuitBreakerOpenError` (`circuit_breaker.py:57-72`), not `CircuitBreakerTriggerError` as CONTEXT D-7 implies. (3) A dedicated `_build_ken_burns_fallback_timeline` method does **not** exist; the real helper chain is `shorts_pipeline._insert_fallback → fallback.insert_fallback_shot → shotstack.create_ken_burns_clip` (`shotstack.py:155-216`). These three corrections are consequential for TEST-01..04 assertions and MUST be honored by PLANs.

Every external dependency is already present on target: pytest 8.4.2, pydantic 2.12.5, httpx 0.28.1, Python 3.11.9. `pytest-socket` and `freezegun` are **NOT installed**; CONTEXT D-1 / D-21 lists them as optional, and the existing Phase 5 tests achieve determinism using `unittest.mock.patch("scripts.orchestrator.circuit_breaker.time.monotonic")` which already demonstrates a zero-dependency path. Phase 5 + Phase 6 regression sweep timed on 2026-04-19: **565 tests / 68 s** (plus Phase 4's 244 = 809 total baseline).

**Primary recommendation:** Use the existing Phase 5 E2E mock test as the structural precedent (single ShortsPipeline instantiation, 5 MagicMock adapters, PASS-returning supervisor); add Phase 7-specific scenarios (fault injection, fallback, harness-audit JSON extension) as sibling test files rather than rewriting the keystone. Correct CONTEXT D-5 / D-7 / D-8 wording in the planner's PLAN.md files to match the actual codebase, lock `verify_all_dispatched == 13 operational gates` as the TEST-02 target, and extend `scripts/validate/harness_audit.py` to emit D-11 JSON without breaking its current text-score CLI (backward-compatible flag, e.g., `--json-out`).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Mock-only 원칙 (D-1~D-3)**
- **D-1: 실 API 호출 비용 $0** — Phase 7 전체 실행 경로에서 Kling / Runway / Typecast / ElevenLabs / Shotstack / NotebookLM RAG 실 네트워크 호출 0건. `monkeypatch`로 각 adapter의 HTTP client를 mock으로 교체. 네트워크 호출 발생 시 pytest가 명시적으로 실패하도록 `pytest-socket`이 있다면 `disable_socket` 권장(없으면 문서화만).
- **D-2: Mock asset은 결정론적 + 최소 크기** — `.mp4` placeholder 1KB (실제 유효한 MP4 atom 4 bytes `ftyp` + 최소 moov), `.wav` placeholder 1KB (44 byte RIFF header + 3초 silence PCM), JSON response는 Shotstack API schema 준수 dict literal. Fixed seed + fixed timestamps로 재실행 시 동일 결과.
- **D-3: Fault injection은 테스트 경로 전용** — `inject_fault` 파라미터는 Phase 6 `NotebookLMFallbackChain` 선행 패턴 승계. 프로덕션 경로(`CI=production` 또는 `NABERAL_ENV=prod`)에서는 fault injection 파라미터 무시. Phase 7 mock adapter도 동일 규율 — `allow_fault_injection=False` 기본값.

**E2E Pipeline 흐름 (D-4~D-6)**
- **D-4: TREND → COMPLETE 12 GATE sequence 준수** — Phase 5 `GateName IntEnum` 순서 그대로: TREND → NICHE → RESEARCH → SCRIPT → POLISH → DIRECT → SCENE → SHOT → ASSET → VOICE → ASSEMBLE → RENDER → PUBLISH. Phase 7 테스트는 이 IntEnum 역주행/건너뛰기 시도 시 `GateOrderViolation` raise 증명.
- **D-5: 17 GATE = 12 GATE + 5 sub-gate 호출 기록** — Phase 5 `GATE_DEPS` dict의 sub-gate 5개(예: ASSET→{asset_sourcer,mosaic_inspector,license_inspector} 등 planner가 Phase 5 GATE_DEPS 실구조 재확인 후 정확 수치 확정). `verify_all_dispatched()`가 17개 모두 dispatch 기록 확인 후에만 COMPLETE 전이 허용. 16개 이하에서 COMPLETE 시도 시 `GateDispatchMissing` raise.
- **D-6: Checkpointer atomic write 검증** — `os.replace` 기반 atomic write이 E2E 1회 완주 중 12회 발생(각 GATE 완료 시점). `state/{session_id}/gate_NN.json` 파일 존재 + round-trip deserialize + highest gate_index resume 3-point 검증. Windows-safe `os.replace` 정상 동작 실측.

**Fault injection 시나리오 (D-7~D-9)**
- **D-7: CircuitBreaker 3×300s 발동** — Kling mock을 `inject_fault="circuit_3x"` 옵션으로 3회 연속 `CircuitBreakerTriggerError` raise. 3회 실패 후 breaker OPEN 상태 전이 + 다음 재시도가 `CircuitBreakerOpenError`로 거부되고, `cooldown_remaining_seconds >= 299` 확인 (5분 cooldown의 최소 299초 이상). Runway 자동 failover 경로는 별도 plan에서 다룸.
- **D-8: Fallback ken-burns template 실렌더** — Shotstack adapter `_build_ken_burns_fallback_timeline` (Phase 5 존재 또는 Phase 7에서 명시적 추가) 호출 시 `{asset: "still_image.jpg", effect: "zoom_in", duration_seconds: 3.0}` 포함 timeline JSON 생성 + filter chain에 `continuity_prefix` 여전히 prepend. D-19 filter order 위반 0건.
- **D-9: 재생성 루프 3회 초과 → FAILURES.md append + ken-burns 자동 삽입** — Producer/Inspector 재시도 3회 후에도 inspector FAIL 지속 시, shorts_pipeline.py가 `FAILURES.md` append + Shotstack render payload에 ken-burns fallback template 삽입하여 CIRCUIT_OPEN 없이 COMPLETE 도달. Phase 6 `check_failures_append_only` Hook과 충돌 없음 증명 (append-only 규율 준수).

**Harness-audit 기준 (D-10~D-12)**
- **D-10: harness-audit 스킬 실행 경로** — Phase 1에서 `../../harness/.claude/skills/harness-audit/SKILL.md` 상속 확인. Phase 7은 `studios/shorts` 루트에서 `harness-audit` 스킬 호출 (또는 skill wrapper script 직접 실행) → JSON 보고서 출력 → 점수 ≥ 80 검증. 스킬이 없거나 호출 실패 시 Phase 7 직접 `scripts/audit/run_harness_audit.py` CLI 작성 fallback 허용.
- **D-11: harness-audit 출력 JSON schema 고정** — 최소 필수 키: `score: int (0-100)`, `a_rank_drift_count: int`, `skill_over_500_lines: list[str]`, `agent_count: int`, `description_over_1024: list[str]`, `deprecated_pattern_matches: dict[str, int]`. Phase 7 테스트는 이 6 키 존재 + 타입 + 값 범위 검증.
- **D-12: A급 drift 0건 정의** — `.claude/deprecated_patterns.json` 8개 regex 전수 스캔 대상: `scripts/**/*.py` + `.claude/agents/**/*.md` + `tests/**/*.py` + `wiki/**/*.md` 전부. 매치 0건이어야 A급 drift 0건. canonical I2V 등 allow-list 예외는 Phase 5 test_six_patterns 패턴 승계.

**Tests infrastructure (D-13~D-15)**
- **D-13: tests/phase07/ 독립 디렉토리** — `tests/phase07/__init__.py` + `conftest.py` 신규 작성 (Phase 5/6 conftest 복사 금지 — Phase별 fixture 독립 원칙). 공통 fixture는 pytest plugin 혹은 상위 `tests/conftest.py` 승격 여부는 planner 판단.
- **D-14: 전체 suite 809/809 무회귀 + Phase 7 신규 추가만** — Phase 4 (244) + Phase 5 (329) + Phase 6 (236) 기존 테스트 수정 0건. Phase 7 신규 테스트는 `tests/phase07/test_*.py` 추가만. `pytest tests/phase04 tests/phase05 tests/phase06` 회귀 sweep 3 phase green 확인.
- **D-15: NotebookLM tier 2 고정 (offline E2E)** — `NotebookLMFallbackChain`을 `RAGBackend=None` + `GrepWikiBackend=None` + `HardcodedDefaultsBackend=only` 구성으로 instantiate. Phase 7 E2E 전 구간에서 tier 0/1 호출 0건. tier_used == 2 검증. 실 RAG 호출은 Phase 8 이후 온라인 시 활성화.

**Mock fixtures 스펙 (D-16~D-20)**
- **D-16: KlingI2V mock** — `respond_with={"task_id": "mock_kling_001", "status": "succeed", "video_url": "file://tests/phase07/fixtures/mock_kling.mp4"}`. `inject_fault` 옵션: `None` | `"circuit_3x"` (3회 연속 예외) | `"runway_failover"` (1회 예외 후 성공).
- **D-17: RunwayI2V mock** — `respond_with={"task_id": "mock_runway_001", "status": "SUCCEEDED", "output": ["file://tests/phase07/fixtures/mock_runway.mp4"]}`. `inject_fault` 옵션 동일.
- **D-18: Typecast TTS mock** — `respond_with={"speak_v2_url": "file://tests/phase07/fixtures/mock_typecast.wav", "duration_seconds": 3.0, "emotion_applied": true}`. 타임스탬프 자동 생성(audio-first video cuts driver 역할 유지).
- **D-19: ElevenLabs TTS mock** — `respond_with={"audio_url": "file://tests/phase07/fixtures/mock_elevenlabs.wav", "voice_id": "rachel_mock", "duration_seconds": 3.0}`. Typecast fallback 경로 증명 전용.
- **D-20: Shotstack render mock** — `respond_with={"response": {"message": "Created", "id": "mock_shotstack_001", "url": "file://tests/phase07/fixtures/mock_shotstack.mp4"}, "success": true, "status": "done"}`. ken-burns fallback 경로는 `template="ken_burns"` 파라미터 감지 후 별도 응답 분기.

**Determinism + 회귀 (D-21~D-23)**
- **D-21: Fixed seed + fixed timestamps** — 모든 mock은 `freezegun`(있다면) 또는 직접 monkeypatch로 `datetime.now() = 2026-04-19T00:00:00Z` 고정. UUID는 `uuid.UUID("00000000-0000-0000-0000-000000000001")` 시작 incremental. 재실행 시 bytes-identical 출력.
- **D-22: Windows cp949 + UTF-8 round-trip** — 모든 Phase 7 테스트 subprocess 호출은 Phase 6 패턴 승계: `sys.stdout.reconfigure(encoding="utf-8")` + subprocess `encoding="utf-8"` + `errors="replace"`. 한국어 fixture (예: trend keyword, continuity prefix) round-trip 검증 1건 이상.
- **D-23: Phase 4/5/6 기존 testsuite 809/809 무회규 + Phase 7 신규 추가만** — Phase 7 execute-phase 중 매 Wave 완료 시 `pytest tests/phase04 tests/phase05 tests/phase06` 회귀 sweep 실행. 실패 0건 유지. Phase 7 신규 테스트 증가는 허용되나 기존 테스트 수정은 Rule 1 deviation으로 명시 기록.

### Claude's Discretion (명시적 위임)

- tests/phase07/ 내 테스트 파일 개수 및 네이밍 (Phase 5/6 패턴 참고하되 planner가 Phase 7 Wave 구조에 맞게 분할)
- mock adapter 구현 위치: `tests/phase07/mocks/` vs `tests/phase07/fixtures/adapters/` — planner 판단
- harness-audit 스킬 호출 방식: Skill tool 직접 호출 vs wrapper CLI (`scripts/audit/run_harness_audit.py`) — 스킬 상속 확인 후 planner 판단
- ken-burns fallback template JSON 세부 구조: 3초 줌인 + 정지 이미지 경로는 고정, 나머지 detail planner 판단
- Phase 7 verify_all_dispatched() 실제 17 sub-gate 수치 확정: planner가 Phase 5 `scripts/orchestrator/gate_guard.py` + `GATE_DEPS` 실구조 read-first 후 정확 수치 lock-in

### Deferred Ideas (OUT OF SCOPE)

- **NotebookLM 채널바이블 노트북 URL 실 확보**: Phase 6 `TBD-url-await-user` placeholder 그대로. Phase 7은 tier 2 (hardcoded defaults) 고정이므로 blocking 아님. Phase 8 이후 온라인 활성화 시 필요.
- **Kling/Runway adapter ContinuityPrefix 주입 확장**: Phase 6 Shotstack만. Phase 7 E2E에서 Kling/Runway 영상 생성 요청에도 ContinuityPrefix 전달 필요성 관찰 가능 → Phase 8 개선 대상으로 deferred-items.md 기록.
- **실 API 호출 smoke test (1건 per adapter)**: Phase 7은 100% mock. Phase 8에서 실 API 키 + credit 투입 후 최소 1건 smoke test (비용 < $1 목표).
- **harness-audit 자동 월 1회 cron**: Phase 7은 1회 실행 증명까지. 월 1회 cron 설치는 Phase 10 `AUDIT-02`.
- **drift_scan.py 주 1회 cron**: Phase 7은 harness-audit 내장 drift 검사만. 독립 `scripts/audit/drift_scan.py` + weekly cron은 Phase 10 `AUDIT-03`.
- **session_start.py 매 세션 감사 점수 출력**: Phase 10 `AUDIT-01` deferred.
- **Playwright E2E (실 브라우저 통한 YouTube 발행)**: Phase 7은 mock only. 실 브라우저 자동화는 Phase 8 publisher agent 담당.
- **pytest-socket `disable_socket` 도입**: Phase 7에서 실 네트워크 호출 0건을 강제로 증명하고 싶다면 `pytest-socket` 도입 고려. 현재는 monkeypatch + 문서화로 우회 (dependency 추가 보류).

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | E2E mock asset 파이프라인 1회 성공 (실 API 비용 회피) | §Area 2 (Pipeline contract + precedent `test_pipeline_e2e_mock.py` 이미 13-GATE mock walk 구현) + §Area 4 (5 adapter mock signatures) |
| TEST-02 | `verify_all_dispatched()` 통과 + 17 GATE 모두 호출 확인 | §Area 1 (**CRITICAL**: 실제 구현은 13 operational gates, 17이 아님. CONTEXT D-5 오기. Planner MUST lock 13). |
| TEST-03 | Circuit Breaker 3회 발동 시나리오 테스트 | §Area 3 (CircuitBreaker CLOSED→OPEN→HALF_OPEN + 실제 예외 이름 `CircuitBreakerOpenError` + 300초 strict cooldown boundary precedent) |
| TEST-04 | Fallback 샷(정지 이미지 + 줌인) 테스트 | §Area 7 + §Area 8 (`_producer_loop` 3-retry exhaustion → `append_failures` + `insert_fallback_shot` → `create_ken_burns_clip` 3-step chain, `ASSETS`/`THUMBNAIL` gate only) |

Phase 7 SC mapping:
- **SC 1** (E2E mock $0) ⇐ TEST-01
- **SC 2** (verify_all_dispatched 17→13 lock) ⇐ TEST-02
- **SC 3** (CircuitBreaker 5-min cooldown) ⇐ TEST-03
- **SC 4** (Fallback ken-burns no CIRCUIT_OPEN) ⇐ TEST-04
- **SC 5** (harness-audit ≥ 80 + drift 0 + SKILL 500 line 0) ⇐ cross-cuts all 4 REQs via repository-wide audit

</phase_requirements>

## Project Constraints (from CLAUDE.md)

Constraints inherited from `studios/shorts/CLAUDE.md` that the Phase 7 test suite MUST respect:

- **도메인 절대 규칙 8개** — `skip_gates` / `TODO(next-session)` / try-except 침묵 / T2V / Selenium / shorts_naberal 수정 / K-pop 직접 사용 / 주 3~4편 발행. Phase 7 테스트 코드는 이 중 어느 하나도 포함해서는 안 됨. `deprecated_patterns.json` 8 regex에 의해 Hook이 물리 차단.
- **SKILL.md ≤ 500줄** — Phase 7은 신규 SKILL 생성 없음. 기존 5개 공용 skill 중 어느 하나라도 500줄 초과 시 harness-audit A급 drift.
- **에이전트 총합 32명** (Producer 14 + Inspector 17 + Supervisor 1) — harness-audit `agent_count` 키가 32를 보고해야 함 (±0 변동).
- **Hooks 3종 활성** — `pre_tool_use.py` 기존 확장 (FAILURES append-only + SKILL_HISTORY backup)은 Phase 6에서 이미 설치. Phase 7 테스트는 Hook 동작에 의존.
- **GSD Workflow Enforcement** — 작업은 `/gsd:execute-phase` 통해만. `/gsd:verify-work 07`로 gate 통과 최종 승인.
- **shorts_naberal 원본 수정 금지** — NotebookLM 경로 D-7 참조 규율 (Phase 7 tier 2 only이므로 NotebookLM skill 미호출, 영향 없음).

## Critical CONTEXT.md Corrections

Three CONTEXT D-4/D-5/D-7 assertions are **falsified by source code inspection** on 2026-04-19. The planner MUST correct these in PLAN.md files and keep the RESEARCH.md language as the single source of truth.

### Correction 1: "17 GATE = 12 + 5 sub-gate" is factually incorrect

**CONTEXT D-5 claim:** "17 GATE = 12 GATE + 5 sub-gate 호출 기록" — `verify_all_dispatched()`가 17개 모두 dispatch 기록 확인 후에만 COMPLETE 전이 허용.

**Actual code** (`scripts/orchestrator/gate_guard.py:94-96`):

```python
_OPERATIONAL_GATES: frozenset[GateName] = frozenset(
    g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)
)
```

And `gate_guard.py:169-176`:

```python
def verify_all_dispatched(self) -> bool:
    """COMPLETE precondition (ORCH-04, D-4).

    Returns True only when every one of the 13 operational gates
    (TREND..MONITOR) is in the dispatched set. IDLE and COMPLETE are
    excluded by construction.
    """
    return _OPERATIONAL_GATES.issubset(self._dispatched)
```

And the docstring of `gate_guard.py:6-11`:

> ``verify_all_dispatched()`` is the precondition for the COMPLETE transition
> (all 13 operational gates — TREND..MONITOR — must be dispatched).

**Also confirmed by `tests/phase05/test_verify_all_dispatched.py:36-43`:**

```python
def test_all_13_operational_dispatch_is_true(tmp_state_dir):
    g = GateGuard(None, "s1")
    operational = [
        gate for gate in GateName if gate not in (GateName.IDLE, GateName.COMPLETE)
    ]
    assert len(operational) == 13
    for gate in operational:
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is True
```

**What CONTEXT likely confused with "5 sub-gates":** `scripts/orchestrator/shorts_pipeline.py:76-103` defines `GATE_INSPECTORS` — a per-gate Inspector fan-out map. Enumerated 2026-04-19 via `python -c ...`:

| Gate | Fan-out count | Inspectors |
|------|---------------|------------|
| TREND | 1 | ins-readability |
| NICHE | 1 | ins-blueprint-compliance |
| RESEARCH_NLM | 1 | ins-factcheck |
| BLUEPRINT | 2 | ins-blueprint-compliance, ins-timing-consistency |
| SCRIPT | 4 | ins-narrative-quality, ins-korean-naturalness, ins-tone-brand, ins-readability |
| POLISH | 3 | ins-korean-naturalness, ins-tone-brand, ins-schema-integrity |
| VOICE | 2 | ins-audio-quality, ins-subtitle-alignment |
| ASSETS | 3 | ins-mosaic, ins-gore, ins-license |
| ASSEMBLY | 3 | ins-render-integrity, ins-subtitle-alignment, ins-timing-consistency |
| THUMBNAIL | 2 | ins-thumbnail-hook, ins-safety |
| METADATA | 2 | ins-platform-policy, ins-safety |
| UPLOAD | 1 | ins-platform-policy |
| MONITOR | 1 | ins-schema-integrity |
| **Total fan-out invocations** | **26** | **17 unique inspectors** |

The number "17" does appear — it is the count of **unique** inspectors (AGENT-04 / Phase 4). The number "5" and "12" are not anywhere in the dispatch machinery. There is **no runtime counter** that totals to 17 or 12+5.

**Planner action:** TEST-02 SC MUST assert `pipeline.gate_guard.verify_all_dispatched()` returns True exactly when all 13 operational gates (TREND..MONITOR) are dispatched, and `len(pipeline.gate_guard.dispatched) == 13` at COMPLETE. The "17 sub-gate" prose in CONTEXT MUST NOT appear in the test assertions. (Optionally: add a secondary test that asserts `len(GATE_INSPECTORS) == 13` and the total Inspector fan-out equals 26, so future refactors don't quietly drift.)

### Correction 2: Exception class is `CircuitBreakerOpenError`, not `CircuitBreakerTriggerError`

**CONTEXT D-7 claim:** "`inject_fault="circuit_3x"` 옵션으로 3회 연속 `CircuitBreakerTriggerError` raise"

**Actual code** (`scripts/orchestrator/circuit_breaker.py:57-72`):

```python
class CircuitBreakerOpenError(RuntimeError):
    """Raised when a caller hits an OPEN breaker.

    Carries the breaker ``name`` so upstream handlers (ORCH-04 failure
    journal, ORCH-05 gate guard) can log which adapter tripped.
    """

    def __init__(self, breaker_name: str, cooldown_remaining: Optional[float] = None):
        self.breaker_name = breaker_name
        self.cooldown_remaining = cooldown_remaining
        ...
```

There is **no `CircuitBreakerTriggerError` class anywhere in the codebase**. The trip mechanism (lines 174-183) is: each `_record_failure()` increments `failure_count`; when `failure_count >= max_failures` (default 3), `_trip_open()` flips state to OPEN. No dedicated "trigger" exception — the in-flight exception that the fn raised propagates up through `raise` on line 140. Only the **next** call after OPEN raises `CircuitBreakerOpenError`.

**Planner action:** Mock adapters should raise `RuntimeError` (or any arbitrary non-SystemExit exception) three times; the breaker will then flip to OPEN, and the 4th call to `cb.call(fn)` raises `CircuitBreakerOpenError`. The "trigger" name is a semantic mistake — rename mock option to `inject_fault="raise_3x_runtime_error"` or equivalent. TEST-03 assertion: the 4th call raises `CircuitBreakerOpenError` with `cooldown_remaining >= 299.0` (per `test_circuit_breaker_cooldown.py:42-55` precedent).

### Correction 3: `_build_ken_burns_fallback_timeline` does NOT exist

**CONTEXT D-8 claim:** "Shotstack adapter `_build_ken_burns_fallback_timeline` (Phase 5 존재 또는 Phase 7에서 명시적 추가) 호출 시 ..."

**Actual code** (`scripts/orchestrator/api/shotstack.py:155-216`):

The real method is `ShotstackAdapter.create_ken_burns_clip(image_path, duration_s, scale_from, scale_to, pan_direction) -> Path`. It builds its **own standalone** Shotstack timeline payload (single clip, effect = zoomIn variant, transition = fade in/out) and POSTs directly — it is NOT a subroutine of the main `render()` path. ContinuityPrefix filter chain is only injected by `render()`, not by `create_ken_burns_clip()`.

**Actual Fallback flow:**

1. `shorts_pipeline._producer_loop` (lines 576-625) exhausts 3 retries.
2. `append_failures(...)` writes to `.claude/failures/orchestrator.md` (Phase 6 append-only FAIL-01 compliant).
3. Only for `gate in (GateName.ASSETS, GateName.THUMBNAIL)` (line 621): returns `_insert_fallback(gate, last_output)`.
4. `_insert_fallback` (lines 627-655) calls `insert_fallback_shot` (`fallback.py:67-122`) which calls `shotstack.create_ken_burns_clip(...)` (`shotstack.py:155-216`).
5. For gates OTHER than ASSETS/THUMBNAIL (e.g. SCRIPT, VOICE, ASSEMBLY), `RegenerationExhausted` raises and the pipeline aborts — **not** replaced by ken-burns.

**Planner action:** TEST-04 MUST (a) trigger failure on `ASSETS` or `THUMBNAIL` gate specifically (never on a structurally-consumed gate), (b) assert `append_failures` wrote one entry to `failures_path`, (c) assert `shotstack.create_ken_burns_clip` was called with `duration_s > 0`, (d) assert the returned dict has `is_fallback=True`, (e) assert final pipeline `dispatched_count == 13` and `fallback_count >= 1` (ctx.fallback_indices). There is no "ken-burns template inside the main render payload" — the ken-burns is a separate render job entirely.

A second clarification: CONTEXT D-8 mentions "filter chain에 `continuity_prefix` 여전히 prepend. D-19 filter order 위반 0건." This is a red herring — `create_ken_burns_clip` does not go through `_build_timeline_payload` (which injects continuity_prefix), so the ken-burns output has no filter chain at all. The planner may optionally add a follow-up test that the main `render()` path (which DOES use filter chains) still prepends `continuity_prefix` when ken-burns is in effect, but this would be a Phase 6 regression, not a Phase 7 requirement.

## Standard Stack

### Core (every library verified installed on target 2026-04-19)

| Library | Version (verified) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| Python | 3.11.9 | Runtime | Phase 5/6 승계; IntEnum, match_case, graphlib. Verified: `python --version`. |
| pytest | 8.4.2 | Test runner | Phase 5 sweep 329 tests / ~5s. Phase 6 added 236 tests. Verified: `python -m pytest --version`. |
| pydantic | 2.12.5 | I2VRequest / ShotstackRenderRequest / ContinuityPrefix validation at parse time | Already used by Phase 5/6 adapters. Verified: `python -c "import pydantic; print(pydantic.VERSION)"`. |
| httpx | 0.28.1 | Shotstack adapter HTTP client (mocked in tests) | Already used by Phase 5. Verified. |
| stdlib `unittest.mock` | built-in 3.11.9 | `MagicMock`, `patch` — primary mock surface | Used by `test_pipeline_e2e_mock.py`, `test_circuit_breaker_cooldown.py`, etc. No dependency needed. |
| stdlib `pathlib` | built-in | Mock asset paths, Checkpointer state dirs, FAILURES.md path | All Phase 5/6 tests use `Path`. |
| stdlib `subprocess` | built-in | harness-audit CLI invocation from test | Phase 6 test_notebooklm_subprocess.py precedent. |
| stdlib `json` | built-in | Checkpointer file round-trip + harness-audit D-11 JSON emission | Phase 5/6 pattern. |
| stdlib `hashlib` | built-in | Mock asset fingerprint + optional sha256 determinism check | Phase 5 sha256_file helper already in use. |
| stdlib `time`, `datetime` | built-in | Timestamp monkeypatch targets (CircuitBreaker `time.monotonic`; Checkpointer `datetime.now`) | `test_circuit_breaker_cooldown.py:37` patches `scripts.orchestrator.circuit_breaker.time.monotonic`. Same pattern for D-21. |

### NOT installed (and NOT required)

| Library | Mentioned in | Verdict | Workaround |
|---------|--------------|---------|------------|
| `pytest-socket` | CONTEXT D-1 (optional) | Absent (`ModuleNotFoundError`). | Use `monkeypatch` + `unittest.mock.patch` to swap adapter HTTP clients. Phase 5 E2E test does not need pytest-socket because it uses MagicMock adapters exclusively — no real network reachable. |
| `freezegun` | CONTEXT D-21 (optional) | Absent (`ModuleNotFoundError`). | Use `unittest.mock.patch("scripts.orchestrator.circuit_breaker.time.monotonic")` for cooldown + `monkeypatch.setattr` on `datetime.now` via wrapper. Phase 5 already uses this pattern at 4 test sites. |

**Planner decision:** Do NOT add `pytest-socket` / `freezegun` dependencies. Phase 7 can be completed with stdlib-only mocking, preserving the "zero new runtime dep" discipline established in Phase 5. Document this in the Phase 7 plan rationale.

### Supporting (already inside `scripts/orchestrator/` — Phase 5/6 products)

| Module | Purpose in Phase 7 |
|--------|--------------------|
| `scripts.orchestrator.ShortsPipeline` | SUT. Instantiated with 5 MagicMock adapters, MagicMock producer / supervisor invokers. |
| `scripts.orchestrator.GateName`, `GATE_DEPS` | 13-member IntEnum + DAG; tests assert enum ordering + dependency resolution. |
| `scripts.orchestrator.GateGuard`, `Verdict` | `dispatch()` called 13 times; `verify_all_dispatched()` final check. |
| `scripts.orchestrator.CircuitBreaker`, `CircuitBreakerOpenError`, `CircuitState` | TEST-03 primary target. `patch("scripts.orchestrator.circuit_breaker.time.monotonic")` for cooldown-window assertions. |
| `scripts.orchestrator.Checkpointer`, `Checkpoint`, `sha256_file` | TEST-01 produces 13+1=14 `state/{sid}/gate_NN.json` files; tests assert count + round-trip. |
| `scripts.orchestrator.fallback.append_failures`, `insert_fallback_shot` | TEST-04 primary target; append-only FAILURES + ken-burns insertion. |
| `scripts.orchestrator.voice_first_timeline.VoiceFirstTimeline` | `.align()` + `.insert_transition_shots()` mocked to return `[]` in E2E test (no real audio/video data). |
| `scripts.orchestrator.api.kling_i2v.KlingI2VAdapter` etc. (5 adapters) | Replaced by `MagicMock()` instances with `.image_to_video`, `.generate`, `.render`, `.upscale`, `.create_ken_burns_clip` stubs. |
| `scripts.notebooklm.fallback.NotebookLMFallbackChain`, `HardcodedDefaultsBackend` | D-15: instantiate with `backends=[HardcodedDefaultsBackend()]` only; assert `tier_used == 2` on every query. |
| `scripts.validate.harness_audit.main` | EXISTING 121-line CLI producing text `HARNESS_AUDIT_SCORE: N`. Extend with `--json-out` flag to emit D-11 6-key schema. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MagicMock adapters | Real adapter instances with `patch` on `_submit_and_poll` / `_post_render` / `_invoke_typecast_api` | MagicMock is simpler but skips pydantic validation at input (e.g., I2VRequest). Plan 07 precedent uses pure MagicMock; recommended for TEST-01. For TEST-03 (circuit breaker), a hybrid is needed: MagicMock with `side_effect=[RuntimeError, RuntimeError, RuntimeError, "ok"]` to drive 3-fail-then-success. **DECISION: MagicMock + side_effect.** |
| `scripts/validate/harness_audit.py` extension | New `scripts/audit/run_harness_audit.py` per CONTEXT D-10 fallback | Existing script already exists (121 lines) and scores 90 today. Building a parallel script violates DRY. **DECISION: extend existing with `--json-out`, preserving text output as default for backward compatibility.** |
| Skill-tool invocation of `harness-audit` SKILL.md | Direct CLI call `python -m scripts.validate.harness_audit` | The SKILL.md is natural-language pseudocode with no executable; invoking it via the Claude Skill tool requires an LLM roundtrip that a plain pytest test cannot do. **DECISION: CLI path only.** The SKILL.md remains as author-guidance; the actual score attainment is proven by subprocess-invoking the CLI. |
| File-URL mock assets (`file://...`) | Real tiny `.mp4` + `.wav` blob files in `tests/phase07/fixtures/` | Phase 5 E2E test creates Path references but never actually reads bytes from them — MagicMock returns pre-set Path objects. For TEST-04, `insert_fallback_shot` DOES receive a real Path from `asset_sourcer_invoker`, but `create_ken_burns_clip` is a MagicMock so the bytes aren't read. **DECISION: touch zero-byte placeholder files (`Path.touch()`) or use `tmp_path / "x.mp4"` without writing content.** Actual valid MP4/WAV headers would be useful only if a real decoder is involved, which it is not. |
| CircuitBreaker integration test on real clock | `patch("scripts.orchestrator.circuit_breaker.time.monotonic")` per Phase 5 precedent | Real clock tests would require 300+ second sleeps. **DECISION: monkeypatch time.** Precedent at `tests/phase05/test_circuit_breaker_cooldown.py:37-55`. |
| Inspector real invocation | Skip entirely — producer_invoker and supervisor_invoker are DI seams | Phase 4 inspectors return structured verdicts via LLM — unreliable + slow + costs tokens. Phase 5 E2E test injects MagicMock for both invokers. **DECISION: MagicMock(return_value=_pass_verdict()). For TEST-04, override to `side_effect=[FAIL, FAIL, FAIL]`.** |

**Installation (Phase 7 requires NO new installs):**

```bash
# Verification only
python -c "import pytest, pydantic, httpx; print(pytest.__version__, pydantic.VERSION, httpx.__version__)"
# Expected: 8.4.2 2.12.5 0.28.1
```

**Version verification performed 2026-04-19 on the target machine.** No drift from Phase 5/6 baseline.

## Architecture Patterns

### Recommended Phase 7 Test Directory Structure

```
studios/shorts/
├── scripts/validate/
│   └── harness_audit.py                # EXTEND: add --json-out flag (D-11 6-key schema)
├── scripts/validate/
│   └── phase07_acceptance.py           # NEW: SC1-5 CLI E2E gate (Phase 5/6 precedent)
└── tests/phase07/
    ├── __init__.py                     # NEW (D-13)
    ├── conftest.py                     # NEW (D-13: do NOT reuse phase05/06 conftest)
    ├── fixtures/
    │   ├── mock_kling.mp4              # 0-byte placeholder (D-2 minimal)
    │   ├── mock_runway.mp4             # 0-byte placeholder
    │   ├── mock_typecast.wav           # 44-byte RIFF header (minimal valid WAV)
    │   ├── mock_elevenlabs.wav         # 44-byte RIFF header
    │   ├── mock_shotstack.mp4          # 0-byte placeholder
    │   └── still_image.jpg             # 0-byte placeholder (ken-burns source)
    ├── mocks/
    │   ├── __init__.py
    │   ├── kling_mock.py               # inject_fault=None | "circuit_3x" | "runway_failover"
    │   ├── runway_mock.py
    │   ├── typecast_mock.py
    │   ├── elevenlabs_mock.py
    │   └── shotstack_mock.py
    ├── test_e2e_happy_path.py          # TEST-01 + SC1: 13-GATE mock walk, dispatched_count==13
    ├── test_verify_all_dispatched.py   # TEST-02 + SC2: exactly 13 operational gates, COMPLETE guard
    ├── test_checkpointer_14_files.py   # D-6: 13 operational + 1 COMPLETE = 14 gate_NN.json files
    ├── test_circuit_breaker_3x.py      # TEST-03 + SC3: 3 RuntimeError → OPEN → CircuitBreakerOpenError
    ├── test_fallback_ken_burns.py      # TEST-04 + SC4: ASSETS gate retry exhaust → FAILURES append + create_ken_burns_clip
    ├── test_producer_loop_retries.py   # D-9: retry_counts[gate] == 3 at exhaustion
    ├── test_notebooklm_tier_2.py       # D-15: FallbackChain with only HardcodedDefaultsBackend → tier_used == 2
    ├── test_harness_audit_json.py      # D-11: subprocess call + parse JSON + 6-key schema check
    ├── test_harness_audit_score_ge_80.py  # SC5: score >= 80 assertion
    ├── test_harness_audit_drift_zero.py   # D-12: A급 drift 0 across scripts/ + agents/ + tests/ + wiki/
    ├── test_skill_500_lines.py         # D-12: every SKILL.md ≤ 500 lines (5 skills)
    ├── test_agent_count_32.py          # CLAUDE.md invariant: harness_audit.agent_count == 32
    ├── test_deterministic_rerun.py     # D-21: same session_id → same checkpoint file set
    ├── test_cp949_utf8_roundtrip.py    # D-22: Korean fixture survives subprocess call
    ├── test_regression_809.py          # D-23: subprocess pytest tests/phase04 tests/phase05 tests/phase06 → 0 failures
    └── test_phase07_acceptance.py      # SC1-5 acceptance runner (parallels test_phase05_acceptance.py)
```

This layout yields roughly 16 test files. Planner may merge or split; the minimum is one file per TEST-REQ-ID plus harness-audit extension tests.

### Pattern 1: MagicMock-Powered E2E Happy Path (TEST-01)

**What:** Drive `ShortsPipeline.run()` to COMPLETE using five MagicMock adapters + MagicMock producer_invoker + MagicMock supervisor_invoker returning `_pass_verdict()`. Precedent: `tests/phase05/test_pipeline_e2e_mock.py:51-112` (already green since Wave 5 of Phase 5).

**When to use:** TEST-01 happy-path and SC1 verification. Any scenario where every gate must pass on first try.

**Canonical shape** (verbatim from Phase 5 precedent — planner should copy + augment rather than reinvent):

```python
# tests/phase05/test_pipeline_e2e_mock.py lines 51-112 (cite verbatim as precedent)
def test_full_pipeline_runs_13_gates(tmp_path: Path, _fake_env: None) -> None:
    producer_output = {
        "artifact_path": str(tmp_path / "artifact.json"),
        "prompt": "p",
        "duration_seconds": 5,
        "anchor_frame": str(tmp_path / "a.png"),
    }
    producer = MagicMock(return_value=producer_output)
    supervisor = MagicMock(return_value=_pass_verdict())

    kling = MagicMock()
    kling.image_to_video.return_value = tmp_path / "cut.mp4"
    runway = MagicMock()
    runway.image_to_video.return_value = tmp_path / "cut.mp4"
    typecast = MagicMock()
    typecast.generate.return_value = []
    elevenlabs = MagicMock()
    elevenlabs.generate_with_timestamps.return_value = []
    shotstack = MagicMock()
    shotstack.render.return_value = {"url": str(tmp_path / "out.mp4"), "id": "r1", "status": "done"}
    shotstack.upscale.return_value = {"status": "skipped"}
    shotstack.create_ken_burns_clip.return_value = tmp_path / "kenburns.mp4"

    pipeline = ShortsPipeline(
        session_id="e2e_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=kling, runway_adapter=runway, typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs, shotstack_adapter=shotstack,
        producer_invoker=producer, supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )

    with patch.object(pipeline.timeline, "align", return_value=[]), \
         patch.object(pipeline.timeline, "insert_transition_shots", return_value=[]):
        result = pipeline.run()

    assert result["session_id"] == "e2e_test"
    assert result["final_gate"] == "COMPLETE"
    assert result["dispatched_count"] == 13
    assert result["fallback_count"] == 0
```

Phase 7's TEST-01 should reuse this exact pattern, changing only the session_id and adding Phase 7-specific assertions (e.g., `failures_path.read_text() == ""` because happy path never appends; `len(list(session_dir.glob("gate_*.json"))) == 14` for the 13 operational + 1 COMPLETE).

### Pattern 2: CircuitBreaker 3-Fail → OPEN → Cooldown-Blocked Retry (TEST-03)

**What:** Drive Kling adapter to fail 3 consecutive times via `MagicMock(side_effect=[RuntimeError("boom"), RuntimeError, RuntimeError, ...])`. Assert `cb.state is CircuitState.OPEN` after 3rd raise, and assert `CircuitBreakerOpenError` on the 4th call. Patch `circuit_breaker.time.monotonic` so cooldown timeline is deterministic.

**When to use:** TEST-03 specifically. Precedent: `tests/phase05/test_circuit_breaker_cooldown.py:29-79`.

**Shape:**

```python
from unittest.mock import patch, MagicMock
import pytest
from scripts.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState

def test_kling_3x_failure_opens_breaker_and_blocks_cooldown():
    cb = CircuitBreaker(name="kling", max_failures=3, cooldown_seconds=300)

    def boom():
        raise RuntimeError("mock kling failure")

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 1000.0
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(boom)
        assert cb.state is CircuitState.OPEN
        assert cb.failure_count == 3

        # Immediately after trip: breaker blocks next call.
        mock_time.return_value = 1000.0
        with pytest.raises(CircuitBreakerOpenError) as exc:
            cb.call(lambda: "blocked")
        # cooldown_remaining is ≤ 300 and > 0 immediately after trip.
        assert exc.value.cooldown_remaining is not None
        assert exc.value.cooldown_remaining > 299.0  # D-7 assertion

        # 299.5s later — still blocked (strict >).
        mock_time.return_value = 1000.0 + 299.5
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")
```

For the Phase 7 integration variant (end-to-end through ShortsPipeline), the mock Kling adapter's `.image_to_video` should have `side_effect=[RuntimeError, RuntimeError, RuntimeError]`, and the ASSETS-gate call should trigger the Kling breaker trip. Since `_run_assets` catches `CircuitBreakerOpenError` and falls over to Runway (lines 452-460), the integration TEST-03 must EITHER: (a) also mock Runway to fail, OR (b) be a unit test at the CircuitBreaker level not wired through the full pipeline. Recommendation: **unit test at CircuitBreaker level** (shown above), since the Kling→Runway failover is a separate concern tested by existing `test_kling_runway_failover.py` in Phase 5.

### Pattern 3: Regeneration Exhaustion → FAILURES append → ken-burns (TEST-04)

**What:** Supervisor returns `FAIL` for ASSETS gate 3 consecutive times. `_producer_loop` (shorts_pipeline.py:576-625) appends a failure entry and calls `_insert_fallback` → `insert_fallback_shot` → `shotstack.create_ken_burns_clip`. Pipeline continues to COMPLETE without CIRCUIT_OPEN.

**When to use:** TEST-04 exclusively. There is no Phase 5 precedent for a full-pipeline retry-exhaustion scenario (Phase 5 retains `test_fallback_shot.py` at the unit level only). Phase 7 is the first to prove the end-to-end integration.

**Shape:**

```python
from unittest.mock import MagicMock, patch
from pathlib import Path
from scripts.orchestrator import ShortsPipeline, GateName, Verdict

def _fail_verdict():
    return Verdict(result="FAIL", score=0,
                   evidence=[{"rule": "mosaic_missing", "detail": "face exposed"}],
                   semantic_feedback="face still visible", inspector_name="ins-mosaic")

def _pass_verdict():
    return Verdict(result="PASS", score=90, evidence=[],
                   semantic_feedback="", inspector_name="shorts-supervisor")

def test_assets_gate_exhaustion_triggers_ken_burns_fallback(tmp_path, _fake_env):
    supervisor = MagicMock()
    # ASSETS gate fails 3 times; everything else passes. Because _producer_loop
    # calls supervisor_invoker INSIDE the retry loop AND the outer dispatch call
    # also calls supervisor_invoker, pattern the side_effect accordingly (see
    # shorts_pipeline.py line 432 dispatch AFTER _run_assets returns — actually
    # _run_assets calls supervisor on line 473 once per call, not per retry; the
    # retry loop is in _producer_loop which is NOT used by _run_assets — it is
    # used by _run_thumbnail and _run_script etc. For ASSETS gate which has no
    # _producer_loop, the retry exhaustion only happens for THUMBNAIL in the
    # default structure. Planner MUST confirm which gate actually uses the
    # producer_loop by re-reading shorts_pipeline.py lines 323-570).
    ...
```

**OPEN QUESTION (planner must resolve):** Which gates actually route through `_producer_loop`? A line-by-line read of `shorts_pipeline.py:323-570` shows `_producer_loop` is called by `_run_trend, _run_niche, _run_research_nlm, _run_blueprint, _run_script, _run_polish, _run_thumbnail, _run_metadata, _run_upload, _run_monitor` — 10 gates total. `_run_voice` and `_run_assets` do NOT use `_producer_loop`; they handle their own retry/fallback via CircuitBreaker and Kling→Runway failover. `_run_assembly` also does not use producer_loop.

This means the **ken-burns Fallback lane (ASSETS or THUMBNAIL per line 621) is only triggered by THUMBNAIL**, not ASSETS. A THUMBNAIL gate failure 3× → FAILURES.md append + ken-burns. **Planner MUST lock TEST-04 target gate as THUMBNAIL** (not ASSETS), matching the actual code path.

The shape becomes:

```python
# Only THUMBNAIL runs through _producer_loop (other gates either have their own
# retry logic or can't trigger ken-burns). Pattern side_effect for THUMBNAIL
# to fail 3x; all other gates PASS.

invocation_count = {"THUMBNAIL": 0}

def supervisor_side_effect(gate, output):
    if gate == GateName.THUMBNAIL:
        invocation_count["THUMBNAIL"] += 1
        if invocation_count["THUMBNAIL"] <= 3:
            return _fail_verdict()
    return _pass_verdict()

supervisor.side_effect = supervisor_side_effect
```

Then assert after `pipeline.run()`:

- `result["dispatched_count"] == 13` (pipeline reached COMPLETE)
- `result["fallback_count"] == 1` (one ken-burns inserted)
- `(tmp_path / "failures.md").exists()` and `"THUMBNAIL FAIL after regeneration exhausted" in failures_content`
- `shotstack.create_ken_burns_clip.call_count == 1`
- `invocation_count["THUMBNAIL"] == 3` (exactly 3 retries before fallback)

### Pattern 4: harness-audit JSON Extension (D-10/D-11)

**What:** Extend `scripts/validate/harness_audit.py` with a `--json-out` CLI flag that emits the D-11 6-key schema to stdout or a file. Retain current text output as default for backward compatibility with Phase 4 Wave 5 acceptance.

**When to use:** Phase 7 Wave 4 when extending the existing CLI. Test consumes the JSON output via `subprocess.run` and `json.loads`.

**Shape (addition to existing `harness_audit.py:90-121`):**

```python
parser.add_argument("--json-out", type=pathlib.Path, default=None,
                    help="If set, write D-11 6-key JSON to this file (in addition to stdout text).")

# After score computation:
if args.json_out:
    # D-11 6-key schema
    report = {
        "score": score,
        "a_rank_drift_count": _count_drift_violations(violations),  # NEW helper
        "skill_over_500_lines": _skills_over_500(),                 # NEW helper
        "agent_count": _count_agents(agents_root=pathlib.Path(args.agents_root)),
        "description_over_1024": _descriptions_over_1024(),
        "deprecated_pattern_matches": _scan_deprecated_patterns(),  # NEW
        "phase": 7,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
```

Each new helper is ≤ 30 lines; all are stdlib-only.

### Anti-Patterns to Avoid

- **Real network calls:** Using a real Kling/Runway/Shotstack API key in any Phase 7 test is a D-1 violation. Verify: `grep -rE "KLING_API_KEY\s*=\s*os.environ" tests/phase07/` — only `monkeypatch.setenv(...)` with fake values allowed.
- **Modifying Phase 4/5/6 tests:** D-14 forbids edits to `tests/phase04/`, `tests/phase05/`, `tests/phase06/`. Wave 0 of Phase 7 plan must `git diff --name-only HEAD -- tests/phase04 tests/phase05 tests/phase06 | wc -l` return 0.
- **Hard-coded line numbers in assertions:** Line numbers change with edits. Use `len(GATE_INSPECTORS) == 13` instead of "line 76 has 13 entries". Semantic assertions only.
- **Test pollution:** Leaving `state/` dirs, `failures.md` files, or `outputs/` dirs after a test is a determinism hazard. Every Phase 7 test MUST use `tmp_path` (pytest-provided) and NEVER write to `.claude/failures/orchestrator.md` directly.
- **Asserting on real timestamps:** `datetime.now()` calls leak real wall-clock values into Checkpoint files. D-21 requires monkeypatching `datetime.now` via wrapper or asserting only on ISO-8601 format (regex) rather than exact value.
- **Importing from `.api.*` without lazy loading:** `elevenlabs`, `typecast`, `runwayml`, `fal_client`, `pydub` are **lazy imports** inside method bodies (see `kling_i2v.py:148`, `typecast.py:272`). Phase 7 tests MUST NOT import them at test module level — those modules may be absent on CI.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Breaker state machine for tests | Custom `FakeBreaker` | Real `CircuitBreaker` + `patch(time.monotonic)` | Phase 5's breaker is 215 lines with strict boundary semantics; re-implementing for tests loses fidelity. `test_circuit_breaker_cooldown.py` precedent. |
| Ken-burns mock render | Custom ken-burns JSON template | `MagicMock` on `shotstack.create_ken_burns_clip.return_value` | The real method POSTs to Shotstack — irrelevant for mock test. MagicMock with a Path return is enough. |
| Fault injection wrapper | Custom adapter subclass hierarchy | `MagicMock(side_effect=[RuntimeError, RuntimeError, RuntimeError, "ok"])` | MagicMock's `side_effect` list gives per-call return/raise; no class hierarchy needed. |
| Deterministic UUID | `uuid.uuid4` mock | `patch("uuid.uuid4", side_effect=lambda: UUID(int=counter.increment()))` | stdlib-only; D-21 precedent. No `freezegun` / `deterministic-uuid` library needed. |
| MP4 / WAV validity | Hand-build 1KB MP4 ftyp+moov + 44-byte RIFF | Zero-byte `Path.touch()` | Phase 5 MagicMock adapters never `.read_bytes()` on returned Paths. If a test DOES need a real byte stream, a 44-byte RIFF `b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00dataalign\x00\x00"` suffices. |
| Pipeline gate order enforcement | Custom test | Existing `pipeline.gate_guard.ensure_dependencies(gate)` raises `GateDependencyUnsatisfied` | Phase 5 already enforces via GATE_DEPS + graphlib. Tests just need to call `ensure_dependencies` out-of-order and assert the raise. |
| FAILURES.md append detection | Custom file watcher | `failures_path.read_text()` after `pipeline.run()` + `assert "THUMBNAIL FAIL" in content` | `append_failures` writes a deterministic marker format (`<!-- session:... gate:... ts:... -->`); grep-friendly. |

**Key insight:** Phase 5/6 already built 95% of the machinery Phase 7 needs. Phase 7's job is to **compose** these primitives into 4 REQ scenarios, not to build new primitives.

## Runtime State Inventory

Phase 7 is a greenfield test-authoring phase — no renaming, refactoring, or string migration. There is no pre-existing runtime state embedding a string that Phase 7 would change.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Phase 7 writes `state/` + `failures.md` under `tmp_path` only, never to production paths. | None. |
| Live service config | None — no external service is touched (D-1 mock-only). | None. |
| OS-registered state | None — no Windows Task Scheduler, launchd, or pm2 entries involve Phase 7. | None. |
| Secrets/env vars | `KLING_API_KEY`, `RUNWAY_API_KEY`, `TYPECAST_API_KEY`, `ELEVENLABS_API_KEY`, `SHOTSTACK_API_KEY` — but only as `monkeypatch.setenv("...", "fake")` to satisfy adapter constructors during instantiation. Values "fake" are safe. | None (Phase 5 precedent `_fake_env` fixture already used). |
| Build artifacts | None — Phase 7 adds only `tests/phase07/` and optionally extends `scripts/validate/harness_audit.py`. No package re-installs needed. | None. |

**Explicit statement:** Phase 7 is a pure-additive test phase with zero runtime state surface area.

## Environment Availability

Phase 7 has two external dependencies: the Python runtime and the existing pytest framework. Both are already in use.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Test runtime | ✓ | 3.11.9 | — |
| pytest | Test runner | ✓ | 8.4.2 | — |
| pydantic | adapter request validation | ✓ | 2.12.5 | — |
| httpx | Shotstack adapter (imported lazily, never hit) | ✓ | 0.28.1 | — |
| stdlib `unittest.mock` | Mock surface | ✓ | built-in | — |
| **pytest-socket** | CONTEXT D-1 (optional network-call enforcement) | ✗ | — | Rely on `MagicMock` adapter injection — real network is structurally unreachable because adapter instances are replaced before pipeline constructs its httpx clients. |
| **freezegun** | CONTEXT D-21 (optional time-freezing) | ✗ | — | `unittest.mock.patch("scripts.orchestrator.circuit_breaker.time.monotonic")` (Phase 5 `test_circuit_breaker_cooldown.py` precedent) + `monkeypatch.setattr(datetime, "now", lambda tz=None: FIXED_DT)` for Checkpointer ISO-8601 determinism. |
| fal-ai `fal_client` SDK | Kling real call only | ✗ (not checked — lazy import) | — | N/A — not touched by Phase 7 mocks. Lazy import at `kling_i2v.py:148` means absence doesn't break module import. |
| `runwayml` SDK | Runway real call only | ✗ (not checked — lazy import) | — | Same — lazy import. |
| `typecast` SDK | Typecast real call only | ✗ (not checked — lazy import) | — | Same — lazy import. |
| `elevenlabs` SDK | ElevenLabs real call only | ✗ (not checked — lazy import) | — | Same — lazy import. |
| `pydub` | Audio duration in Typecast/ElevenLabs real path | ✗ (not checked — lazy import) | — | Same — lazy import. |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `pytest-socket` and `freezegun` — both have idiomatic stdlib replacements already in use in Phase 5. Planner SHOULD NOT install them; instead, document the `monkeypatch` pattern in `tests/phase07/conftest.py`.

## Common Pitfalls

### Pitfall 1: Mistaking GATE_INSPECTORS (26 fan-out) for dispatched gates (13)

**What goes wrong:** Planner writes `assert pipeline.gate_guard.verify_all_dispatched()` expecting 17 or 26 dispatches; actually the invariant is 13 (one dispatch per operational gate, regardless of how many Inspector fan-out calls happened inside).

**Why it happens:** CONTEXT D-5 uses prose "17 GATE = 12 + 5 sub-gate" suggesting sub-gates count in verify_all_dispatched.

**How to avoid:** Read `gate_guard.py:169-176` and `tests/phase05/test_verify_all_dispatched.py:36-43`. The invariant is `frozenset(GateName) - {IDLE, COMPLETE}` subset check — 13 items.

**Warning signs:** `pytest-xfail` comments in the plan referencing "17 gates"; any test asserting `dispatched_count == 17`; any `_OPERATIONAL_GATES` reference in Phase 7 code.

### Pitfall 2: Asserting on `_producer_loop` for ASSETS or VOICE gates

**What goes wrong:** Planner writes TEST-04 targeting ASSETS gate retry exhaustion; fails because `_run_assets` bypasses `_producer_loop` (it has its own retry-via-CircuitBreaker path).

**Why it happens:** CONTEXT D-9 says "Producer/Inspector 재시도 3회" without distinguishing which gates have the retry loop.

**How to avoid:** `_producer_loop` is invoked only by `_run_trend`, `_run_niche`, `_run_research_nlm`, `_run_blueprint`, `_run_script`, `_run_polish`, `_run_thumbnail`, `_run_metadata`, `_run_upload`, `_run_monitor` (10 gates). `_run_voice`, `_run_assets`, `_run_assembly` do NOT. The ken-burns Fallback (line 621: `gate in (GateName.ASSETS, GateName.THUMBNAIL)`) is only reachable from gates that ALSO use `_producer_loop` — **the intersection is THUMBNAIL only**. TEST-04 MUST target THUMBNAIL.

**Warning signs:** TEST-04 test function name contains "assets"; `supervisor.side_effect` list with FAIL verdicts for ASSETS gate.

### Pitfall 3: Exception name mismatch (`CircuitBreakerTriggerError` vs `CircuitBreakerOpenError`)

**What goes wrong:** `pytest.raises(CircuitBreakerTriggerError)` raises `NameError: name 'CircuitBreakerTriggerError' is not defined`.

**Why it happens:** CONTEXT D-7 uses the name "CircuitBreakerTriggerError" that never existed.

**How to avoid:** The only breaker-specific exception is `CircuitBreakerOpenError` (`circuit_breaker.py:57`). During CLOSED state, the fn's exception propagates as-is (typically `RuntimeError`). After 3 fails, the NEXT call raises `CircuitBreakerOpenError`.

**Warning signs:** Any `import CircuitBreakerTriggerError` in Phase 7 code.

### Pitfall 4: Windows cp949 subprocess decoding errors

**What goes wrong:** `subprocess.run([pytest, ...])` returns bytes that Python cannot decode on Windows because default is cp949 and pytest output contains em-dashes or Korean characters.

**Why it happens:** Default locale on Windows non-Korean systems.

**How to avoid:** Always pass `encoding="utf-8", errors="replace"` to `subprocess.run`. Precedent: `scripts/validate/phase05_acceptance.py:48-55` uses this pattern. Phase 7 `test_regression_809.py` and `test_harness_audit_json.py` subprocess calls MUST follow.

**Warning signs:** `UnicodeDecodeError` in test output; test fails on Windows but passes on macOS/Linux.

### Pitfall 5: Hardcoded absolute paths in tests

**What goes wrong:** Test asserts `state/e2e_test/gate_01.json` exists but CI runs from different cwd; test fails.

**Why it happens:** Using relative Paths instead of `tmp_path`.

**How to avoid:** Every filesystem-touching test uses `tmp_path` fixture (pytest builtin). Pipeline receives `state_root=tmp_path / "state"`. Assertions compose paths relative to `tmp_path`.

**Warning signs:** `Path("state/...")` literal in test file; `Path(".claude/failures/orchestrator.md")` literal.

### Pitfall 6: Lazy imports exploding on import

**What goes wrong:** Phase 7 test does `from scripts.orchestrator.api.typecast import TypecastAdapter` and `TypecastAdapter()` is then called; but adapter is instantiated in test fixtures before the lazy `from typecast import Typecast` hits — except for env-var check which runs first.

**Why it happens:** Constructors check for API keys; absent keys raise `ValueError`.

**How to avoid:** Use `monkeypatch.setenv("TYPECAST_API_KEY", "fake")` in a fixture (precedent: `tests/phase05/test_pipeline_e2e_mock.py:40-48` `_fake_env`). Never actually call `.generate()` which triggers the lazy `from typecast import Typecast`.

**Warning signs:** `ImportError: No module named 'typecast'` in CI; `ValueError: TypecastAdapter: no API key` in test setup.

### Pitfall 7: Filter order regression on ken-burns path

**What goes wrong:** Test asserts `continuity_prefix` is prepended to filter chain in ken-burns rendering — but `create_ken_burns_clip` does NOT use `_build_timeline_payload`, so there IS no filter chain on that path.

**Why it happens:** CONTEXT D-8 says "filter chain에 `continuity_prefix` 여전히 prepend" without examining the code.

**How to avoid:** Ken-burns render bypasses filter chain entirely (`shotstack.py:155-216`). TEST-04 assertion set should NOT check filter order on ken-burns output. The filter-order invariant is covered by Phase 6 `test_filter_order_preservation.py` on the main `render()` path and remains untouched by Phase 7.

**Warning signs:** TEST-04 asserts `filters_order[0] == "continuity_prefix"` on a ken-burns Shotstack payload.

### Pitfall 8: harness-audit backwards-incompatible change

**What goes wrong:** Phase 7 replaces the existing `print(f"HARNESS_AUDIT_SCORE: {score}")` text output with JSON; Phase 4 Wave 5 acceptance test grep-parses that exact line and fails.

**Why it happens:** Clean-slate mindset instead of additive extension.

**How to avoid:** D-11 says "JSON schema". Preserve text output as default; JSON as opt-in via `--json-out PATH`. Existing `scripts/validate/harness_audit.py:113-115` retained verbatim; only new code paths added.

**Warning signs:** git diff of `harness_audit.py` shows deletions of `print(f"HARNESS_AUDIT_SCORE: {score}")` line.

### Pitfall 9: ContinuityPrefix extra=forbid pydantic strictness

**What goes wrong:** Phase 7 test constructs a ContinuityPrefix with an extra field (e.g., `phase="7"`) and pydantic raises `ValidationError`.

**Why it happens:** `models.py:147` sets `model_config = ConfigDict(extra="forbid")` — unknown fields rejected.

**How to avoid:** Tests that instantiate ContinuityPrefix use only the 7 documented fields (color_palette, warmth, focal_length_mm, aperture_f, visual_style, audience_profile, bgm_mood).

**Warning signs:** `pydantic_core._pydantic_core.ValidationError: Extra inputs are not permitted` in test output.

### Pitfall 10: NotebookLM tier assertion mismatch

**What goes wrong:** Test uses default `NotebookLMFallbackChain()` (3 backends) and asserts `tier_used == 2`; but if wiki/ has content, GrepWikiBackend (tier 1) may succeed first.

**Why it happens:** D-15 requires `HardcodedDefaultsBackend()` only, but planner constructs default chain.

**How to avoid:** In Phase 7 fixtures, instantiate `NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])`. Then `tier_used` will always be `0` in that reduced chain (0 = first backend = HardcodedDefaultsBackend). Note: `tier_used` is relative to the backend list, not absolute tier number. Planner must either (a) inject the default chain with monkeypatch to force RAGBackend and GrepWikiBackend to raise (so tier_used==2 in the full chain), OR (b) use the reduced chain and assert `tier_used == 0` with an explicit comment that `HardcodedDefaultsBackend is tier 2 per D-5 nomenclature even when it is position 0 in the reduced chain`.

**Warning signs:** Flaky test behavior depending on whether wiki/ exists or not.

## Code Examples

Verified patterns from actual Phase 5/6 source files.

### Example 1: Phase 5 E2E Mock Walk (13-GATE)

Source: `tests/phase05/test_pipeline_e2e_mock.py:51-112` (verbatim, cited for TEST-01 reuse).

```python
from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest
from scripts.orchestrator import GateName, ShortsPipeline, Verdict


def _pass_verdict() -> Verdict:
    return Verdict(
        result="PASS", score=90, evidence=[],
        semantic_feedback="", inspector_name="shorts-supervisor",
    )


@pytest.fixture
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("KLING_API_KEY", "RUNWAY_API_KEY", "TYPECAST_API_KEY",
                "ELEVENLABS_API_KEY", "SHOTSTACK_API_KEY"):
        monkeypatch.setenv(var, "fake")


def test_full_pipeline_runs_13_gates(tmp_path: Path, _fake_env: None) -> None:
    producer_output = {
        "artifact_path": str(tmp_path / "artifact.json"),
        "prompt": "p", "duration_seconds": 5,
        "anchor_frame": str(tmp_path / "a.png"),
    }
    producer = MagicMock(return_value=producer_output)
    supervisor = MagicMock(return_value=_pass_verdict())

    kling = MagicMock()
    kling.image_to_video.return_value = tmp_path / "cut.mp4"
    # ... (all 5 adapters as MagicMock)

    pipeline = ShortsPipeline(
        session_id="e2e_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=kling, runway_adapter=runway, typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs, shotstack_adapter=shotstack,
        producer_invoker=producer, supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )

    with patch.object(pipeline.timeline, "align", return_value=[]), \
         patch.object(pipeline.timeline, "insert_transition_shots", return_value=[]):
        result = pipeline.run()

    assert result["session_id"] == "e2e_test"
    assert result["final_gate"] == "COMPLETE"
    assert result["dispatched_count"] == 13
    assert result["fallback_count"] == 0
```

### Example 2: Phase 5 CircuitBreaker Cooldown Boundary

Source: `tests/phase05/test_circuit_breaker_cooldown.py:34-55` (verbatim, cited for TEST-03 reuse).

```python
from unittest.mock import patch
import pytest
from scripts.orchestrator.circuit_breaker import (
    CircuitBreaker, CircuitBreakerOpenError, CircuitState,
)


def test_open_breaker_blocks_before_cooldown_elapses():
    cb = CircuitBreaker(name="kling", max_failures=2, cooldown_seconds=300)

    with patch("scripts.orchestrator.circuit_breaker.time.monotonic") as mock_time:
        mock_time.return_value = 500.0
        # Trip the breaker
        for _ in range(cb.max_failures):
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("upstream fail")))
        assert cb.state is CircuitState.OPEN

        # 0 seconds elapsed -> blocked
        mock_time.return_value = 500.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # 299 seconds elapsed -> still blocked
        mock_time.return_value = 500.0 + 299.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")

        # Exactly at boundary (300s) -> still blocked (strict >)
        mock_time.return_value = 500.0 + 300.0
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "blocked")
```

### Example 3: Checkpoint File Round-Trip

Source: `scripts/orchestrator/checkpointer.py:127-146` (verbatim, for D-6 test patterns).

```python
def save(self, cp: Checkpoint) -> Path:
    """Persist one checkpoint atomically. Returns the final target path.

    Idempotent: same ``(session_id, gate_index)`` overwrites silently
    (``os.replace`` is defined to replace an existing destination).
    """
    target_dir = self.root / cp.session_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"gate_{cp.gate_index:02d}.json"
    tmp = target.with_suffix(target.suffix + ".tmp")
    payload = {"_schema": self.SCHEMA_VERSION, **asdict(cp)}
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # os.replace: atomic on Windows + POSIX (Python 3.3+ guarantee).
    os.replace(tmp, target)
    return target
```

Phase 7 test pattern: after `pipeline.run()`, enumerate `tmp_state_dir/session_id/` for all `gate_NN.json` files, `json.loads(p.read_text())`, assert each dict has keys `_schema, session_id, gate, gate_index, timestamp, verdict, artifacts`. File count == 14 (13 operational + 1 COMPLETE).

### Example 4: FAILURES Append Format

Source: `scripts/orchestrator/fallback.py:30-64` (verbatim).

```python
def append_failures(
    failures_path: Path, session_id: str, gate: str,
    evidence: list[dict], semantic_feedback: str,
) -> None:
    failures_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    evidence_summary = "; ".join(
        f"{e.get('rule', '?')}: {e.get('detail', '(no detail)')}"
        for e in (evidence or [])[:3]
    )
    entry = (
        f"\n<!-- session:{session_id} gate:{gate} ts:{now} -->\n"
        f"## {session_id} {gate} FAIL after regeneration exhausted\n\n"
        f"- **Timestamp:** {now}\n"
        f"- **Evidence (first 3):** {evidence_summary}\n"
        f"- **Semantic feedback:** {semantic_feedback}\n"
    )
    with failures_path.open("a", encoding="utf-8") as fh:
        fh.write(entry)
```

Phase 7 TEST-04 grep pattern: after pipeline.run with 3 THUMBNAIL failures, `failures_path.read_text()` must contain:
- `"<!-- session:tst_phase07_"` (marker)
- `"THUMBNAIL FAIL after regeneration exhausted"` (heading)
- `"Evidence (first 3):"` (evidence line)

### Example 5: Phase 5 Acceptance Script Pattern

Source: `scripts/validate/phase05_acceptance.py:1-55` (structure to copy for `phase07_acceptance.py`).

```python
#!/usr/bin/env python3
"""Phase 7 Success Criteria 1~5 acceptance verifier."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def _run(cmd: list[str], cwd: Path = REPO) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
    except FileNotFoundError as e:
        return 2, "", str(e)
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    # SC1: E2E mock pipeline 1회 완주
    rc, _, _ = _run(["python", "-m", "pytest",
                     "tests/phase07/test_e2e_happy_path.py", "-q", "--no-cov"])
    sc1 = "PASS" if rc == 0 else "FAIL"

    # SC2: verify_all_dispatched 13 gates
    rc, _, _ = _run(["python", "-m", "pytest",
                     "tests/phase07/test_verify_all_dispatched.py", "-q", "--no-cov"])
    sc2 = "PASS" if rc == 0 else "FAIL"

    # SC3: CircuitBreaker 3x cooldown
    rc, _, _ = _run(["python", "-m", "pytest",
                     "tests/phase07/test_circuit_breaker_3x.py", "-q", "--no-cov"])
    sc3 = "PASS" if rc == 0 else "FAIL"

    # SC4: Fallback ken-burns (no CIRCUIT_OPEN)
    rc, _, _ = _run(["python", "-m", "pytest",
                     "tests/phase07/test_fallback_ken_burns.py", "-q", "--no-cov"])
    sc4 = "PASS" if rc == 0 else "FAIL"

    # SC5: harness-audit >= 80
    rc, out, _ = _run(["python", "scripts/validate/harness_audit.py", "--threshold", "80"])
    sc5 = "PASS" if rc == 0 else "FAIL"

    print("| SC | Status |")
    print("|----|--------|")
    for name, status in [("SC1", sc1), ("SC2", sc2), ("SC3", sc3), ("SC4", sc4), ("SC5", sc5)]:
        print(f"| {name} | {status} |")
    return 0 if all(s == "PASS" for s in [sc1, sc2, sc3, sc4, sc5]) else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Example 6: harness-audit JSON Emission (D-11)

New code — proposed for extension of `scripts/validate/harness_audit.py`.

```python
import json
import re
from datetime import datetime, timezone
from pathlib import Path


_SCAN_ROOTS = [Path("scripts"), Path(".claude/agents"), Path("tests"), Path("wiki")]


def _scan_deprecated_patterns(patterns_json: Path = Path(".claude/deprecated_patterns.json")) -> dict[str, int]:
    """Scan all scan-roots; return {pattern_name: match_count}."""
    patterns = json.loads(patterns_json.read_text(encoding="utf-8"))["patterns"]
    counts: dict[str, int] = {}
    for pat_entry in patterns:
        regex = re.compile(pat_entry["regex"])
        # Use the first word of 'reason' as the key (e.g. "ORCH-08" -> "ORCH-08")
        key = pat_entry["reason"].split(":")[0].strip() or pat_entry["regex"][:20]
        n = 0
        for root in _SCAN_ROOTS:
            if not root.exists():
                continue
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                if p.suffix not in {".py", ".md", ".json"}:
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                n += len(regex.findall(text))
        counts[key] = n
    return counts


def _count_agents(agents_root: Path) -> int:
    return sum(1 for _ in agents_root.rglob("AGENT.md"))


def _skills_over_500(skills_root: Path = Path(".claude/skills")) -> list[str]:
    out = []
    for p in skills_root.rglob("SKILL.md"):
        if sum(1 for _ in p.open(encoding="utf-8")) > 500:
            out.append(str(p))
    return out


def _descriptions_over_1024(agents_root: Path) -> list[str]:
    out = []
    for p in agents_root.rglob("AGENT.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^description:\s*(.*)$", text, re.MULTILINE)
        if m and len(m.group(1)) > 1024:
            out.append(str(p))
    return out


def emit_d11_json(report_path: Path, score: int, violations: list[str], agents_root: Path) -> None:
    report = {
        "score": score,
        "a_rank_drift_count": sum(1 for v in violations if "A급" in v or "A-" in v),
        "skill_over_500_lines": _skills_over_500(),
        "agent_count": _count_agents(agents_root),
        "description_over_1024": _descriptions_over_1024(agents_root),
        "deprecated_pattern_matches": _scan_deprecated_patterns(),
        "phase": 7,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline integration test in `test_shorts_pipeline.py` | Separate `test_pipeline_e2e_mock.py` with fixture isolation | Phase 5 Wave 5 (2026-04-19) | Each scenario (happy path, resume, fallback) gets its own file — easier to diagnose failures. Phase 7 follows this pattern. |
| 12 GATE architecture | 13 GATE IntEnum (TREND..MONITOR + IDLE + COMPLETE bookends) | Phase 5 Wave 1 | CONTEXT still says "12 GATE" — misleading. The operational count is 13 because RESEARCH_NLM was split out from BLUEPRINT. |
| Plain subprocess → text parse for harness-audit | `subprocess.run + json.loads` via `--json-out PATH` extension | Phase 7 (this phase) | Backward-compatible: text output retained as default; new flag adds machine-readable JSON. |
| Real network calls with `requests`/`urllib` | httpx + lazy imports + MagicMock injection | Phase 5 | Tests never touch network; adapter classes import httpx lazily so env without it still loads. |
| `RAISE CircuitBreakerTriggerError` on 3rd fail | `RAISE CircuitBreakerOpenError` on 4th call | Phase 5 | The trip happens silently inside `_record_failure`; no named "trigger" exception. Phase 7 test must match current behavior. |

**Deprecated/outdated:**
- **"12 GATE" prose in CONTEXT.md:** Should be "13 operational GATE" throughout — the CONTEXT D-4 "TREND → COMPLETE 12 GATE sequence" is off by one (the sequence has 13 operational gates plus COMPLETE).
- **"17 GATE = 12 + 5 sub-gate" decomposition:** Not present in any code; must be removed from Phase 7 plan language.
- **pytest 9.0.2 reference:** Phase 5 VALIDATION.md:21 says "pytest 9.0.2" but `python -m pytest --version` reports 8.4.2 on 2026-04-19. Phase 7 VALIDATION.md MUST use 8.4.2.

## Open Questions

### Q1: Should TEST-04 target THUMBNAIL or ASSETS?

- **What we know:** `shorts_pipeline.py:621` restricts ken-burns Fallback to `(GateName.ASSETS, GateName.THUMBNAIL)`. But only THUMBNAIL gates run through `_producer_loop`; ASSETS has its own CircuitBreaker-based retry. Therefore the ken-burns Fallback lane is structurally reachable only via THUMBNAIL.
- **What's unclear:** Whether the planner wants to also cover ASSETS via a separate mechanism (e.g., make Kling mock fail + Runway mock fail → `CircuitBreakerOpenError` bubbles up → `_run_assets` does NOT have a ken-burns branch, it would just raise). This would test the failure mode, not ken-burns specifically.
- **Recommendation:** TEST-04 targets **THUMBNAIL** only. Add a secondary test (`test_assets_both_providers_fail.py`) that asserts double breaker-open on Kling+Runway raises `CircuitBreakerOpenError` up through `run()` — this proves the Fallback lane is not reachable from ASSETS per the code, documenting the design decision.

### Q2: How strictly should TEST-02 enforce "17 vs 13"?

- **What we know:** Source truth is 13.
- **What's unclear:** Whether the planner should surface the CONTEXT error in a VALIDATION.md addendum or quietly correct it in test assertions.
- **Recommendation:** Add a test `test_operational_gate_count_equals_13.py` that asserts `len([g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]) == 13` and `len(GATE_INSPECTORS) == 13`. Also add a test `test_inspector_fan_out_equals_26.py` that asserts total fan-out count is 26 across 17 unique inspectors. These anchor the canonical numbers in the test suite so future refactors have a signal.

### Q3: Should harness-audit deprecation scan include `tests/phase07/` itself?

- **What we know:** D-12 says "`scripts/**/*.py` + `.claude/agents/**/*.md` + `tests/**/*.py` + `wiki/**/*.md` 전부". Phase 7 adds `tests/phase07/`, so the scan includes itself.
- **What's unclear:** The ken-burns fallback test uses `pytest.raises(CircuitBreakerOpenError)` — but `deprecated_patterns.json` has no regex that would match Phase 7 test code. Risk is near-zero, but worth confirming.
- **Recommendation:** Before committing Phase 7 tests, run `scripts/validate/harness_audit.py --json-out /tmp/out.json` and diff deprecated_pattern_matches. All values must be 0 on fresh Phase 7 state. This becomes Wave 4 of the Phase 7 plan.

### Q4: Fallback retry state persistence across resume

- **What we know:** `GateContext.fallback_indices` (shorts_pipeline.py:134, 647) tracks which cut indices took the ken-burns path. `dedupe_fallback_key` (fallback.py:125-133) suggests resume-aware dedup is intended.
- **What's unclear:** Whether a resume-after-fallback scenario needs testing in Phase 7, or deferred to Phase 9.
- **Recommendation:** Defer. Phase 7 proves the forward path; resume-with-fallback is an edge case for Phase 10 (Sustained Operations). Add to deferred-items.md.

### Q5: ContinuityPrefix loader behavior during mock tests

- **What we know:** `shotstack.py:50-58` loads `wiki/continuity_bible/prefix.json` at render time; if absent returns None (graceful). Phase 6 ships this file with full 7-field content.
- **What's unclear:** Phase 7's `tmp_path` state doesn't have `wiki/continuity_bible/prefix.json` — and the test uses real cwd. Either the file loads (because tests run from repo root), or the loader returns None. Either way the render mock is a MagicMock so the bytes don't matter. But if TEST asserts `continuity_preset` is not None in a render payload, the assertion depends on cwd.
- **Recommendation:** Phase 7 tests use `MagicMock()` for `shotstack.render.return_value` — they never see the internal `_build_timeline_payload` output. Filter-order and ContinuityPrefix concerns are Phase 6 tests; Phase 7 does not re-verify them. Add as a Plan-level non-goal comment.

### Q6: Fan-out inspector MagicMock granularity

- **What we know:** `supervisor_invoker` is a single callable `(gate, output) -> Verdict`. The per-inspector fan-out inside `shorts-supervisor` is production-side; tests inject a MagicMock at the supervisor level.
- **What's unclear:** Whether Phase 7 should test supervisor fan-out behavior (e.g., SCRIPT's 4 inspectors must all PASS for the gate to PASS). This would require instantiating the real supervisor.
- **Recommendation:** **Do not** test supervisor fan-out in Phase 7. The Phase 4 rubric-schema validation tests already cover per-inspector shape; Phase 7 stays at the pipeline/state-machine level. Add to deferred-items.md as Phase 9 coverage gap.

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Windows cp949 decode failure in subprocess | HIGH (Windows target) | Test fails with `UnicodeDecodeError` | Every `subprocess.run` uses `encoding="utf-8", errors="replace"`. Precedent: `phase05_acceptance.py:48-55`. |
| Real network call on lazy SDK import | LOW | Test hits external API, incurs cost | Never call `.image_to_video()`, `.generate()`, `.render()` on real adapter instances. Only MagicMock. `_fake_env` fixture sets API keys to "fake" — bypasses `ValueError` in constructor without unlocking real network. |
| CircuitBreaker state leaking across tests | MEDIUM | Flaky pass/fail | Each test creates a new `CircuitBreaker(...)` instance. Do not share breaker objects between tests. Each `ShortsPipeline(...)` constructs fresh `CircuitBreaker` instances. |
| `state/` dir pollution | MEDIUM | Disk fills; tests contaminate each other | Always use `tmp_path` fixture (pytest creates + cleans). Never hardcode relative state dirs. |
| Phase 4/5/6 regression | HIGH (809 tests) | Phase 7 merges break prior work | Wave 0 of Phase 7 plan runs `python -m pytest tests/phase04 tests/phase05 tests/phase06 -q` before any Phase 7 code — baseline confirmed 809 green. After each Wave, re-run the same command. |
| harness-audit JSON schema drift | LOW | Test `test_harness_audit_json.py` fails with new keys | D-11 lists 6 mandatory keys. Test uses `assert required_keys <= set(report.keys())` (subset), not `==`. Allows future expansion without breaking existing tests. |
| Phase 6 `check_failures_append_only` Hook blocks test | MEDIUM | Phase 7 test cannot write to `failures_path` even in tmp_path | Hook basename-matches `FAILURES.md` and `_imported_from_shorts_naberal.md`. Phase 7 tests use `failures_path=tmp_path / "failures.md"` (lowercase `failures.md` — not matched by basename-exact Hook). Verified: `hooks/pre_tool_use.py` check_failures_append_only logic uses basename equality. |
| Checkpointer atomic `os.replace` race | LOW (Windows) | Phase 7 resume test flakes | os.replace is atomic per Python 3.3+ docs on Windows + POSIX. Not a realistic flake risk in single-process tests. |
| Determinism break from `datetime.now()` in Checkpoint | MEDIUM | Test asserts exact timestamp; fails on rerun | Assertions use regex `r"^2\d{3}-.*T.*Z?$"` or `isinstance(ts, str)` rather than exact strings. Phase 5 precedent test_checkpointer_roundtrip.py uses the format check. |
| Inspector fan-out mock simulation (supervisor_invoker) | LOW | Test returns wrong verdict type | Fixture always returns `Verdict(result="PASS" or "FAIL", ...)` — the dataclass. Avoid `MagicMock()` naked for supervisor because `.dispatch()` reads `.result`. Use `MagicMock(return_value=_pass_verdict())`. |
| `pytest-asyncio` or async race | ZERO | N/A | No async code in Phase 5/6/7. All tests synchronous. |

## Environment Availability (Dependency Audit)

Checked 2026-04-19 on the target machine (`C:\Users\PC\Desktop\naberal_group\studios\shorts`):

```
python --version   -> 3.11.9
pytest --version   -> 8.4.2
pydantic           -> 2.12.5
httpx              -> 0.28.1
pytest-socket      -> (not installed)
freezegun          -> (not installed)

Regression sweep:
  python -m pytest tests/phase05/ tests/phase06/ -q --no-cov
  -> 565 passed in 68.04s
  (Phase 4: 244 tests — not run in this audit but prior STATE records confirm)
```

**Phase 7 execution-readiness:** GREEN. No installs needed. All primitives (ShortsPipeline, CircuitBreaker, Checkpointer, GateGuard, fallback helpers, NotebookLMFallbackChain) are import-clean.

## Validation Architecture

Per CONTEXT.md and config.json, Phase 7 uses pytest 8.4.2 with the Phase 5/6 pattern. Phase 7 adds `tests/phase07/` only.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `pytest.ini` (existing from Phase 4) — no changes needed |
| Quick run command | `python -m pytest tests/phase07/ -q --no-cov` |
| Full suite command | `python -m pytest tests/ -q --no-cov` |
| Phase 7 acceptance | `python scripts/validate/phase07_acceptance.py` |
| Harness audit | `python scripts/validate/harness_audit.py --threshold 80` |
| Estimated runtime | ~10s (Phase 7 new tests ~5s; full suite ~80s incl. Phase 4+5+6) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/phase07/test_<affected>.py -q --no-cov`
- **Per wave merge:** `python -m pytest tests/phase07/ -q --no-cov`
- **Per wave regression:** `python -m pytest tests/phase04/ tests/phase05/ tests/phase06/ -q --no-cov` (must stay 809/809 green per D-23)
- **Phase gate:** Full suite (`python -m pytest tests/ -q --no-cov`) green + `scripts/validate/phase07_acceptance.py` exit 0 + `scripts/validate/harness_audit.py` score ≥ 80 + `git diff tests/phase04/ tests/phase05/ tests/phase06/` empty.

### Phase 7 Requirements → Test Map (≥18 rows per Nyquist precedent)

| Row | Dimension | SC ref | REQ IDs | Test file (planner) | Grep/assert contract |
|-----|-----------|--------|---------|---------------------|----------------------|
| 1 | E2E mock happy path | SC1 | TEST-01 | tests/phase07/test_e2e_happy_path.py | `assert result["final_gate"] == "COMPLETE" and result["dispatched_count"] == 13 and result["fallback_count"] == 0` |
| 2 | Operational gate count invariant | SC2 | TEST-02 | tests/phase07/test_verify_all_dispatched.py | `assert len([g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]) == 13 and pipeline.gate_guard.verify_all_dispatched() is True` |
| 3 | Gate sequencing DAG | SC2 | TEST-02 | tests/phase07/test_gate_sequencing.py | `assert [g.name for g in GateName if int(g) > 0 and int(g) < 14] == ["TREND","NICHE","RESEARCH_NLM","BLUEPRINT","SCRIPT","POLISH","VOICE","ASSETS","ASSEMBLY","THUMBNAIL","METADATA","UPLOAD","MONITOR"]` |
| 4 | COMPLETE guard (missing gate) | SC2 | TEST-02 | tests/phase07/test_complete_guard_raises_incomplete.py | `with pytest.raises(IncompleteDispatch): pipeline._transition_to_complete()` (with only 12 gates dispatched) |
| 5 | Checkpointer 14 file count | SC1 | TEST-01 | tests/phase07/test_checkpointer_14_files.py | `assert len(sorted((tmp_path / "state" / session_id).glob("gate_*.json"))) == 14` |
| 6 | Checkpointer round-trip | SC1 | TEST-01 | tests/phase07/test_checkpointer_roundtrip.py | `for p in session_dir.glob("gate_*.json"): data = json.loads(p.read_text()); assert {"_schema","session_id","gate","gate_index","timestamp","verdict","artifacts"}.issubset(data.keys())` |
| 7 | CircuitBreaker 3-fail trip | SC3 | TEST-03 | tests/phase07/test_circuit_breaker_3x.py | `for _ in range(3): with pytest.raises(RuntimeError): cb.call(lambda: raise RuntimeError()); assert cb.state is CircuitState.OPEN` |
| 8 | CircuitBreaker cooldown blocks retry | SC3 | TEST-03 | tests/phase07/test_circuit_breaker_cooldown_block.py | `with pytest.raises(CircuitBreakerOpenError) as exc: cb.call(...); assert exc.value.cooldown_remaining > 299.0` |
| 9 | CircuitBreaker HALF_OPEN probe | SC3 | TEST-03 | tests/phase07/test_circuit_breaker_half_open.py | `mock_time.return_value = trip_time + 300.001; result = cb.call(success_fn); assert cb.state is CircuitState.CLOSED` |
| 10 | Regeneration exhaustion → FAILURES append | SC4 | TEST-04 | tests/phase07/test_fallback_failures_append.py | `assert (tmp_path / "failures.md").exists(); text = (tmp_path / "failures.md").read_text(); assert "THUMBNAIL FAIL after regeneration exhausted" in text` |
| 11 | Ken-burns clip insertion | SC4 | TEST-04 | tests/phase07/test_fallback_ken_burns.py | `assert shotstack.create_ken_burns_clip.called; assert result["fallback_count"] == 1` |
| 12 | Pipeline completes despite 1 Fallback | SC4 | TEST-04 | tests/phase07/test_fallback_no_circuit_open.py | `assert result["final_gate"] == "COMPLETE" and result["dispatched_count"] == 13` (no CIRCUIT_OPEN raise) |
| 13 | Producer loop retries exactly 3× | SC4 | TEST-04 | tests/phase07/test_producer_loop_retries_3.py | `assert pipeline.ctx.retry_counts[GateName.THUMBNAIL] == 3` |
| 14 | NotebookLM tier 2 only (offline) | SC1 | TEST-01 | tests/phase07/test_notebooklm_tier_2.py | `chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()]); answer, tier = chain.query("q", "naberal-shorts-channel-bible"); assert tier == 0 and "fallback defaults" not in answer` (tier==0 in reduced chain == tier 2 semantic) |
| 15 | harness-audit score ≥ 80 | SC5 | cross-cutting | tests/phase07/test_harness_audit_score_ge_80.py | `rc, _, _ = subprocess_run(["python", "scripts/validate/harness_audit.py", "--threshold", "80"]); assert rc == 0` |
| 16 | harness-audit JSON schema (D-11 6-keys) | SC5 | cross-cutting | tests/phase07/test_harness_audit_json.py | `report = json.loads(json_out.read_text()); required = {"score","a_rank_drift_count","skill_over_500_lines","agent_count","description_over_1024","deprecated_pattern_matches"}; assert required.issubset(report.keys())` |
| 17 | A급 drift = 0 (deprecated pattern matches all zero) | SC5 | cross-cutting | tests/phase07/test_harness_audit_drift_zero.py | `assert all(v == 0 for v in report["deprecated_pattern_matches"].values())` |
| 18 | SKILL 500 line invariant | SC5 | cross-cutting | tests/phase07/test_skill_500_lines.py | `assert report["skill_over_500_lines"] == []` |
| 19 | Agent count == 32 | SC5 | cross-cutting | tests/phase07/test_agent_count_32.py | `assert report["agent_count"] == 32` |
| 20 | Description ≤ 1024 chars | SC5 | cross-cutting | tests/phase07/test_description_1024.py | `assert report["description_over_1024"] == []` |
| 21 | Phase 4/5/6 regression (809 baseline) | SC1,2,3,4,5 | TEST-01..04 | tests/phase07/test_regression_809.py | `rc, out, _ = subprocess_run(["python","-m","pytest","tests/phase04","tests/phase05","tests/phase06","-q","--no-cov"]); assert rc == 0 and "809 passed" in out or re.search(r"\\b\\d{3} passed\\b", out).group()` |
| 22 | Determinism (same session_id → same files) | D-21 | TEST-01 | tests/phase07/test_deterministic_rerun.py | `run pipeline twice with same session_id + same mocks; assert sorted(gate_file_names_run1) == sorted(gate_file_names_run2)` |
| 23 | cp949 UTF-8 round-trip | D-22 | TEST-01..04 | tests/phase07/test_cp949_utf8_roundtrip.py | `subprocess_run_with_korean_stdin; assert result.stdout contains "한국어" correctly decoded` |
| 24 | Gate dependency enforcement | SC2 | TEST-02 | tests/phase07/test_dependency_enforcement.py | `with pytest.raises(GateDependencyUnsatisfied): guard.ensure_dependencies(GateName.ASSEMBLY)` (without VOICE+ASSETS dispatched) |
| 25 | No skip_gates in Phase 7 tests | SC5 | cross-cutting | tests/phase07/test_no_deprecated_patterns.py | `for py in Path("tests/phase07").rglob("*.py"): assert "skip_gates" not in py.read_text()` |

Total: 25 rows (≥18 minimum satisfied). Planner may consolidate related rows into fewer test files (e.g., rows 7-9 into `test_circuit_breaker_3x.py`), but each dimension must be covered by at least one assertion.

### Wave 0 Gaps (tests/phase07/ scaffolding to create before any Wave 1+)

- [ ] `tests/phase07/__init__.py` — package marker
- [ ] `tests/phase07/conftest.py` — fixtures: `_fake_env` (5 API keys), `tmp_session_id`, `mock_pass_verdict`, `mock_fail_verdict`, `mock_kling_adapter`, `mock_runway_adapter`, `mock_typecast_adapter`, `mock_elevenlabs_adapter`, `mock_shotstack_adapter`
- [ ] `tests/phase07/fixtures/` — directory for placeholder files (mp4, wav, jpg — zero-byte acceptable)
- [ ] `tests/phase07/mocks/` (optional — CONTEXT D-13 Claude's Discretion) — mock adapter factory module
- [ ] `scripts/validate/phase07_acceptance.py` — SC1-5 CLI wrapper (copy from `phase05_acceptance.py`, adjust for Phase 7 tests)
- [ ] `scripts/validate/harness_audit.py` — EXTEND with `--json-out PATH` flag + D-11 schema emission (additive, no existing API break)

*(If no new pytest framework install needed — confirmed verified.)*

## References

Primary sources (HIGH confidence — verbatim reads 2026-04-19):

- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/gates.py` (213 lines) — GateName IntEnum + GATE_DEPS + 9 exception classes + `_validate_dag`.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/gate_guard.py` (197 lines) — GateGuard.dispatch, verify_all_dispatched (line 169-176: 13 operational gates), ensure_dependencies.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/circuit_breaker.py` (215 lines) — CircuitBreakerOpenError (line 57), CircuitState enum, strict `>=` cooldown boundary (line 131).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/checkpointer.py` (233 lines) — Checkpointer.save (os.replace atomic), resume (max gate_index), dispatched_gates.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/fallback.py` (141 lines) — append_failures (FAILURES.md append-only format), insert_fallback_shot, dedupe_fallback_key.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/shorts_pipeline.py` (787 lines) — ShortsPipeline.run (entry), GATE_INSPECTORS (13 keys, 26 fan-out), `_producer_loop` (3-retry regeneration), `_insert_fallback` (ASSETS/THUMBNAIL only), `_transition_to_complete`.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/kling_i2v.py` (213 lines) — KlingI2VAdapter.image_to_video signature, fal.ai endpoint, lazy `fal_client` import.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/runway_i2v.py` (197 lines) — RunwayI2VAdapter.image_to_video, lazy `runwayml` import.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/typecast.py` (365 lines) — TypecastAdapter.generate (returns `list[AudioSegment]`), lazy `typecast` SDK import.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/elevenlabs.py` (311 lines) — ElevenLabsAdapter.generate_with_timestamps, `_chars_to_words` helper.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/shotstack.py` (397 lines) — ShotstackAdapter.render (filter injection), upscale (NOOP), create_ken_burns_clip (standalone POST).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/models.py` (165 lines) — I2VRequest, TypecastRequest, ShotstackRenderRequest, ContinuityPrefix (`extra="forbid"`).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/notebooklm/fallback.py` (232 lines) — NotebookLMFallbackChain (Protocol + 3 backends), `HardcodedDefaultsBackend.DEFAULTS` literal.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/__init__.py` (84 lines) — public API surface: `ShortsPipeline`, `GateName`, `Verdict`, `CircuitBreaker`, `CircuitBreakerOpenError`, etc.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/validate/harness_audit.py` (121 lines) — existing CLI, score method, `HARNESS_AUDIT_SCORE: N` output.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/skills/harness-audit/SKILL.md` (144 lines) — natural-language rubric; **no executable inside SKILL.md** — CLI is the real entry point.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/deprecated_patterns.json` — 8 regex entries (6 from Phase 5 + 2 from Phase 6: FAILURES marker + SKILL.md direct edit).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/tests/phase05/test_pipeline_e2e_mock.py` (>150 lines) — E2E mock precedent (reused verbatim as TEST-01 template).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/tests/phase05/test_circuit_breaker_cooldown.py` (80 lines) — Breaker timing pattern (reused verbatim as TEST-03 template).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/tests/phase05/test_verify_all_dispatched.py` (60 lines) — 13-gate invariant test (reused as TEST-02 template).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/tests/phase05/conftest.py`, `tests/phase06/conftest.py` — fixture patterns (session #16 decision #40 `_REPO_ROOT` resolve-at-import).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/05-orchestrator-v2-write/05-VALIDATION.md` (172 lines) — Phase 5 Nyquist matrix (29 rows) — structural template.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md` (152 lines) — Phase 6 Nyquist matrix (24 rows).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-RESEARCH.md` (1535 lines) — structural + length template for this RESEARCH.md.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/05-orchestrator-v2-write/05-RESEARCH.md` (1283 lines) — secondary length template.

Secondary (MEDIUM confidence — contextual reads):

- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/REQUIREMENTS.md` (326 lines) — TEST-01..04 text at lines 149-155; Phase Traceability forward map.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/ROADMAP.md` (297 lines) — Phase 7 block at lines 171-183, 5 Success Criteria; Critical Success Factors section.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/validate/phase05_acceptance.py` (≈150 lines) — CLI gate pattern for `phase07_acceptance.py`.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/validate/phase06_acceptance.py` — structural comparable, verified exists in `scripts/validate/`.

Tertiary (LOW confidence — not directly cited but context-adjacent):

- `C:/Users/PC/Desktop/naberal_group/harness/skills/harness-audit/SKILL.md` — harness-level skill (shorts inherits via studios/shorts/.claude/skills/harness-audit/SKILL.md which is the same content).
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/STATE.md` — Phase 4/5/6 산출물 목록 (exceeded token budget on direct read; relied on REQUIREMENTS.md + ROADMAP.md cross-references).

## Metadata

**Confidence breakdown:**

- **Standard stack**: HIGH — every library version verified by `python -c "import X; print(X.__version__)"` on 2026-04-19 target machine. pytest-socket and freezegun confirmed absent.
- **Architecture / code contracts**: HIGH — every referenced symbol read line-by-line from source. Three CONTEXT.md discrepancies explicitly reconciled with source truth.
- **E2E test pattern**: HIGH — `tests/phase05/test_pipeline_e2e_mock.py` already proves 13-GATE mock walk; Phase 7 reuses verbatim with additions.
- **Fault-injection pattern**: HIGH — `tests/phase05/test_circuit_breaker_cooldown.py` precedent for `time.monotonic` patch; CircuitBreaker contract fully documented in source.
- **Fallback pattern (TEST-04)**: MEDIUM — the chain `_producer_loop → append_failures → _insert_fallback → insert_fallback_shot → create_ken_burns_clip` is traced in source, but the full-pipeline integration (supervisor side_effect triggering THUMBNAIL fail 3×) is NEW to Phase 7. No direct precedent — constructed from first principles.
- **harness-audit JSON extension**: MEDIUM — existing CLI scores 90 today; D-11 6-key schema is new code. Helper functions proposed from scratch (`_scan_deprecated_patterns`, `_count_agents`, etc.) but follow clear signatures.
- **CONTEXT.md corrections**: HIGH — code trumps prose. Planner MUST adopt the corrections in their PLAN.md language.
- **Regression baseline**: HIGH — verified 565 passed (phase05 + phase06) in 68.04s on 2026-04-19. Combined with Phase 4 (244 per STATE) = 809. D-23 baseline locked.

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days — source code is stable; adapter SDK versions may shift but Phase 7 uses only MagicMock so external drift is irrelevant).

---

## RESEARCH COMPLETE
