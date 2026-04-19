# Phase 5: Orchestrator v2 Write — Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Source:** Orchestrator direct authorship (skip_discuss=true, YOLO mode Session #14)

<domain>
## Phase Boundary

Phase 5는 **문서/스펙 → 실행 가능한 Python state machine으로의 궤도 변경**. Phase 1~4가 인프라/도메인/파일이관/에이전트 스펙이었다면, Phase 5는 shorts_pipeline.py 단일 파일 500~800줄 안에 12 GATE DAG + CircuitBreaker + Checkpointer + 영상/음성 분리 합성 + Low-Res First 렌더를 구현한다.

**핵심 딜리버러블:**
- `scripts/orchestrator/shorts_pipeline.py` (500~800줄 단일 파일, 분할 금지)
- `scripts/orchestrator/` 하위 지원 모듈 (wrappers, checkpointer, circuit_breaker, gate_guard, video/audio API adapters)
- regression baseline 이관: `.preserved/harvested/hc_checks_raw/hc_checks.py` → `scripts/hc_checks/hc_checks.py` 재작성 (public 함수 시그니처 보존)
- Python 단위/통합 테스트 (12 GATE transition + CircuitBreaker mock + Checkpointer round-trip + skip_gates 부재 grep + T2V 부재 grep)

**phase_req_ids (MUST cover 17/17):**
- ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, ORCH-08, ORCH-09, ORCH-10, ORCH-11, ORCH-12
- VIDEO-01, VIDEO-02, VIDEO-03, VIDEO-04, VIDEO-05

**Phase 5에서 다루지 않는 것 (out of scope):**
- NotebookLM RAG 통합 자체 (Phase 6 WIKI-03)
- GitHub remote push / YouTube API v3 업로드 (Phase 8)
- E2E mock asset 통합 테스트 (Phase 7)
- KPI Dashboard / Taste Gate (Phase 9)

</domain>

<decisions>
## Implementation Decisions (Locked)

### D-1. Single File Constraint (Non-Negotiable)
- `shorts_pipeline.py` **단일 파일 500~800줄** 상한선.
- 여러 모듈 분할 금지 (state machine 본체). 단, wrappers/adapters/checkpointer/circuit_breaker 등 **지원 파일은 별도 모듈**로 구성 가능.
- 5166줄 drift 재발을 구조적으로 차단하는 임계. 700줄 초과 시 즉시 리팩터링 필요.
- **Why**: Phase 3이 폐기한 orchestrate.py 5166줄의 1/6. 이 숫자가 "충분히 작게 유지하되 의미 있게 전체"의 경계.

### D-2. 12 GATE State Machine (Canonical Order)
Python `enum.Enum` + 명시적 transition table:
```
IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH
  → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE
```
- **총 15 상태** (IDLE/COMPLETE 포함). Success Criteria 1에서 언급된 "12 GATE"는 IDLE/COMPLETE 제외 가동 GATE 수.
- 각 GATE는 (1) Producer 호출 → (2) Inspector 검증 → (3) GateGuard.dispatch() 순.
- 잘못된 전이 시 `InvalidGateTransition` raise.

### D-3. GateGuard.dispatch() 강제 (ORCH-03)
- 시그니처: `GateGuard.dispatch(gate: GateName, verdict: Verdict) -> None`
- `verdict.result == "FAIL"` → `raise GateFailure(gate, evidence=verdict.evidence)`
- 재생성 루프는 호출자가 try/except로 관리.
- Inspector 호출 없이 GATE 통과 시도 → `MissingVerdict` raise.

### D-4. verify_all_dispatched() = COMPLETE 진입 조건 (ORCH-04)
- **모든 인스펙터 17명 + 17 GATE 모두 호출되었음**을 내부 dispatched set으로 추적.
- COMPLETE 전이 시 `verify_all_dispatched()` 가 False → `IncompleteDispatch` raise.
- 세트는 session_id별 분리. 중간 재시작 시 Checkpointer에서 복구.

### D-5. Checkpointer (ORCH-05)
- 경로: `state/{session_id}/gate_{n}.json`
- 저장 시점: GATE 통과 직후 (GateGuard.dispatch 성공 후).
- 스키마:
  ```json
  {
    "session_id": "...",
    "gate": "NICHE",
    "gate_index": 2,
    "timestamp": "2026-04-19T...",
    "verdict": {...},
    "artifacts": {"path": "...", "sha256": "..."}
  }
  ```
- 재시작 시 `Checkpointer.resume(session_id)` → 가장 큰 gate_index 이후부터 재개.

