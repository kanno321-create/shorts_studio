# Phase 11: Pipeline Real-Run Activation + Script Quality Mode - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning
**Source:** Executive delegation — 대표님(비개발자)이 "전체 코드 맵핑 후 제대로 실행되게, 욜로모드로 묻지말고 진행"으로 4 gray area의 기술 결정을 AI 최고 품질 기준으로 위임. Phase 10 CONTEXT 패턴 동일.

<domain>
## Phase Boundary

**Goal (ROADMAP §292-294)**: v1.0.1 milestone 구조 완결 상태에서 (a) **pipeline real-run 작동 확보** — D10-PIPELINE-DEF-01 5-에러 chain 해결 → full 0→13 GATE smoke 완주 → 영상 1편 실 발행, (b) **SCRIPT-01 옵션 확정** — 대표님 품질 평가로 A/B/C 선택 (구현 scope는 조건부 분기), (c) **D10-01-DEF-02 idempotency 수정** — 2026-05-20 첫 월간 scheduler 실행 전. 본 phase 완결 = 대표님 Core Value(외부 수익) 경로 실제 개통.

**Depends on:** Phase 10 (v1.0.1 audit PASSED 96/96 REQ + 55/55 SC, commit 43bea97)

**Phase 11 scope (이 Plan들이 건드릴 경계)**:
- `scripts/orchestrator/invokers.py:141-171` — Claude CLI 호출 형식 수정 (stdin piping)
- `scripts/orchestrator/shorts_pipeline.py:210-235, :746-760` — 4개 adapter graceful degrade 통일 + argparse --session-id optional화
- `run_pipeline.cmd` + `run_pipeline.ps1` (repo root 신규 2파일) — Windows 더블클릭 wrapper
- `.env` 자동 로드 통합 — zero-dep 파서 또는 python-dotenv
- `scripts/audit/skill_patch_counter.py` — idempotency grep + `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` 신규
- `wiki/script/` + `.claude/agents/producers/scripter/AGENT.md` — **옵션 A 유지** pre-committed, B/C 선택 시 Phase 12 spawn

