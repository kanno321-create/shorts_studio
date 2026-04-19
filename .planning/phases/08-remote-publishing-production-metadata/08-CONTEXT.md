---
phase: 8
phase_name: remote-publishing-production-metadata
status: ready-for-planning
gathered: 2026-04-19
mode: auto (YOLO continuation from Phase 7)
smoke_test_gate: before_first_real_youtube_upload
---

# Phase 8: Remote + Publishing + Production Metadata — Context

**Gathered:** 2026-04-19 (session #21 YOLO auto-continuation)
**Status:** Ready for planning
**Mode:** `--auto` (recommended defaults auto-selected, logged per decision)

<domain>
## Phase Boundary

Phase 8 delivers **실제 외부 상태 변이**를 일으키는 세 가지 능력만:

1. **Remote** — `github.com/kanno321-create/shorts_studio` Private 저장소 생성 + `git push -u origin main` + `naberal_harness v1.0.1` submodule 연결 (REMOTE-01/02/03)
2. **Publishing** — `scripts/publisher/youtube_uploader.py` YouTube Data API v3 실 업로드 모듈 + OAuth 2.0 refresh token + 48h+ 랜덤 간격 + KST 피크 윈도우 enforcement (PUB-01/02/03 실행층)
3. **Production Metadata** — `production_metadata.json` 생성 + video description HTML 주석 삽입 + 핀 댓글 + end-screen subscribe funnel (PUB-04/05)

Phase 4 publisher AGENT.md는 업로드 **계획 JSON 스펙**만 생성. Phase 8은 그 JSON을 받아 실제 `videos.insert` API를 호출하고 YouTube 채널에 물리적 업로드를 수행한다.

**Not in scope (defer to Phase 9+):**
- KPI 수집 / Analytics cron (KPI-01/02 → Phase 9)
- Taste Gate / Auto Research Loop (KPI-03/05 → Phase 9/10)
- 실시간 SKILL patch 금지 규율 장기 운영 (FAIL-04 → Phase 10)
- Auto-draft 재업로드 / 삭제 복구 로직 (out of v1)

</domain>

<decisions>
## Implementation Decisions

### Remote 연결 (REMOTE-01/02/03)

- **D-01 (auto-selected):** GitHub 인증 = **Fine-grained Personal Access Token (PAT)** — repo별 scope 제한, 90일 만료 갱신 가능, OAuth App 오버헤드 회피
  - **Why:** 단일 사용자 Private repo에 OAuth App은 과도. Fine-grained PAT가 scope(`contents:write`, `metadata:read`)만 부여 가능하여 최소권한 원칙 준수. Deploy Key는 push 전용으로는 가능하나 repo 생성 API 호출 불가.
  - **How to apply:** PAT를 `GITHUB_TOKEN` env var로 주입 (gitignore된 `.env` 파일 또는 세션 export). 하드코딩/commit 금지.

- **D-02 (auto-selected):** 하네스 연결 방식 = **git submodule** (경로 `harness/` 로컬, remote URL `github.com/kanno321-create/naberal_harness`)
  - **Why:** REQUIREMENTS REMOTE-03이 "submodule or 참조"로 표기 — submodule이 버전 고정 + clone 시 자동 연결 + PROJECT.md "v1.0.1 상속" 선언과 정합. Subtree는 harness 원본 수정 리스크. Symlink는 clone 이식성 부재.
  - **How to apply:** `git submodule add` 후 `.gitmodules` 커밋. 경로는 PROJECT Constraints의 `../../harness/`가 아닌 **studio 내 `harness/`** — clone 시 항상 같은 레이아웃 보장을 위해.

- **D-03 (auto-selected):** Push 대상 branch = **`main`** (master → main 전환은 shorts_studio 신규 저장소이므로 main으로 직접 시작). shorts_studio 로컬 현재 branch는 `master` — Phase 8 Wave 1에서 `git branch -m master main` 후 push.
  - **Why:** GitHub 2020+ default branch = main. 신규 저장소에 master로 시작할 이유 없음.
  - **How to apply:** Wave 1 atomic commit 내에서 rename + remote push 일괄 수행.

### YouTube Publishing (PUB-01/02/03)

- **D-04 (auto-selected):** YouTube OAuth 2.0 flow = **Installed Application (desktop)** + refresh token stored in `config/youtube_token.json` (gitignored)
  - **Why:** publisher AGENT.md 명시 `auth: oauth2_refresh_token`. Service Account는 YouTube Data API v3 채널 업로드 미지원 (Google 정책). Web OAuth는 flask 서버 필요.
  - **How to apply:** `client_secret.json` (Google Cloud Console 생성, gitignored) → `InstalledAppFlow.run_local_server(port=0)` 로 1회 인증 → refresh token 획득 후 `youtube_token.json` 저장. 이후 세션은 refresh token만 사용.

- **D-05 (auto-selected):** AI disclosure 강제 방식 = **업로드 metadata에 `syntheticMedia` flag hardcoded True** (PUB-01, A-P3 차단)
  - **Why:** Typecast/ElevenLabs 합성 음성을 항상 사용. 스위치 off 경로 자체를 코드에 넣지 않음 (D-7 "물리 차단" 원칙 계승).
  - **How to apply:** `scripts/publisher/youtube_uploader.py`의 upload payload 빌드 함수에서 `ai_disclosure.syntheticMedia=True` 하드코딩. grep 검사로 `syntheticMedia.*False` 0 hit anchor test.

- **D-06 (auto-selected):** 48h+ 랜덤 간격 enforcement = **filesystem JSON lock** (`.planning/publish_lock.json`, last_upload_iso + jitter_applied_min)
  - **Why:** publisher AGENT.md 이미 `.planning/publish_lock.json` 명시. SQLite는 단일 lock state에 과도. Redis는 인프라 의존.
  - **How to apply:** Upload 직전 lock 파일 atomic read → elapsed_hours < 48 + jitter → raise `PublishLockViolation`. Upload 성공 직후 `os.replace`로 lock 갱신.

- **D-07 (auto-selected):** KST 피크 윈도우 = **평일 20:00-23:00 KST / 주말 12:00-15:00 KST** (PUB-03, publisher AGENT.md 그대로 승계)
  - **Why:** publisher AGENT.md 이미 확정. 재논의 불필요.
  - **How to apply:** `zoneinfo.ZoneInfo("Asia/Seoul")` + `datetime.now(kst)` → weekday()/hour 검사 → 윈도우 밖이면 다음 윈도우까지 sleep 또는 raise `PublishWindowViolation`.

### Production Metadata + Funnel (PUB-04/05)

- **D-08 (auto-selected):** production_metadata 삽입 위치 = **video description 말미 HTML 주석** (`<!-- production_metadata ...JSON... -->`)
  - **Why:** publisher AGENT.md 이미 확정. YouTube 시청자에게 보이지 않음. E-P2 (Reused Content 이의제기) 역추적 가능. 태그 필드 (500 char limit) 대비 공간 여유.
  - **How to apply:** 4-field minimum: `script_seed`, `assets_origin`, `pipeline_version`, `checksum` (sha256 of mp4). Phase 4 ins-platform-policy가 이미 production_metadata 4-field enforcement 검증.

- **D-09 (auto-selected):** 핀 댓글 + end-screen = **업로드 직후 자동 실행** (`comments.insert` + `captions.insert` 체인)
  - **Why:** PUB-05 DF-9. 수동 실행 시 누락 리스크.
  - **How to apply:** Upload 성공 → `videos.list(id)` 대기 processingStatus=succeeded → `commentThreads.insert` 핀 댓글 → end-screen은 `videos.update` endScreen 필드 (Data API v3 미지원 — **YouTube Studio UI 한정**; 대안으로 description 내 subscribe 링크 + pinned comment CTA로 대체).

### Test Strategy

- **D-10 (auto-selected):** 테스트 전략 = **Phase 7 mock 스타일 + smoke test 1회 실 업로드**
  - **Why:** Phase 7이 177 테스트 + 3 Correction anchor로 mock 파이프라인 완성. 실 API 호출은 smoke test 1회로 최소화 (Option A 사용자 선택).
  - **How to apply:** Unit + integration 테스트는 Phase 7 MockShotstack 패턴 계승 (`MockYouTube`, `MockGitHub`). Smoke test는 **privacyStatus=unlisted** + 업로드 직후 `videos.delete` cleanup (실 채널 이력 방지). Phase 8 Wave 5가 smoke test gate 전용 plan.

- **D-11 (auto-selected, Option A):** Smoke test gate = **최초 `MockYouTube` → `RealYouTubeAdapter` 교체 직전 1회 승인 멈춤**
  - **Why:** 사용자 Option A 확정. GitHub push (SC1/2)는 reversible. YouTube upload (SC3/4/5/6)는 채널 영구 이력.
  - **How to apply:** Wave 5 plan 내에 "SMOKE-GATE" 마커 섹션 명시. Plan 08-05-PLAN.md 실행 직전 orchestrator가 `대표님 승인 필요` 출력 후 정지. 대표님 "진행" 확인 후 smoke test 실행.

### Claude's Discretion

- **CD-01:** Unit test 파일 네이밍 (`test_youtube_uploader.py`, `test_github_remote.py` 등) — Phase 7 `test_{gate}.py` 관례 계승
- **CD-02:** 예외 클래스 이름 (`PublishLockViolation`, `PublishWindowViolation`, `AIDisclosureViolation`) — scripts/orchestrator/ 기존 10-class hierarchy 스타일 계승
- **CD-03:** submodule 내부 경로 충돌 시 resolution — Wave 1 실행 중 발견 시 내부 판단

### Folded Todos

*No pending todos matched Phase 8 scope (TODO_MATCHES returned empty).*

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher, planner, executor) MUST read these before acting.**

