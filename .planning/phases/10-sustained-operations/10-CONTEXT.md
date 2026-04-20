# Phase 10: Sustained Operations - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning
**Source:** Executive delegation path — 대표님(경영자)이 "최고 품질 기준으로 AI 결정"으로 3개 Locked Decision을 위임. `C:\Users\PC\.claude\plans\mellow-tumbling-pudding.md` Part B 에서 확정.

<domain>
## Phase Boundary

**Goal (ROADMAP §267)**: 주 3~4편 자동 발행 지속 + 첫 1~2개월 SKILL patch 전면 금지 (D-2 저수지 실증) + FAILURES/KPI 데이터 축적 + 월 1회 harness-audit + drift_scan + FAILURES batch 리뷰 (A급 drift 0건 유지) + Auto Research Loop (YouTube Analytics → NotebookLM RAG 피드백) 완성. **영구 지속 phase**, 종료 시점 = YPP 진입 + 외부 수익 발생.

**Depends on**: Phase 9 + Phase 9.1 (UAT Entry Gate PASSED, commit 969d84d)

**Pre-Phase10 Plan-0 (이미 완료, commit `8172e9c`)**: 세션 컨텍스트 단절 영구 수정 — `.claude/memory/` 로컬 저장소 10 파일 + `session_start.py` Step 4-6 확장 + `FAILURES.md` 신규 + CLAUDE.md Session Init 업데이트. Phase 10 진입 전 전제 조건.

**Phase 10 scope (이 Plan들이 건드릴 경계)**:
- `scripts/audit/*.py` — skill_patch_counter, drift_scan (신규)
- `scripts/analytics/*.py` — YouTube Analytics daily fetch + 월간 집계 (신규)
- `scripts/research_loop/*.py` — 월 1회 NotebookLM RAG 업데이트 (신규)
- `scripts/schedule/*.py` — cron 엔트리 + 실패 알림 (신규, 선택적 GH Actions 경로)
- `.github/workflows/*.yml` — GH Actions cron 3종 (신규)
- `scripts/session_start.py` — 30일 rolling 감사 점수 집계 (신규, hook `session_start.py` 와 별도)
- `wiki/ypp/trajectory.md` + `wiki/shorts/kpi_log.md` — 월별 자동 append (기존 scaffold 확장)
- `.planning/phases/10-sustained-operations/` meta-docs

**D-2 Lock 물리적 경계 (Plan 1 `skill_patch_counter.py` 가 enforce)**:
- **금지 (count된다)**: `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md` 본문
- **허용**: `SKILL.md.candidate`, `scripts/**/*.py`, `.planning/phases/10-*/`, `wiki/**/*.md` append, `FAILURES.md` append, `.claude/memory/*.md`

</domain>

<decisions>
## Implementation Decisions (Locked by 대표님 delegation)

### Exit Criterion — 옵션 B+C 하이브리드 (Rolling 12개월 + 3단계 Milestone)

- **1차 gate (3개월, 2026-07-20 평가)**: 누적 구독자 ≥ 100명. 미달 시 니치/훅 iteration Plan 추가.
- **2차 gate (6개월, 2026-10-20 평가)**: 누적 구독자 ≥ 300명, 3초 retention ≥ 60%.
- **3차 gate (12개월, 2027-04-20 평가)**: Rolling 12개월 기준 구독자 ≥ 1000 + 뷰 ≥ 10M. 달성 월에 YPP 진입 + Phase 10 "성공 선언" (sustained는 계속).

**Why**: YPP 공식 계산이 rolling 12개월. 동시에 경영자용 pivot 판단을 위해 3단계 milestone 추가. `wiki/ypp/trajectory.md` 월별 자동 append 로 SC#6 충족.

### D-2 Lock Scope — 최대 보수 2개월 lock

- **기간**: 2026-04-20 ~ 2026-06-20 (ROADMAP "1~2개월" 상한 채택)
- **검증 파일**: `scripts/audit/skill_patch_counter.py` — `git log --since="2026-04-20" --name-only` 기반, 금지 경로 hit 시 count++
- **Exit 조건 (lock 해제)**: 2개월 경과 + FAILURES.md 엔트리 ≥ 10건 (실 데이터 충분) + 월 1회 taste gate 2회 완료
- **해제 후 정책**: SKILL patch 허용하되 모든 patch 는 `FAILURES.md` 의 특정 엔트리 reference 필수 (root-cause grounding)

