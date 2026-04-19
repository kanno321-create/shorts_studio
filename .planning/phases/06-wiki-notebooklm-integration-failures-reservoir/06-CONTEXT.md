# Phase 6: Wiki + NotebookLM Integration + FAILURES Reservoir — Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Source:** YOLO mode direct authoring (workflow.skip_discuss=true, workflow._auto_chain_active=true — session #13/#14 precedent)
**Authoring method:** Orchestrator-direct (Phase 5 패턴 승계; plan-checker는 researcher/planner 아웃풋 기반 검증)

<domain>
## Phase Boundary

**In-Scope (이 Phase에서 구축):**
- `studios/shorts/wiki/` Tier 2 도메인 특화 노드 실 콘텐츠 (algorithm, ypp, render, kpi, continuity_bible — 각 카테고리 최소 1개 ready 노드)
- NotebookLM 2-노트북 세팅 (일반 노트북 재사용 + 채널바이블 노트북 신규 생성)
- Continuity Bible prefix 자동 주입 메커니즘 (`scripts/orchestrator/api/shotstack.py`의 color/camera preset 직접 주입)
- NotebookLM Fallback Chain 실장 (RAG → grep wiki → hardcoded defaults) + 의도적 fail 시뮬레이션 검증
- `FAILURES.md` append-only 파일 + Hook 차단 regex + SKILL 직접 편집 감지
- `SKILL_HISTORY/` 백업 디렉토리 + `v{n}.md.bak` 자동 생성 훅
- 30일 집계 로직 (패턴 ≥ 3회 감지 → `SKILL.md.candidate` 생성 → 7일 staged rollout state) — dry-run 검증까지만
- Phase 4 에이전트 프롬프트의 `@wiki/shorts/xxx.md` 참조 경로 실주입 (32 agents 전수 순회)

**Out-of-Scope (다른 Phase 이관):**
- Phase 7: E2E mock 파이프라인 통합 테스트 (wiki/NotebookLM 런타임 호출 검증)
- Phase 8: GitHub Private push + YouTube API v3 발행
- Phase 9: KPI 대시보드 + Taste Gate
- Phase 10: 실제 30일 운영 기반 패턴 수집 + SKILL.md.candidate → 승격 실행 (Phase 6은 dry-run까지)
- Tier 1 공유 노드 승격: 성급한 일반화 방지, Phase 10 데이터 수집 후 재검토

**Upstream 의존성:**
- Phase 2 scaffold: `wiki/` 5 카테고리 폴더 + MOC.md 스켈레톤 ✅ 존재
- Phase 3 harvest: `.preserved/harvested/` 55 파일 Tier 3 immutable ✅
- Phase 3 imported failures: `.claude/failures/_imported_from_shorts_naberal.md` 500줄 ✅ (sha256 고정)
- Phase 4 agents: 32개 (17 Inspector + 14 Producer + 1 Supervisor) ✅ 존재 — prompt 수정 대상
- Phase 5 orchestrator: `scripts/orchestrator/shorts_pipeline.py` 787줄 + `scripts/orchestrator/api/shotstack.py` ✅ (Continuity prefix 주입 지점)

</domain>

<decisions>
## Implementation Decisions (Locked)

### Tier 규율 (D-1~D-3)

- **D-1: Tier 2 단독 범위** — `naberal_harness/wiki/`(Tier 1)는 Phase 2 결정 D2-A대로 빈 폴더 유지. 공유 가능성 판단 Phase 10까지 deferred. Phase 6에서 생성되는 모든 노드는 `studios/shorts/wiki/` 아래에만 배치. 성급한 일반화는 shorts 편향을 공용 제약으로 변질시킴.
- **D-2: 5 카테고리 구조 고정** — `algorithm/`, `ypp/`, `render/`, `kpi/`, `continuity_bible/` 5개만. 신규 카테고리 추가 금지 (Phase 6 범위). 카테고리별 MOC.md 기존 `Planned Nodes` checkbox가 실노드 파일로 변환되는 것을 최소 단위로 함.
- **D-3: 노드 참조 포맷 `@wiki/shorts/xxx.md` 고정** — 에이전트 프롬프트에서 절대 경로/상대 경로 혼용 금지. `@wiki/shorts/algorithm/ranking_factors.md` 형식만 허용. Phase 4 32 agents 전수 grep + 교체.

### NotebookLM 2-노트북 분리 (D-4~D-8)

