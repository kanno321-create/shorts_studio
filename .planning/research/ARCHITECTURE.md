# Architecture Research — naberal-shorts-studio

**Domain:** AI-powered YouTube Shorts automated production studio
**Layer 1 Base:** `naberal_harness v1.0.1` (Hook / Dispatcher / Audit 3중 방어선 + 공용 스킬 5개)
**Researched:** 2026-04-18
**Overall confidence:** HIGH (architecture patterns) / MEDIUM (tool integration choices)
**Companion docs:** `STACK.md`, `FEATURES.md`, `PITFALLS.md`, `SUMMARY.md`

---

## 0. Executive Orientation

이 문서는 **`shorts_naberal`에서 실패한 것을 반복하지 않기 위한** 설계도다. 핵심 실패 원인 3가지:

1. **5166줄 오케스트레이터** — 텍스트 체크리스트 기반, 에이전트가 "스킵" 결정 가능
2. **32 inspector 과포화** — 동일 항목 3중 검사, 서로 반대 평결 (A-4: unique 60/80/100% 충돌)
3. **TODO(next-session) 4건 미연결** — 문서는 "자동 실행" 선언, 코드는 TODO 잔존 (A-5)

Layer 1의 `naberal_harness v1.0.1`이 **물리적 차단**(pre_tool_use Hook) + **강제 디스패치**(gate-dispatcher 스킬) + **정기 감사**(harness-audit 스킬)의 3중 방어선을 이미 제공한다. Layer 2 Shorts Studio의 과제는:

- Layer 1 인프라에 **올라타서**
- Producer-Reviewer 이중 생성을 **표준 파이프라인으로 고정**하고
- state machine 오케스트레이터로 **자의적 순서 조정 물리 차단**
- 32 → 16~20 inspector 통합 (**rubric JSON Schema 강제**)
- 3-Tier 위키 + NotebookLM RAG로 **지식 재발견 반복 회피**

학계 레퍼런스(FilmAgent ACL 2024, Mind-of-Director arXiv 2603.14790, Omniagent OpenReview 2025)와 89% 일치하는 구조이지만, **PhD 논문 구현이 아닌 10 phase 내 빌드 가능한 pragmatic 적용**이 목표다.

---

## 1. Component Diagram (Ownership & State)

### 1.1 3-Layer 전체 뷰

```
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 1: naberal_harness v1.0.1 (읽기 전용, pull 방식 업데이트)       │
│                                                                       │
│  Hooks 3종         Skills 공용 5개         Scripts CLI                │
│  ├ pre_tool_use    ├ progressive-disc      ├ new_domain.py           │
│  ├ post_tool_use   ├ drift-detection       ├ drift_scan.py           │
│  └ session_start   ├ gate-dispatcher       └ context_audit.py        │
│                    ├ context-compressor                              │
│                    └ harness-audit                                    │
│                                                                       │
│  Templates 5종 (AGENT/SKILL/FAILURES/CLAUDE/gitignore)               │
└──────────────────────────────────────────────────────────────────────┘
                    ↓ scaffold 1회 (new_domain.py)
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 2: studios/shorts/ (이 프로젝트, 독립 git)                      │
│                                                                       │
│  ┌─ Orchestrator (state machine, 500~800줄) ──────────────────────┐  │
│  │  ShortsStateMachine (enum + transitions.py 기반)                │  │
│  │  GateGuard (gate-dispatcher 패턴 - 코드 guard 강제)             │  │
│  │  CircuitBreaker (3회 실패 → cooldown 5분)                       │  │
│  │  Checkpointer (state/{session_id}/{gate}.json)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│       ↓ invoke                                                        │
│  ┌─ Agent Team (12~20명) ─────────────────────────────────────────┐  │
│  │  Supervisor (1명):  shorts-supervisor                            │  │
│  │  Producers  (6~8):  trend-collector → niche-classifier →         │  │
│  │                     researcher (NLM) → scripter → script-polisher │  │
│  │                     → voice-producer → asset-sourcer →           │  │
│  │                     assembler → publisher                        │  │
│  │  Reviewers  (5~7):  rubric-based, 병렬 실행 (Fan-out)            │  │
│  │                     ins-content, ins-style, ins-technical,       │  │
│  │                     ins-compliance, ins-structure, ins-media     │  │
│  │  Harvest    (0~1):  harvest-importer (Phase 3에서만 활성)        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│       ↓ knowledge query                                              │
│  ┌─ Knowledge Layer (3-Tier Wiki + NotebookLM) ───────────────────┐  │
│  │  Tier 1:  naberal_group/harness/wiki/  (공통 지식, 읽기)         │  │
│  │  Tier 2:  studios/shorts/wiki/         (도메인 전용, 쓰기)       │  │
│  │  Tier 3:  studios/shorts/.preserved/harvested/  (불변 아카이브)  │  │
│  │  NotebookLM skill: Tier 2 RAG 쿼리 엔진 (source-grounded)        │  │
│  │  FAILURES.md 저수지: 월 1회 batch → SKILL_HISTORY 버저닝         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│       ↓ feedback                                                      │
│  ┌─ Analytics Loop ────────────────────────────────────────────────┐  │
│  │  YouTube Analytics API → wiki/shorts/kpi_log.md                  │  │
│  │  → 월 1회 Producer 프롬프트 업데이트                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Ownership Table

| Component | Owns (State) | Reads (Input) | Writes (Output) | Who Calls It |
|-----------|--------------|---------------|-----------------|--------------|
| **Orchestrator** | Pipeline state machine, checkpoint DB, session_id | User command, PROJECT.md, config/ | state/{sid}/*.json, logs/ | 대표님 (CLI 또는 `/shorts-run`) |
| **GateGuard** | `dispatched_gates: set[str]` | Orchestrator state | `verify_all_dispatched()` raise | Orchestrator (강제 호출) |
| **CircuitBreaker** | `failure_count: dict[agent, int]`, `cooldown_until` | Agent invocation result | `is_open()` block or `allow()` | Orchestrator pre-invoke |
| **Supervisor** | 에이전트 호출 순서 (state machine 지시) | Orchestrator 현재 state | 다음 agent 이름 반환 (재귀 위임 안 함) | Orchestrator |
| **Producer agents** | 자체 생성물만 (stateless between calls) | 이전 stage output + Tier 1/2 wiki | 구조화 JSON + artifact 파일 | Supervisor |
| **Reviewer agents** | rubric JSON Schema 결과 | Producer output (별도 context — GAN 분리) | InspectorVerdict pydantic | Orchestrator (Fan-out 병렬) |
| **NotebookLM skill** | Tier 2 wiki 인덱스 | Natural language query | Source-grounded 답변 + citations | Producer/Reviewer 누구나 |
| **FAILURES.md** | Append-only 실패 아카이브 | 실패 이벤트 (runtime) | 월 1회 batch → SKILL.md patch | harness-audit 스킬 (월 1회) |
| **KPI logger** | `wiki/shorts/kpi_log.md` | YouTube Analytics API | KPI time series (CTR, retention) | 스케줄러 (주 1회) |

### 1.3 경계 규칙 (Layer 보호)

- **Layer 1 → Layer 2**: 단방향. Layer 2가 Layer 1 수정 금지 (fork 감지 시 drift_scan.py FAIL).
- **Layer 2 → Tier 3 (`.preserved/`)**: **읽기 전용**. Harvest 시에도 원본 수정 금지. Python 심볼릭 링크 또는 `cp -p` 원본 타임스탬프 보존.
- **Reviewer ↔ Producer**: **별도 context**. Reviewer는 Producer의 체인 오브 생각(CoT)을 보지 못함 — "looks good 👍" 자기 확신 방지 (Anthropic GAN 분리 원칙).
- **Orchestrator → Agent**: 1 depth only. Agent가 다른 Agent 호출 금지 (Task tool 재귀 차단 — Anthropic 공식 룰).

---

## 2. Data Flow

### 2.1 Pipeline Stages (State Machine Transitions)

```
[IDLE]
  ↓ /shorts-run "topic" (user)
