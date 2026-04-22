# WORK HANDOFF — shorts_studio

## 최종 업데이트
- 날짜: 2026-04-22 (세션 **#30** — Phase 13 + Phase 14 + Phase 15 연속 실행, 해외범죄 샘플 쇼츠 1편 실제 제작 시도 + 대표님 원칙 2종 각인 + FAILURES auto-injection wiring)
- 세션: **#30** (commits: Phase 13 complete + Phase 14 complete + Phase 15 Wave 0~4 2/3 + handoff `08fbce3` + **세션 후반 unstaged wiring**: session_start.py / FAILURES.md / FAILURES_INDEX.md / CLAUDE.md)
- 상태: **Phase 15 Wave 4 Task 3 + Wave 5 + Wave 6 대기** — Live smoke retry (SPC-06) 가 Claude CLI JSON non-compliance 으로 실패. 대표님 "무한루프다" 지적 + `--skip-supervisor` 경로로 선택 합의. 세션 종료 직전 대표님 추가 지적 2건 반영: "봐주면서 하라" + "실패 교훈 자동 참조". 다음 세션 시작점 = NEXT_SESSION_START.md.

---

## 세션 #30 (2026-04-22) 완료 항목

### ✅ Phase 13 Live Smoke 재도전 — complete_with_deferred
- 6 plans shipped (13-01~06) + TRACEABILITY + VALIDATION flip
- Phase 13 Tier 1: 60 tests green, Tier 2: 5 collected (live_smoke opt-in)
- SC#1~4 + AUDIT PASS / SC#5 deferred (Tier 2 live run = empirical validation 잔여)
- commits: `c1b9117` (plans) + `d680465` (complete)

### ✅ Phase 14 API Adapter Remediation — complete_with_deferred
- 5 plans shipped (14-01~05): pytest.ini adapter_contract + 15 failures → 0 청산 + 30 contract tests + wiki/render/adapter_contracts.md + warn-only Hook
- SC#1~4 + AUDIT PASS / SC#5 (full pytest tests/ 1시간+ timeout, 비-scope 실패 2건) deferred
- commits: `a1628a2` + `02f8e9f`

### ✅ Phase 15 SPC + UFL Wave 0~4 (2/3) — 27 commits
- **Wave 0 15-01**: tests/phase15 scaffold + SPC-01 reproducer + SPC-04 `--append-system-prompt-file` empirical
- **Wave 1 15-02**: **invokers.py encoding fix** (tempfile + `--append-system-prompt-file`) — Phase 13 live smoke attempt 1 실패 원인 root cause 해소. 10 contract tests green.
- **Wave 2 15-03**: shorts-supervisor AGENT.md 10591 → **5712 chars** (Progressive Disclosure) + references/ 2 files + `verify_agent_md_size.py` (CHAR_LIMIT 18000)
- **Wave 3 15-04**: 5 UFL flags (`--evidence-dir` + `--revision-from` + `--feedback` + `--revise-script` + `--pause-after`) + `PipelinePauseSignal` + `GateGuard(ctx_config=...)` + ShortsPipeline ctx→gate_guard reorder + 18 tests
- **Wave 4 15-05 Task 1+2**: `rate_video.py` CLI + `verify_feedback_format.py` + `feedback_video_quality.md` seed (UFL-04 2/3)

### 🚧 Live Smoke Retry (세션 #30 직접 실행) — NEW 문제 노출
- 1차 시도: 0.09초 rc=1 실패 (argv encoding) → Wave 1 15-02 가 해소
- 2차 시도 (오늘): **115초, Claude CLI 실제 실행, $0** — 하지만:
  - TREND supervisor 첫 호출: 자연어 반환 "TREND gate PASS, 다음 게이트 NICHE 로 진행합니다, 대표님" (JSON schema 미준수)
  - JSON nudge retry 3회: stdout 비어있음 (quota/session 가능성)
  - attempt 2: 3 retries 모두 empty stdout → FAIL
- 결론: **encoding fix 성공 but Claude CLI JSON schema 엄수 brittle** — 새 실패 유형

### 🛑 대표님 "무한루프다" 지적 + 합의 경로
- Phase 11 defer → Phase 12 closure → Phase 13 실패 → Phase 15 fix 패턴 중단
- 합의: **A. 수동 혼합 경로** — `--skip-supervisor` flag 1개 추가 + 대표님 대본 1개 주입 + VOICE/ASSETS/UPLOAD 실 API 실행 + 영상 1편 완성. Supervisor quality gate 는 영상 생성 후 점진 복구.
- **Memory 박제**: `.claude/memory/feedback_infinite_loop_avoidance.md` — 다음 세션부터 자동 참조

### ✅ 세션 #30 후반 — 대표님 원칙 2종 각인 + FAILURES auto-injection wiring (unstaged)

**대표님 지적 #1 (2026-04-22, 세션 종료 직전)**: "너무 타이트하게하지말고 어느정도 봐주면서해라,,, 자연어 사용으로 실패했으면 되돌려보내서 다시하게하면되잖아"
- 박제: `.claude/memory/feedback_lenient_retry_over_strict_block.md` (사용자 global memory)
- 원칙: JSON/포맷 비준수 → hard-fail 차단 금지. nudge retry (원본 + 예시) 로 되돌려보내 재작성 유도. 최소 2~3회 retry. Empty stdout 도 같은 경로.
- Hard-block 유지 영역: AF-4 (voice clone) / AF-5 (실존 피해자) / AF-8 (Selenium) / AF-13 (KOMCA) / skip_gates=True — 법적·플랫폼 strike 위험만.

**대표님 지적 #2 (2026-04-22, 세션 종료 직전)**: "원칙에 실패하면 실패리스트에 올려서 교훈까지 제공하고 그걸 참조한뒤 작업시작하게하는거 아니가??"
- 원칙 있어도 wiring 없음 = 무의미 → 코드 강제 전환
- 패치 4종 (unstaged, 다음 세션 커밋 대상):
  1. `.claude/hooks/session_start.py` — `load_recent_failures()` 함수 추가, FAILURES.md open entry 전수 + 최근 5건 자동 주입 (Step 6a). Entry 1500자 truncate + 상태 필드 preserve.
  2. `.claude/failures/FAILURES.md` — 신규 entry `F-META-HOOK-FAILURES-NOT-INJECTED` append (Tier A, resolved, Lessons 4항 포함).
  3. `.claude/failures/FAILURES_INDEX.md` — Phase 6+ Entries 섹션 stale 해소, 6 entry 실전 등재 (FAIL-ARCH-01 + F-D2-EXCEPTION-01/02 Wave 2/3 + F-LIVE-SMOKE-JSON-NONCOMPLIANCE + F-META-HOOK).
  4. `CLAUDE.md` — Session Init 6→7 step 확장 (FAILURES.md 추가), 필수사항 4번 강화 (Lessons 필드 필수 + INDEX 동기화 + auto-injection 명시).
- Smoke test 6/6 PASS: session_start.py 실행 시 "📛 최근 실패 사례 + 교훈" 섹션 + open entry + Lessons 필드 + 경고문 전수 주입 (13428자 context).

---

## 다음 세션 진입점 (세션 #31)

1. **System context 자동 주입 확인** (session_start.py 가 자동 실행) — 다음 섹션이 시스템 reminder 로 자동 노출됨:
   - 🔑 .env API keys 목록 (재질문 금지)
   - 🧠 MEMORY.md index (2 feedback memory 포함 — infinite loop avoidance + lenient retry)
   - 📛 최근 실패 사례 + 교훈 (open 1 + 최근 5 entry 자동 노출 — F-LIVE-SMOKE-JSON-NONCOMPLIANCE + F-META-HOOK 포함)
2. **NEXT_SESSION_START.md** 읽기 (본 저장소 root) — 1-page 시작 프롬프트 + 4-step 경로
3. **첫 commit 작업**: 세션 #30 후반 unstaged wiring 4종 commit (session_start.py + FAILURES.md + FAILURES_INDEX.md + CLAUDE.md)
4. 순서: `--skip-supervisor` flag 추가 → 해외범죄 대본 1편 작성 → live run → 영상 1편 → rating

---

## (이전 기록 — 세션 #28 이전)

### 세션 #28 (2026-04-21) — 생략
CLAUDE.md Perfect Navigator + naberal_game bootstrap + NotebookLM deep research. 상세는 `docs/HARNESS_CHANGELOG.md` 참조.

---

## (아래는 이전 세션 기록, 참조용)

---

## 세션 #28 완료 항목 (2026-04-21)

### ✅ CLAUDE.md Perfect Navigator 재설계 (commit `e57f891`)
대표님 지시: "claude.md는 100미만이 좋다. 정체성·금기·지켜야할사항 + 나머지는 지도·네비게이션역할":
- CLAUDE.md **426 → 96 lines** (78% 감량)
- Navigator matrix: 상황 → 자산 **1-hop 라우팅**, 32 agents + 5 skills = **37/37 coverage (100%)**
- verb-grouped 6 카테고리 (제작/검증/조사/수정/점검/복구) — 대표님 실제 발화 패턴 매칭
- GSD markers: pointer-only sentinel (재주입 방지, `<!-- managed: pointer-only -->`)
- 신설 `docs/HARNESS_CHANGELOG.md` — 하네스 변경 이력 append-only 분리
- 신설 `scripts/validate/navigator_coverage.py` — 자산 drift 자동 검증 (196줄)
- `session_start.py` Step 6b 추가 — Navigator Coverage 경고 자동 주입
- `harness_audit.py` D-11 JSON `navigator_coverage` 필드 추가
- `docs/ARCHITECTURE.md` L6 Phase status drift 패치 (Phase 8 → Phase 9+9.1 완결 + Phase 10 Entry Gate PASSED)
  - 다른 나베가 "Phase 8" 이라고 오인한 원인 근절 — F-ARCH-01 박제

### ✅ naberal_game 스튜디오 창업 (별도 git repo, Phase 0 Bootstrap)
대표님 "평생의 꿈 — Unity 6 Steam 솔로 인디 게임":
- 장르: 로그라이크/시뮬/RPG 복합, 12~24개월 장기 창작
- 스택: Unity 6 LTS + C# + Steam PC + AI 도구 체인 (Claude Code, Nano Banana Pro, Suno, ElevenLabs, Meshy)
- 위치: `studios/game/` (shorts 자매 스튜디오) + GitHub 원격 `github.com/kanno321-create/naberal_game` (Private, main 브랜치)
- `new_domain.py game` 스캐폴드 + Perfect Navigator 패턴 Day 1 이식 (CLAUDE.md 84줄)
- wiki/ 6 카테고리 (design/engine/gameplay/art/audio/steam) + MOC.md + Obsidian vault anchor
- scaffolding 확장: memory + failures + deprecated_patterns + session_start.py Step 6b 이식

### ✅ naberal_game NotebookLM 딥 리서치 (6 쿼리, 57,609자 수집)
대표님 노트북 `a0bb9e88-b8cc-4a8d-a55a-75ffa01996eb` 소스 자료 기반:
- Q1 인디 현실 + MVP + 게임 디자인 (7,152자)
- Q2 Unity 6 LTS 전부 (9,301자)
- Q3 게임 아트 2D/3D + AI 2026 (12,265자)
- Q4 게임 오디오 (9,665자)
- Q5 Steam + 마케팅 + 한국 인디 (12,182자)
- Q6 관리/멘털 + 법률(한국) + AI 2026 (7,044자)
- 박제: `.planning/research/nlm_summary.md` + `.claude/memory/reference_beginner_gamedev_knowledge.md` + 6 wiki MOC 전수 반영
- 인프라 패치: `query.py` UTF-8 강제 (PYTHONUTF8=1) + `--notebook-url` lookup 우회 (secondjob_naberal skill cp949 호환) — game FAIL-001 박제

### Git Commits (세션 #28)
**shorts**:
```
e57f891 docs(claude-md): slim to 96 lines + add Perfect Navigator (대표님 directive)
```
+418/-418 대칭 교체 (Navigator 도입 효과).

**game (신규 repo)**:
```
02da275 feat(bootstrap): naberal_game studio Phase 0 창업 — 하네스 + AI 위키 + Obsidian 3층 조합
70a4bf1 feat(research): NotebookLM deep research 6-query — 초보 1인 인디 게임 개발 전 영역 지식
```

---

## 세션 #27 완료 항목

### ✅ Part A: 컨텍스트 단절 영구 수정 (commit `8172e9c`)
대표님 지적 "맨날 그거 안 읽고 모른다는 등 대화가 단절된다" 근본 원인 수정:
- `.claude/memory/` 로컬 저장소 10 파일 신규 (MEMORY.md + 9 메모리)
- `session_start.py` Step 4-6 추가 (WORK_HANDOFF 요약 + .env key 이름 + MEMORY 인덱스 자동 주입)
- `FAILURES.md` 신규 + F-CTX-01 등록 (재발 방지 박제)
- `CLAUDE.md` Session Init 섹션 업데이트
- 검증 12/12 PASS

### ✅ Phase 10 Plan 작성 (commit `83d2af8`)
GSD plan-phase workflow 전수 실행:
- 10-CONTEXT.md (3 Locked Decision 박제 — Exit Criterion B+C 하이브리드 / D-2 Lock 2개월 / Scheduler 하이브리드)
- 10-RESEARCH.md (1204줄, 73KB, HIGH confidence, 재사용 자산 7종 API 확인)
- 10-VALIDATION.md (Continuous Monitoring Model + 13 per-task map + Wave 0 requirements 14건)
- **8 PLAN.md** (4 Wave 구조)
- gsd-plan-checker iter 1: 2 BLOCKER + 4 WARNING + 2 INFO 발견
- gsd-planner revision iter 1: 6/6 issue 전수 resolved
- gsd-plan-checker iter 2: **VERIFICATION PASSED**
- 9 REQ-IDs 전수 커버 + D-2 Lock 준수 확인

### ✅ OAuth SCOPES 확장 (commit `2fda570`, Plan 3 Wave 0 선행)
대표님 "창 띄워봐" 요청:
- `scripts/publisher/oauth.py` SCOPES 2 → 3 (`yt-analytics.readonly` 추가)
- 기존 `config/youtube_token.json` 백업 후 재인증 실행
- 브라우저 자동 팝업 → 대표님 승인 → 3 scopes 확정
- `.gitignore` 에 `config/youtube_token.json.bak*` 패턴 추가
- Plan 3 Wave 0 OAuth step 이미 통과 상태

### ✅ Mac Mini 인프라 전환 계획 박제 (commit `e4ab949`)
대표님 세션 #27 확언 "맥미니 셋팅 안 해놔서 구현만 해놓고, 한동안 Windows PC 로 작업":
- `.claude/memory/project_server_infrastructure_plan.md` 신규 (10번째 메모리)
- Windows Task Scheduler → macOS launchd plist 3종 이관 절차 8단계 명시
- 이관 판정 3 조건 (Mac Mini OS 셋팅 + 상시 가동 + Windows 1개월+ 실적 축적)
- Plan 4 objective 에 Server Migration Note 추가
- 10-CONTEXT.md Deferred Ideas 에 Mac Mini migration 엔트리 추가

### ✅ NotebookLM 월간 업로드 합의 확인
대표님 확언 "매달 요구하면 업로드할게":
- Plan 6 (monthly_update.py line 446-452) 이미 stdout + email reminder 구조 완비
- 매달 1일 GH Actions cron 실행 → 대표님 이메일로 "업로드 요청" 발송 → 대표님 브라우저 1분 수동 업로드
- 추가 구현 불필요 (Plan 6 설계대로 실행되면 자동)

---

## 🎯 다음 세션 진입 경로

### A. Phase 10 execute-phase 진입
```bash
/gsd:execute-phase 10
```
Wave 1 (Plan 01 skill_patch_counter + Plan 02 drift_scan) 병렬 실행 시작. 대표님이 실행 시점 결정.

**Wave 구조**:
- Wave 1: Plans 01, 02 (D-2 Lock 실증 + drift 안전망)
- Wave 2: Plans 03, 04 (YouTube Analytics fetch + Scheduler 하이브리드)
- Wave 3: Plans 05, 06, 07 (session audit + research loop + YPP trajectory)
- Wave 4: Plan 08 (Rollback runbook)

### B. Phase 10 실행 중 대표님 manual dispatch 시점
1. **Plan 3 실행 직전**: OAuth 는 이미 완료 (세션 #27) ✅
2. **Plan 4 실행 시점**:
   - SMTP app password 생성 (Gmail 또는 Naver 2단계 인증 → 앱 비밀번호)
   - PowerShell 관리자 권한 실행 → `scripts/schedule/windows_tasks.ps1` 1회 (작업 3개 등록)
   - GH repo Settings → Secrets 에 5개 값 등록 (2개는 파일 복사, 3개는 대표님 입력)
3. **Plan 6 월간 운영 시작 후**: 매달 1일 이메일 알림 → NotebookLM 브라우저 업로드 1분

### C. 중장기 (Phase 11 candidate)
- Mac Mini 서버 이관 (memory: `project_server_infrastructure_plan`)
- auto-route Kling → Veo (수동 플래그 → 자동 fallback)
- audienceRetention timeseries 정확도 개선 (현재 audienceWatchRatio proxy)
- Producer AGENT.md monthly_context wikilink 추가 (D-2 Lock 해제 후)

---

## 세션 #27 Git Commits (shorts_studio)

```
e4ab949 docs(memory): 서버 인프라 전환 계획 박제 + Plan 4/CONTEXT 에 Mac Mini migration note
2fda570 feat(oauth): SCOPES 확장 — yt-analytics.readonly 추가 (Plan 3 Wave 0 선행)
83d2af8 docs(phase-10): plan 8 PLAN.md + RESEARCH + VALIDATION + CONTEXT — Sustained Operations 진입 준비
8172e9c fix(context): 세션 컨텍스트 단절 영구 수정 — memory 9종 + session_start Step 4-6 + FAILURES.md F-CTX-01
```

총 4 commits, +6394 lines.

---

## ⚠️ 세션 #27 이전 기록 (참고용, 세션 #26 상태)

## 세션 #24 최종 완료 항목

### ✅ Phase 9: Documentation + KPI Dashboard + Taste Gate
- 6/6 plans + 4/4 automated SC PASS + 14 commits
- ARCHITECTURE.md 332 lines (Mermaid 3 blocks, ⏱29 min)
- wiki/kpi/kpi_log.md Hybrid Part A/B + YouTube Analytics v2 contract
- taste_gate_protocol.md + taste_gate_2026-04.md (6 synthetic rows)
- scripts/taste_gate/record_feedback.py (Hook-compat, D-13 filter)
- UAT #3 technical pass (GitHub repo, Mermaid 렌더 확증)
- HUMAN-UAT #1/#2 pending (30분 온보딩 실측, Taste Gate UX)

### ✅ Phase 9.1: Production Engine Wiring
- 8/8 plans + 7/7 SC + phase091_acceptance ALL_PASS + 42/42 isolated tests
- invokers.py (Claude CLI subprocess, Max 구독, no API key)
- NanoBananaAdapter / CharacterRegistry / KenBurnsLocal / VALID_RATIOS_BY_MODEL / voice discovery
- 실 smoke $0.29 첫 Nano Banana → Runway chain
- **Architecture fix**: anthropic SDK → Claude CLI subprocess (commit 8af5063)

### ✅ 영상 I2V 스택 최종 확정 (세션 #24 후반)
대표님 결정 경위 4차 번복:
1. (오전) Runway Gen-4.5 primary (hair/smile 단순 motion 기준)
2. (오후) Runway Gen-3a Turbo primary (비용 절감 유혹)
3. (저녁) 복합 limb motion 실패 → Kling 2.6 Pro 실측 Pareto-dominant 확인
4. **(최종) Kling 2.6 Pro primary + Veo 3.1 Fast fallback** — 대표님 "Kling 2.5-turbo deprecated 사용안하다. kling 2.6 사용, 정밀하고 세세한걸 만들때는 kling이 실패하면 veo 3.1"

**최종 스택:**

| Tier | 모델 | Endpoint | 비용/5s | 상태 |
|------|------|----------|---------|------|
| Primary | Kling 2.6 Pro | `fal-ai/kling-video/v2.6/pro/image-to-video` | $0.35 | ✅ 확정 |
| Fallback | Veo 3.1 Fast | `fal-ai/veo3.1/fast/image-to-video` | $0.50 | ✅ 확정 |
| ~~Deprecated~~ | ~~Kling 2.5-turbo Pro~~ | — | — | 제거 |
| Hold (미호출) | Runway Gen-4.5 | `gen4.5` | $0.60 | adapter 유지 |

### ✅ Deep Research — I2V Prompt 3원칙 박제
- Research 18개 소스 (Tier 1/2/3), HIGH confidence
- Report: `.planning/research/runway_i2v_prompt_engineering_2026_04.md`
- **3원칙**: Camera Lock 명시 / Anatomy Positive Persistence (negative prompt 금지) / Micro Verb
- Templates A/B/C 세션 #24 실측 검증
- Memory `feedback_i2v_prompt_principles` 신규 박제

### ✅ 메모리 박제 (4건, 세션 #26 에서 #1 rename)
- `project_video_stack_kling26.md` (세션 #24 생성 시 `project_video_stack_runway_gen4_5.md`, 세션 #26 rename — D091-DEF-02 #3) 전면 재작 (Kling 2.6 primary + Veo 3.1 fallback)
- `feedback_i2v_prompt_principles.md` 신규 (3원칙 + Templates + fallback 조건)
- `project_claude_code_max_no_api_key.md` (세션 중 추가, anthropic SDK 영구 금지)
- `project_shorts_production_pipeline.md` (세션 중 추가, 4-stage chain)
- MEMORY.md index 4항목 갱신

---

## ✅ 박제 batch 전수 완료 (세션 #25, commit 4eb864d)

세션 #24 stack 4차 번복 이후 남은 drift 전파가 완전 복구됨. 실제 touch 범위는 handoff 기준(5항목) 대비 **7 파일 / ARCHITECTURE.md 5지점** 으로 확장 — drift cascade 로 추가 발견.

### 1. ✅ smoke CLI refactor (`scripts/smoke/phase091_stage2_to_4.py`)
- Kling 2.6 Pro primary + `--use-veo` 플래그 (수동 fallback)
- Template A (27단어, 3원칙) motion prompt 내재화
- Cost constant 갱신 (KLING $0.35, VEO $0.50)
- dry-run 양 경로 통과 (`provider=kling2.6-pro` / `veo3.1-fast`)
- auto-route 은 Phase 10 실패 패턴 축적 후 정식화 (Phase 9.1 out-of-scope)

### 2. ✅ wiki/docs drift 전수 복구
- `wiki/render/MOC.md` Scope + 5-model 실측 비교표 + Planned Nodes
- `wiki/render/remotion_kling_stack.md` 전면 재작성 (파일명 legacy, rename 은 Phase 10)
- `docs/ARCHITECTURE.md` **5지점** (handoff 지시 3 + 추가 발견 2: L187 Tier 2 render, L238-241 Video Generation Chain)

### 3. ✅ 신규 wiki node
- `wiki/render/i2v_prompt_engineering.md` 신설 (3원칙 + Templates A/B/C + 3-way 실측)

### 4. ✅ Phase 9.1 HUMAN-UAT + deferred-items 갱신
- 09.1-HUMAN-UAT.md #1: Kling 2.6 재생성 가이드 + procedure ($0.39 예상)
- deferred-items.md: D091-DEF-01 DEACTIVATED by stack switch 마크 + D091-DEF-02 신규 (7 cleanup items → Phase 10 batch window)

### 5. ✅ 통합 commit + 원격 푸시
- `4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)`
- `git push origin main` 완료 (dadfe58..4eb864d)
- 7 files changed, 399 insertions, 81 deletions

---

## 🎯 다음 세션 진입 경로

### A. ✅ Phase 10 Entry Gate PASSED (세션 #26 3차 batch flip)

**더 이상 HUMAN-UAT 대기 없음**. Phase 9 + 9.1 UAT 전수 resolved:
- Phase 9 UAT #1 `deprecated_single_operator_scope` (1인 운영자 scope 외)
- Phase 9 UAT #2 `deferred_phase_10_organic` (실 사용 시 자연 평가)
- Phase 9 UAT #3 `passed` (technical, 세션 #24)
- Phase 9.1 UAT #1 `passed_by_evidence` (세션 #24 실측 clip `output/prompt_template_test/kling26/kling_20260420_152355.mp4` 4.5MB + 대표님 피드백 후 스택 전환 commit `ff5459b`)
- Phase 9.1 UAT #2-a `passed_by_attestation` (대표님 "Typecast 계속 사용해왔던거다")
- Phase 9.1 UAT #2-b `deferred_phase_10` (primary Typecast 안정 시 실 호출 희귀)

### B. Phase 10 Sustained Operations — 대표님 `/gsd:plan-phase 10` trigger 대기
- Go Criteria #2 #3 은 Plan 작성 킥오프 시점 대표님 일괄 선언:
  - #2: Phase 10 missing deliverable 6개 (SC#1~6) 전부 vs 일부 선별
  - #3: D-2 저수지 규율 발동 조건 선언 (커밋 메시지 규칙 + 월별 검토 cadence)
- 주 3~4편 자동 발행 + **첫 1-2개월 SKILL patch 전면 금지 (D-2 저수지)** + 월 1회 Taste Gate
- Entry Gate: `.planning/PHASE_10_ENTRY_GATE.md` §5 참조

### C. Phase 10 batch window cleanup backlog (D091-DEF-02 잔여 6항목, 실 실패 데이터 축적 후)
- RunwayI2VAdapter 완전 제거 / hold 명시 주석 (tests 2개 연쇄)
- KlingI2VAdapter `NEG_PROMPT` 하드코드 재검토 (3원칙 원칙 2 충돌 가능성, Phase 10 실측 필요)
- ~~메모리 파일명 rename~~ (**세션 #26 RESOLVED** — `project_video_stack_runway_gen4_5` → `project_video_stack_kling26`, cascade 9 파일)
- Wiki 파일명 rename (`remotion_kling_stack.md` → `remotion_i2v_stack.md`, Phase 6 tests 3 + 29 파일 연쇄)
- NLM Step 2 `runway_prompt` 필드 → `i2v_prompt` rename (scripter agent template 동시 갱신)
- `remotion_src_raw/` 40 파일 고아 자산 integration (신규 작업)
- `Shotstack.create_ken_burns_clip` 완전 제거 (Phase 9.1 Plan 03 에서 deprecated 완료, 제거만 남음)

---

## 세션 #26 Git Commits (shorts_studio) — 3 batch

```
05a00f3 docs(memory): D091-DEF-02 #3 resolved — project_video_stack rename to kling26 + Stage 4 drift 복구 (1차, 7 files)
edd7312 feat(config): shorts_naberal TTS settings port + UAT #2 Typecast primary 재정의 (2차, 8 files +1558/-6)
(pending) fix(uat): evidence-first audit — Phase 9/9.1 UAT 전수 resolved + VERIFICATION passed flip + Entry Gate PASSED (3차)
```

## 세션 #26 3차 batch — evidence-first audit 요약

**대표님 질책 trigger**: "이미 어딘가에 입력되어있는거 자꾸 빠트린다고. 하네스 위키 이걸로 구현했는데 결과는 똑같은일이 반복되네"

**근본 원인 (하네스 설계 실패)**: HUMAN-UAT.md 작성자가 output/ 산출물 + SESSION_LOG 실측 기록 cross-reference 안 함. UAT.md 만 보고 "pending" 수용이 여러 세션 반복.

**3차 batch 결과**:
- **9 파일 변경** (memory 1 신규 + index 1 + UAT 2 + VERIFICATION 2 + Entry Gate 1 + 기타 2)
- **UAT 전수 resolved** (Phase 9 UAT #1 deprecated / #2 deferred / #3 passed + Phase 9.1 UAT #1 passed_by_evidence / #2-a passed_by_attestation / #2-b deferred_phase_10)
- **VERIFICATION 2종 passed flip** (09-VERIFICATION + 09.1-VERIFICATION)
- **PHASE_10_ENTRY_GATE status draft → PASSED**
- **재발 방지 메모리** `feedback_session_evidence_first` 영구 박제

## 세션 #26 2차 — shorts_naberal settings port 요약

**트리거**: 대표님 새 정보 2건 → "api key는 shorts_naberal" + "주 채널은 타입캐스트"
**정책 박제**: `feedback_clean_slate_rebuild` §예외 확장 — declarative config 포팅 허용

**포팅 완료**:
- `config/voice-presets.json` (611 lines) — 11 채널 Typecast + ElevenLabs voice matrix
- `config/channels.yaml` (693 lines) + PROVENANCE header
- `config/PROVENANCE.md` (신규, import 이력 + 비 이관 자산 13건 분류)
- `.env.example` (신규, TTS/Image/Video/YouTube key + ANTHROPIC 금지 명시)

**메모리 박제 3건 + 1 업데이트**:
- `reference_api_keys_location.md` (신규)
- `project_tts_stack_typecast.md` (신규) — Typecast primary / ElevenLabs fallback / Fish dead / EdgeTTS 폴백
- `reference_shorts_naberal_voice_setup.md` (신규) — 11 채널 매트릭스 + 숨은 규약 6개
- `feedback_clean_slate_rebuild.md` §예외 확장 추가

**UAT #2 재정의 (Phase 9.1)**:
- 2-a: Typecast primary voice resolution (주 채널 검증)
- 2-b: ElevenLabs fallback Korean voice (기존 내용 유지)

**D091-DEF-02 +3 항목**:
- #8 voice_discovery.py Typecast 확장
- #9 Fish Audio Tier 제거 → 3-tier 단순화
- #10 Phase 2 config port backlog (api-budgets, niche-profiles 등)

## 세션 #25 Git Commits (shorts_studio) — 박제 batch 완결

```
4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)  ← 세션 #25
(push: dadfe58..4eb864d → origin/main)
```

## 세션 #24 주요 Git Commits (shorts_studio)

```
425f385 docs: 세션 #24 핸드오프 3종 — shorts_studio Phase 9 + 9.1 + I2V stack final
ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)
8af5063 fix(09.1): architecture correction — anthropic SDK → Claude CLI subprocess
c86c570 docs(phase-9.1): evolve PROJECT.md
60dee8e test(09.1): persist VERIFICATION + HUMAN-UAT (status=human_needed)
3798b08..8dd3901 Phase 9.1 chain (20+ commits, discuss→plan→execute)
3292142 fix(drift): Runway Gen-3a Turbo primary (세션 중반, 후 번복)
5597440 (전 세션 #23) Phase 9 최종 commit
```

---

## 🚨 중요 Context (다음 세션 필독)

### 원칙 1: Claude Code Max 구독
- **ANTHROPIC_API_KEY 영구 금지** (memory: `project_claude_code_max_no_api_key`)
- `anthropic.Anthropic().messages.create()` = 별도 usage billing (금지)
- 모든 Claude 호출 = `subprocess.run(["claude", "--print", ...])` 경로

### 원칙 2: I2V 3원칙 (모든 motion prompt 필수 적용)
1. **Camera Lock 명시** (`"camera holds still"`)
2. **Anatomy Positive Persistence** (negative prompt 절대 금지)
3. **Micro Verb** (`"gently brings"` NOT `"lifts"`)

### 원칙 3: Kling → Veo Fallback 조건
- 정밀/세세한 motion 에서 Kling 실패 시 자동 전환
- 트리거: 얼굴 micro-expression / 손가락 articulation / 머리카락 simulation / 미세 light
- 비용 43% 증가 ($0.35 → $0.50), 빈도 제한 필요

### 원칙 4: D-2 저수지
- Phase 10 진입 후 **첫 1-2개월 SKILL patch 전면 금지**
- 실 실패 데이터 축적 → Phase 10 batch window 에서 일괄 patch

---

## 파일 경로 Quick Reference

```
Phase 9.1 smoke (구 Gen-3a Turbo 실패): output/phase091_smoke/clip.mp4
3-way 비교 MP4:                          output/prompt_template_test/{,gen45,kling26}/
Research report:                         .planning/research/runway_i2v_prompt_engineering_2026_04.md
Next session entry (HUMAN-UAT):          .planning/phases/09.1-production-engine-wiring/09.1-HUMAN-UAT.md
Phase 10 Entry Gate:                     .planning/PHASE_10_ENTRY_GATE.md
핵심 메모리:                              MEMORY.md (이번 세션 4개 갱신)
```

---

## 나베랄 감마 메모 (세션 #26 회고)

세션 #25 말미 대표님 "작업이어서 시작해라" 지시 → 세션 #25 제안 safe cleanup 실행 해석. D091-DEF-02 7항목 중 #3 (메모리 rename) 선별 실행. 원 scope 2 파일 → 실 touch **9 파일** cascade (세션 #25 교훈 재현).

**Cascade 구성**: 메모리 3 (신 파일 + index + cross-ref wikilink) + Stage 4 drift 복구 1 (production_pipeline 세션 #24 오전 기록 중 Runway Gen-4.5 잔재) + code docstrings 2 (kling_i2v / veo_i2v) + wiki backlinks 3 (remotion_kling_stack + i2v_prompt_engineering ×2) + deferred-items self 1 + MEMORY.md index line 20 drift 동반 발견.

**교훈 (세션 #26)**: 파일명은 여러 곳에 "박혀" 있음 — 박제 batch 계획 시 grep scope 가 기본 검증 수단이어야 함. "handoff 의 N 파일 추정" 을 신뢰하지 말고 실 grep 결과를 evidence 로 사용.

**의도적 미변경**: SESSION_LOG / Phase 9.1 CONTEXT.md 등 historical artifact 는 "사건 발생 시점의 명명" 이 증거가치를 가지므로 rename 전파 안 함. 세션 #26 SESSION_LOG entry 에 기준 명시.

**D091-DEF-02 잔여 6항목**: Phase 10 batch window 유지 (D-2 저수지 규율, 실측 데이터 대기). 특히 wiki rename (#4) 은 Phase 6 tests 3개 + 29 파일 touch 로 regression 위험 커 불가.

Phase 10 진입까지 남은 실 작업 = **HUMAN-UAT 4건 (대표님 수동 only, 무변경)**. AI 추가 작업 없음.

---

*Updated 2026-04-20 by 나베랄 감마 (session #26 safe memory rename + Stage 4 drift 복구)*
*세션 #24/#25 handoff: archived in SESSION_LOG.md*