**Phase 11 scope 밖 (deferred 또는 Phase 12 조건부)**:
- NLM 2-step scripter 재설계 구현 (옵션 B 선택 시 Phase 12 spawn)
- Shorts/Longform 2-mode 분리 구현 (옵션 C 선택 시 Phase 12 spawn)
- Phase 04/08 retrospective VERIFICATION.md (선택 SC#6) — deferred to post-Phase 11 cleanup
- Adapter registry + lazy 전역 refactor (Option C for PIPELINE-03) — Phase 12+ scope

</domain>

<decisions>
## Implementation Decisions (AI-resolved by 대표님 delegation)

### PIPELINE-01 — Invoker 수정 방식

- **D-01**: **Option A (stdin piping)** 채택. `_invoke_claude_cli`를 `subprocess.Popen(stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(input=user_prompt, timeout=timeout_s)`로 전환. argv에서 user_prompt positional 제거.
- **D-02**: argv 최종 형태는 `[cli_path, "--print", "--append-system-prompt", body, "--json-schema", schema]`. `user_prompt`는 stdin으로만 전달.
- **D-03**: Claude Agent SDK 전환(Option C) 금지 — `.claude/memory/project_claude_code_max_no_api_key.md` "anthropic/claude_agent_sdk 금지" 결정 유지 (Max 구독 중복결제 방지, commit 8af5063).
- **D-04**: `_invoke_claude_cli` 시그니처/반환/에러 메시지(Korean-first) 유지 — 테스트 seam(`cli_runner` 주입) 무변경으로 regression 최소화.

**Rationale (ranked)**: (1) Blast radius 1 함수, (2) Max 구독 billing 경로 불변, (3) CLI 2.1.112 canonical form, (4) Windows argv 길이 한계(AGENT.md body 큼) 자동 회피, (5) Phase 9.1 smoke 아키텍처 미파괴.

### PIPELINE-03 — Adapter graceful degrade 범위

- **D-05**: **Option A (pipeline-site 통일 wrap)** 채택. `shorts_pipeline.py:210-213`의 Kling/Runway/Typecast/ElevenLabs 4개 인스턴스화를 Phase 9.1 shotstack/nanobanana/ken_burns 블록(L214-235)과 **동일한 try/except/logger.warning/self.X = adapter_arg** 패턴으로 래핑.
- **D-06**: adapter 내부(`scripts/orchestrator/api/*.py` `__init__`)는 **무변경** — eager ValueError 유지. Phase 9.1도 adapter 내부 건드리지 않고 pipeline site에서만 처리함을 그대로 따름.
- **D-07**: 발견된 defect: shotstack adapter도 실제로는 adapter 내부 eager(`shotstack.py:81-97`). 대표님 session #28 "즉석 graceful degrade 패치"는 pipeline site(L214-218)에만 반영된 상태 — Phase 11에서 pipeline site 일괄 통일로 해소.
- **D-08**: Adapter registry/lazy refactor(Option C)는 Phase 12+ deferred — 244/244 phase04 regression baseline 보호.

**Rationale**: (1) Phase 9.1 패턴 verbatim 복제, (2) 1 파일 ~20줄 변경, (3) MagicMock 주입 테스트 seam 보존, (4) adapter 내부 건드리면 각 adapter별 테스트(5파일+) 영향.

### PIPELINE-04 — 더블클릭 Wrapper UX

- **D-09**: **Option B (.cmd bootstrap + .ps1 engine)** 채택. 2 파일 신규:
  - `run_pipeline.cmd` (repo root) — 단일 라인 `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"` + `pause`
  - `run_pipeline.ps1` (repo root) — `.env` 파싱(Get-Content + regex) → env 주입 → `py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id $(Get-Date -Format "yyyyMMdd_HHmmss")` 호출 → try/catch/Read-Host pause-on-error.
- **D-10**: Windows 11 `CurrentUser` PS ExecutionPolicy `Restricted` 우회 — `.cmd`가 `-ExecutionPolicy Bypass`로 `.ps1` 시작. **관리자 권한 불필요**.
- **D-11**: `.ps1`는 컬러드 gate-progress 출력 + try/catch Read-Host (Python launcher Option C의 ImportError 시 창 즉시 닫힘 문제 회피).
- **D-12**: 기존 `scripts/schedule/windows_tasks.ps1` 컨벤션(Korean block-comments, `-NoProfile`, absolute ScriptRoot) 준수.

**Rationale**: (1) 대표님 double-click UX 핵심 요구 충족, (2) Restricted policy 자동 우회, (3) .env API key의 `=` 포함값을 .bat `for /f` 파싱보다 PS regex가 안전, (4) 에러 시 창 유지.

### PIPELINE-02 / D-13~D-16 — `.env` 자동 로드

- **D-13**: **zero-dep 파서** 채택 — `scripts/orchestrator/__init__.py`에 `_load_dotenv_if_present()` 함수 추가 (Path(".env") 읽기 + `KEY=VALUE` line regex + `os.environ.setdefault`). `python-dotenv` 미설치.
- **D-14**: Reason: repo root에 `requirements.txt` / `pyproject.toml` 부재 — 외부 dep 추가는 harness 의존성 변경 필요. zero-dep가 실행 단순성 보장.
- **D-15**: `.env` 부재 시 silently skip (기존 환경변수 경로 보존). 중복 호출 멱등.
- **D-16**: `shorts_pipeline.py` argparse에서 `--session-id required=False, default=None` + `session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")` 처리 — wrapper가 session-id 자동 주입하지 않아도 Python단에서 생성.

### SCRIPT-01 — 옵션 A/B/C 구현 경계

- **D-17**: **Option X3 (Phase 11 pre-commit to Option A baseline)** 채택. Phase 11 내 scripter 재설계/2-mode 분리 구현 **없음**.
- **D-18**: 대표님 영상 1편 품질 평가 후 옵션 B/C 선택 시 → **Phase 12: NLM 2-Step Scripter Redesign** (또는 "Script Quality Mode") 자동 spawn. Phase 11 VERIFICATION 단계에서 선택 기록만 locked.
- **D-19**: REQ SCRIPT-01 원문 "선택된 옵션의 구현까지 완료" **amendment 권고** — plan-phase 단계에서 "옵션 선정 + Phase 12 조건부 발행" 으로 REQUIREMENTS.md 수정. 원문은 "post-smoke video evaluation 트리거 → 동일 phase 내 구현" 논리 모순(평가 후 구현 시간 부족 + Phase sprawl).
- **D-20**: scripts/notebooklm/query.py는 **이미 multi-notebook 호환** (D-4 per Plan 06-06 `notebook_id` 인자 필수) — 옵션 B 선택 시 query.py 자체 변경 불필요. scripter AGENT.md + 신규 `scripter_nlm_2step.py` orchestration 모듈만 Phase 12 scope.
- **D-21**: 옵션 A pre-commit이 의미하는 바: Phase 11 smoke는 현 scripter agent(Claude Opus prompt-based duo dialogue)로 영상 1편 생성. B/C가 선택되더라도 **Phase 11 발행 영상 1편은 옵션 A 산출물**.

**Rationale**: (1) Phase 11 이미 6 plan — B/C 구현 추가 시 9-10 plan sprawl (AF-10 Anthropic sweet spot 위반 위험), (2) REQ 원문의 논리 모순 해소(평가 트리거와 구현 완료가 동일 phase 불가능), (3) D-2 저수지 규율 유지(SKILL.md / agent prompt 변경은 실증 데이터 축적 후).

### AUDIT-05 — skill_patch_counter idempotency

- **D-22**: 2026-05-20 첫 월간 scheduler(`skill-patch-count-monthly.yml`) 실행 **전** 완료. Phase 11 entry gate.
- **D-23**: Append 전 `FAILURES.md` grep — 동일 commit hash set(violation의 git SHA union) 이미 기록 시 skip. 신규 violation만 append.
- **D-24**: 신규 test: `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` — 동일 git state 2회 연속 실행 시 첫 회만 append 검증.
- **D-25**: 사후 수동 정리(F-D2-02~F-D2-05 제거 + F-D2-01 보존)는 이미 완료(commit 2026-04-21). Phase 11은 regression 방지 로직만 추가.

### Claude's Discretion (AI 재량)

- Plan 실행 Wave 구조 (Phase 9.1/10과 동일 Wave 1~4 discipline 권장)
- 각 Plan의 구체적 테스트 케이스 설계
- run_pipeline.ps1 세부 에러 메시지 문구 (대표님 친화 Korean)
- zero-dep .env 파서의 주석/docstring 스타일
- Phase 11 전체 smoke 실 발행 cost 추적 방식 (cap 없이 실비 기록)
- D-19 REQUIREMENTS.md amendment 문구

### Folded Todos

(Phase 10 deferred-items로부터 편입된 3개 defects — 이미 ROADMAP §296-304 REQ로 박제됨)
- D10-PIPELINE-DEF-01 (CRITICAL) → PIPELINE-01/02/03/04 REQ로 전개
- D10-SCRIPT-DEF-01 → SCRIPT-01 REQ로 전개
- D10-01-DEF-02 → AUDIT-05 REQ로 전개

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents(phase-researcher, planner) MUST read these before planning.**

### Phase 11 motivation + scope
- `.planning/phases/10-sustained-operations/deferred-items.md` §D10-PIPELINE-DEF-01 — 5-error chain 증상/원인/해결 우선순위
- `.planning/phases/10-sustained-operations/deferred-items.md` §D10-SCRIPT-DEF-01 — 옵션 A/B/C 원문
- `.planning/phases/10-sustained-operations/deferred-items.md` §D10-01-DEF-02 — skill_patch_counter idempotency defect
- `.planning/ROADMAP.md` §267-314 — Phase 10 scope + Phase 11 goal/SC/plan 초안
- `.planning/REQUIREMENTS.md` — PIPELINE-01~04, SCRIPT-01, AUDIT-05 원문 (lines 336-347)

### PIPELINE-01 Invoker
- `scripts/orchestrator/invokers.py:118-171` — `_invoke_claude_cli` 현 argv + 에러 분기
- `scripts/orchestrator/invokers.py:174-234` — `ClaudeAgentProducerInvoker` 래퍼
- `scripts/orchestrator/invokers.py:237-292` — `ClaudeAgentSupervisorInvoker` 래퍼
- `.claude/memory/project_claude_code_max_no_api_key.md` — anthropic/claude_agent_sdk 금지 결정 (commit 8af5063)

### PIPELINE-03 Adapter degrade
- `scripts/orchestrator/shorts_pipeline.py:210-235` — pipeline-site adapter instantiation (Phase 9.1 shotstack/nanobanana/ken_burns 패턴 L214-235)
- `scripts/orchestrator/api/kling_i2v.py:81-95` — KlingI2VAdapter `__init__` eager
- `scripts/orchestrator/api/runway_i2v.py:77-117` — RunwayI2VAdapter `__init__` eager
- `scripts/orchestrator/api/typecast.py:51-65` — TypecastAdapter `__init__` eager
- `scripts/orchestrator/api/elevenlabs.py:109-140` — ElevenLabsAdapter `__init__` eager
- `scripts/orchestrator/api/shotstack.py:81-97` — ShotstackAdapter `__init__` (adapter 내부도 eager임 — D-07 defect)

### PIPELINE-04 Wrapper + PIPELINE-02 dotenv
- `scripts/orchestrator/shorts_pipeline.py:746-760` — argparse block (`--session-id required=True` 완화 대상)
- `scripts/schedule/windows_tasks.ps1` — PS convention 참조 (Korean block-comments, `-NoProfile`, `-ExecutionPolicy Bypass`)
- `.env` (repo root) — loader 타겟. git-ignored.

### SCRIPT-01
- `wiki/script/NLM_2STEP_TEMPLATE.md` — NLM 2-step 규약 전문 (Step 1 `crime-stories-+-typecast-emotion` → Step 2 `script-production-deep-research`)
- `wiki/script/QUALITY_PATTERNS.md` — 대본 품질 패턴 (옵션 B/C 결정 시 기준)
- `.claude/agents/producers/scripter/AGENT.md` (212줄) — 현 scripter 프롬프트 (옵션 A 산출물 생성자)
- `scripts/notebooklm/query.py` — `query_notebook(notebook_id=...)` 이미 multi-notebook 호환

### AUDIT-05
- `scripts/audit/skill_patch_counter.py` — idempotency 추가 대상
- `tests/phase10/test_skill_patch_counter.py` — regression test 추가 대상
- `.claude/failures/FAILURES.md` — append 전 grep 대상 (F-D2-01 보존 상태 확인)
- `.github/workflows/skill-patch-count-monthly.yml` (Plan 10-04 산출) — 2026-05-20 첫 실행 deadline

### Harness 규율
- `../../harness/STRUCTURE.md` — whitelist 준수 (run_pipeline.cmd/.ps1 신규 파일 root 배치 허용 확인 필요)
- `../../harness/docs/ARCHITECTURE.md` — Layer 1 principle

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 9.1 shotstack/nanobanana/ken_burns graceful degrade block** (`shorts_pipeline.py:214-235`) — 4개 신규 adapter wrap의 verbatim 템플릿
- **`scripts/schedule/windows_tasks.ps1`** — PS script convention reference (block comments, -NoProfile, idempotent defensive style)
- **`scripts/notebooklm/query.py:query_notebook(notebook_id=...)`** — 이미 multi-notebook 호환 (D-4 per Plan 06-06) — 옵션 B 선택 시 query.py 자체는 무변경
- **`scripts/orchestrator/invokers.py:cli_runner` 주입 seam** — regression 없이 stdin 전환 가능
- **Phase 10 deferred-items.md 구조** — Phase 11 deferred-items.md 템플릿으로 재사용

### Established Patterns
- **Wave 1~4 plan discipline** (Phase 9.1/10) — Phase 11에도 동일 적용
- **Korean-first error messages** (대표님 호칭 포함) — 신규 wrapper/파서에도 유지
- **try/except + logger.warning + self.X = None** graceful degrade (Phase 9.1)
- **Zero-dep preference** (requirements.txt 부재, python-dotenv 미설치) — 신규 파서도 zero-dep
- **`notebook_id` 인자 필수** (D-4 per Plan 06-06, default skill constant 금지)

### Integration Points
- `shorts_pipeline.py` `__init__` (L60~240) — adapter instantiation + (신규) `_load_dotenv_if_present()` 호출 지점
- `shorts_pipeline.py:main()` (L746~) — argparse relax + auto-timestamp session-id 진입점
- `invokers.py:_invoke_claude_cli` (L141~) — stdin piping 단일 수정점
- `run_pipeline.cmd` + `run_pipeline.ps1` (repo root 신규) — 대표님 double-click 진입점
- `.env` loader — `scripts/orchestrator/__init__.py` 신규 함수 (또는 shorts_pipeline.py top-of-file import time)

</code_context>

<specifics>
## Specific Ideas

- **대표님 명시 지시**: "욜로모드로 묻지말고 진행" — 4 gray area 모두 AI 최고 품질 기준 결정, 추가 질문 없이 CONTEXT 박제 + plan-phase 진입.
- **대표님 명시 지시**: "전체 코드 맵핑 후 제대로 실행되게" — planning/execution 전 반드시 invokers.py + 5 adapters + argparse + query.py + scripter AGENT.md 전수 확인. 이미 discuss-phase에서 수행 완료 (4 parallel code-mapping agents).
- **대표님 Core Value**: 외부 수익 발생 (기술 성공 ≠ 비즈니스 성공). Phase 11 완결 시점 = 영상 1편 실 발행 = 수익 경로 최초 개통.
- **Phase 9.1 smoke "$0.29 live run"**은 Stage 2→4 mock invoker 기반 — Phase 11 full 0→13 smoke는 **실 Claude CLI + 실 API 전수** 첫 실증.
- **Windows 11 더블클릭 UX**: 대표님 "관리자 권한 불필요 + 창 안 꺼짐" 명시 요구.

</specifics>

<deferred>
## Deferred Ideas

### Phase 12 조건부 (SCRIPT-01 옵션 B/C 선택 시)
- **Phase 12: NLM 2-Step Scripter Redesign** — 옵션 B 선택 시 spawn. 내용: `.claude/agents/producers/scripter/AGENT.md` 재작성 + `scripts/orchestrator/scripter_nlm_2step.py` 신규(~300~400줄, Step 1 호출 → source.md 파싱 → Step 2 호출 → cut JSON 파싱 → follow-up loop 5 patterns) + 5 신규 테스트. NLM daily 50-query limit + follow-up 거부 패턴 대응.
- **Phase 12 대안: Shorts/Longform 2-mode 분리** — 옵션 C 선택 시. channel_bible.길이 기반 routing. Shorts(59s, 현 scripter 유지) + Longform(15min, 순수 NLM 2-step). scripter agent 2개 분리 또는 mode flag.

### Phase 12+ (독립 후속)
- **Adapter registry + lazy instantiation 전역 refactor** (PIPELINE-03 Option C) — 5+ 파일 touch + 244/244 regression 위험, 별 phase.
- **Phase 04/08 retrospective VERIFICATION.md** (ROADMAP SC#6 optional) — Phase 04(33 agent filesystem invariant) + Phase 08(smoke upload 2 evidence) 증거 체인 공식화. Phase 11 sprawl 방지 위해 별 cleanup phase로 분리.
- **Shotstack adapter 내부(`shotstack.py:81-97`) eager → lazy 직접 수정** — D-07 defect의 근본 수정. Phase 11은 pipeline site wrap으로 회피, 근본 수정은 adapter registry refactor 시점.
- **Phase 11 smoke 실 발행 cost aggregation dashboard** — 실 API cost per session 추적. 1편 발행 후 필요 시.

### 로드맵 backlog
- **REQ SCRIPT-01 원문 amendment 공식 처리** (D-19) — plan-phase 첫 과제로 REQUIREMENTS.md 문구 수정 또는 별 admin 커밋.

### Reviewed Todos (not folded)
(Phase 10 deferred-items 중 이미 `phase-regression-cleanup` 전용 별 phase 후보로 명시된 항목 — Phase 11 scope 외)
- D10-01-DEF-01 Phase 5/6 pre-existing regressions (inherited from Phase 9.1 stack migration)
- D10-03-DEF-01 drift_scan STATE.md frontmatter assertion (Plan 10-02 follow-up)
- D10-03-DEF-02 Phase 5/6/7/8 regression cascade sweep
- D10-06-DEF-01 trajectory_append collection error (이미 Plan 10-07 GREEN 처리)

</deferred>

---

*Phase: 11-pipeline-real-run-activation-script-quality-mode*
*Context gathered: 2026-04-21 (session #29)*