**Why**: 데이터 수집 길수록 D-2 저수지 규율 실증 강함. Phase 10 최초 2개월의 "학습 침묵" 이 본질.

### Scheduler — 하이브리드 (GH Actions + Windows Task Scheduler)

**GH Actions cron (`.github/workflows/`, 클라우드 24/7)**:
- `analytics-daily.yml` — `scripts/analytics/fetch_kpi.py` 매일 KST 05:00 (UTC 20:00 전일) 실행. API key 는 GH secrets.
- `drift-scan-weekly.yml` — `scripts/audit/drift_scan.py` 매주 월요일 KST 09:00 실행. A급 drift 발견 시 GitHub issue 자동 생성.
- `skill-patch-count-monthly.yml` — `scripts/audit/skill_patch_counter.py` 매월 1일 KST 09:00 실행 + 리포트 append.

**Windows Task Scheduler (대표님 로컬 PC)**:
- 영상 생성 파이프라인 (Kling 2.6 Pro + Typecast + Nano Banana Pro 호출, 로컬 캐시 + 파일 크기 문제로 로컬 실행)
- YouTube 업로드 (`scripts/publisher/youtube_uploader.py`, refresh token `config/youtube_token.json` 로컬 저장)
- `scripts/publisher/publish_lock.py` 48시간+jitter + `kst_window.py` 평일 20-23 / 주말 12-15 KST 강제

**실패 알림 3 채널**:
- GH Actions 실패 → built-in email → `kanno3@naver.com`
- 로컬 Windows Task Scheduler 실패 → PowerShell SMTP script → Gmail/Naver
- 양쪽 모두 `FAILURES.md` append (F-OPS-XX 카테고리, `check_failures_append_only` hook 자동 enforce)

**Why**: 최고 품질 = 단일 장애점 제거. GH Actions만 쓰면 영상 파일 전송 overhead + secrets 유출 리스크. Windows만 쓰면 PC 꺼지면 stop. 분업이 각 자원의 강점 활용.

### Boundary decisions