### Phase Scope
- `.planning/ROADMAP.md` §Phase 8 — 6 Success Criteria + depends-on Phase 7 + Requirements PUB-01..05 + REMOTE-01..03
- `.planning/REQUIREMENTS.md` lines 116-122 (PUB), 163-167 (REMOTE) — 8 requirements text
- `.planning/PROJECT.md` §Constraints (line 70) — "원격 = github.com/kanno321-create/shorts_studio (Phase 8)"

### Agent Spec
- `.claude/agents/producers/publisher/AGENT.md` — Phase 4 publisher JSON spec (auth: oauth2_refresh_token, 48h+ jitter, KST window, AI disclosure, production_metadata 4-field, 핀 댓글 + end-screen)

### Anti-Patterns (must not violate)
- `.planning/PROJECT.md` §Out of Scope — `shorts_naberal` 직접 수정 금지, Selenium 업로드 금지 (AF-8)
- `.planning/ROADMAP.md` §Hard Constraints — Selenium 업로드 영구 금지, 모든 업로드 YouTube Data API v3 공식만
- `.claude/deprecated_patterns.json` — 8 entries (Phase 5 core 6 + Phase 6 FAIL audit trail 2). Hook이 enforce.

### Prior Phase Wiring
- `.planning/phases/07-integration-test/07-VERIFICATION.md` — Phase 7 all 5 SC PASS, 986/986 tests, 3 Corrections anchored. Phase 8 회귀 baseline.
- `scripts/orchestrator/api/shotstack.py` — Phase 6 continuity_prefix injection 패턴 (Phase 8 youtube_uploader.py가 유사 구조로 payload 빌드 시 참조)
- `scripts/orchestrator/circuit_breaker.py` — CircuitBreaker + CircuitBreakerOpenError (Phase 8 YouTube API 호출도 CircuitBreaker 래핑 필요)

