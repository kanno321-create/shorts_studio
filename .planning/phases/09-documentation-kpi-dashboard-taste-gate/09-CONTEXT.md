# Phase 9: Documentation + KPI Dashboard + Taste Gate - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning
**Mode:** `--auto` (session #23, YOLO 연속 5세션) — all gray areas auto-resolved with recommended defaults

<domain>
## Phase Boundary

Phase 9는 **인간 감독 체계의 마지막 게이트 설치** phase다. Phase 8까지의 실 발행 가능 상태(Phase 8 완결: 8/8 plans + 6/6 SC + 실제 YouTube upload 2건 검증)를 전제로, 다음 3가지 인프라를 구축한다:

1. **ARCHITECTURE.md** — 신규 세션 30분 내 온보딩 가능한 구조 문서 (12 GATE state machine + 17 inspector 카테고리 + 3-Tier 위키)
2. **KPI 선언 + 추적 템플릿** — `wiki/kpi/kpi_log.md` (3초 retention > 60% / 완주율 > 40% / 평균 시청 > 25초)
3. **Taste Gate 프로토콜 + dry-run** — 월 1회 대표님이 상위 3 / 하위 3 영상 평가 + 결과가 `.claude/failures/FAILURES.md`로 흘러드는 경로 샘플 검증

**명시적 비범위 (scope guardrail):**
- 실제 30일간 KPI 측정 데이터 수집 — Phase 10 (Sustained Operations)에서 발생
- SKILL.md patch 반영 — Phase 10 첫 1~2개월 D-2 저수지 규율로 전면 금지
- YouTube Analytics API 실연동 — 템플릿만 Phase 9, 실 연동은 Phase 10
- 다중 채널 대응 / 커스텀 메트릭 추가 — 후속 phase

</domain>

<decisions>
## Implementation Decisions

### ARCHITECTURE.md 구조 (D-01 ~ D-04)

- **D-01:** **Layered 구조 채택** — `12 GATE state machine → 17 inspector 카테고리 → 3-Tier 위키 → 외부 연동 (YouTube/GitHub/NotebookLM)` 순. ROADMAP SC#1 문구를 그대로 반영하여 검증 가능성을 최대화.
- **D-02:** **Mermaid 다이어그램 사용** — GitHub/VSCode/Obsidian 모두 네이티브 렌더링. 외부 툴 의존 0. 최소 3종 다이어그램 필수:
  1. State machine flow (12 GATE)
  2. Agent team tree (Supervisor → 14 Producer + 17 Inspector)
  3. 3-Tier wiki 구조도 (harness/wiki ← studios/shorts/wiki ← .preserved/harvested/)
- **D-03:** **온보딩 30분 목표는 "Reading time" 기준 측정** — Estimated reading time 필드 + TL;DR 섹션 상단 고정. 섹션별 `⏱ N min` 주석 부착. 총합이 30분 이하여야 SC#1 통과.
- **D-04:** **docs/ARCHITECTURE.md 단일 파일** — 분할 (docs/architecture/*.md) 거부. 이유: 신규 세션이 "어디부터 읽어야 하는가" 혼란 발생 방지. 단일 파일 + 목차 + 외부 링크로 충분.

### KPI 선언 템플릿 (D-05 ~ D-07)

- **D-05:** **`wiki/kpi/kpi_log.md` 경로 확정** — ROADMAP에는 `wiki/shorts/kpi_log.md`라 명시됐으나 실제 wiki 구조는 `wiki/{category}/` 이므로 `wiki/kpi/kpi_log.md`가 정합. wiki/README.md가 이미 5 카테고리 확정 상태.
- **D-06:** **Hybrid 포맷** — (a) Target Declaration 섹션: 3개 KPI 목표 + 측정 방식 + 실패 정의 고정, (b) Monthly Tracking 섹션: YYYY-MM 헤더 테이블 (video_id / title / 3sec_retention / completion_rate / avg_view_sec / taste_gate_rank). SC#2 "목표 선언 + 측정 방식 명시" 동시 충족.
- **D-07:** **측정 방식 소스는 YouTube Analytics API v2 (audienceWatchRatio + averageViewDuration)** — 실제 API 연동은 Phase 10, 템플릿 단계에서는 API endpoint + 필드명 + 갱신 주기(주 1회 일요일 KST)만 선언.

### Taste Gate 프로토콜 (D-08 ~ D-11)

- **D-08:** **Semi-automated 선별 + 수동 평가** — 스크립트가 지난 30일 업로드 영상을 KPI 메트릭(3초 retention 기준)으로 정렬하여 상위 3 / 하위 3 자동 선별. 대표님은 평가 컬럼(품질 1-5 점 + 코멘트)만 작성.
- **D-09:** **평가 폼은 Markdown 단일 파일** — `wiki/kpi/taste_gate_YYYY-MM.md` 형식. Google Form 거부 (외부 의존 + privacy + git 추적 불가). 대표님이 VSCode/Obsidian에서 직접 작성.
- **D-10:** **첫 회 dry-run 데이터 전략** — 실제 30일 영상이 없으므로 **합성 샘플 6개** (title/id/metrics) 로 폼을 미리 채워 제공. 대표님은 dry-run에서 "포맷이 편한가"만 검증. 실 평가는 Phase 10 첫 월에 발생.
- **D-11:** **평가 주기: 매월 1일 KST 09:00 자동 알림** — Phase 10에서 cron으로 자동화하되, Phase 9에서는 프로토콜 문서화만 (`wiki/kpi/taste_gate_protocol.md`).

### FAILURES 피드백 경로 (D-12 ~ D-14)

- **D-12:** **Tagged auto-append 방식** — `scripts/taste_gate/record_feedback.py` 스크립트가 `taste_gate_YYYY-MM.md` 완성본을 파싱하여 `.claude/failures/FAILURES.md` 하단에 `### [taste_gate] YYYY-MM 리뷰 결과` 섹션으로 append. 대표님 수동 복사-붙여넣기 제거.
- **D-13:** **점수 3 이하 항목만 FAILURES 승격** — 상위 3 (보통 4-5점) 은 "유지" 분류로 kpi_log.md에만 기록. 하위 3 중 3점 이하만 FAILURES로 흘러감 → 다음 월 Producer 입력에 영향. 노이즈 방지.
- **D-14:** **샘플 검증 (SC#4)은 합성 데이터로** — dry-run taste_gate 파일 → record_feedback.py 실행 → FAILURES.md에 entry 추가 확인까지 end-to-end 1회 검증. 실 영상 데이터는 Phase 10 첫 월에 발생.

### Claude's Discretion

- Mermaid 다이어그램 내 노드 스타일 / 색상 / 정렬 순서 — Claude 재량
- taste_gate_YYYY-MM.md 내 평가 컬럼 세부 라벨 (예: "품질" vs "완성도" vs "임팩트") — Claude 재량으로 1차 제안, 대표님 dry-run 피드백으로 수정 가능
- 스크립트 에러 메시지 한국어/영어 — 한국어 우선 (기존 harness 관행 준수)
- ARCHITECTURE.md 내 코드 예시 언어 — Python 우선 (프로젝트 표준)

### Folded Todos

_No todos folded — `gsd-tools todo match-phase 9` returned 0 matches._

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher + planner) MUST read these before planning or implementing.**

### Phase Definition
- `.planning/ROADMAP.md` §219-229 — Phase 9 정의, SC 1-4, Depends on Phase 8
- `.planning/REQUIREMENTS.md` — KPI-05 (Taste Gate 월 1회), KPI-06 (3 KPI 목표)

### Prior Phase Context (연쇄 의존)
- `.planning/phases/07-integration-test/07-CONTEXT.md` — 12 GATE + verify_all_dispatched 구조
- `.planning/phases/08-remote-publishing-production-metadata/08-CONTEXT.md` — GitHub + YouTube API 통합, FAILURES 자동화 패턴
- `.planning/phases/04-agent-team-design/04-CONTEXT.md` — 17 inspector + 14 Producer + Supervisor 구조
- `.planning/phases/05-orchestrator-v2-write/05-CONTEXT.md` — state machine 500~800줄 제약

### Wiki 구조 (3-Tier)
- `wiki/README.md` — Tier 2 카테고리 5종 정의 (algorithm/ypp/render/kpi/continuity_bible)
- `wiki/kpi/MOC.md` — KPI 노드 맵 (신규 kpi_log.md 링크 추가 필요)
- `wiki/kpi/retention_3second_hook.md` — 3초 hook 기존 연구 (SC#2 측정 방식 근거)
- `../harness/wiki/README.md` — Tier 1 공용 (한국어 존댓말, YouTube API 한도)
- `.preserved/harvested/` — Tier 3 (읽기 전용, chmod -w 적용)

### FAILURES 저수지 (D-2 규율)
- `.claude/failures/FAILURES.md` — 저수지 엔트리 append 대상
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-CONTEXT.md` — 저수지 패턴 (D-14 sha256 immutable lock)

### 외부 연동 (Phase 8 완결 자산)
- `scripts/publisher/` — YouTube API v3 upload 로직 (taste_gate 선별 시 재사용 가능)
- `scripts/publisher/oauth.py` — OAuth refresh token (Phase 10에서 production 재인증 필요)

### Project 기준
- `.planning/PROJECT.md` §Requirements KPI-related — REQ-09 (KPI-driven feedback loop), REQ-10 (harness-audit ≥ 80)
- `CLAUDE.md` — 나베랄 감마 정체성 + 대표님 성향 (품질 최우선)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`wiki/kpi/MOC.md` + `retention_3second_hook.md`** — 이미 KPI 카테고리 2개 노드 존재. kpi_log.md는 MOC에 링크 추가만 필요.
- **`.claude/failures/FAILURES.md`** — Phase 6에서 D-14 sha256 immutable lock 패턴 확립. taste_gate append 시 이 패턴 준수 필요 (append only, no edit of prior entries).
- **`scripts/publisher/` Phase 8 모듈** — YouTube API wrapper 재사용. `list_videos_last_30d()` 식의 신규 헬퍼만 추가하면 taste_gate 선별 가능.
- **Mermaid 다이어그램 관행** — 기존 wiki/*/MOC.md 일부가 이미 Mermaid 사용 중 (확인 필요, 없으면 신규 도입).

### Established Patterns

- **3-Tier 위키 쓰기 금지 규칙** — Tier 3 (`.preserved/`)는 chmod -w, 읽기만. Phase 9 문서는 모두 Tier 2 (`wiki/kpi/`) + `docs/` 에만 쓰기.
- **NotebookLM 2-노트북 세팅** — 채널바이블 B 노트북은 Continuity Bible 용. Phase 9 ARCHITECTURE.md는 A (일반) 노트북 소스로 추가 고려.
- **GSD 커밋 규율** — phase별 `docs(09):` prefix + phase 종료 전 commit 필수 (`gsd-tools commit` 래퍼 사용).
- **Hook 3종 차단** — `skip_gates=True`, `TODO(next-session)`, try-except 조용한 폴백 — Phase 9 스크립트 작성 시 동일하게 준수.

### Integration Points

- **`.claude/failures/FAILURES.md` 하단 append** — taste_gate 스크립트가 쓰는 유일한 write point. 기존 엔트리는 immutable.
- **`wiki/kpi/MOC.md`** — kpi_log.md 신규 링크 추가 (wiki link graph 보존).
- **`docs/ARCHITECTURE.md`** — 신규 생성. README.md에서 "시작하려면 docs/ARCHITECTURE.md 먼저 읽기" 안내 추가.
- **Phase 10 입력 접점** — kpi_log.md 월별 테이블 + FAILURES.md taste_gate 엔트리가 Phase 10 Producer input.

### Constraints (코드 작성 시)

- **SKILL.md ≤ 500줄** — Phase 9에서 신규 SKILL 생성 시 제약 적용. 단, Phase 9는 대부분 문서이므로 SKILL 신규 작성 가능성 낮음.
- **에이전트 12~20명 sweet spot** — Phase 9는 에이전트 추가 없음 (taste_gate는 스크립트 + 수동 평가).
- **오케스트레이터 500~800줄** — Phase 9는 orchestrator 수정 없음 (기존 state machine 재사용).

</code_context>

<specifics>
## Specific Ideas

- **대표님 원샷 리뷰 UX** — taste_gate_YYYY-MM.md 하나만 열면 평가가 끝나야 함. 6개 영상 × 5분 = 최대 30분 내 완료 가능 설계.
- **합성 샘플 데이터는 현실적으로** — dry-run에서 `title: "테스트용 쇼츠 #1"` 같은 placeholder 금지. 실제 niche (shorts_naberal 승계: 탐정/조수 페르소나) 기반 그럴듯한 제목 6개 사용.
- **KPI 목표값은 ROADMAP 원문 그대로** — 3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초. 수정 없음.
- **Phase 10 비간섭 원칙** — Phase 9는 "인프라 + dry-run"만. 실 데이터 수집 / SKILL patch / harness-audit 실행 금지 (Phase 10 D-2 저수지 규율).

</specifics>

<deferred>
## Deferred Ideas

### 후속 phase로 이관 (scope creep 차단)

- **실제 KPI 데이터 기반 첫 Taste Gate 평가** — Phase 10 첫 월 (Month 1 of Sustained Operations)
- **YouTube Analytics API 실연동** — Phase 10 (scripts/analytics/fetch_kpi.py 신규)
- **Auto Research Loop (KPI → NotebookLM RAG 피드백)** — Phase 10 (REQ-09 구조 완성)
- **SKILL.md 자동 patch 검토** — Phase 10 첫 1~2개월 이후 batch (D-2 저수지 규율)
- **다국어 ARCHITECTURE.md** — 필요성 미확정, 후속 phase로 보류
- **Taste Gate 기준 다변화 (3→5 KPI)** — Phase 10 이후 데이터 축적 후 재검토

### Reviewed Todos (not folded)

_None — 0 todos matched Phase 9 scope._

</deferred>

---

*Phase: 09-documentation-kpi-dashboard-taste-gate*
*Context gathered: 2026-04-20 (session #23, YOLO 연속 5세션, --auto 모드)*
*Auto-selected decisions: D-01 ~ D-14 (14 locked decisions + 4 Claude discretion areas)*