[GATE_0_TREND]         ← trend-collector (실시간 트렌드 Google Trends/YouTube API)
  ↓ Reviewer: ins-content.topic_viability_check (rubric: CTR 기대치 ≥ baseline)
[GATE_1_NICHE]         ← niche-classifier (4개 니치 — shorts_naberal 승계)
  ↓ Reviewer: ins-structure.niche_fit (rubric: 채널 바이블 일치)
[GATE_2_RESEARCH_NLM]  ← researcher (NotebookLM 2-노트북 RAG 쿼리)
  ↓ Reviewer: ins-content.factcheck (rubric: 출처 ≥ 3, 최근성 ≤ 6개월)
[GATE_3_BLUEPRINT]     ← script-blueprint (plan.json: scene[], hook, CTA)
  ↓ Reviewer: ins-structure.blueprint_compliance (JSON schema 검증)
[GATE_4_SCRIPT]        ← scripter (Tier 2 바이블 + blueprint → narration)
  ↓ Reviewer: ins-content.script_quality + ins-style.tone (병렬 Fan-out)
[GATE_5_POLISH]        ← script-polisher (tone/grammar/호명 금지 정규식)
  ↓ Reviewer: ins-style.korean_grammar (rubric: 존댓말 일관성)
[GATE_6_VOICE]         ← voice-producer (Typecast/ElevenLabs + WhisperX alignment)
  ↓ Reviewer: ins-technical.audio_quality (LUFS, pause 250ms, tempo 일치)
[GATE_7_ASSETS]        ← asset-sourcer (Runway primary, Veo signature only)
  ↓ Reviewer: ins-media.license + ins-media.diversity (rubric: unique ≥ 80%)
[GATE_8_ASSEMBLY]      ← assembler (Remotion + ffmpeg-python)
  ↓ Reviewer: ins-technical.render_integrity (해상도/FPS/codec)
[GATE_9_THUMBNAIL]     ← thumbnail-designer (CTR 실험용 A/B 3종)
  ↓ Reviewer: ins-style.thumbnail_hook (rubric: 0.3초 가독성)
[GATE_10_METADATA]     ← metadata-seo (제목/설명/태그 SEO)
  ↓ Reviewer: ins-compliance.platform_policy (YouTube Shorts 정책)
[GATE_11_UPLOAD]       ← publisher (YouTube Data API v3, 공식만)
  ↓
[GATE_12_MONITOR]      ← analytics-watcher (24h/7d/30d post-upload 수집)
  ↓