- **D-4: 2-노트북 분리 원칙** — 일반 노트북(리서치/알고리즘/YPP 소스) ≠ 채널바이블 노트북(Continuity prefix 전용). 교차 오염 시 hallucination 재발. 쿼리 대상 노트북 결정은 호출부에서 명시적 노트북 ID 지정.
- **D-5: NotebookLM Fallback Chain 3-tier 필수** — `RAG query → grep wiki/ → hardcoded defaults` 순서로 자동 전환. RAG 단독 의존 시 Google outage = 파이프라인 전체 중단. 의도적 API fail 시뮬레이션으로 fallback 실측 검증 (`test_notebooklm_fallback.py`).
- **D-6: NotebookLM 쿼리 규율 — 완성된 단일 문자열** — `feedback_notebooklm_query.md` 메모리 규칙 준수. 실시간 타이핑·다중 질문 금지. 쿼리는 호출 전 완성된 1개 문자열로 작성 후 browser input에 paste. 한국어 쿼리 허용.
- **D-7: `shorts_naberal/.claude/skills/notebooklm/` 인프라 참조(복사 아님)** — Playwright + browser_state 중복 인증 세션 금지. studios/shorts는 wrapper 스크립트만 작성 + 환경변수로 skill 경로 참조 (`NOTEBOOKLM_SKILL_PATH`). skill 자체 코드는 복제 금지.
- **D-8: library.json 채널바이블 노트북 추가** — 기존 `shorts-production-pipeline-bible` 보존. 신규 `naberal-shorts-channel-bible` 항목 append. 등록 후 최소 1회 query 검증으로 authentication + RAG 동작 증명.

### Continuity Bible Prefix 자동 주입 (D-9~D-10)

- **D-9: ShotstackAdapter color preset 직접 주입** — 수동 복붙 금지. Phase 5 `scripts/orchestrator/api/shotstack.py`의 `DEFAULT_RESOLUTION="hd"` 바로 옆에 `DEFAULT_CONTINUITY_PRESET` dict 추가. 렌더 요청 빌드 시 filter chain 최전단에 자동 삽입. D-17 filter order 준수.
- **D-10: Continuity Bible 5 구성요소** — (a) 색상 팔레트(HEX 3-5색 + warmth), (b) 카메라 렌즈(초점거리 + aperture), (c) 시각적 스타일(photorealistic/cinematic/documentary 중 1개 lock), (d) 한국 시니어 시청자 특성(채도 낮은 톤·깔끔한 구도), (e) BGM 분위기(ambient/tension/uplift 3 preset). wiki 노드 `continuity_bible/channel_identity.md`에 정식 기록 + JSON 직렬화 `continuity_bible/prefix.json` 별도 제공(API adapter가 읽음).

### FAILURES 저수지 규율 (D-11~D-13)

- **D-11: `FAILURES.md` append-only via Hook 차단** — `.claude/deprecated_patterns.json`에 신규 regex 추가: 기존 `FAILURES.md` 라인 수정/삭제 시 write 차단. 새 entry는 파일 끝 append만 허용. Hook subprocess test로 실증.
- **D-12: `SKILL_HISTORY/{skill_name}/v{n}.md.bak` 백업** — SKILL 파일 수정 감지 훅이 수정 직전 기존 버전을 `SKILL_HISTORY/<skill>/v<timestamp>.md.bak`로 복사. 복구 가능성 보장. Phase 10 첫 1~2개월 SKILL patch 금지 기간 규율(FAIL-04)과 연동.
- **D-13: 30-day 집계 dry-run** — `scripts/failures/aggregate_patterns.py` CLI 작성. input=`FAILURES.md` + `_imported_from_shorts_naberal.md`. 패턴 키 해시 기반 카운트 → ≥3 발견 시 `SKILL.md.candidate` + 7-day staged rollout state 기록. Phase 6에서는 **dry-run 출력만** 검증. 실 승격은 Phase 10.

### 기존 자산 보존 (D-14)

- **D-14: `_imported_from_shorts_naberal.md` 500줄 완전 불변** — Phase 3 sha256=978bb938... 고정. Phase 6에서 FAILURES 구조화 시에도 이 파일의 **원본 라인 수정 금지**. 구조화(카테고리 태깅/index) 필요 시 별도 `FAILURES_INDEX.md` 파일로 제공.

### SKILL 슬림화 (D-15)

