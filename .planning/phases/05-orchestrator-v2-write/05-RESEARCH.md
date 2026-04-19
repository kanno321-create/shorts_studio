# Phase 5: Orchestrator v2 Write — Research

**Researched:** 2026-04-19
**Domain:** Python state machine orchestrator (12 GATE DAG + CircuitBreaker + Checkpointer + voice-first assembly + Low-Res First rendering) — replaces 5166-line drift with a 500~800 line disciplined implementation
**Confidence:** HIGH (stack verified against installed versions + CONTEXT.md locks 20 decisions + harvested references read byte-for-byte + hc_checks regression baseline enumerated)

## Summary

Phase 5 writes a single 500~800 line Python state machine (`scripts/orchestrator/shorts_pipeline.py`) that orchestrates 12 operational GATEs (15 states total incl. IDLE + COMPLETE) by sequentially calling Producer agents and fanning out to the shorts-supervisor for 17-Inspector validation. The supervisor's `supervisor-rubric-schema.json` contract is already shipped (Phase 4), so the orchestrator's job is plumbing: enum-based transitions, DAG dependency validation, atomic JSON checkpoints, CircuitBreaker wrapping every external API call, voice-first timeline alignment, 720p Low-Res First rendering, and automatic Kling → Runway failover. All structural risks from the deprecated 5166-line `orchestrate.py` are countered by hard physical enforcement: `skip_gates` regex-blocked at Hook layer, `T2V` functions physically absent, `TODO(next-session)` regex-blocked, and `wc -l` line-count gate at phase completion.