### D-6. CircuitBreaker (ORCH-06)
- 클래스: `CircuitBreaker(name: str, max_failures: int = 3, cooldown_seconds: int = 300)`
- 상태: CLOSED / OPEN / HALF_OPEN.
- 3회 연속 실패 → OPEN (5분 차단) → HALF_OPEN (1회 시도) → 성공=CLOSED, 실패=OPEN 재개.
- Producer/API wrapper 호출마다 CircuitBreaker를 씌워 전파.

### D-7. DAG 의존성 그래프 (ORCH-07)
- 각 GATE는 `depends_on: list[GateName]` 선언.
- 예: `ASSEMBLY` 는 `VOICE + ASSETS` 모두 dispatched=True 요구.
- 선행 GATE 미통과 시 `GateDependencyUnsatisfied` raise.
- NotebookLM T16 참조: 그래프 순회로 유효성 검증.

### D-8. skip_gates 파라미터 물리 제거 (ORCH-08)
- `shorts_pipeline.py` 전체에 `skip_gates` 문자열 **0회** 등장.
- 함수 signature에 `skip_gates` 키워드 **자체 부재**.
- pre_tool_use Hook에 regex `skip_gates\s*=` 차단 등록 (이미 Phase 1 Hook에서 활성).
- 실측 grep + Hook mock 테스트 두 방식으로 검증.

### D-9. TODO(next-session) 물리 차단 (ORCH-09)
- `shorts_pipeline.py` 및 지원 모듈 전체에 `TODO(next-session)` 0회.
- pre_tool_use Hook regex `TODO\s*\(\s*next-session` 차단 (Phase 1 활성).
- 미완 기능은 개별 REQ로 Phase 5+ 이관, 주석 금지.

### D-10. 영상/음성 분리 합성 (ORCH-10 + NotebookLM T3)
- 순서 **강제**: Typecast(TTS) 먼저 → 오디오 타임스탬프 추출 → 영상 cuts 정렬 → Shotstack composite.
- `VoiceFirstTimeline` 클래스로 표현: `audio_segments -> video_cuts.align_to(audio_segments) -> composite()`
- 통합 렌더 (audio + video 동시 generation) **절대 금지**.

### D-11. Low-Res First + AI 업스케일 (ORCH-11 + NotebookLM T4)
- 1차 렌더: 720p (1280×720 for 16:9 / 720×1280 for 9:16).
- 통과 후 Shotstack 또는 별도 업스케일러로 4K 업스케일.
- 720p 통과 시까지 업스케일 호출 금지. CircuitBreaker로 보호.

### D-12. 재생성 루프 3회 → Fallback (ORCH-12 + NotebookLM T8)
- Producer 호출 실패 3회 누적 시:
  1. FAILURES.md에 append (append-only, session_id + gate + evidence).
  2. "정지 이미지 + 줌인" Fallback 샷 자동 삽입 (asset-sourcer 호출 → Shotstack ken-burns effect).
- 카운터는 CircuitBreaker와 독립. CircuitBreaker는 API 장애 보호, 재생성 루프는 품질 루프.

### D-13. T2V 금지 / I2V only + Anchor Frame (VIDEO-01)
- 코드 경로 자체에 `text_to_video` / `t2v` 함수 **부재**.
- `image_to_video(prompt, anchor_frame: Path)` 만 존재.
- Anchor Frame 미지정 시 raise.
- grep으로 `t2v|text_to_video|text2video` 0회 확인.

### D-14. 1 Move Rule + 4~8초 클립 (VIDEO-02)
- I2V 호출 파라미터: `duration_seconds` ∈ [4, 8], `move_count=1`.
- 프롬프트 검증: 카메라 워킹 1개 + 피사체 액션 1개 이상 금지.

### D-15. Transition Shots (VIDEO-03)
- `VoiceFirstTimeline`에 `insert_transition_shots()` 단계 삽입.
- 소품 클로즈업 / 실루엣 / 배경 전환 3 템플릿 중 랜덤 선택.
- 정적 이미지 + 0.5~1초 클립 조합으로 구성.

### D-16. Kling 2.6 Pro primary + Runway Gen-3 Alpha Turbo backup (VIDEO-04)
- `KlingI2V.generate(...)` 실패 (CircuitBreaker OPEN) → `RunwayI2V.generate(...)` 자동 폴백.
- API 키 환경변수: `KLING_API_KEY`, `RUNWAY_API_KEY`.
- 실패 모니터링: 실패 수, 평균 응답 시간 Checkpointer에 기록.