- **D-15: SKILL.md ≤500줄 본문 + 나머지는 wiki 참조** — Lost in the Middle 완화 (RULER 벤치마크 기반). SKILL 500줄 초과 시 harness-audit(Phase 7)에서 A급 drift 경고. Phase 6에서는 기존 SKILL 파일 실측만 수행(위반 시 Phase 9 개선 대상으로 deferred-items.md 기록).

### 한국 시장 특화 (D-16)

- **D-16: 한국 시니어/저관여 B2C 시청자 반영** — 3초 hook, 질문형 제목 패턴, 존댓말/반말 스위칭(스크립터), KOMCA 저작권 준수, Typecast TTS 1위 고정. 채널바이블 노트북에 이 컨텍스트 명시 포함. NotebookLM 쿼리 기본 언어 = 한국어.

### 노드 메타데이터 (D-17)

- **D-17: Wiki 노드 frontmatter 스키마** — `category: <algorithm|ypp|render|kpi|continuity_bible>`, `status: <stub|ready>`, `tags: [...]`, `updated: YYYY-MM-DD`, `source_notebook: <notebook_id>` 필드 필수. 기존 MOC.md 스키마 연속성 유지. `status=ready`만 에이전트 참조 가능(`status=stub`은 WIP).

### Phase 4 Agent Prompt 주입 (D-18)

- **D-18: Phase 6에서 32 agents prompt 전수 수정** — Phase 7 이관 금지. wiki 노드와 agent prompt는 pair로 완성되어야 downstream verification이 의미를 가짐. 수정 대상: `.claude/agents/**/*.md` 에서 기존 placeholder(TBD/Phase 6) → 실 `@wiki/shorts/xxx.md` 참조 교체. 교체 전후 prompt 길이 delta 기록.

### Shotstack 주입 지점 (D-19~D-20)

- **D-19: Shotstack filter order 고정 (D-17 Phase 5 준수)** — ContinuityPrefix filter = first in chain. 기존 Phase 5 filter order 계약 유지: `continuity_prefix → color_correction → stabilize → ken_burns(fallback시)`. 순서 위반 시 pytest 실패.
- **D-20: Continuity prefix JSON 스키마 pydantic v2 고정** — `scripts/orchestrator/api/models.py`에 `ContinuityPrefix` 클래스 추가 (color_palette: list[HexColor], focal_length_mm: int, aperture_f: float, visual_style: Literal["photorealistic","cinematic","documentary"], audience_profile: str, bgm_mood: Literal["ambient","tension","uplift"]). Shotstack adapter가 이 객체를 소비.

### Claude's Discretion (명시적 위임)

- 각 카테고리 내 실노드 파일명·개수(최소 1개 ready). 단 `continuity_bible/channel_identity.md`는 D-10 구성요소 5개 포함 필수.
- NotebookLM query wrapper 위치: `scripts/notebooklm/query.py` vs `scripts/wiki/notebooklm_query.py` — planner 판단.
- FAILURES 30-day aggregation CLI 파일 경로: planner 판단(단 `scripts/failures/` 아래).
- Hook subprocess test 파일 위치: `tests/phase06/` (Phase 5 패턴 승계).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 규율 & 정체성
- `../../../harness/wiki/README.md` — Tier 1 빈 폴더 증거(D-1 근거)
- `.planning/ROADMAP.md §Phase 6` — goal + 6 SC + REQ IDs
- `.planning/REQUIREMENTS.md §WIKI-01~06 + §FAIL-01~03` — 9 REQ 상세

### Phase 2~5 산출물
- `wiki/README.md` — 5 카테고리 맵 + NotebookLM 연동 계획
- `wiki/{algorithm,ypp,render,kpi,continuity_bible}/MOC.md` — Planned Nodes 체크박스(이 Phase에서 채움)
- `.preserved/harvested/` — Tier 3 불변 아카이브(읽기 전용 참조)
- `.claude/failures/_imported_from_shorts_naberal.md` — 500줄 Phase 3 imported(수정 금지)
- `.claude/deprecated_patterns.json` — Phase 5 6 regex + 이 Phase에서 2개 추가(FAILURES write, SKILL direct edit)
- `scripts/orchestrator/api/shotstack.py` — Continuity prefix 주입 대상
- `scripts/orchestrator/api/models.py` — ContinuityPrefix pydantic 클래스 추가
- `scripts/hook/pre_tool_use.py` — Hook 확장 지점