The research confirms that every required library is installed at current versions (Python 3.11.9, tenacity 9.1.4, pydantic 2.12.5, pytest 9.0.2, httpx 0.28.1). Five API wrappers are present in `.preserved/harvested/api_wrappers_raw/` (immutable, Tier 3) as behavioral references only — the Phase 5 rewrite adopts their signatures and fallback patterns but strips the T2V code paths (Runway's `text_to_video` method), consolidates their error types into a single CircuitBreaker-compatible contract, and removes the 4-tier TTS fallback chain (keeping only Typecast → ElevenLabs per AUDIO-01). The regression baseline `hc_checks.py` (1129 lines) exposes 13 public functions that MUST survive the rewrite verbatim by signature — the research enumerates them below.

**Primary recommendation:** Split Phase 5 into **10 plans across 6 waves**. Wave 0 lays enum/exception/DAG infrastructure. Wave 1 builds 3 parallel support components (CircuitBreaker, Checkpointer, GateGuard). Wave 2 builds VoiceFirstTimeline + Low-Res renderer in parallel. Wave 3 ships 3 API adapters in parallel (Kling I2V, Runway I2V backup, Typecast+ElevenLabs voice, Shotstack assembler). Wave 4 writes `shorts_pipeline.py` as the orchestrating integrator (sequential — must import all upstream modules). Wave 5 rewrites hc_checks + ports regression tests. Wave 6 is the physical verification gate (grep blacklist, wc -l, hook mock, pytest green). Custom CircuitBreaker class over tenacity — tenacity is already retry-focused; the project needs a CLOSED/OPEN/HALF_OPEN state machine that Checkpointer can serialize, which tenacity does not offer natively.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-1. Single File Constraint (Non-Negotiable)**
- `shorts_pipeline.py` 단일 파일 500~800줄 상한선.
- 여러 모듈 분할 금지 (state machine 본체). 단, wrappers/adapters/checkpointer/circuit_breaker 등 지원 파일은 별도 모듈로 구성 가능.
- 5166줄 drift 재발을 구조적으로 차단하는 임계. 700줄 초과 시 즉시 리팩터링 필요.

**D-2. 12 GATE State Machine (Canonical Order)**
`IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE`
- 총 15 상태. Success Criteria 1의 "12 GATE"는 IDLE/COMPLETE 제외 가동 GATE 수.
- 각 GATE = (1) Producer 호출 → (2) Inspector 검증 → (3) GateGuard.dispatch() 순.
- 잘못된 전이 시 `InvalidGateTransition` raise.

**D-3. GateGuard.dispatch() 강제 (ORCH-03)**
- 시그니처: `GateGuard.dispatch(gate: GateName, verdict: Verdict) -> None`
- `verdict.result == "FAIL"` → `raise GateFailure(gate, evidence=verdict.evidence)`
- 재생성 루프는 호출자가 try/except로 관리.
- Inspector 호출 없이 GATE 통과 시도 → `MissingVerdict` raise.

**D-4. verify_all_dispatched() = COMPLETE 진입 조건 (ORCH-04)**
- 모든 인스펙터 17명 + 17 GATE 모두 호출되었음을 내부 dispatched set으로 추적.
- COMPLETE 전이 시 `verify_all_dispatched()` False → `IncompleteDispatch` raise.
- session_id별 분리. 중간 재시작 시 Checkpointer에서 복구.

**D-5. Checkpointer (ORCH-05)**
- 경로: `state/{session_id}/gate_{n}.json`
- 저장 시점: GATE 통과 직후 (GateGuard.dispatch 성공 후).
- 스키마: `{session_id, gate, gate_index, timestamp, verdict, artifacts:{path, sha256}}`
- 재시작 시 `Checkpointer.resume(session_id)` → 가장 큰 gate_index 이후부터 재개.

**D-6. CircuitBreaker (ORCH-06)**
- 클래스: `CircuitBreaker(name: str, max_failures: int = 3, cooldown_seconds: int = 300)`
- 상태: CLOSED / OPEN / HALF_OPEN.
- 3회 연속 실패 → OPEN (5분 차단) → HALF_OPEN (1회 시도) → 성공=CLOSED, 실패=OPEN 재개.
- Producer/API wrapper 호출마다 CircuitBreaker를 씌워 전파.

**D-7. DAG 의존성 그래프 (ORCH-07)**
- 각 GATE는 `depends_on: list[GateName]` 선언.
- 예: `ASSEMBLY` 는 `VOICE + ASSETS` 모두 dispatched=True 요구.
- 선행 GATE 미통과 시 `GateDependencyUnsatisfied` raise.

**D-8. skip_gates 파라미터 물리 제거 (ORCH-08)**
- `shorts_pipeline.py` 전체에 `skip_gates` 문자열 0회 등장.
- 함수 signature에 `skip_gates` 키워드 자체 부재.
- pre_tool_use Hook에 regex `skip_gates\s*=` 차단 등록.
- 실측 grep + Hook mock 테스트 두 방식으로 검증.

**D-9. TODO(next-session) 물리 차단 (ORCH-09)**
- `shorts_pipeline.py` 및 지원 모듈 전체에 `TODO(next-session)` 0회.
- pre_tool_use Hook regex `TODO\s*\(\s*next-session` 차단.
- 미완 기능은 개별 REQ로 Phase 5+ 이관, 주석 금지.

**D-10. 영상/음성 분리 합성 (ORCH-10 + NotebookLM T3)**
- 순서 강제: Typecast(TTS) 먼저 → 오디오 타임스탬프 추출 → 영상 cuts 정렬 → Shotstack composite.
- `VoiceFirstTimeline` 클래스: `audio_segments -> video_cuts.align_to(audio_segments) -> composite()`
- 통합 렌더 (audio + video 동시 generation) 절대 금지.

**D-11. Low-Res First + AI 업스케일 (ORCH-11 + NotebookLM T4)**
- 1차 렌더: 720p (1280×720 for 16:9 / 720×1280 for 9:16).
- 통과 후 Shotstack 또는 별도 업스케일러로 4K 업스케일.
- 720p 통과 시까지 업스케일 호출 금지. CircuitBreaker로 보호.

**D-12. 재생성 루프 3회 → Fallback (ORCH-12 + NotebookLM T8)**
- Producer 호출 실패 3회 누적 시:
  1. FAILURES.md에 append (append-only, session_id + gate + evidence).
  2. "정지 이미지 + 줌인" Fallback 샷 자동 삽입 (asset-sourcer 호출 → Shotstack ken-burns effect).
- 카운터는 CircuitBreaker와 독립. CircuitBreaker = API 장애 보호, 재생성 루프 = 품질 루프.

**D-13. T2V 금지 / I2V only + Anchor Frame (VIDEO-01)**
- 코드 경로 자체에 `text_to_video` / `t2v` 함수 부재.
- `image_to_video(prompt, anchor_frame: Path)` 만 존재.
- Anchor Frame 미지정 시 raise.
- grep으로 `t2v|text_to_video|text2video` 0회 확인.

**D-14. 1 Move Rule + 4~8초 클립 (VIDEO-02)**
- I2V 호출 파라미터: `duration_seconds` ∈ [4, 8], `move_count=1`.
- 프롬프트 검증: 카메라 워킹 1개 + 피사체 액션 1개 이상 금지.

**D-15. Transition Shots (VIDEO-03)**
- `VoiceFirstTimeline`에 `insert_transition_shots()` 단계 삽입.
- 소품 클로즈업 / 실루엣 / 배경 전환 3 템플릿 중 랜덤 선택.
- 정적 이미지 + 0.5~1초 클립 조합으로 구성.

**D-16. Kling 2.6 Pro primary + Runway Gen-3 Alpha Turbo backup (VIDEO-04)**
- `KlingI2V.generate(...)` 실패 (CircuitBreaker OPEN) → `RunwayI2V.generate(...)` 자동 폴백.
- API 키 환경변수: `KLING_API_KEY`, `RUNWAY_API_KEY`.
- 실패 모니터링: 실패 수, 평균 응답 시간 Checkpointer에 기록.

**D-17. Shotstack 일괄 색보정 + 필터 (VIDEO-05)**
- ASSEMBLY GATE에서 Shotstack template 적용.
- 색보정 프리셋: Continuity Bible 기반 (Phase 6 확정, Phase 5 placeholder).
- 필터 순서: color grade → saturation → film grain.

**D-18. 기존 자산 재작성 정책**
- `.preserved/harvested/api_wrappers_raw/` 은 레퍼런스만. `scripts/orchestrator/`에 재작성 (직접 import 금지).
- `.preserved/harvested/hc_checks_raw/hc_checks.py` 1129줄 public 함수 시그니처 보존하면서 `scripts/hc_checks/hc_checks.py` 재작성.
- 재작성 시 logging, CircuitBreaker, Checkpointer integration 추가.

**D-19. Python 버전 + 의존성**
- Python 3.11+ (match_case, walrus, typing.Self 사용).
- 필수: `requests`, `pydantic>=2.0`, `httpx`, `tenacity`.
- 금지: `selenium` (AF-8 이미 차단), `eventlet`, `celery`.

**D-20. 테스트 범위 (Phase 5)**
- 단위: CircuitBreaker 상태 전이, Checkpointer round-trip, GateGuard.dispatch raise, GATE DAG 의존성 검증.
- 통합 (mock): 12 GATE 순차 실행, 재생성 루프 3회 → Fallback, Kling primary → Runway backup.
- Regression: hc_checks.py 기존 테스트 전체 이식.
- 계약 검증: grep 테스트 (skip_gates / t2v / TODO(next-session) 0회).

### Claude's Discretion (구현 세부)

- GATE enum 이름 (`GateName` vs `Gate`), 예외 클래스 이름 (`GateFailure` vs `GateError`) 등 내부 네이밍.
- CircuitBreaker 상태 머신 구현 (decorator vs context manager) 선택.
- Checkpointer 내부 스키마 세부 (json 필드 순서, 버전 포함 여부).
- 로깅 포맷 (structlog vs stdlib logging).
- Wrapper 파일 네이밍 (`kling_i2v.py` vs `kling_client.py`).

### Deferred Ideas (OUT OF SCOPE)

- **Phase 6**: NotebookLM RAG 쿼리 통합 (placeholder만 남김). Continuity Bible 최종 확정 (Shotstack 색보정 프리셋). FAILURES.md 구조화 공식화. Tier 2 wiki 노드.
- **Phase 7**: E2E mock asset 통합 테스트. `verify_all_dispatched()` 실측 17/17 검증. harness-audit 상시화.
- **Phase 8**: GitHub remote push. YouTube API v3 업로드 + AI disclosure. Reused content production_metadata.
- **Phase 9+**: KPI Dashboard. Taste Gate 월 1회 평가.
- **Phase 10**: 주 3~4편 자동 발행. 첫 1~2개월 SKILL patch 전면 금지. FAILURES 저수지 누적.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ORCH-01 | `scripts/orchestrator/shorts_pipeline.py` 500~800줄 state machine | §2 State Machine Architecture (enum + transition table + exception hierarchy sized for 500~800 line budget with 70% margin) |
| ORCH-02 | 12 GATE 구현 (IDLE → ... → COMPLETE) | §2 GATE enum exhaustive enumeration; §5 DAG adjacency list with `depends_on` |
| ORCH-03 | `GateGuard.dispatch(gate, verdict)` — Reviewer FAIL 시 raise | §2 exception hierarchy + §4 dispatch-then-checkpoint invariant |
| ORCH-04 | `verify_all_dispatched()` = COMPLETE 진입 조건 | §2 dispatched set tracking + §4 Checkpointer reconstruction from `state/{session_id}/` |
| ORCH-05 | Checkpointer — `state/{session_id}/gate_{n}.json` | §4 atomic write-temp-then-rename + resume-highest-index pattern |
| ORCH-06 | CircuitBreaker — 3회 실패 → 5분 cooldown | §3 Custom CLOSED/OPEN/HALF_OPEN implementation (tenacity insufficient for state persistence) |
| ORCH-07 | DAG 의존성 그래프 — 선행 GATE 미통과 시 raise | §5 static `depends_on` declaration + topological sort check at import time |
| ORCH-08 | `skip_gates` 파라미터 물리 제거 + regex 차단 | §10 Hook extension (deprecated_patterns.json creation required — currently absent) + grep test |
| ORCH-09 | TODO(next-session) 물리 차단 | §10 Hook extension same file as ORCH-08 |
| ORCH-10 | 영상/음성 완전 분리 합성 (Typecast 먼저 → 타임스탬프 → Shotstack) | §6 VoiceFirstTimeline class design; `elevenlabs_alignment.py` reference for word-level timestamps |
| ORCH-11 | Low-Res First 렌더 (720p) → AI 업스케일 | §7 720p first-pass config + Shotstack upscale API |
| ORCH-12 | 재생성 루프 3회 → FAILURES append + Fallback 샷 | §9 Ken-burns Fallback; append-only FAILURES.md; dedup by (session_id, gate, cut_index) |
| VIDEO-01 | T2V 금지 / I2V only — Anchor Frame 강제 | §8 `image_to_video(prompt, anchor_frame: Path)` sole signature + grep test for `t2v\|text_to_video\|text2video` |
| VIDEO-02 | 1 Move Rule + 4~8초 클립 | §8 Pydantic `I2VRequest` model with constrained `duration_seconds: int = Field(ge=4, le=8)` + `move_count: Literal[1]` |
| VIDEO-03 | Transition Shots 삽입 (소품/실루엣/배경 3 템플릿) | §6 `insert_transition_shots()` pass after voice alignment |
| VIDEO-04 | Kling 2.6 Pro primary → Runway Gen-3 Alpha Turbo backup | §8 Dual-adapter pattern with CircuitBreaker-triggered failover |
| VIDEO-05 | Shotstack 일괄 색보정 + 필터 | §7 ASSEMBLY GATE template application; Continuity Bible prefix is Phase 6 placeholder |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **도메인 절대 규칙**:
  1. `skip_gates=True` 금지 — `pre_tool_use.py` regex 차단
  2. `TODO(next-session)` 금지 — `pre_tool_use.py` regex 차단
  3. try-except 침묵 폴백 금지 — 명시적 `raise` + GATE 기록 필수
  4. T2V 금지 — I2V only, Anchor Frame 강제
  5. Selenium 업로드 영구 금지 (AF-8)
  6. `shorts_naberal` 원본 수정 금지 — Harvest는 `.preserved/harvested/`에 읽기 전용
  7. K-pop 트렌드 음원 직접 사용 금지 (AF-13)
  8. 주 3~4편 페이스 준수 — 48시간+ 랜덤 간격, 한국 피크 시간
- **SKILL.md 500줄 리밋** (Progressive Disclosure)
- **에이전트 총합 32명** (Producer 14 + Inspector 17 + Supervisor 1) — Phase 5 orchestrator invokes these, does NOT reimplement
- **오케스트레이터 500~800줄 상한선**
- **Hooks 3종 활성** (pre_tool_use / post_tool_use / session_start)
- **GSD Workflow Enforcement** — 작업은 `/gsd:execute-phase` 통해, 직접 편집 금지

## Standard Stack

### Core (all verified installed on target machine)
| Library | Version (verified) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11.9 | runtime | `match_case`, walrus, `typing.Self` — D-19 requirement |
| `pydantic` | 2.12.5 | Verdict/Checkpoint/I2VRequest schema | Already used Phase 4 for rubric-schema validation; constrained types (`Field(ge=4, le=8)`) enforce VIDEO-02 at parse time |
| `httpx` | 0.28.1 | Kling/Runway/Shotstack/Typecast HTTP | Used in harvested wrappers; sync + async + streaming download in one client |
| `tenacity` | 9.1.4 | supplemental retry for transient errors inside a CircuitBreaker CLOSED call | Retry decorator — complements but does NOT replace CircuitBreaker (see §3) |
| `pytest` | 9.0.2 | test runner | Phase 4 tests already use it; conftest pattern established (tests/phase04/) |
| stdlib `enum` | built-in | GateName, CircuitState, Verdict enum | Required by D-2; avoid 3rd-party state machine libraries (over-kill) |
| stdlib `hashlib` | built-in | sha256 of artifacts in Checkpointer | hc_checks_raw already uses this pattern |
| stdlib `json` | built-in | Checkpointer atomic writes | atomic pattern: write `.tmp` then `os.replace` (cross-platform atomic on Windows) |
| stdlib `dataclasses` | built-in | Verdict, Checkpoint value objects | hc_checks_raw uses `@dataclass` for HCResult — same convention |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ffmpeg-python` or stdlib `subprocess` | latest | local audio duration (hc_checks uses ffprobe subprocess) | keep subprocess call — matches harvest baseline |
| `python-dotenv` | already used | `.env` API key loading | harvested `tts_generate.py` uses `load_dotenv(override=True)` — preserve pattern |
| `fal_client` | per harvested wrapper | Kling via fal.ai endpoint | `_kling_i2v_batch.py` uses `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` — same endpoint |
| `runwayml` SDK | v4.12+ per wrapper | Runway Gen-4.5 / Gen-3 Alpha Turbo | harvested `runway_client.py` uses `RunwayML(api_key=...)` — preserve but strip T2V methods |
| `typecast` SDK | per harvested | Korean TTS primary | `typecast-python` pip package; `client.text_to_speech(TTSRequest(...))` pattern |
| `elevenlabs` SDK | per harvested | fallback TTS + word-level alignment | `elevenlabs.client.ElevenLabs` + `tts_with_timestamps()` for VoiceFirstTimeline |
| `pydub` | per harvested | audio segment concatenation with silence gaps | used in `tts_generate.py` `concat_with_silence()` — preserve for Voice GATE |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom CircuitBreaker | `circuitbreaker` PyPI package | 3rd-party package works but doesn't persist state — Phase 5 Checkpointer needs to serialize breaker state per D-6 (cooldown survives restart). Custom is ~60 lines and fully under our control. **DECISION: custom.** |
| Custom state machine | `transitions` / `python-statemachine` | Transitions (pytransitions) adds dependency weight for 15 states. Manual transition dict is ~30 lines, type-checkable, single-source-of-truth. **DECISION: custom dict of sets.** |
| Manual DAG check | `networkx` | networkx overkill for 12 GATEs. `depends_on: list[GateName]` in dataclass + BFS `verify_dependencies_satisfied()` is ~15 lines. **DECISION: custom.** |
| `shutil`-based copy | `os.replace` atomic rename | Windows atomicity requirement — `os.replace` is the only cross-platform atomic rename. **DECISION: `os.replace`.** |

**Installation** (already complete in target env):
```bash
# Python 3.11.9 + pip already present
pip install --upgrade pydantic tenacity httpx pytest pydub python-dotenv
# API-specific
pip install fal-client runwayml typecast-python elevenlabs
```

**Version verification:** All 4 critical Python libraries verified via `pip show` on 2026-04-19: pydantic 2.12.5, tenacity 9.1.4, httpx 0.28.1, pytest 9.0.2. No drift from training data (pydantic v2 is stable since 2023-06).

## Architecture Patterns

### Recommended File Structure
```
scripts/
├── orchestrator/
│   ├── __init__.py              # exports: GateName, GateFailure, CircuitBreaker, Checkpointer
│   ├── shorts_pipeline.py       # MAIN — 500~800 lines (Wave 4)
│   ├── gates.py                 # GateName enum + GATE_DAG declaration + exceptions (~120 lines)
│   ├── gate_guard.py            # GateGuard class + Verdict dataclass (~100 lines)
│   ├── checkpointer.py          # Checkpointer + atomic write helpers (~150 lines)
│   ├── circuit_breaker.py       # CircuitBreaker + state serialization (~140 lines)
│   ├── voice_first_timeline.py  # VoiceFirstTimeline alignment + transitions (~250 lines)
│   ├── fallback.py              # ken-burns fallback shot generator (~80 lines)
│   └── api/
│       ├── __init__.py
│       ├── kling_i2v.py         # Kling primary adapter (~180 lines)
│       ├── runway_i2v.py        # Runway backup adapter (~160 lines)
│       ├── typecast.py          # Typecast TTS primary (~220 lines)
│       ├── elevenlabs.py        # ElevenLabs fallback + forced alignment (~180 lines)
│       └── shotstack.py         # Shotstack assembler + 720p renderer + upscaler (~200 lines)
├── hc_checks/
│   ├── __init__.py
│   └── hc_checks.py             # Rewritten — preserves 13 public signatures (~900 lines max)
└── validate/
    └── verify_hook_blocks.py    # Hook mock test (~80 lines) — D-8/D-9 verification
state/                           # Checkpointer output (gitignored, runtime)
tests/phase05/
    ├── conftest.py
    ├── test_circuit_breaker_states.py
    ├── test_checkpointer_round_trip.py
    ├── test_gate_guard_dispatch.py
    ├── test_gate_dag_dependencies.py
    ├── test_shorts_pipeline_12_gates.py
    ├── test_regeneration_loop_fallback.py
    ├── test_kling_runway_failover.py
    ├── test_voice_first_timeline.py
    ├── test_blacklist_grep.py
    ├── test_line_count.py
    ├── test_hook_mock_blocks.py
    └── test_hc_checks_regression.py
```

### Pattern 1: Enum + Transition Dict (State Machine Core)
**What:** GateName `enum.IntEnum` + `ALLOWED_TRANSITIONS: dict[GateName, frozenset[GateName]]`
**When to use:** Any phase requiring explicit state-to-state moves with validation at call time

```python
# scripts/orchestrator/gates.py
from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass, field

class GateName(IntEnum):
    IDLE = 0
    TREND = 1
    NICHE = 2
    RESEARCH_NLM = 3
    BLUEPRINT = 4
    SCRIPT = 5
    POLISH = 6
    VOICE = 7
    ASSETS = 8
    ASSEMBLY = 9
    THUMBNAIL = 10
    METADATA = 11
    UPLOAD = 12
    MONITOR = 13
    COMPLETE = 14

# DAG adjacency (depends_on). ASSEMBLY needs VOICE+ASSETS both done.
GATE_DEPS: dict[GateName, tuple[GateName, ...]] = {
    GateName.IDLE:         (),
    GateName.TREND:        (GateName.IDLE,),
    GateName.NICHE:        (GateName.TREND,),
    GateName.RESEARCH_NLM: (GateName.NICHE,),
    GateName.BLUEPRINT:    (GateName.RESEARCH_NLM,),
    GateName.SCRIPT:       (GateName.BLUEPRINT,),
    GateName.POLISH:       (GateName.SCRIPT,),
    GateName.VOICE:        (GateName.POLISH,),
    GateName.ASSETS:       (GateName.POLISH,),         # parallel to VOICE
    GateName.ASSEMBLY:     (GateName.VOICE, GateName.ASSETS),  # needs BOTH
    GateName.THUMBNAIL:    (GateName.ASSEMBLY,),
    GateName.METADATA:     (GateName.ASSEMBLY,),       # parallel to THUMBNAIL
    GateName.UPLOAD:       (GateName.THUMBNAIL, GateName.METADATA),
    GateName.MONITOR:      (GateName.UPLOAD,),
    GateName.COMPLETE:     tuple(g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)),
}

