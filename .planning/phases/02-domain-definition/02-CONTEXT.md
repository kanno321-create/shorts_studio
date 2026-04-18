# Phase 2: Domain Definition - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Session:** #12

<domain>
## Phase Boundary

Phase 2는 **도메인 정체성과 물리적 구조의 기준점**을 확정한다. 구체적 deliverables:

1. **3-Tier 위키 디렉토리 물리 생성** — Tier 1(`naberal_harness/wiki/`) / Tier 2(`studios/shorts/wiki/`) / Tier 3(`studios/shorts/.preserved/harvested/`)
2. **naberal_harness/STRUCTURE.md schema bump** — v1.0.0 → v1.1.0 (minor: 새 폴더 `wiki/` 추가)
3. **CLAUDE.md 5개 TODO 치환** — DOMAIN_GOAL / PIPELINE_FLOW / DOMAIN_ABSOLUTE_RULES / hive 목표 / TRIGGER_PHRASES
4. **HARVEST_SCOPE.md 결정서** — CONFLICT_MAP A급 13건 사전 판정 + Phase 3 입력 지침

Phase 2는 "도메인이 무엇을 다루는지 + 어떤 규칙으로 운영되는지 + 무엇을 상속하는지"를 문서화하여 Phase 3(Harvest) 및 Phase 4(Agent Design)가 모호성 없이 시작할 수 있도록 만든다. 실제 컨텐츠 채움은 Phase 6(Wiki + NotebookLM + FAILURES Reservoir)에서 수행.

**Scope guardrail**: Phase 2는 구조/정체성 확정만 수행. Tier 2 wiki 실제 노드 내용 작성, NotebookLM 세팅, Producer/Reviewer 프롬프트 정의는 각각 Phase 6, Phase 4로 분리되어 있으며 이번 phase에서 선제 구현하지 않는다.

</domain>

<decisions>
## Implementation Decisions

### D2-A: Tier 1 Wiki 초기 시드 (Minimal)
- **선택**: 빈 폴더 + README.md만 생성
- **이유**: Phase 6에서 NotebookLM Fallback Chain 실제 가동 시 정확한 노드 구성이 확정됨. 지금 시드 = 나중 갈아엎기 리스크.
- **구현**:
  - `naberal_harness/wiki/` 폴더 생성 (empty directory)
  - `naberal_harness/wiki/README.md` 작성 — Tier 1 정의, 사용 규칙, `studios/<name>/wiki/`와의 관계, fallback chain 설명, 추가 절차(schema bump 필요 명시)
  - 실제 도메인-독립 공용 노드(korean_honorifics_baseline, youtube_api_limits 등)는 **Phase 6에서 FAILURES 저수지 패턴 발견 후 추가**