[COMPLETE]             ← KPI 로그 기록, FAILURES 리뷰 대상 체크
```

**핵심 설계 결정:**
- **12개 state**, 각 state 진입 시 **반드시 Reviewer PASS** 필요 → GateGuard가 `verify_all_dispatched()`로 강제
- State transition은 Python enum + `transitions` 라이브러리 (또는 수동 dict) — **텍스트 체크리스트 완전 폐기** (D-7)
- 각 state 완료 시 `state/{session_id}/gate_{n}.json` 저장 → Checkpointer가 실패 시 마지막 successful gate부터 재개
- `skip_gates=True` 같은 우회로 **코드 상 존재하지 않음** — 파라미터 자체를 제거 (pre_tool_use Hook이 재삽입 차단)

### 2.2 Data Artifacts (단일 진실 경로)

```
state/{session_id}/
├── 00_trend.json         (trend-collector output)
├── 01_niche.json         (niche-classifier)
├── 02_research.json      (NotebookLM citations 포함)
├── 03_blueprint.json     (scene[], hook, CTA — canonical schema)
├── 04_script.json        ({cuts: [{narration, duration_ms, source_ref}]})
├── 05_polished.json      (04 + style pass)
├── 06_voice/
│   ├── master.wav
│   └── alignment.json    (WhisperX word-level timestamp)
├── 07_assets/
│   ├── manifest.json     (unique sources list)
│   └── media/*.mp4, *.png
├── 08_render.mp4
├── 09_thumbnails/
│   ├── v1.png, v2.png, v3.png
│   └── variants.json
├── 10_metadata.json      (title, desc, tags, shorts flag)
├── 11_upload_receipt.json (YouTube video_id)
└── 12_analytics.json     (post-publish KPI snapshot)
```

**중요:** `script.json` schema는 **`cuts[]` + `narration`** 로 canonical 고정 (A-2 충돌 해결 방향). 과거 `segments[]/text` 허용하는 `_normalize_script()` 함수는 **삭제** (drift 영구 허용 금지).

### 2.3 지식 쿼리 흐름 (NotebookLM RAG)

```
Producer Agent (e.g., scripter)
  │ needs: "incidents 채널 hook 공식"
  ↓
NotebookLM skill invocation
  │ POST query + Tier 2 wiki folder path
  ↓
NotebookLM (external)
  │ vector search + reranking (Tier 2 문서만)
  ↓
Source-grounded answer
  │ { answer, citations: [wiki/shorts/channel_bibles/incidents.md#hook] }
  ↓
Agent uses answer with citation audit trail
```

**핵심 원칙:** Agent가 **직접 Tier 2 wiki의 원본 md를 읽지 않음**. NotebookLM이 중간에서 (a) 관련 chunk만 반환 (b) source citation 제공 (c) 환각 방지. 이렇게 해야 scripter agent가 "어느 문서의 어느 줄에서 가져왔는지" 투명해진다.

---

## 3. Build Order (Phase 1~10 Dependencies)

### 3.1 크리티컬 경로

```
Phase 1: Scaffold
  ↓ naberal_harness v1.0.1 pull + new_domain.py 실행
  ↓ .claude/hooks/ 3종 설치 (물리적 차단 발동 시작)
  ↓
Phase 2: Domain Definition
  ↓ CLAUDE.md {{TODO}} 치환, DOMAIN_CHECKLIST 1~2 완료
  ↓
Phase 3: Harvest (.preserved/harvested/)  ⭐ AGENT 설계 전에 반드시 먼저
  ↓ shorts_naberal에서 선별 복사 (쓰기 금지)
  ↓ theme-bible, hc_checks 유틸, FAILURES 과거 자산, 작동하는 Remotion src/
  ↓ Tier 3 구축 완료 → Tier 2로 "합성 / 정제"할 원재료 확보
  ↓
Phase 4: Agent Team Design  ⭐ Orchestrator 전에 AGENT 먼저
  ↓ 12~20개 .claude/agents/ 작성 (description + rubric schema)
  ↓ Inspector 통합 (32 → 16~20, §5 참조)
  ↓ 각 SKILL.md ≤ 500줄, MUST REMEMBER 섹션 끝 배치
  ↓
Phase 5: Orchestrator v2 Write
  ↓ scripts/orchestrator/shorts_pipeline.py (500~800줄, state machine)
  ↓ GateGuard, CircuitBreaker, Checkpointer 구현
  ↓ deprecated_patterns.json 등록 (skip_gates, TODO(next-session), segments[])
  ↓
Phase 6: 3-Tier Wiki + NotebookLM 통합
  ↓ Tier 2 wiki 초기 합성 (shorts_naberal raw/ → 정제된 노드)
  ↓ NotebookLM 2-노트북 세팅 + skill invocation wrapper
  ↓ FAILURES.md 저수지 초기 구조 + SKILL_HISTORY/ 디렉토리
  ↓
Phase 7: Integration Test
  ↓ end-to-end 쇼츠 1편 생성 (mock 자산으로 빠르게)
  ↓ guard.verify_all_dispatched() 통과 확인
  ↓ harness-audit 점수 ≥ 80
  ↓
Phase 8: Remote + Git
  ↓ github.com/kanno321-create/shorts_studio push
  ↓
Phase 9: Docs 마감
  ↓ ARCHITECTURE.md, WORK_HANDOFF.md 완성
  ↓
Phase 10: 지속 운영
  ↓ 주 3~4편 자동 발행 시작
  ↓ 월 1회 harness-audit + FAILURES batch 리뷰
  ↓ YouTube Analytics → KPI feedback loop
```

### 3.2 Phase 간 의존성 원칙 (중요한 순서)

| Must Exist First | Before You Can | Rationale |
|------------------|----------------|-----------|
| Hook 3종 설치 (Phase 1) | Phase 2 이후 모든 코드 작성 | pre_tool_use가 deprecated 패턴 실시간 차단 |
| Harvest Tier 3 (Phase 3) | Agent design (Phase 4) | 에이전트가 어떤 과거 자산을 참조할지 알아야 description에 트리거 키워드 포함 가능 |
| Agent description 확정 (Phase 4) | Orchestrator 작성 (Phase 5) | Orchestrator는 agent 이름으로 호출 — 없는 agent는 못 부름 |
| Orchestrator (Phase 5) | Wiki 통합 (Phase 6) | NotebookLM skill 호출 지점이 orchestrator에 존재해야 wiring 가능 |
| Wiki + NotebookLM (Phase 6) | E2E test (Phase 7) | 실제 지식 쿼리 없이는 script 품질 검증 불가 |
| E2E test 통과 (Phase 7) | Remote push (Phase 8) | 깨진 파이프라인을 원격에 올리면 rollback 비용 |

### 3.3 절대 하지 말 것 (역순 금지)

- **Agent를 orchestrator 없이 먼저 구현** → agent description만 만들어 놓고 호출 경로 없음 (shorts_naberal의 A-11 "longform-scripter.md 2곳" 원인)
- **Wiki를 Agent보다 먼저 세팅** → 어떤 질문 패턴이 필요한지 모른 채 Tier 2 구축 = 방대한 노드 + 활용 0
- **Harvest 없이 Agent 설계** → 과거 작동 로직을 재발견하는 3~6개월 낭비 (Brooks, Spolsky Second System Effect)

---

## 4. Skip-Prevention Integration (3중 방어선)

### 4.1 Layer 1 Hook이 차단하는 것 (pre_tool_use.py)

`naberal_group/harness/hooks/pre_tool_use.py` + `studios/shorts/.claude/deprecated_patterns.json`:

```json
{
  "patterns": [
    {"regex": "skip_gates\\s*=\\s*True", "reason": "GATE 강제 호출 위반 (D-7)"},
    {"regex": "TODO\\(next-session\\)", "reason": "미완성 wiring 금지 (A-5)"},
    {"regex": "except\\s+\\w+:\\s*pass", "reason": "try-except 조용한 폴백 금지"},
    {"regex": "segments\\[\\]", "reason": "구 스키마 (A-2 cuts[] canonical)"},
    {"regex": "@shorts-researcher|@shorts-scripter", "reason": "구 진입점 (A-3 NLM primary)"},
    {"regex": "Kling.*[Pp]rimary", "reason": "A-1: Runway primary 확정"},
    {"regex": "mascot\\s*:", "reason": "A-10: 조수로 통일"}
  ]
}
```

**효과:** Write/Edit 전에 Hook이 파일 내용 검사 → 해당 패턴 발견 시 **tool call 차단 + 에러 반환**. Agent는 "어? 저장이 안 되네" 경험 후 고쳐 쓴다. 문서로 "하지 마세요"는 무시되지만 **물리 차단은 무시 불가**.

### 4.2 Layer 2 GateGuard (코드 내부)

```python
# scripts/orchestrator/gate_guard.py (gate-dispatcher 스킬 패턴 구현)
class GateGuard:
    REQUIRED_GATES = {
        "GATE_0_TREND", "GATE_1_NICHE", "GATE_2_RESEARCH_NLM",
        "GATE_3_BLUEPRINT", "GATE_4_SCRIPT", "GATE_5_POLISH",
        "GATE_6_VOICE", "GATE_7_ASSETS", "GATE_8_ASSEMBLY",
        "GATE_9_THUMBNAIL", "GATE_10_METADATA", "GATE_11_UPLOAD"
    }
    def __init__(self):
        self._dispatched: set[str] = set()
    def dispatch(self, gate_name: str, reviewer_verdict: InspectorVerdict):
        if not reviewer_verdict.pass_threshold:
            raise GateFailure(f"{gate_name} Reviewer FAIL: {reviewer_verdict.issues}")
        self._dispatched.add(gate_name)
    def verify_all_dispatched(self):
        missing = self.REQUIRED_GATES - self._dispatched
        if missing:
            raise GateSkipDetected(f"Missing gates: {missing}")
```

**호출 강제 방식:** Orchestrator `run()` 마지막에 `self.guard.verify_all_dispatched()` 호출이 **state machine의 종결 전이 조건**. 이 assertion 통과 없이는 `[COMPLETE]` state 진입 불가. `skip_gates=True` 같은 파라미터가 아예 없다 — 존재 자체를 제거.

### 4.3 Layer 1 Audit (session_start.py + harness-audit 스킬)

매 세션 시작 시 자동 실행:

1. `session_start.py` → 지난 세션의 `state/` 디렉토리 스캔 → 불완전 session 경고
2. `harness-audit` 스킬 → `drift_scan.py` 실행 → A급/B급 drift 점수화
3. 점수 < 80 → 세션 시작 전 대표님에게 "먼저 drift 해결하세요" 알림

**효과:** `shorts_naberal`에서 발생한 "세션 77에서 A-5 TODO 4건 발견됐으나 조치 없이 세션 78 진행" 같은 패턴 차단.

### 4.4 종합: 3-Tier 방어선

| Layer | 방어 방식 | 시점 | 우회 가능성 |
|-------|----------|------|-------------|
| L1 Hook | pre_tool_use 차단 | Write/Edit 직전 | ❌ (Claude Code가 tool call 허용 안 함) |
| L2 GateGuard | 코드 assertion | run() 종결 시 | ❌ (예외 raise = state machine 멈춤) |
| L1 Audit | 세션 시작 경고 | 세션 오픈 | ⚠️ (대표님이 "무시" 가능하지만 누적 경고) |

**shorts_naberal 대비 결정적 차이:** L2 GateGuard는 **코드에 존재**. L1 Hook은 **자동 설치**. 둘 다 "문서에 쓴 규칙"이 아니라 **런타임 enforcement**.

---

## 5. Knowledge Architecture (3-Tier + NotebookLM + FAILURES + SKILL_HISTORY)

### 5.1 3-Tier 위키 구조 (D-1)

```
naberal_group/
├── harness/wiki/                    # Tier 1: 공통 지식 (읽기 전용)
│   ├── patterns/                    #   6가지 agent patterns 참조
│   ├── antipatterns/                #   Second System Effect, lost-in-middle 등
│   └── tools/                       #   ffmpeg, WhisperX, Remotion 공통 레퍼런스
│
└── studios/shorts/
    ├── wiki/                        # Tier 2: Shorts 도메인 전용 (쓰기)
    │   ├── channel_bibles/          #   incidents.md, humor.md, trend.md (합성된)
    │   ├── tts_presets/             #   voice-presets.json 해설 + 채널 매핑
    │   ├── kpi_log.md               #   YouTube Analytics 누적
    │   ├── hook_patterns.md         #   0~3초 훅 공식 카탈로그
    │   └── rubric_library/          #   Inspector 6종의 JSON Schema
    │
    └── .preserved/harvested/        # Tier 3: shorts_naberal 원본 (불변)
        ├── _README.md               #   출처 + 읽기 전용 경고
        ├── theme_bible_raw/         #   원본 복사 (수정 금지)
        ├── hc_checks_raw/           #   작동 검증된 유틸 원본
        ├── FAILURES_history/        #   과거 실패 아카이브 (학습 자산)
        └── remotion_src_raw/        #   작동하는 React 컴포넌트 원본
```

### 5.2 계층별 역할 (쓰기 규칙)

| Tier | 쓰기 주체 | 쓰기 시점 | 읽기 경로 |
|------|----------|-----------|-----------|
| **Tier 1** | `naberal_harness` 저장소 PR (대표님 승인) | 하네스 minor/major 릴리스 시 | 모든 agent, 직접 md 읽기 가능 |
| **Tier 2** | Agent (script-polisher), 월 1회 batch 리뷰 | 월 1회 또는 "승격된 학습" 확정 시 | NotebookLM skill 경유 (RAG) |
| **Tier 3** | 절대 없음 (`chmod -w` 또는 `.gitattributes linguist-vendored`) | Phase 3 1회 이후 금지 | 참조 전용, Tier 2 합성 시 원재료 |

### 5.3 NotebookLM 통합 (D-4)

**왜 Tier 2 wiki를 NotebookLM으로 감싸는가:**
- Agent가 `channel_bibles/incidents.md` 전체를 read → context 수천 토큰 소비 + lost-in-the-middle 발생
- NotebookLM RAG → 관련 chunk만 반환 + **citation 강제** → 환각 방지
- 2-노트북 설정: (A) 일반 지식 노트북 (Tier 2 전체), (B) 채널 바이블 노트북 (channel_bibles/만) — 쿼리별 분리 호출

**호출 예시 (`.claude/skills/notebooklm/SKILL.md` 기반):**
```python
# scripter agent 내부
answer = await nlm.query(
    notebook_id="shorts-channel-bibles",
    query="incidents 채널 Part 1 hook 공식과 시그니처 규칙",
    max_citations=3
)
# → answer.text + answer.sources = [wiki/shorts/channel_bibles/incidents.md#L42-58]
```

**중요:** NotebookLM이 외부 서비스이므로 **장애 시 fallback 경로** 필요:
- Primary: NotebookLM RAG
- Fallback 1: 로컬 키워드 grep → 관련 md 반환 (degraded, citation 약함)
- Fallback 2: 기본 hardcoded 프롬프트 (최소 보장)

Circuit breaker 패턴으로 fallback 자동 전환.

### 5.4 FAILURES.md 저수지 (D-2) — "피드백 즉시 SKILL 수정 금지"

**문제 (shorts_naberal):** 대표님이 "놓지 않았습니다 금지" 피드백 → scripter FAILURES 즉시 수정 → 이후 "아니 조건부 허용" → ins-structure 수정 → **3단 진화하며 충돌 A-8 누적**.

**해결 구조:**

```
studios/shorts/
├── FAILURES.md                      # Append-only, 모든 실패 이벤트 기록
│   └── 형식: {timestamp, event, context, proposed_rule}
│
└── SKILL_HISTORY/                   # SKILL.md 버저닝 (D-5)
    ├── scripter/
    │   ├── v1.0_2026-04-19.md       # 초기
    │   ├── v1.1_2026-05-01.md       # 월 1회 batch 후 업데이트
    │   └── v1.1.candidate.md        # 7일 staged rollout (활성 전)
```

**Workflow:**
1. 런타임 중 실패 발생 → `FAILURES.md`에 event 기록만 (SKILL 수정 안 함)
2. 월 1회 `harness-audit` 스킬이 FAILURES 30일치 집계 → 패턴화된 실패 ≥ 3회 건에 한해 `.candidate.md` 작성
3. 7일 staged rollout → 문제 없으면 `v1.1_2026-05-01.md`로 승격 + 현재 SKILL.md 대체
4. 문제 발생 시 `v1.0` 즉시 rollback (SKILL_HISTORY 존재 덕분)

**이렇게 해야 달성되는 것:** 즉시 수정의 충동을 제도적으로 억제 → A-8 같은 "3단 진화 후 모순 잔존" 원천 차단.

### 5.5 KPI Feedback Loop (Closing the Loop Monthly)

```
YouTube Analytics API
  │ 월 1회 cron (publisher-analytics skill)
  ↓
wiki/shorts/kpi_log.md (Tier 2 append)
  │ {date, video_id, niche, CTR, retention_30s, retention_60s, completion_rate}
  ↓
harness-audit 스킬 (월 1회)
  │ KPI 저성과 패턴 → FAILURES.md에 "proposed_rule" 기록
  ↓
ex: "incidents 채널, hook 2초 이상 → retention_30s < 40% (N=8)"
  │
  ↓ 7일 staged rollout 후
  ↓
scripter/SKILL_HISTORY/v1.2.md에 "incidents hook ≤ 1.5초" 규칙 추가
  ↓
다음 달 Producer가 새 규칙 적용
```

**핵심:** KPI → SKILL.md 수정은 **즉시 아님**. FAILURES 저수지 경유 → batch → 승격. 이로써 "이번 영상 실패 → 프롬프트 긴급 수정 → 다음 영상 다른 문제 → 또 긴급 수정" 악순환 차단.

---

## 6. Inspector Consolidation (32 → 16~20)

### 6.1 shorts_naberal의 32 inspector 문제 진단

**문제 1 — 동일 항목 중복 검증 (A-4):**
- ins-matching: unique ≥ 80%
- ins-duplicate: unique 100%
- video-sourcer 목표: unique 100%
→ 서로 반대 평결 가능 → 오케스트레이터 "PASS? FAIL?" 결정 불가

**문제 2 — 역할 겹침 (B-14):**
- ins-duplicate (파일 중복) vs ins-license (소스 채널 다양성) → 같은 scene-manifest 두 번 검사

**문제 3 — maxTurns 무분류 (B-7):**
- 32개 중 maxTurns 값 1/2/3/15/20/25 총 6가지 분포, 문서화 규칙 없음

### 6.2 통합 전략: "6개 카테고리 × 2~3 rubric per category"

**원칙:** 1 inspector = 1 카테고리 책임. 카테고리 내부는 **rubric JSON Schema**로 다차원 채점. "looks good 👍" 대신 **구조화 verdict**.

```yaml
# 제안 (6 카테고리 × 평균 3 = 18개 = sweet spot 16~20 중간값)

structural_inspectors (3명):
  ins-blueprint-compliance:   # 구 ins-structure 통합
    rubric:
      - scene_count_in_range (2~5 for shorts)
      - hook_exists_first_3s
      - cta_present_last_5s
      - duration_within_spec (50~120s)
  ins-timing-consistency:
    rubric:
      - subtitle_word_timestamp_alignment (±50ms)
      - voice_tempo_matches_preset
      - scene_transitions_no_overlap
  ins-schema-integrity:       # NEW — JSON schema 전용
    rubric:
      - script_json_matches_canonical_schema (cuts[]/narration)
      - no_deprecated_field (segments[], text, mascot)

content_inspectors (3명):
  ins-factcheck:              # 구 ins-factcheck 유지
    rubric:
      - source_count_min_3
      - source_recency_within_6mo
      - cited_claim_coverage ≥ 80%
  ins-narrative-quality:      # 구 ins-duo + ins-hook 통합
    rubric:
      - hook_impact_score (LLM judge, 0~1)
      - assistant_ratio_20_to_35 (if duo channel)
      - narrative_arc_completeness
  ins-korean-naturalness:     # 구 ins-korean-grammar + ins-honor 통합
    rubric:
      - honor_consistency (존댓말)
      - detective_naming_rule (탐정님 호명 금지 regex)
      - signature_phrase_conditional (Part1/마지막만 허용)

style_inspectors (3명):
  ins-tone-brand:
    rubric:
      - tone_matches_channel_bible (NotebookLM query로 검증)
      - brand_voice_consistency
  ins-readability:            # 자막 전용
    rubric:
      - chars_per_line_max_13
      - lines_visible_max_2
      - font_contrast_ratio ≥ 4.5
  ins-thumbnail-hook:
    rubric:
      - readable_at_0.3s (LLM judge)
      - emotional_trigger_present
      - clickbait_not_misleading

compliance_inspectors (3명):
  ins-license:                # 구 ins-license + ins-duplicate 통합 (B-14 해결)
    rubric:
      - asset_license_verified (all clips)
      - source_unique_ratio ≥ 80% (A-4 해결 — 80% 단일 기준)
      - channel_diversity_min_3_sources
  ins-platform-policy:
    rubric:
      - youtube_shorts_eligible
      - no_copyright_music
      - no_reused_content_watermark
  ins-safety:                 # 구 ins-gore + ins-mosaic 통합
    rubric:
      - violence_level ≤ channel_threshold
      - pii_masked (얼굴, 주소, 전화)
      - trauma_sensitivity_flag

technical_inspectors (3명):
  ins-audio-quality:
    rubric:
      - integrated_loudness_LUFS_range (-14 ± 1)
      - peak_dBTP ≤ -1
      - no_clipping_samples
  ins-render-integrity:
    rubric:
      - resolution_1080x1920
      - fps_30_or_60
      - codec_h264_aac
  ins-subtitle-alignment:
    rubric:
      - word_level_timestamp_from_whisperx
      - burn_in_visible
      - no_overflow_edges

media_inspectors (2명, 선택적):  # AI 생성 자산 전용
  ins-mosaic:                  # 이미지 특화 (AI generation artifacts)
    rubric:
      - no_text_artifacts (Nano Banana 등)
      - no_hand_deformation
  ins-gore:                    # 영상 특화
    rubric:
      - no_blood_over_threshold
      - no_jumpscare_unannounced
```

**총합: 17개 inspector** (17 in the 16~20 sweet spot).

### 6.3 maxTurns 표준화

모든 inspector `maxTurns=3` 기본. 예외:
- `ins-factcheck`: 10 (외부 웹 검색 필요)
- `ins-tone-brand`: 5 (NotebookLM query + LLM judge)
- 단순 regex/schema 검사: 1

**규칙 문서화:** `studios/shorts/.claude/agents/inspectors/README.md`에 명시 — B-7 해결.

### 6.4 Rubric 강제 (JSON Schema Pydantic)

```python
# studios/shorts/wiki/rubric_library/base.py
class RubricItem(BaseModel):
    name: str
    pass_condition: Literal["exact", "min", "max", "range", "regex", "llm_judge"]
    value: Any
    weight: float = 1.0

class InspectorVerdict(BaseModel):
    inspector: str
    pass_threshold: bool
    overall_score: float  # 0.0~1.0
    rubric_results: list[RubricResult]
    issues: list[Issue]  # {severity: high|med|low, location, description, suggested_fix}
    confidence: float
    recommended_producer_to_recall: Optional[str]  # e.g., "scripter"

class RubricResult(BaseModel):
    item_name: str
    passed: bool
    actual_value: Any
    expected: Any
    evidence: str  # citation to source / line number
```

**효과:**
- "looks good" 불가능 — 각 rubric item별 evidence 필수
- Orchestrator가 `verdict.recommended_producer_to_recall` 기반 **정확히 누굴 다시 부를지** 결정 (재소환 루프 최소화)
- CircuitBreaker와 결합: 같은 Producer 3회 연속 FAIL → 인간 에스컬레이션

### 6.5 Inspector 병렬 실행 (Fan-out)

각 GATE 마다 관련 inspectors **병렬 호출** (Anthropic 3~5 sweet spot):

```python
# GATE_4_SCRIPT 예시
async def gate_4_review(script_json):
    results = await asyncio.gather(
        invoke_reviewer("ins-narrative-quality", script_json),
        invoke_reviewer("ins-korean-naturalness", script_json),
        invoke_reviewer("ins-tone-brand", script_json),
    )
    aggregated = aggregate_verdicts(results)
    if not aggregated.pass_threshold:
        recall_producers = {r.recommended_producer_to_recall for r in results}
        raise GateFailure("GATE_4", recall=recall_producers)
```

---

## 7. Contrast with shorts_naberal (Explicit What Changes)

### 7.1 아키텍처 비교 표

| 측면 | shorts_naberal (실패) | shorts-studio (이 설계) |
|------|----------------------|-------------------------|
| **Orchestrator 크기** | 5166줄 + TODO(next-session) 4건 | 500~800줄 + state machine (transitions) |
| **Stage 관리** | 텍스트 체크리스트, agent 자율 순서 조정 가능 | Python enum + state machine, 자의적 skip 불가 |
| **Skip 방지** | 문서 "MUST" 지시 (무시 가능) | 3중 방어 (Hook 차단 + GateGuard assert + Audit 경고) |
| **Inspector 수** | 32명, 중복 검증, maxTurns 무분류 | 17명, rubric 기반 카테고리 통합, maxTurns 표준화 |
| **Inspector verdict** | "PASS" / "FAIL" 문자열 | Pydantic InspectorVerdict + rubric 다차원 |
| **Schema 관리** | cuts[]/segments[] 2개 허용 (normalize 함수) | cuts[] canonical 1개, normalize 금지 |
| **지식 관리** | raw/ 직접 read + Tier 구분 없음 | 3-Tier (공통/도메인/preserved) + NotebookLM RAG |
| **실패 반영** | 피드백 즉시 SKILL 수정 → 3단 진화 충돌 | FAILURES 저수지 → 월 1회 batch → staged rollout |
| **Entry point** | @shorts-researcher / @shorts-scripter 직접 호출 | Orchestrator 단일 진입점 → state machine이 agent 호출 |
| **Drift detection** | 수동 `grep -rn` | 자동 drift_scan.py + session_start 감사 |
| **KPI feedback** | 없음 (발행 후 loop closure 없음) | YouTube Analytics → kpi_log.md → 월 1회 SKILL patch |
| **Asset priority** | A-1: Kling vs Runway primary 미확정 | config + deprecated_patterns로 Runway primary 물리 고정 |

### 7.2 drift A급 13건이 이 설계에서 사라지는 이유

| shorts_naberal drift | 이 설계의 해결 메커니즘 |
|----------------------|--------------------------|
| A-1 Kling vs Runway | `deprecated_patterns.json`에 Kling-primary regex 차단 + config 단일 소스 |
| A-2 cuts[] vs segments[] | Pydantic schema canonical + segments[] regex 차단 |
| A-3 shorts-researcher vs NLM | orchestrator state machine `GATE_2_RESEARCH_NLM` 단일 경로 + @shorts-researcher regex 차단 |
| A-4 unique 60/80/100% | ins-license 단일 inspector, 80% 단일 rubric item |
| A-5 TODO(next-session) | pre_tool_use Hook이 TODO 패턴 저장 차단 |
| A-6 skip_gates=True | 파라미터 자체 제거 + regex 차단 |
| A-7 Morgan tempo 0.93/0.97 | config/voice-presets.json 단일 진실 + AGENT.md 숫자 언급 금지 |
| A-8 시그니처 조건부 | rubric_library에 "signature_phrase_conditional" 명시 + NotebookLM citation |
| A-9 탐정님 호명 | ins-korean-naturalness rubric regex item |
| A-10 마스코트 vs 조수 | mascot regex 차단 + config key 통일 |
| A-11 longform-scripter.md 2곳 | root 레벨 agent .md 금지 (STRUCTURE.md Whitelist 외) |
| A-12 create-shorts vs create-video | 이 프로젝트는 쇼츠 전용, 롱폼 out-of-scope |
| A-13 Veo 5개 제약 | config note에 "Runway routine + Veo signature only" 명시 |

### 7.3 "작동하는 것" 보존 (Harvest 전략 — D-8)

버릴 것이 아닌 자산:
- Remotion `src/` 작동 컴포넌트 → Tier 3 원본 보존, Tier 2에 해설
- `hc_checks.py` 유틸 → Harvest (읽기)
- `FAILURES.md` 과거 실패 → Tier 3 archive로 학습 자산 유지
- 채널 바이블 핵심 규칙 → Tier 2로 합성 (단순 복사 ≠ 합성)
- 작동하는 API wrapper (Runway, ElevenLabs) → Harvest + Tier 2 보일러 감싸기

**Brooks/Spolsky "Never rewrite from scratch" 준수:** 학습 자산 100% 보존, 에이전트 정의와 오케스트레이터만 재작성.

---

## 8. Risks & Open Questions (Downstream Consumer 대상)

### 8.1 Roadmap이 고려해야 할 경고

- **Phase 3 Harvest가 Phase 4 agent 설계 이전에 완료되어야 함** — 이를 놓치면 agent description에 트리거 키워드 부실
- **Phase 6 NotebookLM은 외부 서비스 의존** — 장애 대비 fallback skill 필요 (추가 phase 혹은 Phase 6 스코프 확장)
- **Phase 7 E2E test는 mock asset**으로 빠르게 — 실제 Runway/ElevenLabs 비용 투입은 Phase 10 운영 시작 후
- **KPI feedback loop (Phase 10+)는 1~2개월 데이터 수집 후 첫 batch** — 그 전까지는 FAILURES 저수지만 채움

### 8.2 Phase별 research 필요 영역 (PITFALLS 담당과 협의)

| Phase | 필요 리서치 | 이유 |
|-------|------------|------|
| Phase 3 | shorts_naberal raw 자산 인벤토리 | 무엇을 harvest할지 선별 |
| Phase 4 | rubric library 구체 정의 | 17개 inspector 각각의 pass_condition value 확정 |
| Phase 5 | `transitions` Python 라이브러리 또는 수동 state machine 비교 | 500~800줄 내 구현 가능성 |
| Phase 6 | NotebookLM API 한계 (쿼리 rate, 노트북 크기 상한) | 2-노트북 분리 근거 강화 |
| Phase 7 | mock asset 제공 패턴 | E2E test 비용 최소화 |
| Phase 10 | YouTube Analytics API 일일 한도 | cron 설계 |

### 8.3 확신도 낮은 영역 (LOW confidence, 재검증 필요)

- **NotebookLM을 ruff agent가 프로그램적으로 호출 가능한지** — 공식 API 불명, 현재 `.claude/skills/notebooklm/`에 수동 브라우저 자동화 존재. API 여부 재확인 Phase 6
- **`transitions` 라이브러리 성능 / 디버깅 편의성** — shorts_naberal에서는 사용 안 함. 실제 사용 경험 필요
- **17 inspector 총비용** — Fan-out 병렬이라도 월 영상 14편 × 17 inspector 호출 비용 Phase 5에서 calibration 필요

---

## 9. References & Sources

### 9.1 Layer 1 (naberal_harness) 문서
- `naberal_group/harness/docs/ARCHITECTURE.md` — 2-Layer 모델, 5 원칙
- `naberal_group/harness/docs/PATTERNS.md` — 6 agent patterns (Pipeline, Fan-out, Expert Pool, **Producer-Reviewer**, Supervisor, Hierarchical)
- `naberal_group/harness/docs/DOMAIN_CHECKLIST.md` — Phase 1~10 스튜디오 창업 가이드

### 9.2 shorts_naberal 진단 자료
- `shorts_naberal/.planning/research/RESEARCH_REPORT.md` — FilmAgent/Mind-of-Director 89% 일치 분석, 7 area 리서치
- `shorts_naberal/.planning/codebase/CONFLICT_MAP.md` — A급 13 / B급 16 / C급 10 drift 전수

### 9.3 학계 / 공식 문서 (HIGH confidence)
- [FilmAgent (arXiv 2501.12909)](https://arxiv.org/abs/2501.12909) — ACL/SIGGRAPH Asia 2024, 감독/각본가/배우/촬영감독 역할 분담 + iterative feedback
- [Mind-of-Director (arXiv 2603.14790)](https://arxiv.org/abs/2603.14790) — multi-modal + debate-judge-validation cycle, FilmAgent 대비 camera collision 13.7% → 2.1% 감소
- [Omniagent (OpenReview 2025)](https://openreview.net/forum?id=SY78p0rIYt) — DAG → cyclic graph 진화, retry 추가
- Anthropic "Building Effective Agents" — 6 pattern + Evaluator-Optimizer 2-조건
- Anthropic Claude Agent SDK — "gather context → take action → verify work → repeat"
- Liu et al. "Lost in the Middle" (2023) — 30%+ 정확도 감소 정량 증거

### 9.4 Tool / Framework 레퍼런스 (MEDIUM confidence)
- [LangGraph + Claude Agent SDK 2026 Guide](https://www.mager.co/blog/2026-03-07-langgraph-claude-agent-sdk-ultimate-guide/) — 이 프로젝트는 Claude Agent SDK 네이티브 (LangGraph는 참조 패턴만)
- [Obsidian + RAG Agentic (Medium 2026)](https://medium.com/@kauxhik77/obsidian-wikis-and-agentic-rag-which-knowledge-base-gives-you-the-edge-dd496914404e) — Tier 2 wiki + NotebookLM 구조의 근거
- [Obsidian Local RAG 2026 (DEV)](https://dev.to/numbpill3d/the-missing-piece-every-obsidian-user-needs-local-rag-that-actually-works-in-2026-2gfp) — hybrid vector + graph 구조

### 9.5 2026 State of the Art (LOW~MEDIUM)
- [Best Multi-Agent Frameworks 2026 (GuruSup)](https://gurusup.com/blog/best-multi-agent-frameworks-2026) — LangGraph vs CrewAI vs Claude SDK 비교
- [Multi-Agent Frameworks Enterprise 2026 (Adopt)](https://www.adopt.ai/blog/multi-agent-frameworks) — 엔터프라이즈 채택 패턴

---

## 10. Downstream Consumer Signals (for Roadmap synthesis)

**Phase 추천 순서 (SUMMARY.md 합성 시 사용):**

1. **Phase 1~2 (인프라)**: harness pull → CLAUDE.md 치환 → Hook 활성화
2. **Phase 3 (Harvest) ⭐**: agent 설계 **전에** 반드시. 1~2일. .preserved/ 디렉토리 완성 + Tier 3 lockdown
3. **Phase 4 (Agent)**: 17 inspector + 6~8 producer + 1 supervisor. rubric JSON Schema 동시 정의. 3~5일
4. **Phase 5 (Orchestrator)**: state machine + GateGuard + CircuitBreaker. 2~3일
5. **Phase 6 (Wiki + NLM)**: Tier 2 합성 + NotebookLM skill 통합 + FAILURES 구조. 2~3일
6. **Phase 7 (E2E Test)**: mock asset으로 빠른 검증. 1~2일
7. **Phase 8~9 (Remote + Docs)**: 반나절
8. **Phase 10 (운영)**: 주 3~4편 + 월 1회 batch 리뷰

**총 예상 기간:** 2~3주 (대표님 투입 집중도 따라)

**Critical Success Factors:**
- Phase 3 Harvest 건너뛰지 말기 (재발견 3~6개월 낭비 회피)
- Phase 4 rubric 정의를 agent 설계와 **동시에** (나중에 추가 = 커플링 깨짐)
- Phase 6 NotebookLM fallback 반드시 설계 (외부 서비스 의존)
- Phase 10 첫 달은 **데이터 수집만**, SKILL patch 성급히 하지 말 것 (D-2 저수지 원칙)

---

*Last updated: 2026-04-18 — ARCHITECTURE research for naberal-shorts-studio based on naberal_harness v1.0.1 Layer 1 infrastructure.*