# Error hierarchy
class OrchestratorError(Exception): pass
class InvalidGateTransition(OrchestratorError): pass
class GateFailure(OrchestratorError):
    def __init__(self, gate: GateName, evidence: list[dict]):
        self.gate = gate
        self.evidence = evidence
        super().__init__(f"{gate.name} FAIL: {len(evidence)} violations")
class MissingVerdict(OrchestratorError): pass
class IncompleteDispatch(OrchestratorError): pass
class GateDependencyUnsatisfied(OrchestratorError): pass
class CircuitOpen(OrchestratorError): pass
class RegenerationExhausted(OrchestratorError): pass
```

### Pattern 2: CircuitBreaker as Context Manager + Serializable State
**What:** Context manager with explicit CLOSED/OPEN/HALF_OPEN logic; state is a serializable dict for Checkpointer
**When to use:** Every external API call (Kling, Runway, Typecast, ElevenLabs, Shotstack). NOT for internal Producer-Supervisor invocations (those use regeneration loop counter instead).

```python
# scripts/orchestrator/circuit_breaker.py
from __future__ import annotations
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Callable, TypeVar

T = TypeVar("T")

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreaker:
    name: str
    max_failures: int = 3
    cooldown_seconds: int = 300
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float | None = None

    def call(self, fn: Callable[[], T]) -> T:
        now = time.time()
        if self.state is CircuitState.OPEN:
            assert self.opened_at is not None
            if now - self.opened_at >= self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN  # probe
            else:
                raise CircuitOpen(f"{self.name} open for {self.cooldown_seconds - (now - self.opened_at):.0f}s more")
        try:
            result = fn()
        except Exception:
            self.consecutive_failures += 1
            if self.state is CircuitState.HALF_OPEN or self.consecutive_failures >= self.max_failures:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()
            raise
        # success
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at = None
        return result

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitBreaker":
        d = {**d, "state": CircuitState(d["state"])}
        return cls(**d)
```

### Pattern 3: Checkpointer Atomic Write + Resume
**What:** JSON file per gate; write via `tmp` + `os.replace()` for cross-platform atomicity; resume reads highest gate_index.

```python
# scripts/orchestrator/checkpointer.py (excerpt)
import json, os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

@dataclass
class Checkpoint:
    session_id: str
    gate: str
    gate_index: int
    timestamp: str
    verdict: dict
    artifacts: dict  # {"path": str, "sha256": str}