### 외부 skill 참조 (복사 금지)
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/SKILL.md` — NotebookLM skill spec(읽기 전용)
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/scripts/run.py` — wrapper 호출 규격
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json` — 2 노트북 등록 포맷

### 메모리 규칙(C:/Users/PC/.claude/projects/.../memory/)
- `feedback_notebookllm_query.md` — 단일 문자열 쿼리 규칙(D-6)
- `feedback_yolo_no_questions.md` — YOLO 기조 승계(CONTEXT 직접 작성 근거)

### 운영 문서
- `CLAUDE.md` (studios/shorts 루트) — 프로젝트 규율
- `.planning/STATE.md` — 현재 Phase position

</canonical_refs>

<specifics>
## Specific Ideas

### Wiki 실노드 우선순위 (D-2 준수, 최소 1개 ready per category)

| Category | Required ready node(s) | Source |
|----------|-----------------------|--------|
| `algorithm/` | `ranking_factors.md` | MOC Planned Nodes #1 |
| `ypp/` | `entry_conditions.md` | Phase 2 research SUMMARY §YPP |
| `render/` | `remotion_kling_stack.md` | Phase 3 harvested remotion/src |
| `kpi/` | `retention_3second_hook.md` | Phase 4 rubric JSON + Phase 5 thumbnail inspector |
| `continuity_bible/` | `channel_identity.md` + `prefix.json` | D-9/D-10 필수 |

### NotebookLM library.json 추가 항목 포맷

```json
"naberal-shorts-channel-bible": {
  "id": "naberal-shorts-channel-bible",
  "url": "[대표님 신규 생성 후 URL 제공]",
  "name": "Naberal Shorts Channel Bible",
  "description": "Continuity Bible prefix 전용. 색상 팔레트 + 카메라 렌즈 + 시각 스타일 + 한국 시니어 타겟팅.",
  "topics": ["continuity","channel-identity","korean-seniors","color-palette","camera-lens"],
  ...
}
```

### FAILURES 구조

```
.claude/failures/
├── _imported_from_shorts_naberal.md  (500줄, UNTOUCHABLE)
├── FAILURES.md                        (NEW, append-only, 신규 실수 기록)
└── FAILURES_INDEX.md                  (NEW, 카테고리 태깅 index — 원본 미수정)

SKILL_HISTORY/
└── <skill_name>/
    ├── v20260419_143000.md.bak
    └── v20260420_090000.md.bak
```

### Hook regex 추가 2건

```json
{
  "pattern": "(?i)^\\s*(#|-|[*])\\s*\\[REMOVED\\]",
  "description": "FAILURES.md entry 삭제 시도 차단 — append-only 규율",
  "blocks": ["Edit","Write"]
},
{
  "pattern": "/SKILL\\.md",
  "description": "SKILL.md 직접 수정 전 SKILL_HISTORY backup 강제 확인",
  "blocks": ["Edit","Write"],
  "requires": "SKILL_HISTORY/{name}/v*.md.bak"
}
```

### Agent prompt 주입 패턴 예시

```diff
- <!-- TBD: Phase 6에서 wiki 노드 참조 주입 -->
+ ## Canonical references
+ - @wiki/shorts/continuity_bible/channel_identity.md
+ - @wiki/shorts/kpi/retention_3second_hook.md
```

</specifics>

<deferred>
## Deferred Ideas

- **Tier 1 공유 노드 승격**: Phase 10 데이터 수집 후 재평가. Phase 6 범위 외 (D-1).
- **실제 30-day 집계 실행**: Phase 10에서 실데이터로. Phase 6는 dry-run 검증까지 (D-13).
- **SKILL 500줄 초과 실제 분할**: Phase 9 deferred-items.md에 기록하고 Phase 9 개선 작업 (D-15).
- **NotebookLM 신규 노트북 URL 확보**: 대표님이 Google NotebookLM 콘솔에서 신규 "채널바이블" 노트북 생성 후 URL 제공 필요. Phase 6 execute 중 blocking 발생 시 placeholder URL로 진행 + deferred-items.md에 실 URL 교체 TODO 기록.
- **NotebookLM authentication refresh**: 기존 `browser_state` 만료 시 재인증 필요 — Phase 6에서 감지 시 대표님에 1회 재인증 요청 후 진행.
- **Continuity prefix를 Kling/Runway adapter에도 주입**: Phase 6은 Shotstack만. Kling/Runway adapter 확장은 Phase 7 통합 테스트에서 필요성 판단.

</deferred>

---

*Phase: 06-wiki-notebooklm-integration-failures-reservoir*
*Context gathered: 2026-04-19 via YOLO orchestrator-direct authoring (skip_discuss=true)*
*Session: #15*