### D-17. Shotstack 일괄 색보정 + 필터 (VIDEO-05)
- ASSEMBLY GATE에서 Shotstack template 적용.
- 색보정 프리셋: Continuity Bible 기반 (Phase 6에서 정의될 예정, Phase 5는 placeholder).
- 필터 순서: color grade → saturation → film grain.

### D-18. 기존 자산 재작성 정책
- `.preserved/harvested/api_wrappers_raw/` 은 **레퍼런스만**. `scripts/orchestrator/` 에 재작성 (직접 import 금지).
- `.preserved/harvested/hc_checks_raw/hc_checks.py` 1129줄 public 함수 시그니처 보존하면서 `scripts/hc_checks/hc_checks.py` 재작성.
- 재작성 시 logging, CircuitBreaker, Checkpointer integration 추가.

### D-19. Python 버전 + 의존성
- Python 3.11+ (match_case, walrus, typing.Self 사용).
- 필수: `requests`, `pydantic>=2.0` (검증 계약), `httpx` (async API 호출), `tenacity` (CircuitBreaker 보완).
- 금지: `selenium` (AF-8 이미 차단), `eventlet`, `celery` (과도한 의존성).

### D-20. 테스트 범위 (Phase 5)
- 단위: CircuitBreaker 상태 전이, Checkpointer round-trip, GateGuard.dispatch raise 동작, GATE DAG 의존성 검증.
- 통합 (mock): 12 GATE 순차 실행, 재생성 루프 3회 → Fallback, Kling primary → Runway backup.
- Regression: hc_checks.py 기존 테스트 전체 이식 (test_hc_checks.py).
- 계약 검증: grep 테스트 (skip_gates 0회, t2v 0회, TODO(next-session) 0회).