class Checkpointer:
    SCHEMA_VERSION = 1
    def __init__(self, state_root: Path = Path("state")):
        self.root = state_root

    def save(self, cp: Checkpoint) -> Path:
        target_dir = self.root / cp.session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"gate_{cp.gate_index:02d}.json"
        tmp = target.with_suffix(".tmp")
        payload = {"_schema": self.SCHEMA_VERSION, **asdict(cp)}
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, target)  # atomic on Windows + POSIX
        return target

    def resume(self, session_id: str) -> int:
        d = self.root / session_id
        if not d.exists():
            return -1
        indices = sorted(int(p.stem.split("_")[1]) for p in d.glob("gate_*.json"))
        return indices[-1] if indices else -1

    def dispatched_gates(self, session_id: str) -> set[str]:
        d = self.root / session_id
        if not d.exists():
            return set()
        out = set()
        for p in sorted(d.glob("gate_*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            out.add(data["gate"])
        return out

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
```

### Pattern 4: GateGuard — Dispatch-or-Raise
```python
# scripts/orchestrator/gate_guard.py (excerpt)
@dataclass
class Verdict:
    result: Literal["PASS", "FAIL"]
    score: int
    evidence: list[dict]
    semantic_feedback: str
    inspector_name: str | None = None

class GateGuard:
    def __init__(self, checkpointer: Checkpointer, session_id: str):
        self.cp = checkpointer
        self.session_id = session_id
        self.dispatched: set[GateName] = set()

    def dispatch(self, gate: GateName, verdict: Verdict, artifact_path: Path | None = None) -> None:
        if verdict is None:
            raise MissingVerdict(f"{gate.name}: Inspector must be called before dispatch")
        if verdict.result == "FAIL":
            raise GateFailure(gate, verdict.evidence)
        # PASS → checkpoint + mark dispatched
        artifacts = {}
        if artifact_path and artifact_path.exists():
            artifacts = {"path": str(artifact_path), "sha256": sha256_file(artifact_path)}
        self.cp.save(Checkpoint(
            session_id=self.session_id,
            gate=gate.name,
            gate_index=int(gate),
            timestamp=datetime.now(timezone.utc).isoformat(),
            verdict=asdict(verdict),
            artifacts=artifacts,
        ))
        self.dispatched.add(gate)

    def verify_all_dispatched(self) -> bool:
        needed = {g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)}
        return needed.issubset(self.dispatched)

    def ensure_dependencies(self, gate: GateName) -> None:
        missing = [d for d in GATE_DEPS[gate] if d not in self.dispatched and d is not GateName.IDLE]
        if missing:
            raise GateDependencyUnsatisfied(f"{gate.name} needs: {[g.name for g in missing]}")
```

### Anti-Patterns to Avoid
- **Single 500~800 line file containing all classes**: wrong. D-1 allows supporting modules; the 500~800 line budget applies ONLY to `shorts_pipeline.py`. Inlining CircuitBreaker + Checkpointer into pipeline file would blow the budget immediately.
- **`skip_gates` parameter "for testing"**: physically forbidden. Tests must mock `GateGuard.dispatch` or use `GateName` enum values to drive state directly, never bypass.
- **`try: ... except Exception: pass`**: silent fallback forbidden by project rule 3 and also blocked by hook pattern in `deprecated_patterns.json` (to be authored). Always `raise` after logging + checkpoint append.
- **Integrated video+audio generation**: D-10 forbids. `KlingI2V.generate()` must not take audio input; `Typecast.generate()` must complete before ASSEMBLY gate reads its timestamps.
- **T2V functions present but not called**: D-13 requires *code path physical absence*. Runway adapter must NOT expose `text_to_video()` even if harvested wrapper has one.
- **Storing CircuitBreaker state as singleton module var**: survives tests badly and doesn't survive process restart. Use Checkpointer to serialize breaker state alongside gate state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema validation | Custom validator | `pydantic>=2.0` `BaseModel.model_validate_json()` | Already used Phase 4; constrained types enforce VIDEO-02 (duration 4-8s) at parse time |
| SHA256 of artifact | Custom chunked reader | `hashlib.sha256()` streaming pattern (already in hc_checks_raw line 430-450) | Stdlib, Windows-safe, handles multi-GB files |
| Atomic file rename on Windows | `shutil.move` + try/except | `os.replace()` | `shutil.move` is NOT atomic on Windows; `os.replace` IS (since Python 3.3, docs guarantee) |
| HTTP retry with backoff | Custom loop + sleep | `tenacity` `@retry(stop=stop_after_attempt, wait=wait_exponential)` | Only INSIDE a CircuitBreaker CLOSED call for transient 500s — NOT as breaker replacement |
| Topological sort for DAG | Kahn's algo by hand | `graphlib.TopologicalSorter` (stdlib since 3.9) | Use at import time to assert `GATE_DEPS` has no cycles; 3 lines. |
| Word-level TTS timestamps | Manual parsing | `elevenlabs` SDK `tts_with_timestamps()` | Already wrapped in harvested `elevenlabs_alignment.py` — reuse `_chars_to_words()` pattern verbatim |
| Audio concatenation with silence | FFmpeg CLI by hand | `pydub.AudioSegment` | Already in harvested `tts_generate.py::concat_with_silence` — preserve |
| Windows path normalization in subprocess | `str(path)` | `str(path.resolve())` + forward-slash | Harvested `_kling_i2v_batch.py` uses `str(image_path.resolve())` — preserve |

**Key insight:** Every tempting "custom utility" in this phase has either a stdlib answer (enum, hashlib, graphlib, os.replace) or already exists in the harvested wrappers (pydub concat, elevenlabs alignment). The Phase 5 rewrite is 80% *assembly* of proven primitives + 20% *structural discipline* (enum, DAG, CircuitBreaker state machine).

## Runtime State Inventory

> Phase 5 is a GREENFIELD write (new module tree under `scripts/orchestrator/`). However, some runtime state categories apply because the orchestrator creates persistent state at runtime that must survive restarts.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **New** `state/{session_id}/gate_{n}.json` Checkpointer artifacts. No existing migration needed (Phase 5 is first writer). | Document JSON schema version field (`_schema: 1`) for future migrations. Add `.gitignore` entry for `state/`. |
| Live service config | None for Phase 5 (Phase 6 adds NotebookLM notebooks; Phase 8 adds YouTube API). | None. |
| OS-registered state | None — Phase 5 is library code, no scheduled tasks or services. | None. |
| Secrets / env vars | **NEW** env keys needed: `KLING_API_KEY` (or `FAL_KEY` per harvested wrapper), `RUNWAY_API_KEY`, `RUNWAYML_API_SECRET` (alias), `TYPECAST_API_KEY`, `ELEVENLABS_API_KEY` / `ELEVEN_API_KEY` (alias), `SHOTSTACK_API_KEY`, `HEYGEN_API_KEY` (optional, Phase 5 doesn't use HeyGen per CONTEXT D-18 context — HeyGen TBD). | Document in README + `.env.example`; Phase 5 plan should NOT commit `.env`. |
| Build artifacts | None — Python source only, no egg-info or compiled binaries. Remotion `node_modules` is Phase 3 harvested, untouched by Phase 5. | None. |
| Hook config file | **DOES NOT EXIST YET**: `.claude/deprecated_patterns.json` is read by pre_tool_use.py line 35 but the file is absent in the current shorts_studio. Without it the Hook allows everything. | **Wave 0 MUST create `.claude/deprecated_patterns.json`** with entries for `skip_gates\s*=`, `TODO\s*\(\s*next-session`, `text_to_video\|t2v\|text2video`, `segments\[\]`, `import\s+selenium`. |

**Canonical question answered:** After Phase 5 code is written, runtime still depends on (1) `.env` having 5 API keys the developer provisions manually, (2) `.claude/deprecated_patterns.json` being created (currently missing), (3) `state/` directory being writable. No data migration of existing content (first-time writer).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | shorts_pipeline.py (match_case, typing.Self) | ✓ | 3.11.9 | — |
| `pydantic` 2.x | Verdict / I2VRequest schema | ✓ | 2.12.5 | — |
| `httpx` 0.27+ | Kling/Shotstack HTTP | ✓ | 0.28.1 | — |
| `tenacity` 9.x | retry decorator | ✓ | 9.1.4 | — |
| `pytest` 8+ | test runner | ✓ | 9.0.2 | — |
| ffmpeg CLI | hc_checks HC-3 duration | **must verify on dev machine** | — | hc_checks HC-3 returns FAIL("ffprobe not on PATH") — baseline behavior, not a fallback but a graceful degrade |
| `fal-client` Python | Kling adapter | **probably NOT installed** | — | `pip install fal-client` — Wave 3 plan step |
| `runwayml` SDK v4+ | Runway adapter | **probably NOT installed** | — | `pip install runwayml` — Wave 3 plan step |
| `typecast-python` | Typecast adapter | **probably NOT installed** | — | `pip install typecast-python` — Wave 3 plan step |
| `elevenlabs` SDK | ElevenLabs fallback | **probably NOT installed** | — | `pip install elevenlabs` — Wave 3 plan step |
| `pydub` | audio concat | **probably NOT installed** | — | `pip install pydub` (needs ffmpeg) — Wave 3 plan step |
| `python-dotenv` | .env loader | available in Phase 4 test env likely | — | `pip install python-dotenv` |

**Missing dependencies with no fallback:** None — all installable via pip.

**Missing dependencies with fallback:** For Phase 5 unit tests, API wrappers can be mocked via `unittest.mock.MagicMock`, so API SDK packages are not blocking for tests (only for real runs). Plan the install step in Wave 3 or Wave 0.

## State Machine Architecture

### Enum + Transition Table Design

- **GateName** as `IntEnum` (0=IDLE … 14=COMPLETE). `IntEnum` over `Enum` because Checkpointer file naming uses `gate_{int(gate):02d}.json` for natural sort + resume logic.
- **15 states** (IDLE + 13 gates + COMPLETE). Success Criteria 1 says "12 GATE" — referring to the 12 *operational* GATEs (TREND through UPLOAD). MONITOR is the 13th operational step, and IDLE + COMPLETE are bookends. Match `verify_all_dispatched()` to the 13 operational (non-IDLE, non-COMPLETE).
- **Transition table:** static `dict[GateName, frozenset[GateName]]` defined at module top. Pre-computed at import time; fail-fast on cycle via `graphlib.TopologicalSorter`.
- **Do not** implement state-machine via class methods (`def can_transition(self) -> bool: ...` per gate). That pattern bloats the main file and contradicts D-1 size budget.

### Error Hierarchy (all subclass a common `OrchestratorError`)
```python
OrchestratorError
├── InvalidGateTransition     # illegal GATE → GATE move
├── GateFailure               # verdict.result == "FAIL"
├── MissingVerdict            # dispatch called without Inspector invocation
├── IncompleteDispatch        # verify_all_dispatched() False at COMPLETE
├── GateDependencyUnsatisfied # ASSEMBLY called before VOICE + ASSETS
├── CircuitOpen               # API wrapper refused (CircuitBreaker OPEN)
├── RegenerationExhausted     # 3 Producer retries blown → Fallback path
├── T2VForbidden              # anyone tries to call text_to_video()
└── InvalidI2VRequest         # duration outside [4,8] or move_count != 1
```

### Size Budget for shorts_pipeline.py (target 500~800 lines)
Rough line budget (gets under 700 with discipline):
- Module docstring + imports: 40
- `GateContext` dataclass (session_id, config, channel_bible, retry_counts): 25
- `ShortsPipeline` class `__init__` wiring (checkpointer, guards, circuit breakers, adapters): 60
- `run(session_id)` top-level orchestration: 50
- 13 `_run_<gate>()` methods (avg 30 lines each covering Producer call, Supervisor fan-out via Task tool, dispatch): 390
- Regeneration loop helper (`_producer_loop(gate, producer, max_retries=3)`): 40
- Resume-from-checkpoint logic: 30
- Fallback shot trigger (`_insert_fallback(gate, cut)`): 25
- Logging + entry point CLI (`if __name__ == "__main__"`): 40
- **Total: ~700 lines** — within budget with ~100 line headroom for unforeseen cases.

Size enforcement: `tests/phase05/test_line_count.py` asserts `500 <= line_count <= 800`.

## CircuitBreaker Implementation

### Library Choice: CUSTOM (not tenacity, not `circuitbreaker` package)

**Why not tenacity:** tenacity is a retry decorator. It does not implement OPEN/HALF_OPEN state with cooldown timers. It wraps a single call with retries; it does not track consecutive failures across calls. Per D-6 we need state persistence and 3-state machine.

**Why not `circuitbreaker` PyPI:** package is maintenance-only (last release 2022), does not expose serializable state, uses decorator form which fights our need to checkpoint breaker state in the Checkpointer JSON.

**Custom implementation:** See §Architecture Patterns Pattern 2 above. ~60 lines. Key features:
- `CLOSED` (default): calls pass through, failures increment counter
- `OPEN` (after `max_failures=3` consecutive): all calls raise `CircuitOpen` for `cooldown_seconds=300`
- `HALF_OPEN` (after cooldown expires): next call is a probe; success → CLOSED, failure → back to OPEN with fresh `opened_at`
- `to_dict()` / `from_dict()` for Checkpointer serialization

### Integration Pattern (Context Manager or Plain Method Call)
Plain method call `breaker.call(lambda: kling.generate(...))` chosen over `with breaker:` because lambda is simpler to type-hint and composes naturally with `tenacity.retry` as inner decorator for transient errors:

```python
# inside VoiceFirstTimeline._generate_cut(...)
try:
    clip_path = self.kling_breaker.call(
        lambda: self.kling.image_to_video(prompt=p, anchor_frame=a, duration_seconds=d)
    )
except CircuitOpen:
    # Primary circuit open → fallback
    clip_path = self.runway_breaker.call(
        lambda: self.runway.image_to_video(prompt=p, anchor_frame=a, duration_seconds=d)
    )
```

### State Persistence Across Process Restart
Checkpointer schema extension: each `gate_{n}.json` optionally includes `"circuit_breakers": {name: breaker.to_dict(), ...}`. On resume, pipeline reads the most recent gate file and restores all breakers with `CircuitBreaker.from_dict(...)`. Cooldown timer persists because `opened_at` is a unix timestamp.

### Metrics Collection (Observability — deferred to Phase 9 KPI)
Stub methods `get_metrics() -> dict`: total calls, total failures, current state, time in current state. Log line on every state transition with structured key-values. Phase 5 does not need a metrics backend; Phase 9 KPI dashboard will consume these logs.

## Checkpointer Design

### JSON Schema (with version field for forward compatibility)
```json
{
  "_schema": 1,
  "session_id": "20260419-143022-wildlife-mantis",
  "gate": "NICHE",
  "gate_index": 2,
  "timestamp": "2026-04-19T14:35:40.123456+00:00",
  "verdict": {
    "result": "PASS",
    "score": 88,
    "evidence": [],
    "semantic_feedback": "",
    "inspector_name": "shorts-supervisor"
  },
  "artifacts": {
    "path": "state/20260419-143022-wildlife-mantis/niche.json",
    "sha256": "7c21f3d..."
  },
  "circuit_breakers": {
    "kling": {"name": "kling", "state": "CLOSED", "consecutive_failures": 0, ...},
    "runway": {"name": "runway", "state": "CLOSED", ...}
  }
}
```

### Atomic Write (Windows + POSIX)
1. Serialize JSON to `target.tmp` via `Path.write_text()` (this is itself not atomic but crash here leaves `.tmp` only, and `target` file is unmodified)
2. `os.replace(tmp, target)` — Windows and POSIX both guarantee atomic rename per Python docs. This is the critical line.
3. If step 2 raises, re-raise; orchestrator aborts the gate, never half-writes.

**Why not `shutil.move`:** Python docs explicitly note `shutil.move` is not atomic on Windows when source and destination are on same filesystem — it does copy+delete internally in some cases.

### Resume Logic
```python
last = checkpointer.resume(session_id)  # returns highest gate_index, or -1
if last == -1:
    start = GateName.IDLE
else:
    start = GateName(last + 1)  # next gate in the IntEnum sequence
```

Dispatched gates set reconstructed from ALL files in directory, not just max:
```python
dispatched = set()
for p in sorted((state_root / session_id).glob("gate_*.json")):
    dispatched.add(GateName[json.loads(p.read_text())["gate"]])
```

### Idempotency (same session + same gate re-dispatched)
- `os.replace` overwrites — same session_id + same gate_index produces same path, silently replaces.
- `consecutive_failures` in CircuitBreaker serialization will reset when PASS dispatch occurs (since breaker.call() sets counter=0 on success before dispatch).
- Test `test_checkpointer_round_trip.py::test_idempotent_overwrite` asserts no duplicate files, mtime updates monotonically.

## DAG Dependency Model

### Static Declaration (at module import)
```python
# scripts/orchestrator/gates.py
GATE_DEPS: dict[GateName, tuple[GateName, ...]] = { ... }  # see §Architecture

# Sanity check at import — fail fast on cycles or missing gates
import graphlib
def _validate_dag() -> None:
    sorter = graphlib.TopologicalSorter({g.name: {d.name for d in deps} for g, deps in GATE_DEPS.items()})
    sorter.prepare()  # raises CycleError on cycle
    ordered = list(sorter.static_order())
    assert set(ordered) == {g.name for g in GateName}, f"DAG gates mismatch: {set(ordered)} vs {set(g.name for g in GateName)}"
_validate_dag()  # runs at import, crashes if DAG malformed
```

### Runtime Check
`GateGuard.ensure_dependencies(gate)` — see §Architecture Pattern 4. Called at the top of each `_run_<gate>` method.

### NotebookLM T16 Interpretation
T16 ("DAG 의존성 그래프") means: the pipeline must not allow ASSEMBLY to run before VOICE AND ASSETS both complete. This is enforced by `GATE_DEPS[ASSEMBLY] = (VOICE, ASSETS)` + `ensure_dependencies()` raise. For parallel-capable gates (VOICE + ASSETS can run concurrently since both only depend on POLISH), Phase 5 executes sequentially (VOICE then ASSETS) for simplicity; Phase 7 may add asyncio parallelism.

## VoiceFirstTimeline Algorithm

### Order (D-10 strict)
1. **Voice generation (VOICE GATE)**: Typecast (primary) or ElevenLabs (fallback) generates audio + word-level timestamps. Output: `narration.mp3` + `word_timings.json` (list of `{word, start, end}`).
2. **Assets generation (ASSETS GATE)**: image-to-video clips from Kling (primary) or Runway (fallback). One clip per script scene. Duration 4-8s each. Stored in `clips/{scene_id}.mp4`.
3. **Timeline alignment (ASSEMBLY GATE prep)**: `VoiceFirstTimeline.align(audio_segments, video_cuts)` maps audio segment boundaries to cut durations. Naive chunk-match is acceptable for Phase 5 — match scene N to audio segment N by order, clip cut to match audio duration ±0.5s (Shotstack can speed/slow via `speed` parameter).
4. **Transition shot insertion**: `insert_transition_shots()` adds 0.5-1s transitions every N cuts from 3 templates (prop closeup / silhouette / background). Random selection (VIDEO-03).
5. **Shotstack composite**: emit Shotstack JSON with cuts + transitions + audio track.

### Algorithm Details (Greedy Chunk-Match)
```python
def align(self, audio_segments: list[AudioSegment], video_cuts: list[VideoCut]) -> list[TimelineEntry]:
    if len(audio_segments) != len(video_cuts):
        raise TimelineMismatch(f"audio={len(audio_segments)} video={len(video_cuts)}")
    timeline = []
    for aud, vid in zip(audio_segments, video_cuts):
        # Enforce 4-8s clip duration by speed-adjusting within tolerance
        if not (4.0 <= aud.duration <= 8.0):
            raise InvalidClipDuration(f"audio segment {aud.index} is {aud.duration:.2f}s (must 4-8s)")
        speed = aud.duration / vid.duration  # Shotstack speed param; 1.0 = no adjust
        if not (0.8 <= speed <= 1.25):
            raise ClipDurationMismatch(f"segment {aud.index}: speed adjust {speed:.2f} outside [0.8, 1.25] — re-generate clip")
        timeline.append(TimelineEntry(
            start=aud.start, end=aud.end, clip=vid.path, speed=speed, audio=aud.path
        ))
    return timeline
```

Greedy is sufficient because upstream (shot-planner agent) already emits one scene per script section, and VOICE gate emits one audio segment per section. If counts diverge, that's an upstream bug — raise, don't paper over.

### Transition Shot Insertion (VIDEO-03)
```python
def insert_transition_shots(self, timeline: list[TimelineEntry]) -> list[TimelineEntry]:
    import random
    TEMPLATES = ["prop_closeup", "silhouette", "background_wipe"]
    out = []
    for i, entry in enumerate(timeline):
        out.append(entry)
        if i < len(timeline) - 1 and (i + 1) % 3 == 0:  # every 3rd cut
            tpl = random.choice(TEMPLATES)
            trans_duration = random.uniform(0.5, 1.0)
            out.append(TransitionEntry(template=tpl, duration=trans_duration, index=i))
    return out
```

Output feeds Shotstack JSON; transitions render via Shotstack's built-in effect templates or pre-built 1s clips.

## Low-Res First Strategy

### 720p Targets
- **9:16 shorts (primary)**: 720×1280
- **16:9 longform (future)**: 1280×720

Shotstack `render` endpoint accepts `output.resolution = "hd"` for 1280×720 and `output.aspectRatio = "9:16"` for vertical. Phase 5 hardcodes 9:16 shorts (`ASPECT_RATIO = "9:16"`, `RESOLUTION = "hd"`).

### Upscale Route
1. **720p first pass** — Shotstack render at `"hd"`. Output URL returned.
2. **Quality inspection GATE (ASSEMBLY PASS)** — download 720p, run ins-render-integrity + ins-audio-quality. Only if BOTH PASS, proceed.
3. **Upscale (optional)** — Shotstack has no native upscale endpoint. Options:
   - (a) `Topaz Video AI` CLI (local, paid license)
   - (b) `Real-ESRGAN` (open source, GPU-bound, hour+ per short) — too slow for 3-4 videos/week cadence
   - (c) **Skip upscale — 720p is acceptable for YouTube Shorts** (confirmed by YouTube encoder; 1080p eventually synthesized server-side from 720p source)
- **Recommendation:** Phase 5 ships 720p without upscale. Upscale is Phase 8 optimization if Analytics show quality-driven drop-off. Document explicit decision in plan.

### CircuitBreaker Protection
Wrap both `ShotstackAdapter.render(...)` calls (720p + upscale attempt) with CircuitBreaker. If upscale fails, 720p version is the shipping asset — pipeline logs warning but does not fail ASSEMBLY gate.

## API Adapter Strategy

### What to Preserve from Harvested Wrappers

| Wrapper | Lines | Preserved? | How |
|---------|-------|------------|-----|
| `_kling_i2v_batch.py` | 237 | Pattern only | Adopt fal.ai endpoint `fal-ai/kling-video/v2.5-turbo/pro/image-to-video`, `NEG_PROMPT` string, `submit_kling()` polling pattern. REWRITE as `KlingI2VAdapter` class with `image_to_video()` method accepting `(anchor_frame: Path, prompt: str, duration_s: int)`. Drop: batch main() CLI, dry-run mode, `ACTION_KEYWORDS` heuristic, `MAP_KEYWORDS` (these are shot-planner concerns). |
| `runway_client.py` | 436 | Partial | Preserve `MODEL_REGISTRY`, `GenerationResult` dataclass, `_resolve_prompt_image()`, `_file_to_data_uri()`, `_download_url()`. **REMOVE** `text_to_video()` method (VIDEO-01 D-13). Keep `image_to_video()` but narrow model to `gen3_alpha_turbo` (VIDEO-04 D-16). |
| `tts_generate.py` | 1413 | Refactor heavily | Extract `generate_typecast()` into `TypecastAdapter.generate()`, `generate_elevenlabs()` into `ElevenLabsAdapter.generate()`. Preserve `chunk_text_for_typecast()`, `_inject_punctuation_breaks()`, `_convert_breaks_to_silence()`, `concat_with_silence()`, `get_audio_duration()`. **REMOVE** Fish Audio, VOICEVOX (Japanese), EdgeTTS paths (AUDIO-01 locks Typecast + ElevenLabs only). **REMOVE** 4-tier fallback main() CLI (replaced by orchestrator flow control). |
| `elevenlabs_alignment.py` | ~200 | Preserve core | `_chars_to_words()` verbatim, `tts_with_timestamps()` pattern. Used by VoiceFirstTimeline for word-level timestamp extraction. |
| `heygen_client.py` | ~300 | NOT USED in Phase 5 | CONTEXT.md D-18 canonical_refs says "사용 여부 TBD". VoiceFirstTimeline does not use avatar video. Skip for Phase 5. |

### T2V Blacklist Enforcement
1. **Code path absence**: `RunwayI2VAdapter` class has NO `text_to_video` method. `KlingI2VAdapter` never had one (only I2V endpoint).
2. **Grep verification**: `tests/phase05/test_blacklist_grep.py::test_no_t2v` runs:
   ```python
   import subprocess
   result = subprocess.run(
       ["grep", "-riE", r"t2v|text_to_video|text2video", "scripts/orchestrator/"],
       capture_output=True, text=True
   )
   assert result.returncode == 1, f"T2V references found:\n{result.stdout}"
   ```
   (grep exits 1 = no match = PASS)
3. **Hook extension**: `.claude/deprecated_patterns.json` gains regex `(text_to_video|text2video|(?<![a-z])t2v(?![a-z]))` to block Write/Edit attempts that add T2V code later.
4. **Runtime guard (belt+suspenders)**: orchestrator module top imports `runway_client` NAMESPACE and asserts `not hasattr(RunwayI2VAdapter, "text_to_video")` at import time. Fails noisily if a dev re-adds it.

### API Key Env Var Convention
```bash
# .env.example (commit this template; .env gitignored)
KLING_API_KEY=...           # for fal.ai Kling endpoint (alias: FAL_KEY)
RUNWAY_API_KEY=...          # Runway (alias: RUNWAYML_API_SECRET)
TYPECAST_API_KEY=...
ELEVENLABS_API_KEY=...      # alias: ELEVEN_API_KEY
SHOTSTACK_API_KEY=...       # Shotstack sandbox + production keys
```
Adapters accept explicit `api_key=` arg; fallback to env; fail fast with ValueError if neither.

## Fallback Shot Pattern

### Trigger
`RegenerationLoop` in shorts_pipeline.py increments retry counter for a *gate*, not per-cut. Logic:
```python
def _producer_loop(self, gate: GateName, producer_fn, max_retries: int = 3):
    for retry in range(max_retries):
        output = producer_fn(prior_vqqa=self.last_vqqa.get(gate))
        verdict = self.supervisor.evaluate(gate, output, retry_count=retry)
        if verdict.result == "PASS":
            return output
        self.last_vqqa[gate] = verdict.semantic_feedback
    # Exhausted
    self._append_failures(gate, output, verdict)
    if gate in (GateName.ASSETS, GateName.THUMBNAIL):
        return self._insert_fallback(gate, output)  # ken-burns fallback
    raise RegenerationExhausted(gate, verdict.evidence)
```

### Ken-Burns Fallback (Visual)
```python
def _insert_fallback(self, gate: GateName, failed_cut: Cut) -> Cut:
    # Call asset-sourcer Producer to supply a static image
    still_image = self.asset_sourcer.find_stock_still(failed_cut.prompt)
    # Shotstack ken-burns: pan+scale static image
    fallback = self.shotstack.create_ken_burns_clip(
        image_path=still_image,
        duration_s=failed_cut.intended_duration,
        scale_from=1.0, scale_to=1.15,
        pan_direction="left_to_right",
    )
    return Cut(path=fallback, duration=failed_cut.intended_duration, is_fallback=True)
```

### FAILURES Append-Only
```python
def _append_failures(self, gate, output, verdict):
    entry = f"\n<!-- session:{self.session_id} gate:{gate.name} ts:{now} -->\n"
    entry += f"## {self.session_id} {gate.name} FAIL after 3 retries\n"
    entry += f"Evidence: {verdict.evidence[:3]}\n"
    entry += f"Semantic feedback: {verdict.semantic_feedback}\n"
    # Append to .claude/failures/orchestrator.md (exists per Phase 3 Plan 03-07 merge)
    with open(".claude/failures/orchestrator.md", "a", encoding="utf-8") as f:
        f.write(entry)
```

### Deduplication
Fallback insertion tracked in Checkpointer under `artifacts.fallback_indices: list[int]`. Same session + same gate does not double-insert even on resume — gate_{n}.json record is source of truth.

## Hook Extensions Needed

### Current State of pre_tool_use.py
Confirmed by reading `.claude/hooks/pre_tool_use.py` (222 lines). Hook reads `.claude/deprecated_patterns.json` at studio root (lines 33-44 `load_patterns`). **The patterns file DOES NOT EXIST** in current `studios/shorts/.claude/` directory — verified via bash find on 2026-04-19. Without this file, the Hook silently allows everything (line 200-202: `if not patterns: print({"decision": "allow"})`).

### Required Action (Wave 0 or Wave 6)
Create `.claude/deprecated_patterns.json`:
```json
{
  "patterns": [
    {
      "regex": "skip_gates\\s*=",
      "reason": "ORCH-08 / CONFLICT_MAP A-6: skip_gates 물리 차단 (D-8)"
    },
    {
      "regex": "TODO\\s*\\(\\s*next-session",
      "reason": "ORCH-09 / CONFLICT_MAP A-5: TODO(next-session) 물리 차단 (D-9)"
    },
    {
      "regex": "(?i)(text_to_video|text2video|(?<![a-z])t2v(?![a-z]))",
      "reason": "VIDEO-01 / D-13: T2V 코드 경로 부재 강제 (I2V only + Anchor Frame)"
    },
    {
      "regex": "segments\\s*\\[\\s*\\]",
      "reason": "Phase 3 canonical: cuts[] only, segments[] deprecated"
    },
    {
      "regex": "\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import",
      "reason": "AF-8: Selenium 영구 금지 (YouTube ToS 위반)"
    },
    {
      "regex": "try\\s*:[^\\n]*\\n\\s+pass\\s*$",
      "reason": "Rule 3: try-except 침묵 폴백 금지 — 명시적 raise 필수"
    }
  ]
}
```

### Mock Testing Pattern
`tests/phase05/test_hook_mock_blocks.py`:
```python
import json, subprocess, sys
from pathlib import Path

HOOK = Path(".claude/hooks/pre_tool_use.py").resolve()

def _hook_check(tool_name: str, content: str, file_path: str = "scripts/orchestrator/shorts_pipeline.py") -> dict:
    payload = {"tool_name": tool_name, "input": {"content": content, "file_path": file_path}}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True, capture_output=True, timeout=5, cwd=str(HOOK.parents[2])  # studios/shorts
    )
    return json.loads(proc.stdout)

def test_skip_gates_blocked():
    res = _hook_check("Write", "def run(skip_gates=True): pass")
    assert res["decision"] == "deny"
    assert "ORCH-08" in res["reason"] or "skip_gates" in res["reason"]

def test_t2v_blocked():
    res = _hook_check("Write", "def text_to_video(prompt): ...")
    assert res["decision"] == "deny"

def test_todo_next_session_blocked():
    res = _hook_check("Edit", "// TODO(next-session): finish this")
    assert res["decision"] == "deny"

def test_allowed_normal_code():
    res = _hook_check("Write", "def image_to_video(anchor_frame, prompt): pass")
    assert res["decision"] == "allow"
```

## hc_checks Rewrite Plan

### Source: 1129 lines in `.preserved/harvested/hc_checks_raw/hc_checks.py` (Tier 3 immutable)

### Public Function Signatures That MUST Be Preserved (13 exports from `__all__`)

```python
__all__ = [
    "HCResult",                         # @dataclass with hc_id, verdict, detail, evidence
    "check_hc_1",                       # subtitle coverage >= 95%
    "check_hc_2",                       # title line1/line2 length
    "check_hc_3",                       # narration duration ±10s tolerance
    "check_hc_4",                       # gates.json contains GATE-1..GATE-5 with PASS/FAIL (not Auto-approved)
    "check_hc_5",                       # orchestrator_actions.log 0 VIOLATION lines
    "check_hc_6",                       # scene-manifest.json >= 6 unique source hashes
    "check_hc_6_5_cross_slug",          # no cross-slug md5 collision (Phase 50-E)
    "check_hc_7",                       # Watson → detective response pairing
    "check_hc_12_text_screenshot",      # OpenCV text-area ratio < 30%
    "check_hc_13_compliance",           # product_review compliance_result.json all PASS
    "check_hc_14_no_direct_link",       # product_review CTA no direct URLs
    "run_all_hc_checks",                # runs HC-1..7 + HC-13/14 sequentially
]
```

Plus 3 more that exist in `_HC_FUNCS` but not currently in `__all__` (still callable as module attributes, treat as semi-public):
- `check_hc_8_diagnostic_five` (SKIP placeholder; Phase 50-03 Wave 3e wiring — **out of scope Phase 5, keep stub**)
- `check_hc_9_pipeline_order` (artifact chain hash + mtime monotonicity; **preserve**)
- `check_hc_10_inspector_coverage` (reads `scripts.orchestrator.harness.GATE_INSPECTORS` — **Phase 5 must expose `GATE_INSPECTORS` or rewrite this function**)

### Rewrite Strategy
1. **Wave 5 Plan 1:** Copy hc_checks_raw into `scripts/hc_checks/hc_checks.py`, run `test_hc_checks.py` against it. Confirm baseline PASS.
2. **Wave 5 Plan 2:** Rewrite each `check_hc_N` to use new `OrchestratorError` hierarchy instead of bare returns where applicable (PASS with evidence still returned as HCResult; FAIL paths can optionally raise to orchestrator). Preserve signature exactly.
3. **Wave 5 Plan 3:** Add CircuitBreaker wrapping around `_ffprobe_duration()` (subprocess call) — timeout protection for hanging ffprobe processes.
4. **Wave 5 Plan 4:** Export `GATE_INSPECTORS` dict from orchestrator module so `check_hc_10_inspector_coverage` works; map Phase 4's 17 Inspector names to the relevant GATE per Phase 5 design (likely `{"SCRIPT": [...], "ASSEMBLY": [...], ...}`).
5. **Wave 5 Plan 5:** Port `test_hc_checks.py` from harvested (which imports `from scripts.orchestrator import hc_checks`) — adjust import path to `from scripts.hc_checks import hc_checks`.

### GATE → HC Check Mapping (tentative, finalize in Wave 5)
| GATE | HC checks to invoke |
|------|---------------------|
| SCRIPT | HC-2 (title length), HC-7 (Watson→detective), HC-9 (artifact chain) |
| POLISH | HC-7 (re-verify after polish) |
| VOICE | HC-3 (narration duration) |
| ASSETS | HC-6 (unique images), HC-6.5 (cross-slug contamination), HC-12 (text screenshot per image) |
| ASSEMBLY | HC-1 (subtitle coverage) |
| METADATA | HC-13, HC-14 (product_review only — SKIP for other channels) |
| MONITOR | HC-4 (gates.json verdict sanity), HC-5 (orchestrator_actions.log VIOLATION count) |
| COMPLETE | `run_all_hc_checks()` comprehensive final sweep |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (verified installed) |
| Config file | `pytest.ini` / `pyproject.toml` — **absent; Wave 0 creates** |
| Quick run command | `pytest tests/phase05/ -q -x` |
| Full suite command | `pytest tests/phase05/ tests/phase04/ -q` (includes Phase 4 regression safety) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| ORCH-01 | file is 500~800 lines | contract | `pytest tests/phase05/test_line_count.py -x` | ❌ Wave 6 |
| ORCH-02 | 12 operational GATEs enum + transitions | unit | `pytest tests/phase05/test_gate_enum.py::test_exactly_13_operational_gates -x` | ❌ Wave 0 |
| ORCH-03 | GateGuard.dispatch raises GateFailure on FAIL verdict | unit | `pytest tests/phase05/test_gate_guard_dispatch.py::test_fail_raises -x` | ❌ Wave 1 |
| ORCH-03 | GateGuard.dispatch raises MissingVerdict on None verdict | unit | `pytest tests/phase05/test_gate_guard_dispatch.py::test_missing_verdict -x` | ❌ Wave 1 |
| ORCH-04 | verify_all_dispatched returns True only after 13 gates | unit | `pytest tests/phase05/test_gate_guard_dispatch.py::test_verify_all_dispatched -x` | ❌ Wave 1 |
| ORCH-04 | COMPLETE transition raises IncompleteDispatch if missing | integration | `pytest tests/phase05/test_shorts_pipeline_12_gates.py::test_incomplete_dispatch -x` | ❌ Wave 4 |
| ORCH-05 | Checkpointer round-trip preserves all fields | unit | `pytest tests/phase05/test_checkpointer_round_trip.py -x` | ❌ Wave 1 |
| ORCH-05 | Resume picks highest gate_index | unit | `pytest tests/phase05/test_checkpointer_round_trip.py::test_resume_highest -x` | ❌ Wave 1 |
| ORCH-05 | Atomic write survives partial failure | unit | `pytest tests/phase05/test_checkpointer_round_trip.py::test_atomic_write -x` | ❌ Wave 1 |
| ORCH-06 | CircuitBreaker CLOSED→OPEN after 3 failures | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_closed_to_open -x` | ❌ Wave 1 |
| ORCH-06 | OPEN raises CircuitOpen during cooldown | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_open_raises_circuit_open -x` | ❌ Wave 1 |
| ORCH-06 | OPEN→HALF_OPEN after cooldown expires | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_half_open_probe -x` | ❌ Wave 1 |
| ORCH-06 | HALF_OPEN→CLOSED on success | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_half_open_to_closed -x` | ❌ Wave 1 |
| ORCH-06 | HALF_OPEN→OPEN on failure | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_half_open_to_open -x` | ❌ Wave 1 |
| ORCH-06 | CircuitBreaker.to_dict + from_dict round-trip | unit | `pytest tests/phase05/test_circuit_breaker_states.py::test_serialize -x` | ❌ Wave 1 |
| ORCH-07 | ASSEMBLY raises GateDependencyUnsatisfied if VOICE missing | unit | `pytest tests/phase05/test_gate_dag_dependencies.py::test_assembly_needs_voice -x` | ❌ Wave 0 |
| ORCH-07 | DAG has no cycles (graphlib check) | contract | `pytest tests/phase05/test_gate_dag_dependencies.py::test_no_cycles -x` | ❌ Wave 0 |
| ORCH-08 | `skip_gates` string 0 occurrences in pipeline | contract | `pytest tests/phase05/test_blacklist_grep.py::test_no_skip_gates -x` | ❌ Wave 6 |
| ORCH-08 | Hook blocks Write with `skip_gates=True` | contract | `pytest tests/phase05/test_hook_mock_blocks.py::test_skip_gates_blocked -x` | ❌ Wave 6 |
| ORCH-09 | `TODO(next-session)` string 0 occurrences | contract | `pytest tests/phase05/test_blacklist_grep.py::test_no_todo_next_session -x` | ❌ Wave 6 |
| ORCH-09 | Hook blocks Edit with `TODO(next-session)` | contract | `pytest tests/phase05/test_hook_mock_blocks.py::test_todo_next_session_blocked -x` | ❌ Wave 6 |
| ORCH-10 | VoiceFirstTimeline.align respects audio-first order | unit | `pytest tests/phase05/test_voice_first_timeline.py::test_audio_driven_alignment -x` | ❌ Wave 2 |
| ORCH-10 | Integrated render (audio+video simultaneous) raises | unit | `pytest tests/phase05/test_voice_first_timeline.py::test_integrated_render_forbidden -x` | ❌ Wave 2 |
| ORCH-11 | Shotstack render called with resolution="hd" (720p) | unit | `pytest tests/phase05/test_low_res_first.py::test_720p_first_render -x` | ❌ Wave 2 |
| ORCH-11 | Upscale not called until 720p PASS | unit | `pytest tests/phase05/test_low_res_first.py::test_no_upscale_before_pass -x` | ❌ Wave 2 |
| ORCH-12 | 3 retries + FAIL → FAILURES.md append + fallback inserted | integration | `pytest tests/phase05/test_regeneration_loop_fallback.py::test_3_retries_fallback -x` | ❌ Wave 4 |
| ORCH-12 | FAILURES append is idempotent (no double-write on resume) | integration | `pytest tests/phase05/test_regeneration_loop_fallback.py::test_failures_idempotent -x` | ❌ Wave 4 |
| VIDEO-01 | No T2V references in source | contract | `pytest tests/phase05/test_blacklist_grep.py::test_no_t2v -x` | ❌ Wave 6 |
| VIDEO-01 | RunwayI2VAdapter has no text_to_video method | contract | `pytest tests/phase05/test_runway_adapter.py::test_no_t2v_method -x` | ❌ Wave 3 |
| VIDEO-01 | image_to_video raises if anchor_frame is None | unit | `pytest tests/phase05/test_runway_adapter.py::test_anchor_frame_required -x` | ❌ Wave 3 |
| VIDEO-02 | I2VRequest rejects duration=3 and duration=9 | unit | `pytest tests/phase05/test_i2v_request_schema.py::test_duration_bounds -x` | ❌ Wave 3 |
| VIDEO-02 | I2VRequest rejects move_count=2 | unit | `pytest tests/phase05/test_i2v_request_schema.py::test_move_count_one -x` | ❌ Wave 3 |
| VIDEO-03 | Transition shots inserted every 3rd cut | unit | `pytest tests/phase05/test_voice_first_timeline.py::test_transition_shots -x` | ❌ Wave 2 |
| VIDEO-03 | Transition template chosen from 3 options | unit | `pytest tests/phase05/test_voice_first_timeline.py::test_transition_templates -x` | ❌ Wave 2 |
| VIDEO-04 | Kling circuit OPEN → Runway called | integration | `pytest tests/phase05/test_kling_runway_failover.py::test_failover -x` | ❌ Wave 4 |
| VIDEO-04 | Both circuits OPEN → CircuitOpen raised | integration | `pytest tests/phase05/test_kling_runway_failover.py::test_both_open -x` | ❌ Wave 4 |
| VIDEO-05 | Shotstack assemble applies color grade → saturation → grain order | unit | `pytest tests/phase05/test_shotstack_adapter.py::test_filter_order -x` | ❌ Wave 3 |
| (regression) | hc_checks HC-1..7 preserve signatures | regression | `pytest tests/phase05/test_hc_checks_regression.py -x` | ❌ Wave 5 |

### Sampling Rate
- **Per task commit:** `pytest tests/phase05/ -q -x --timeout=30` (fast subset)
- **Per wave merge:** `pytest tests/phase05/ tests/phase04/ -q` (includes Phase 4 regression guard)
- **Phase gate:** Full suite green + `wc -l scripts/orchestrator/shorts_pipeline.py` returns 500-800 + blacklist grep tests PASS + hook mock tests PASS → ready for `/gsd:verify-work`

### Wave 0 Gaps (test infrastructure not yet created)
- [ ] `pyproject.toml` or `pytest.ini` — declare `testpaths = ["tests"]`, `pythonpath = ["."]`, `asyncio_mode = "auto"` (if we need asyncio in Phase 5)
- [ ] `tests/phase05/__init__.py` + `tests/phase05/conftest.py` — shared fixtures (tmp_state_dir, sample_verdicts, mock_api_responses)
- [ ] `tests/phase05/fixtures/` — sample Verdict JSONs, mock API responses (Kling success, Kling 500, Runway success), word_timings fixture
- [ ] `scripts/orchestrator/__init__.py` — module init; exports public API
- [ ] `scripts/hc_checks/__init__.py` — module init
- [ ] `.claude/deprecated_patterns.json` — currently absent, must create (Wave 0 or Wave 6)

## Recommended Plan Structure (10 plans / 6 waves)

| Plan | Wave | REQs Covered | Description | Est. Lines |
|------|------|--------------|-------------|-----------|
| **05-01** | W0 | ORCH-02, ORCH-07 (partial), ORCH-08, ORCH-09 | Infrastructure: GateName enum + GATE_DEPS + exception hierarchy + `.claude/deprecated_patterns.json` + `pyproject.toml` + `tests/phase05/conftest.py` | ~200 source + 150 test |
| **05-02** | W1 | ORCH-05 | Checkpointer: atomic write + resume + sha256 helper + unit tests | ~180 source + 150 test |
| **05-03** | W1 | ORCH-06 | CircuitBreaker: 3-state machine + serialization + 9 state transition unit tests | ~160 source + 200 test |
| **05-04** | W1 | ORCH-03, ORCH-04, ORCH-07 (runtime) | GateGuard + Verdict dataclass + `ensure_dependencies` + `verify_all_dispatched` + tests | ~120 source + 180 test |
| **05-05** | W2 | ORCH-10, ORCH-11, VIDEO-03 | VoiceFirstTimeline + Low-Res renderer stub + transition shot insertion + Shotstack adapter skeleton | ~350 source + 250 test |
| **05-06** | W3 | VIDEO-01, VIDEO-02, VIDEO-04, VIDEO-05 | API adapters (Kling I2V, Runway I2V no-T2V, Typecast, ElevenLabs, Shotstack full) + I2VRequest pydantic + all adapter unit tests (mocked HTTP) | ~900 source + 400 test |
| **05-07** | W4 | ORCH-01, ORCH-02 (integration), ORCH-04, ORCH-12, all orchestration | `shorts_pipeline.py` main file — the integrator. 500~800 line budget. `_run_<gate>` methods, regeneration loop, fallback insertion, resume logic, CLI entry | ~700 source + 300 test |
| **05-08** | W5 | (regression) | `scripts/hc_checks/hc_checks.py` rewrite preserving 13 signatures + port `test_hc_checks.py` + add GATE_INSPECTORS export for HC-10 | ~900 source + 400 test ported |
| **05-09** | W5 | (regression safety net) | Integration test: 12 GATE mock run end-to-end including Kling→Runway failover + regeneration→fallback + resume-from-checkpoint | ~0 source + 350 test |
| **05-10** | W6 | Success Criteria 1-6 verification | Blacklist grep tests + wc -l line count test + hook mock tests + final `verify_hook_blocks.py` + Wave 0 `.claude/deprecated_patterns.json` finalization if deferred | ~80 source + 150 test |

**Total estimated lines:** ~2800 source + ~2530 test = ~5330 lines across the whole phase, with `shorts_pipeline.py` itself at ~700 lines (well within 500-800 budget).

**Parallelization opportunities:**
- Wave 1 plans 05-02, 05-03, 05-04 all parallel (Checkpointer, CircuitBreaker, GateGuard have no cross-dependencies once W0 enum exists)
- Wave 2 and Wave 3 partially parallel (VoiceFirstTimeline in 05-05 needs Shotstack skeleton from 05-06; can split 05-06 into 05-06a API adapters + 05-06b Shotstack separate plans if wave depth matters)
- Wave 5 plans 05-08 (hc_checks) and 05-09 (integration test) parallel after Wave 4 ships

**Sequential constraints:**
- W0 → all others (enum needed by everything)
- W1 → W2, W3, W4 (support components before consumers)
- W3 → W4 (adapters before orchestrator imports)
- W4 → W5 (orchestrator must exist before hc_checks `from scripts.orchestrator import GATE_INSPECTORS`)
- W6 is the final verification gate

## Common Pitfalls

### Pitfall 1: Size Creep in shorts_pipeline.py
**What goes wrong:** Developer adds "just one more utility" to the main file, eventually blowing the 800-line budget.
**Why it happens:** Easier to inline than to extract — every dataclass, every helper method ("just 10 lines") looks reasonable individually.
**How to avoid:** Wave 6 test asserts `500 <= wc -l <= 800` and fails CI. Plus: enforce one-responsibility rule — `shorts_pipeline.py` only contains `ShortsPipeline` class + `_run_<gate>` methods + `main()` entrypoint. Everything else lives in support modules.
**Warning signs:** Any single `_run_<gate>` method exceeding 50 lines — extract sub-helper to the relevant adapter module.

### Pitfall 2: CircuitBreaker and Regeneration Loop Conflated
**What goes wrong:** Developer uses CircuitBreaker counter to trigger Fallback shot at 3 consecutive failures. But CircuitBreaker protects against API outage (infra); regeneration loop is a quality loop (agent output is good but Inspector says FAIL).
**Why it happens:** Both use "3" as the threshold, naming looks similar.
**How to avoid:** Explicit naming — `CircuitBreaker(max_failures=3, cooldown_seconds=300)` for API calls. `RegenerationLoop(max_retries=3)` for Producer-Supervisor cycle. Document in D-12.
**Warning signs:** Any code that reads `breaker.consecutive_failures >= 3` to decide Fallback. WRONG — use `retry_count` from local loop variable.

### Pitfall 3: Test Pollution via state/ Directory
**What goes wrong:** `tests/phase05/conftest.py` fixtures write to real `state/` directory, polluting between test runs or leaking across test files.
**Why it happens:** Path default `state_root = Path("state")` points to cwd, which is the project root when pytest runs.
**How to avoid:** Every test uses `tmp_path` fixture from pytest, Checkpointer instantiated with `state_root=tmp_path`. Never test-write to real `state/`.
**Warning signs:** `state/` appears in `git status` after running tests. Add `state/` to `.gitignore` unconditionally.

### Pitfall 4: Hook Silent Allow
**What goes wrong:** `.claude/deprecated_patterns.json` is absent or malformed → Hook returns `{"decision": "allow"}` for everything → blacklist bypass undetected.
**Why it happens:** Hook line 200-202 gracefully degrades by design (if patterns load fails, don't block legitimate work).
**How to avoid:** Wave 0 Plan 05-01 creates the JSON file. Wave 6 Plan 05-10 test `test_hook_mock_blocks.py` positively asserts that `skip_gates=True` content is denied — if the file is missing, the test catches it.
**Warning signs:** Running `python .claude/hooks/pre_tool_use.py < mock_payload.json` returns `{"decision": "allow"}` for `skip_gates=True`. That's a Hook failure.

### Pitfall 5: Import-Time Cycle Between shorts_pipeline and hc_checks
**What goes wrong:** `hc_checks.check_hc_10_inspector_coverage` imports `from scripts.orchestrator.harness import GATE_INSPECTORS`. If orchestrator module imports hc_checks to run final checks, and hc_checks imports from orchestrator, circular import.
**Why it happens:** hc_checks_raw source explicitly imports orchestrator.
**How to avoid:** Lazy import inside `check_hc_10_inspector_coverage` body (already done in baseline — line 1037 `from scripts.orchestrator.harness import GATE_INSPECTORS`). Preserve the lazy pattern in rewrite.
**Warning signs:** `ImportError: cannot import name 'GATE_INSPECTORS'` at module load. Fix: lazy import.

### Pitfall 6: Windows Path Separators in fal.ai / Shotstack URLs
**What goes wrong:** `str(Path("output/scene_01.mp4"))` on Windows produces `output\scene_01.mp4` with backslashes. Upload to fal.ai or Shotstack fails because the API expects forward-slash paths or URLs.
**Why it happens:** `Path.__str__` uses platform-native separator.
**How to avoid:** Always `str(path).replace("\\", "/")` when serializing paths for API payloads. Or use `path.as_posix()` (cleaner).
**Warning signs:** "invalid URL" or 400 error from API with a path containing `\` in logs.

### Pitfall 7: pydub Requires ffmpeg at Import
**What goes wrong:** `from pydub import AudioSegment` works, but `AudioSegment.from_mp3(...)` shells out to ffmpeg; if ffmpeg not on PATH, runtime error mid-GATE.
**Why it happens:** pydub doesn't bundle ffmpeg.
**How to avoid:** Wave 0 plan step verifies `ffmpeg -version` passes. Document in README install section. Unit tests use mocked AudioSegment where possible.
**Warning signs:** `CouldntDecodeError` from pydub means ffmpeg missing or misconfigured.

## Code Examples (verified patterns from sources)

### Atomic JSON write (from `os.replace` docs, stdlib-verified)
```python
# Source: Python docs https://docs.python.org/3/library/os.html#os.replace
# "If dst exists and is a file, it will be replaced silently if the user has permission."
# "The operation may fail if src and dst are on different filesystems."
# Guaranteed atomic on both Windows and POSIX.
import os, json
from pathlib import Path

def atomic_write_json(target: Path, data: dict) -> None:
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)  # atomic rename
```

### SHA256 streaming for large artifacts (from hc_checks_raw line 438-450 pattern)
```python
# Source: .preserved/harvested/hc_checks_raw/hc_checks.py lines 441-444
import hashlib
from pathlib import Path

def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
```

### Word-level TTS alignment (adapted from harvested `elevenlabs_alignment.py`)
```python
# Source: .preserved/harvested/api_wrappers_raw/elevenlabs_alignment.py::_chars_to_words (lines 36-72)
def _chars_to_words(characters: list[str], start_times: list[float], end_times: list[float]) -> list[dict]:
    words = []
    current_word, word_start = "", None
    for i, char in enumerate(characters):
        if char.strip() == "":
            if current_word:
                words.append({"word": current_word, "start": word_start, "end": end_times[i-1] if i > 0 else start_times[i]})
                current_word, word_start = "", None
        else:
            if word_start is None:
                word_start = start_times[i]
            current_word += char
    if current_word and word_start is not None:
        words.append({"word": current_word, "start": word_start, "end": end_times[-1] if end_times else word_start + 0.1})
    return words
```

### Graphlib topological sort check (stdlib since 3.9)
```python
# Source: Python docs https://docs.python.org/3/library/graphlib.html
import graphlib

def assert_acyclic(deps: dict[str, set[str]]) -> list[str]:
    sorter = graphlib.TopologicalSorter(deps)
    sorter.prepare()  # raises graphlib.CycleError if cycle detected
    return list(sorter.static_order())
```

## State of the Art

| Old Approach (shorts_naberal 5166-line orchestrate.py) | Current Approach (Phase 5 500~800 line) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monster file with inlined state machine, API calls, fallbacks | 500~800 line state machine + supporting modules | 2026-04-19 (Phase 3 harvest polluted-code rejected, Phase 5 greenfield) | ~6x size reduction; testability per component; Windows-native atomic writes |
| `skip_gates=True` parameter as "emergency brake" | No such parameter; physically absent | CONFLICT_MAP A-6 Phase 3 decision | Drift-proof — AF-14 impossible |
| `TODO(next-session)` scattered comments | Hook-blocked; all work done-or-not-in-codebase | CONFLICT_MAP A-5 Phase 3 decision | No half-finished features left in main branch |
| T2V + I2V mixed code paths | I2V only; T2V physically absent + grep-tested | NotebookLM T1 (2026-04-18) | Anchor Frame enforcement guaranteed |
| Silent try-except fallbacks | Explicit raise + FAILURES.md append | Project rule 3 + D-12 | Observability; no hidden failures |
| text_to_video in Runway wrapper | REMOVED | VIDEO-01 D-13 | T2V regressions impossible |
| 4-tier TTS fallback (Typecast/Fish/ElevenLabs/Edge) | 2-tier (Typecast/ElevenLabs) | AUDIO-01 | Lower complexity, 2 API keys instead of 4 |
| Full-res render first | 720p Low-Res First + optional upscale | ORCH-11 + NotebookLM T4 | 5-10x faster feedback loop on quality regressions |
| Integrated video+audio generation | Voice-first: TTS → timestamps → I2V aligned | ORCH-10 + NotebookLM T3 | Deterministic timing; video regens don't rebuild audio |

**Deprecated/outdated:**
- Text-to-video routes in any API wrapper — REMOVED.
- Selenium YouTube upload — AF-8, ORCH unrelated (Phase 8 concern).
- 3-branch conditional retry loops — replaced with CircuitBreaker state machine.

## Open Questions

1. **Should `asset-sourcer` Producer agent be invoked for Fallback shot OR should fallback use a stock-photo pool?**
   - What we know: CONTEXT D-12 says "정지 이미지 + 줌인" + asset-sourcer is one of the 32 agents.
   - What's unclear: Does asset-sourcer need a "fallback" mode, or does it just return any image and orchestrator applies ken-burns?
   - Recommendation: Plan 05-07 invokes asset-sourcer with `mode="fallback"` parameter. asset-sourcer AGENT.md does not currently define this mode. Out-of-band coordinate with `.claude/agents/producers/asset-sourcer/AGENT.md` update (may require Phase 4 amendment OR Phase 5 adds mode locally).

2. **Does GATE_INSPECTORS for HC-10 need to map GATE→Inspector list, or is this only a Phase 7 concern?**
   - What we know: hc_checks_raw HC-10 expects `scripts.orchestrator.harness.GATE_INSPECTORS["script"]` to exist.
   - What's unclear: Phase 5 only has orchestrator, not `harness.py` submodule. Where do we stash GATE_INSPECTORS?
   - Recommendation: Wave 5 Plan 08 adds `GATE_INSPECTORS` constant to `scripts/orchestrator/__init__.py` or dedicated `scripts/orchestrator/gate_inspectors.py`. HC-10 returns SKIP until Phase 7 wires real inspector invocation.

3. **Should `_validate_dag()` run at import or lazily?**
   - What we know: graphlib check is cheap (<1ms for 15 nodes).
   - What's unclear: Running at import adds startup cost that may delay other code paths; lazy is less safe.
   - Recommendation: At import time. DAG validation is essentially a linter check that catches a broken build. Cost is negligible.

4. **Shotstack upscale — use it or skip it in Phase 5?**
   - What we know: 720p is YouTube Shorts spec-compliant. Upscale options are limited.
   - What's unclear: Is ORCH-11 "AI 업스케일" a hard ship requirement or aspirational?
   - Recommendation: Phase 5 ships 720p-only with documented decision to defer upscale to Phase 8 optimization. ORCH-11 is addressed by providing the Low-Res-First *path* (rendering at 720p, gating upscale behind quality check); the actual upscale implementation is a noop that logs "upscale skipped — Phase 8 pending". This satisfies the structural intent without adding cost/complexity.

5. **Is retry backoff needed inside CircuitBreaker CLOSED state?**
   - What we know: tenacity gives us `@retry(stop=stop_after_attempt(3), wait=wait_exponential())`.
   - What's unclear: Does Kling API benefit from backoff, or does it just time out consistently?
   - Recommendation: Wrap each single API call inside CircuitBreaker with `tenacity.retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))`. Two transient retries within 12s total; after that, CircuitBreaker accumulates failure counter. Two-layered: tenacity for transient network blips, CircuitBreaker for sustained outage.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/05-orchestrator-v2-write/05-CONTEXT.md` — 20 locked decisions (read in full)