### Google / YouTube API 공식 문서 (researcher가 context7 조회 대상)
- YouTube Data API v3 `videos.insert` 엔드포인트 spec
- `commentThreads.insert` (핀 댓글)
- `thumbnails.set` (커스텀 썸네일)
- Google OAuth 2.0 Installed Application flow
- `google-api-python-client` + `google-auth-oauthlib` (Python client libraries)

### GitHub API 공식 문서 (researcher가 context7 조회 대상)
- `POST /user/repos` (Private repo 생성)
- Fine-grained PAT scope matrix
- `.gitmodules` + `git submodule add` 공식 ref

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`scripts/orchestrator/circuit_breaker.py`** — CircuitBreakerOpenError + 3x/300s state machine. Phase 8 YouTube API 호출 시 동일 패턴 재사용 권장.
- **`scripts/orchestrator/checkpointer.py`** — atomic `os.replace` JSON round-trip. `publish_lock.json` 저장 시 동일 패턴 재사용.
- **`scripts/orchestrator/api/shotstack.py`** — lazy loader + dict payload build 패턴. `youtube_uploader.py` 구조 레퍼런스.
- **`tests/phase07/mocks/shotstack_mock.py`** — 5번째 mock adapter의 D-3 `allow_fault_injection` 기본값 False 패턴. `MockYouTube` / `MockGitHub` 에 계승.

### Established Patterns
- **Hook 3종 (pre_tool_use.py / post_tool_use.py / session_start.py)** — 이미 `selenium` import 시도를 차단. Phase 8 코드에 selenium 0 hits anchor test 필수.
- **atomic commit discipline** — Phase 5/6/7 48+ commit 관례: test RED → feat GREEN → docs. Phase 8 도 동일 리듬.
- **frontmatter + VALIDATION.md 체크박스 flip** — 08-VALIDATION.md 생성 후 각 task 완료마다 ❌→✅ flip.