- **Plan 수 = 8 개** (SC#1~6 각 1 + Scheduler 1 + Rollback docs 1). Pre-Phase10 Plan-0 은 이미 완료된 별도 작업.
- **우선순위**: SC#1 (skill_patch_counter) → SC#4 (drift_scan, 안전망) → SC#2 (KPI fetch) → Scheduler → SC#3 (session audit 30-day rolling) → SC#5 (research loop) → SC#6 (trajectory) → Rollback docs
- **첫 실 영상 발행 시점**: Plan 1~4 완료 후 (D-2 Lock enforce + drift 안전망 + KPI 수집 + 최소 scheduler). 이후 주 3~4편 자동 운영 시작.
- **실패 알림 수신처**: `kanno3@naver.com` (대표님 email)
- **LLM 호출 경로**: 모든 Claude 호출은 `subprocess.run(["claude", "--print", ...])` — `ANTHROPIC_API_KEY` 등록 영구 금지 (`.claude/memory/project_claude_code_max_no_api_key.md`)

### Claude's Discretion (구현 세부)

- `skill_patch_counter.py` 의 정확한 git grep 정규식
- `drift_scan.py` 의 A급 판정 heuristic 세부 (harness 참조: `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py`)
- YouTube Analytics v2 API 엔드포인트 선택 (reportsQuery vs queryReport)
- GH Actions matrix 구성 (single job vs parallel)
- Rollback docs 포맷 (md vs runbook.sh)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ROADMAP + Requirements
- `.planning/ROADMAP.md` (§265-277) — Phase 10 정의 + 6 SC 본문
- `.planning/REQUIREMENTS.md` (line 138-161) — FAIL-04 + KPI-01~04 + AUDIT-01~04 본문
- `.planning/PHASE_10_ENTRY_GATE.md` — §2 deliverable 인벤토리 + §3 D-2 Lock + §4 rollback 개요

### 컨텍스트 단절 수정 (Pre-Phase10 Plan-0, 이미 완료)
- `.claude/memory/MEMORY.md` — 9 박제 메모리 인덱스
- `.claude/memory/project_video_stack_kling26.md` — Stage 4 I2V 스택
- `.claude/memory/project_claude_code_max_no_api_key.md` — Claude CLI subprocess 강제
- `.claude/memory/project_tts_stack_typecast.md` — Stage 3 TTS 스택
- `.claude/memory/reference_api_keys_location.md` — `.env` key 매핑 (대표님께 재질문 금지)
- `FAILURES.md` — F-CTX-01 (컨텍스트 단절 재발 방지)
- `.claude/hooks/session_start.py` (Step 4-6 확장됨)

### Phase 10 re-use 대상 (Plan 작성 시 import)
- `scripts/publisher/publish_lock.py` (`assert_can_publish()`, `record_upload()`, `MIN_ELAPSED_HOURS=48`, `MAX_JITTER_MIN=720`)
- `scripts/publisher/kst_window.py` (`assert_in_window()`, 평일 20-23 / 주말 12-15 KST)
- `scripts/publisher/oauth.py` (YouTube OAuth2, `config/client_secret.json` + `config/youtube_token.json`)
- `scripts/publisher/youtube_uploader.py` (videos.insert)
- `scripts/failures/aggregate_patterns.py` (30일 패턴 집계, Phase 6)
- `scripts/validate/harness_audit.py` (280줄, AUDIT-02 구현, 점수 ≥80 기준)
- `.claude/hooks/pre_tool_use.py` (`check_failures_append_only()` line 160, `backup_skill_before_write()` line 213)

### Harness 참조 구현 (Layer 1 공용)
- `C:/Users/PC/Desktop/naberal_group/harness/hooks/session_start.py` — 감사 3단계 참조 (Step 1-3)
- `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` — drift_patterns.json 로드 + scan_studio() + write_conflict_map() 구조

### 금지 항목 (hard constraints)
- T2V 금지 — I2V only (CLAUDE.md 도메인 절대 규칙 #4)
- Selenium 업로드 영구 금지 — YouTube Data API v3 공식만 (AF-8)
- ANTHROPIC_API_KEY 영구 금지 — Claude CLI subprocess 경로 사용
- K-pop 트렌드 음원 직접 사용 금지 — KOMCA + Content ID strike (AF-13)
- 주 3~4편 페이스 — 일일 업로드 = Inauthentic Content (AF-1, AF-11). 48시간+ jitter 필수

</canonical_refs>

<specifics>
## Specific Ideas

### Plan 1: SC#1 — skill_patch_counter (D-2 Lock 실증)
- 파일: `scripts/audit/skill_patch_counter.py`
- 입력: git log --since="2026-04-20" --name-only --pretty=format:"%H|%s"
- 출력: `reports/skill_patch_count_YYYY-MM.md` + FAILURES.md append (count > 0 시 F-D2-XX)
- 의존: Part A 에서 만든 FAILURES.md + pre_tool_use hook
- REQ: FAIL-04

### Plan 2: SC#4 — drift_scan (안전망)
- 파일: `scripts/audit/drift_scan.py` + `.claude/deprecated_patterns.json` 보강
- 참조: harness 공용 `scripts/drift_scan.py` 구조 (load_patterns, scan_studio, write_conflict_map)
- Phase 차단: A급 drift > 0 시 `.planning/STATE.md` phase lock 필드 세팅
- REQ: AUDIT-03, AUDIT-04

### Plan 3: SC#2 — KPI daily fetch + monthly aggregate
- 파일: `scripts/analytics/fetch_kpi.py` + `scripts/analytics/monthly_aggregate.py`
- YouTube Analytics API v2: reportsQuery 엔드포인트 (audience retention / CTR / avg view duration)
- 출력: `wiki/shorts/kpi_log.md` 월별 append
- 재사용: `scripts/failures/aggregate_patterns.py` 30일 집계 로직
- REQ: KPI-01, KPI-02

### Plan 4: Scheduler (Supporting)
- 파일: `.github/workflows/analytics-daily.yml` + `drift-scan-weekly.yml` + `skill-patch-count-monthly.yml`
- Windows Task Scheduler batch: `scripts/schedule/windows_tasks.ps1` (영상 생성 + 업로드)
- 실패 알림: `scripts/schedule/notify_failure.py` (email SMTP) + FAILURES.md append
- REQ: (SC#1~6 의존성)

### Plan 5: SC#3 — session audit 30-day rolling
- 파일: `scripts/session_start.py` (hook 의 session_start.py 와 다름 — 이건 30일 집계 리포트)
- 입력: `.claude/hooks/session_start.py` 출력 로그 (jsonl 축적)
- 30일 평균 점수 ≥ 80 assertion, 미달 시 FAILURES.md append
- REQ: AUDIT-01

### Plan 6: SC#5 — Auto Research Loop
- 파일: `scripts/research_loop/monthly_update.py`
- 월 1회 YouTube Analytics 상위 3 영상 → NotebookLM RAG 자동 업데이트
- 재사용: `.claude/skills/notebooklm/` 기존 스킬
- 다음 월 Producer 입력에 KPI 반영 assertion
- REQ: KPI-03, KPI-04

### Plan 7: SC#6 — YPP trajectory
- 파일: `wiki/ypp/trajectory.md` (scaffold 확장) + `scripts/analytics/trajectory_append.py`
- 월별 자동 append: 구독자 / 누적 뷰 / YPP 진행률 (1차/2차/3차 gate 대비)
- 시각화: Mermaid line chart (optional)
- REQ: (SC#6 본질, Phase 10 목적)

### Plan 8: Rollback docs
- 파일: `.planning/phases/10-sustained-operations/ROLLBACK.md` + `scripts/rollback/stop_scheduler.py`
- 무인 운영 사고 3 시나리오 (업로드 사고 / scheduler 버그 / 학습 회로 오염) 별 복구 경로
- Entry Gate §4 내용 확장
- REQ: (meta, FAIL-04 지원)

</specifics>

<deferred>
## Deferred Ideas

- **auto-route Kling → Veo**: `project_video_stack_kling26` fallback 조건 자동화. 수동 `--use-veo` 플래그만 Phase 10 에서 유지 — Phase 10 실패 패턴 축적 후 Phase 11 candidate.
- **D091-DEF-02 #4 wiki rename** (`remotion_kling_stack.md` → `remotion_i2v_stack.md`): Phase 6 tests 3개 + 29 파일 cascade — D-2 Lock 기간 내 금지.
- **NEG_PROMPT 하드코드 재검토** (KlingI2VAdapter, feedback_i2v_prompt_principles 원칙 2 충돌): 실측 데이터 축적 대기.
- **remotion_src_raw/ 40 파일 integration**: Phase 10 batch window 이후.
- **Typecast voice_discovery 확장** (D091-DEF-02 #8): primary 안정 확인 후.
- **audienceRetention timeseries 정확도 개선** (WARNING #3, Plan 3 관련): Phase 10 v1 은 audienceWatchRatio 를 retention_3s proxy 로 사용. audienceRetention timeseries 호출로 정확도 개선은 Phase 11 candidate — 실 데이터 축적 후 proxy ↔ 실측 오차 확인.
- **Producer AGENT.md monthly_context wikilink 추가** (INFO #2, Plan 6 관련): Producer AGENT.md 에 `@wiki/shorts/kpi/monthly_context_latest.md` 참조를 추가하여 KPI-04 end-to-end cascade 완성. D-2 Lock (2026-06-20) 해제 후 Plan 11 candidate — AGENT.md 는 `.claude/agents/*/` 에 위치하므로 D-2 Lock 범위.
- **Mac Mini 서버 이관** (세션 #27 박제, memory: `project_server_infrastructure_plan`): 현재 Scheduler 는 대표님 Windows PC (임시). 장기 계획은 Mac Mini (상시 가동 headless 서버). Windows Task Scheduler → macOS launchd plist 3종 이관. GH Actions cron 4종 은 클라우드 기반이라 영향 없음. 이관 판정 3 조건 (Mac Mini OS 셋팅 + 상시 가동 + Windows 운영 1개월+ 실적 축적) 충족 시 Phase 11 candidate.

</deferred>

---

*Phase: 10-sustained-operations*
*Context gathered: 2026-04-20 via Executive Delegation Path (대표님 3 Locked Decision 위임)*
*Upstream: `C:\Users\PC\.claude\plans\mellow-tumbling-pudding.md` Part B + `.planning/PHASE_10_ENTRY_GATE.md` + ROADMAP §265-277*