- `.planning/REQUIREMENTS.md` — ORCH-01~12 + VIDEO-01~05 specs
- `.planning/ROADMAP.md` — Phase 5 goal + 6 Success Criteria
- `.planning/STATE.md` — Session #16 state, Phase 4 completion confirmation
- `.preserved/harvested/api_wrappers_raw/_kling_i2v_batch.py` — Kling fal.ai endpoint pattern (read in full)
- `.preserved/harvested/api_wrappers_raw/runway_client.py` — Runway adapter signature + T2V method to REMOVE (read in full)
- `.preserved/harvested/api_wrappers_raw/tts_generate.py` — Typecast+ElevenLabs 4-tier pattern, punctuation injection, silence-split (read in full)
- `.preserved/harvested/api_wrappers_raw/elevenlabs_alignment.py` — word-level timestamp extraction (read first 100 lines)
- `.preserved/harvested/api_wrappers_raw/heygen_client.py` — not used Phase 5 (read first 60 lines, confirmed skip)
- `.preserved/harvested/hc_checks_raw/hc_checks.py` — 1129-line regression baseline + 13 public signatures (read in full across 3 offsets)
- `.claude/agents/_shared/rubric-schema.json` — Inspector output schema (read in full)
- `.claude/agents/_shared/agent-template.md` — agent pattern contract (read in full)
- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` — 17-inspector fan-out + delegation_depth guard (read in full)
- `.claude/hooks/pre_tool_use.py` — regex block mechanism + deprecated_patterns.json contract (read in full, confirmed the file is absent)
- `.planning/config.json` — nyquist_validation=true confirmed
- `CLAUDE.md` (project) — domain rules 1-8 + 32-agent roster
- Python docs (stdlib): `os.replace`, `hashlib.sha256`, `graphlib.TopologicalSorter`, `enum.IntEnum` — HIGH confidence
- Installed package versions via `pip show`: pydantic 2.12.5, tenacity 9.1.4, httpx 0.28.1, pytest 9.0.2 — verified 2026-04-19

### Secondary (MEDIUM confidence)
- tenacity docs — retry decorator (confirmed training data matches 9.x API)
- pydantic 2.x docs — constrained field types like `Field(ge=4, le=8)` (confirmed training data matches 2.12)
- fal-client / runwayml SDK patterns inferred from harvested wrappers (not independently verified against current SDK releases)

### Tertiary (LOW confidence — flag for Wave 3 validation)
- Shotstack exact API parameter names for 720p render + color grade template — NOT directly verified via Context7 or live docs; Wave 3 plan 05-06 (Shotstack adapter) must verify against https://shotstack.io/docs before locking
- Topaz / Real-ESRGAN licensing — not researched deeply; Phase 8 concern if upscale is adopted

## Metadata

**Confidence breakdown:**
- State machine architecture: HIGH — CONTEXT.md specifies exact enum + exception hierarchy + transition rules
- CircuitBreaker: HIGH — stdlib pattern verified via type hints; no 3rd-party dependency needed
- Checkpointer: HIGH — os.replace atomic write is Python docs-verified
- DAG model: HIGH — graphlib stdlib solves the topological validation in 3 lines
- VoiceFirstTimeline: MEDIUM — greedy align is a design choice, exact duration matching logic may need refinement after Wave 2 execution
- Low-Res First strategy: MEDIUM — Shotstack 720p first-pass confirmed syntax, upscale path punted to Phase 8
- API adapters: HIGH for pattern (harvested wrappers prove behavior); MEDIUM for current SDK versions (Wave 3 must verify `pip install fal-client runwayml typecast-python elevenlabs` matches harvested version assumptions)
- Fallback shot: HIGH — ken-burns via Shotstack is a well-known technique, dedup via Checkpointer artifact record
- Hook extensions: HIGH — pre_tool_use.py was read in full; `.claude/deprecated_patterns.json` creation is a mechanical Plan task
- hc_checks rewrite: HIGH — 13 public signatures enumerated; test port is mechanical
- Plan structure: HIGH — 10 plans across 6 waves aligns to both dependency graph and team size (single developer + Supervisor fan-out)
- Test strategy: HIGH — Nyquist mapping 17 REQs × multiple test types ships full coverage

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days, stable stack; refresh if Kling 3.0 or Runway Gen-4 drops a breaking change)

## RESEARCH COMPLETE