### Integration Points
- **`scripts/publisher/` 디렉토리** — 미존재 (Phase 8에서 최초 생성). `scripts/orchestrator/api/` 레이아웃 레퍼런스.
- **`.planning/publish_lock.json`** — 미존재 (Phase 8 Wave 3에서 최초 생성). gitignore 추가 필요 (upload 이력 노출 방지).
- **`.gitmodules`** — 미존재 (Phase 8 Wave 1에서 최초 생성).
- **`config/client_secret.json` + `config/youtube_token.json`** — 미존재 (Phase 8 Wave 2에서 획득). `.gitignore` 이미 `client_secret.json` + `token.json` 추가되어 있음 (line 3-4).

</code_context>

<specifics>
## Specific Ideas

- **Option A 사용자 확정:** smoke test gate는 **최초 real YouTube adapter 실행 직전 1회**만 멈춤. GitHub push는 YOLO로 통과. 이후 smoke test 성공 시 YOLO 재개.
- **Smoke test 본체 디자인:** privacyStatus=unlisted로 업로드 → upload_id 수신 → 30초 대기 → `videos.list` 로 processingStatus 확인 → `videos.delete` 로 cleanup. 실 채널 이력에 남지 않음.
- **harness submodule 버전 고정:** `naberal_harness v1.0.1` 상응 commit hash 확인 후 submodule add 시 해당 SHA로 checkout. drift 방지.
- **shorts_studio 디렉토리 독립 git repo 확인 완료:** `cd studios/shorts && git status` 작동 확인 (session log). 저장소 생성 후 remote add만 남음.

</specifics>

<deferred>
## Deferred Ideas

- **자동 재업로드 / 실패 복구** — 업로드 실패 시 다음 윈도우 자동 재시도. v2 에서 검토 (현재 1회 실패 시 FAILURES.md append 후 수동 재시도).
- **multi-channel publishing** — 같은 영상을 여러 채널에 동시 업로드. 현재 단일 채널 확정.
- **automated subscribe funnel A/B testing** — 핀 댓글 문구 2가지 variant 랜덤 할당. KPI-03 Auto Research Loop (Phase 10)에서 처리.
- **YouTube Shorts 썸네일 커스터마이즈 API** — 공식 지원 확인 필요. 현재 `thumbnails.set`로 처리.

</deferred>

<auto_log>
## Auto-Selected Decisions (--auto Mode Log)

Each choice logged for user review per discuss-phase-auto protocol:

- [auto] Remote — Q: "GitHub 인증 방식?" → Selected: "Fine-grained PAT" (recommended: 최소권한 + 90일 회전)
- [auto] Remote — Q: "harness 연결 방식?" → Selected: "git submodule" (recommended: 버전 고정 + clone 이식성)
- [auto] Remote — Q: "Push 대상 branch?" → Selected: "main" (recommended: 신규 저장소 현대 관례)
- [auto] Publishing — Q: "YouTube OAuth flow?" → Selected: "Installed Application" (recommended: refresh token 내구성)
- [auto] Publishing — Q: "AI disclosure 구현?" → Selected: "hardcoded True flag" (recommended: D-7 물리 차단 계승)
- [auto] Publishing — Q: "48h 간격 enforcement?" → Selected: "filesystem JSON lock" (recommended: AGENT.md 기존 스펙)
- [auto] Publishing — Q: "KST 윈도우?" → Selected: "평일 20-23 / 주말 12-15 KST" (AGENT.md 확정)
- [auto] Metadata — Q: "production_metadata 위치?" → Selected: "description HTML 주석" (AGENT.md 확정)
- [auto] Metadata — Q: "핀 댓글 + end-screen 자동?" → Selected: "업로드 직후 API 체인" (recommended: 수동 누락 방지)
- [auto] Test — Q: "테스트 전략?" → Selected: "mock + smoke 1회" (Option A 사용자 확정)
- [auto] Test — Q: "Smoke gate 위치?" → Selected: "real YouTube 교체 직전" (Option A 사용자 확정)

</auto_log>

---

*Phase: 08-remote-publishing-production-metadata*
*Context gathered: 2026-04-19 by gsd-discuss-phase --auto (session #21 YOLO)*
*Next: `/gsd:plan-phase 8 --auto` to research + generate PLAN per wave*