### D2-B: Tier 2 Wiki Scaffold Depth (Category + MOC Skeleton)
- **선택**: 5 카테고리 폴더 + 각각 MOC.md 스켈레톤 파일
- **이유**: Phase 4 에이전트 prompt가 `@wiki/shorts/<category>/MOC.md` 참조 가능해야 한다. 존재하지 않는 파일을 참조하면 Phase 4 testing 시 조기 발견되지만, Phase 6까지 미루면 Phase 4 에이전트 설계 시 참조 형식 고정 불가능.
- **구현**:
  - 카테고리 5개 물리 생성 (ROADMAP Phase 6 Success Criteria #1 기준):
    1. `studios/shorts/wiki/algorithm/` — YouTube Shorts 추천 알고리즘/ranking factors
    2. `studios/shorts/wiki/ypp/` — YouTube Partner Program 기준 + 진입 조건
    3. `studios/shorts/wiki/render/` — Remotion/Kling/Runway 렌더 파이프라인
    4. `studios/shorts/wiki/kpi/` — 3초 hook retention, 완주율, 평균 시청 지표
    5. `studios/shorts/wiki/continuity_bible/` — 색상 팔레트, 카메라 렌즈, 시각 스타일 prefix
  - 각 카테고리에 `MOC.md` 생성 — 표준 템플릿: 제목, 스코프 한 줄, Planned Nodes 섹션(bullet placeholder), Related 섹션(cross-tier refs placeholder)
  - 루트에 `studios/shorts/wiki/README.md` 작성 — Tier 2 정의 + NotebookLM 2-노트북(일반/채널바이블) 연동 예정 언급

### D2-C: Harvest Scope — A급 13건 사전 판정 (B급/C급은 Phase 3)
- **선택**: Phase 2 HARVEST_SCOPE.md가 CONFLICT_MAP A급 13건만 사전 판정 (승계/폐기/통합-후-재작성 3-way 분류). B급 16건 + C급 10건은 Phase 3 harvest-importer 에이전트가 판정.
- **이유**:
  - A급 = Blocking 수준. 이미 D-1~D-10 + SUMMARY.md Build Order에서 대부분 해결 방향 결정(예: Kling primary, 32→17 inspector, 오케스트레이터 500~800줄). 문서화만 하면 됨.
  - B급/C급은 실제 Harvest 실행 중 맥락 발견되어야 정확 판정 가능. 선제 전수 판정은 Phase 2 부담 + 재작업 리스크.
- **구현**:
  - `HARVEST_SCOPE.md` 구조:
    - § A급 13건 판정 테이블 — `{conflict_id, 요약, 판정(승계/폐기/통합), 근거(D# or SUMMARY §)}`
    - § Harvest Blacklist — `orchestrate.py:1239-1291 skip_gates 블록` 등 금지 import 목록
    - § 4개 raw 디렉토리 매핑 (theme_bible_raw / remotion_src_raw / hc_checks_raw / api_wrappers_raw)
    - § FAILURES 이관 경로 (`.claude/failures/_imported_from_shorts_naberal.md`)
    - § B/C급 Phase 3 위임 지침 — harvest-importer 에이전트가 참조
- **판정 주체**: Claude가 shorts_naberal CONFLICT_MAP + 현 프로젝트 SUMMARY/PROJECT + D-1~D-10 교차 참조로 드래프트 → 대표님이 HARVEST_SCOPE.md 커밋 직전 batch 검토. (yolo 모드 원칙: 단건 approval 금지, batch 승인)

### D2-D: CLAUDE.md 5 TODO 치환 수준 (중간)
- **선택**: 확정된 D-1~D-10만 구체적으로 반영. Phase 4~10에서 결정될 실무 수치는 `TBD (Phase X)` 명시.
- **이유**: D-1~D-10은 이미 확정이라 치환해도 드리프트 없음. 반대로 12 GATE 명칭, 17 inspector 카테고리 세부, 에이전트 수 등은 Phase 4~5 산출물 — 미리 고착하면 Phase 4에서 변경 시 desync 리스크.
- **치환 매핑 (5개)**:
  - **Line 3 DOMAIN_GOAL** (# shorts — AI 영상 제작 아래): "AI 에이전트 팀이 자율 제작하는 주 3~4편 YouTube Shorts로 기존 채널 YPP 궤도 확보. Core Value = 외부 수익 발생 (기술 성공 ≠ 비즈니스 성공)."
  - **Line 41 PIPELINE_FLOW**: state machine 12 GATE 개념 다이어그램 (IDLE → TREND → NICHE → RESEARCH → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE). 단 GATE 이름은 "대표 후보, Phase 5에서 확정" 주석 추가.
  - **Line 45 DOMAIN_ABSOLUTE_RULES**: 8개 Hard Constraint 명시 — skip_gates 금지, TODO(next-session) 금지, try-except 침묵 폴백 금지, T2V 금지(I2V only + Anchor Frame), Selenium 업로드 금지(YouTube Data API v3만), shorts_naberal 원본 수정 금지, KPop 트렌드 음원 직접 사용 금지, 주 3~4편 페이스 준수(봇 패턴 회피).
  - **Line 64 hive 목표**: "주 3~4편 자동 영상 제작 + YPP 진입 궤도(1000구독 + 10M views/년) 확보. TBD(Phase 4): 에이전트 개수·이름 최종 확정."
  - **Line 68 TRIGGER_PHRASES**: "쇼츠 돌려 / 영상 뽑아 / shorts 파이프라인 / YouTube 업로드" (한국어 자연어 4-5개, description 트리거 최적화)

### Claude's Discretion

- Tier 1 README.md 문체·구조 (표준 템플릿)
- Tier 2 카테고리별 MOC.md 내부 placeholder 문구
- HARVEST_SCOPE.md 표 컬럼 순서/디자인
- CLAUDE.md 치환 문장의 세부 문장 구조 (D-1~D-10의 요지 유지)
- `naberal_harness/STRUCTURE.md` 백업 파일명 (`STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak`)

### Folded Todos

(cross_reference_todos에서 매칭된 pending todos 없음 — skip)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### Phase 2 Roadmap & Requirements
- `naberal_group/studios/shorts/.planning/ROADMAP.md` §Phase 2 — Domain Definition goal/REQ/Success Criteria (4개)
- `naberal_group/studios/shorts/.planning/REQUIREMENTS.md` §INFRA-02 — 3-Tier wiki 물리 구조 요구사항
- `naberal_group/studios/shorts/.planning/STATE.md` — Phase 1 완료 증빙 + Phase 2 entry 상태

### Project Vision & Decisions
- `naberal_group/studios/shorts/.planning/PROJECT.md` §Key Decisions — D-1~D-10 (모두 Pending, Phase 2 종료 시 D-1/D-8/D-10 일부 검증)
- `naberal_group/studios/shorts/.planning/research/SUMMARY.md` §10 Build Order — Phase 2/3 분리 논리 + 17 Novel Techniques §14
- `naberal_group/studios/shorts/.planning/research/PITFALLS.md` — 28 pitfalls (Harvest 판정 시 피할 구형 패턴 근거)

### Layer 1 Infrastructure
- `naberal_group/harness/STRUCTURE.md` — schema bump 대상 (v1.0.0 → v1.1.0), amendment_policy 7단계 절차 준수
- `naberal_group/harness/docs/DOMAIN_CHECKLIST.md` — Phase 2 진행 체크리스트
- `naberal_group/harness/docs/ARCHITECTURE.md` — Layer 1 원칙 (Tier 1 wiki 생성 시 준수)
- `naberal_group/harness/scripts/structure_check.py` — Whitelist 준수 검증 유틸 (schema bump 후 재실행 필수)
- `naberal_group/harness/hooks/pre_tool_use.py` — 실시간 차단 룰 (skip_gates, TODO(next-session), 비-whitelist 경로 Write)

### Target Document (Phase 2 직접 수정)
- `naberal_group/studios/shorts/CLAUDE.md` — 5 TODO 치환 대상 (Line 3, 41, 45, 64, 68)

### Harvest Source (Phase 3 입력, Phase 2에서 A급 13건 판정에 사용)
- `shorts_naberal/.planning/codebase/CONFLICT_MAP.md` — A:13/B:16/C:10 드리프트 명세
- `shorts_naberal/.planning/research/RESEARCH_REPORT.md` — 학계 89% 일치 + 32→16~20 inspector 권고
- `shorts_naberal/.planning/research/DECISIONS_TEMPLATE.md` — 15개 아키텍처 결정 체크리스트
- `shorts_naberal/CLAUDE.md` — 기존 도메인 규칙 (Harvest 참조용, 수정 금지)

### Pattern Reference (위키 scaffold 규약 참조)
- `secondjob_naberal/wiki/MOC.md` — Blog 도메인 Tier 2 wiki MOC 패턴 예시
- `secondjob_naberal/wiki/README.md` — wiki README entry 패턴
- `secondjob_naberal/wiki/_templates/` — 4종 노드 템플릿 (node_stub, node_ready, daily_note, post_idea)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`naberal_harness/scripts/structure_check.py`** — STRUCTURE.md Whitelist 위반 탐지. schema bump 후 재실행하여 `wiki/` 신규 폴더가 위반 없이 인식되는지 확인.
- **`naberal_harness/hooks/pre_tool_use.py`** — Write 도구 호출 시 Whitelist 검증 + deprecated 패턴 차단. schema bump 전 Write 시도 시 실시간 차단됨 → **순서 엄수**: STRUCTURE.md 먼저 수정 → 커밋 → wiki/ 폴더 생성.
- **`naberal_harness/templates/CLAUDE.md.template`** — shorts/CLAUDE.md 원본 템플릿. 5 TODO 위치 확인 + placeholder 매칭.
- **`secondjob_naberal/wiki/`** — 27+ 노드 + blog-mastery/ 서브 도메인. Tier 2 MOC 패턴 직접 참조 가능. 단 Blog 도메인 콘텐츠는 이관 대상 아님 (D2-A에서 "빈 폴더 + README만" 결정).

### Established Patterns
- **wiki README 엔트리 패턴** — secondjob_naberal/wiki/README.md가 벤치마크. 용도 1문장 + 사용 규칙 + `_templates/` + `_bases/` 섹션 구조.
- **MOC.md per 카테고리** — Obsidian convention. 제목 + Scope 1문장 + Planned Nodes(bullet) + Related(cross-ref).
- **STRUCTURE.md amendment procedure** — 백업 → schema bump → Whitelist 수정 → 변경 이력 추가 → 커밋 (5-step). STRUCTURE.md:92-110 명시.
- **frontmatter 표준** — secondjob_naberal 노드의 `tags/status/category/updated` YAML 형식. Tier 2 MOC 스켈레톤에 동일 적용.

### Integration Points
- **Phase 4 에이전트 prompts** — `@wiki/shorts/<category>/MOC.md` 경로로 참조 예정. Phase 2가 이 참조 경로를 미리 확보함으로써 Phase 4 prompt 템플릿 고정 가능.
- **Phase 6 NotebookLM 통합** — Tier 2 wiki 실제 노드 채움 + 2-노트북 세팅. Phase 2는 빈 스캐폴드만 제공, 내용은 Phase 6.
- **Phase 3 harvest-importer 에이전트** — HARVEST_SCOPE.md를 입력으로 받아 `.preserved/harvested/` 4 raw 디렉토리 생성 + chmod -w. Phase 2가 Phase 3의 blueprint 상반부를 확정.
- **`.claude/skills/notebooklm/`** — 이미 shorts_studio에 상속됨 (Phase 1). Phase 6에서 2-노트북(일반/채널바이블)으로 세팅 + Tier 2 wiki 노드를 소스로 주입.

</code_context>

<specifics>
## Specific Ideas

- **schema bump 버전**: v1.0.0 → **v1.1.0** (Minor — 새 폴더 `wiki/` 추가 = STRUCTURE.md:104 amendment_policy에 명시된 Minor 조건과 일치). 백업 파일명: `STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak`
- **Tier 1 wiki README 구조** (대표님 승인된 minimal 수준):
  1. 이 폴더의 용도 1문장
  2. `studios/<studio_name>/wiki/`와의 차이 (도메인-독립 vs 도메인-전용)
  3. Fallback Chain 순서 (RAG 실패 → Tier 2 → Tier 1 → hardcoded defaults)
  4. 노드 추가 절차 — "schema bump 필요" 명시
- **Tier 2 카테고리 5개 확정 (ROADMAP Phase 6 SC#1 준거)**:
  1. `algorithm/` — YouTube Shorts 추천 알고리즘 + ranking 요소
  2. `ypp/` — YouTube Partner Program 진입 조건
  3. `render/` — Remotion v4 + Kling 2.6 Pro / Runway Gen-3 Alpha Turbo 렌더 스택
  4. `kpi/` — 3초 hook retention > 60%, 완주율 > 40%, 평균 시청 > 25초 지표 정의
  5. `continuity_bible/` — 색상 팔레트, 카메라 렌즈, 시각적 스타일 prefix (D-1 3-Tier 준수)
- **MOC.md 스켈레톤 표준 포맷**:
  ```
  # [Category Name] - Map of Content
  frontmatter: {category, status: scaffold, updated: 2026-04-19}
  ## Scope
  [1문장]
  ## Planned Nodes
  - (Phase 6에서 채움) TODO
  ## Related
  - Tier 1: (추후)
  - Other Tier 2 categories: (추후)
  ```
- **CONFLICT_MAP A급 13건 판정 근거 soft-mapping** (HARVEST_SCOPE.md에서 확정):
  - Runway vs Kling primary (A-1) → **Kling primary**, Runway backup (STACK.md 확정)
  - shorts-researcher vs NLM-fetcher 진입점 (A-3) → **NLM-fetcher 승계, shorts-researcher 폐기** (D-4 NotebookLM RAG)
  - TODO(next-session) 4건 미연결 (A-5) → **전수 폐기** (pre_tool_use 훅이 이미 차단)
  - 32 inspector 과포화 (A-?) → **16~20명 통합** (SUMMARY §14 + PROJECT.md constraint)
  - orchestrate.py 5166줄 (A-?) → **전수 폐기, 500~800줄 재작성** (D-7 state machine)
  - 나머지 7건 → 드래프트 시 CONFLICT_MAP 실제 로드 후 항목별 판정
- **CLAUDE.md 치환 시 유지 vs 교체 영역**:
  - 유지: Identity 섹션(라인 16~27), 운영 원칙 섹션(라인 97~104), GSD Project 블록(라인 109~133)
  - 교체: 5 TODO 지점 + 하네스 hive 섹션(라인 64~70)
  - 추가 없음 — 기존 섹션 구조 보존

</specifics>

<deferred>
## Deferred Ideas

이번 논의에서 등장했으나 Phase 2 스코프 밖이라 다른 phase로 이관:

### Phase 3 (Harvest)
- **CONFLICT_MAP B급 16건 + C급 10건 전수 판정** — Phase 2는 A급 13건 판정 + 나머지 26건의 위임 지침만 작성. Phase 3 harvest-importer 에이전트가 실제 Harvest 맥락에서 판정.
- **4개 raw 디렉토리 실제 복사 + chmod -w 적용** — Phase 3 실행 작업.
- **`.claude/failures/_imported_from_shorts_naberal.md` 생성** — Phase 3 실행 작업. Phase 2는 경로 매핑만.

### Phase 4 (Agent Team Design)
- **12 GATE 명칭 최종 확정** — Phase 2 CLAUDE.md PIPELINE_FLOW에는 "대표 후보, Phase 5에서 확정" 주석만 포함.
- **17 inspector 6 카테고리 세부** — Phase 4 rubric JSON Schema와 동시 정의 원칙.
- **에이전트 총 개수 12~20명 내 최종 확정** — Phase 4 산출물.

### Phase 6 (Wiki + NotebookLM + FAILURES)
- **Tier 1 wiki 실제 노드 채움** — korean_honorifics_baseline, youtube_api_limits 등. Phase 6 FAILURES Reservoir 패턴 발견 후.
- **Tier 2 wiki 5 카테고리 실제 내용 작성** — Phase 2는 MOC 스켈레톤만, Phase 6에서 본문 작성.
- **NotebookLM 2-노트북(일반/채널바이블) 세팅** — Phase 6 통합 작업.
- **Continuity Bible Prefix 자동 주입 로직** — Phase 6 (D-1 구현).

### 미래 스튜디오 창립 시 (blog/rocket)
- **secondjob_naberal/wiki/의 도메인-독립 노드 추출 및 Tier 1 이관** — 스튜디오 N=3 이상 시 패턴 발견 후 batch 이관. 현재는 Tier 1 빈 폴더 유지.

### Reviewed Todos (not folded)
(cross_reference_todos 매칭 없음 — subsection omitted)

</deferred>

---

*Phase: 02-domain-definition*
*Context gathered: 2026-04-19 (Session #12, 대표님 decisive single-turn approval of all 4 recommended options)*