### Claude's Discretion (구현 세부)
- GATE enum 이름 (`GateName` vs `Gate`), 예외 클래스 이름 (`GateFailure` vs `GateError`) 등 내부 네이밍.
- CircuitBreaker 상태 머신 구현 (decorator vs context manager) 선택.
- Checkpointer 내부 스키마 세부 (json 필드 순서, 버전 포함 여부).
- 로깅 포맷 (structlog vs stdlib logging).
- Wrapper 파일 네이밍 (`kling_i2v.py` vs `kling_client.py`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Guidelines
- `./CLAUDE.md` — shorts_studio 프로젝트 규칙
- `./.planning/ROADMAP.md` — Phase 5 목표 + Success Criteria 6개
- `./.planning/REQUIREMENTS.md` — ORCH-01~12 + VIDEO-01~05 상세

### Phase 3 Harvested (읽기 전용 레퍼런스)
- `.preserved/harvested/api_wrappers_raw/_kling_i2v_batch.py` — Kling I2V batch 로직 레퍼런스 (재작성 대상)
- `.preserved/harvested/api_wrappers_raw/runway_client.py` — Runway wrapper 레퍼런스
- `.preserved/harvested/api_wrappers_raw/tts_generate.py` — Typecast TTS 레퍼런스
- `.preserved/harvested/api_wrappers_raw/elevenlabs_alignment.py` — ElevenLabs fallback 레퍼런스
- `.preserved/harvested/api_wrappers_raw/heygen_client.py` — HeyGen 레퍼런스 (사용 여부 TBD)
- `.preserved/harvested/hc_checks_raw/hc_checks.py` — HC-1~7 + HC-12 regression baseline (1129줄)
- `.preserved/harvested/hc_checks_raw/test_hc_checks.py` — HC 테스트 baseline

### Phase 4 Agent Contracts (Inspector/Producer 호출 규격)
- `.claude/agents/_shared/rubric-schema.json` — Inspector output 계약 (draft-07)
- `.claude/agents/_shared/agent-template.md` — MUST REMEMBER at END 패턴
- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` — 재귀 방지 + 17 fan-out 패턴
- `.claude/agents/inspectors/` 하위 17 AGENT.md — 각 Inspector 호출 규격
- `.claude/agents/producers/` 하위 14 AGENT.md — 각 Producer 호출 규격

### Validation Tools (기존)
- `scripts/validate/harness_audit.py` — 에이전트 감사 (description + MUST REMEMBER position)
- `scripts/validate/grep_gan_contamination.py` — GAN 분리 검증
- `scripts/validate/validate_all_agents.py` — 32 agent validation
- `scripts/validate/rubric_stdlib_validator.py` — draft-07 stdlib 검증

### FAILURES Reservoir
- `.claude/failures/_imported_from_shorts_naberal.md` — 500 lines, Phase 3 이관 + 실패 패턴
- Phase 5 재생성 루프 실패 시 추가 append 대상 (Phase 6 FAIL-01에서 구조 확정 예정)

### Hook 3종 (Phase 1 활성)
- `.claude/hooks/pre_tool_use.py` — skip_gates + TODO(next-session) + selenium + segments[] regex 차단
- `.claude/hooks/post_tool_use.py` — 후처리
- `.claude/hooks/session_start.py` — 자동 감사 발동

</canonical_refs>

<specifics>
## Specific Ideas (Hard Constraints)

### 수치 제약
- shorts_pipeline.py: 500 ≤ lines ≤ 800
- CircuitBreaker: max_failures=3, cooldown_seconds=300
- 재생성 루프 max: 3회 (이후 Fallback)
- Initial render: 720p (1280×720 or 720×1280)
- I2V 클립 길이: 4~8초
- I2V 1 Move Rule: camera_walks=1, subject_actions=1

### Blacklist (Phase 1 Hook 차단 확장)
- `skip_gates` → 0회 등장
- `TODO(next-session)` → 0회 등장
- `t2v` / `text_to_video` / `text2video` → 0회 등장
- `segments[]` → Phase 3 이래 `cuts[]` canonical, 0회 등장
- `selenium` → AF-8 차단

### File Organization
- `scripts/orchestrator/shorts_pipeline.py` — 메인 state machine (500~800줄)
- `scripts/orchestrator/gate_guard.py` — GateGuard + 예외
- `scripts/orchestrator/checkpointer.py` — Checkpointer
- `scripts/orchestrator/circuit_breaker.py` — CircuitBreaker
- `scripts/orchestrator/video_first_timeline.py` — VoiceFirstTimeline (오디오→영상 순서)
- `scripts/orchestrator/api/kling_i2v.py`, `runway_i2v.py`, `shotstack.py`, `typecast.py`, `elevenlabs.py` — API adapters
- `scripts/hc_checks/hc_checks.py` — 재작성 (1129줄 baseline, public 시그니처 보존)
- `tests/phase05/` — 단위/통합/regression 테스트

### Verification Commands (Phase 5 완료 시 반드시 통과)
```bash
# 1. 파일 줄수 검증
wc -l scripts/orchestrator/shorts_pipeline.py  # 500~800 범위

# 2. Blacklist grep 검증
! grep -q "skip_gates" scripts/orchestrator/shorts_pipeline.py
! grep -qiE "t2v|text_to_video|text2video" scripts/orchestrator/
! grep -q "TODO(next-session)" scripts/orchestrator/
! grep -q "segments\[\]" scripts/orchestrator/

# 3. 테스트 실행
python -m pytest tests/phase05/ -q  # 100% PASS 기대

# 4. Hook 차단 실증 (regex mock)
python scripts/validate/verify_hook_blocks.py  # skip_gates= 추가 시도 차단 확인
```

</specifics>

<deferred>
## Deferred Ideas

### Phase 6 이관 (WIKI + NotebookLM + FAILURES Reservoir)
- NotebookLM RAG 쿼리 통합 (shorts_pipeline.py 내부 호출은 placeholder로 남김)
- Continuity Bible 주입 (Shotstack 색보정 프리셋 최종 확정)
- FAILURES.md 구조화 (append-only 스키마 공식화)
- Tier 2 wiki/ 노드 작성

### Phase 7 이관 (Integration Test)
- E2E mock asset 준비 (실제 API 호출 없이 12 GATE 완주)
- verify_all_dispatched() 실측 17/17 검증
- harness-audit 스코어 ≥ 80 상시화

### Phase 8 이관 (Remote + Publishing)
- GitHub push 통합 (공개 레포로 현재 커밋 푸시)
- YouTube API v3 업로드 + AI disclosure 자동 ON
- Reused content 증명 메타데이터 (YPP 진입 조건)

### Phase 9+ 이관
- KPI Dashboard (조회수/CTR/시청 유지율 추적)
- Taste Gate (월 1회 대표님 평가 회로)

### Phase 10 이관
- 주 3~4편 자동 발행 + 첫 1~2개월 SKILL patch 전면 금지
- FAILURES 저수지 누적

</deferred>

---

*Phase: 05-orchestrator-v2-write*
*Context authored: 2026-04-19 — 나베랄 감마 YOLO mode (skip_discuss=true)*
*Session: #14 (post Session #13 Phase 3+4 완결)*
