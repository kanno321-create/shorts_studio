---
document: PHASE_10_EXECUTE_PREFLIGHT
status: ready
created: 2026-04-20
author: 나베랄 감마 (session #27)
consumers: [gsd-executor, 대표님 execute-phase 진입 시]
purpose: /gsd:execute-phase 10 실행 직전 preflight 체크리스트 + Wave 별 대표님 액션 포인트 + 예상 소요 + 돌발 상황 대응
supersedes: none
---

# Phase 10 Execute — Preflight Checklist

> **언제 읽는가**: 대표님이 `/gsd:execute-phase 10` 실행하기 직전 또는 중간에 막힐 때.
>
> **왜 3번째 핸드오프인가**: WORK_HANDOFF 는 "전체 상태", SESSION_LOG 는 "역사 박제". 이 문서는 "다음 action 을 1 페이지로 요약" — preflight 전용.

---

## §0. Pre-Flight Checklist (실행 전 확인)

다음 5개 **전부 YES** 일 때만 `/gsd:execute-phase 10` 실행 허가:

- [x] **§1 Entry Gate PASSED** — 세션 #26 3차 batch flip 완료. `.planning/PHASE_10_ENTRY_GATE.md` status: PASSED.
- [x] **Part A 컨텍스트 단절 수정 완료** — commit `8172e9c`. 메모리 10종 + session_start Step 4-6 + FAILURES.md.
- [x] **Phase 10 Plan 8개 작성 + 검증 완료** — commit `83d2af8`. gsd-plan-checker iter 2 VERIFICATION PASSED.
- [x] **OAuth analytics scope 확장 완료** — commit `2fda570`. Plan 3 Wave 0 선행 처리. 3 scopes + refresh_token 확인.
- [x] **origin 동기화 완료** — commit `628e4b7` (본 문서 포함). GitHub private repo 에 push 완료.

현재 상태 **5/5 YES** ✅ → `/gsd:execute-phase 10` 실행 허가됨.

---

## §1. Wave 별 실행 흐름 + 대표님 액션 포인트

### Wave 1 (병렬 2개, 예상 30~60분) — D-2 Lock 실증 + drift 안전망

| Plan | 파일 | 핵심 액션 |
|------|------|---------|
| 10-01 | `scripts/audit/skill_patch_counter.py` | git log --since="2026-04-20" 기반 금지 경로 수정 카운트. `reports/skill_patch_count_YYYY-MM.md` 월간 리포트 출력. FAILURES.md F-D2-XX 자동 append (count > 0 시). |
| 10-02 | `scripts/audit/drift_scan.py` + `.claude/deprecated_patterns.json` grade 확장 + `.planning/STATE.md` phase_lock 필드 | harness drift_scan.py import + A급 drift 감지 시 `phase_lock: true` + gh issue 자동 생성. |

**대표님 액션**: **없음** (AI 가 자동). 완료 시 터미널에 "Wave 1 COMPLETE" 출력.

**돌발 상황**:
- Plan 2 Wave 0 에서 `STATE.md frontmatter 확장` 이 GSD parser 호환 안 맞으면 smoke fail → AI 가 자동으로 `phase_lock` 필드만 minimal 추가 대안 채택.
- `deprecated_patterns.json` grade 추가 후 Phase 5/6 regression 깨지면 → AI 가 gsd-debugger 로 원인 분석 + fix.

---

### Wave 2 (병렬 2개, 예상 60~90분) — 데이터 수집 + Scheduler

| Plan | 파일 | 핵심 액션 |
|------|------|---------|
| 10-03 | `scripts/analytics/fetch_kpi.py` + `monthly_aggregate.py` | YouTube Analytics v2 `reports.query` 엔드포인트 호출. 기존 oauth.get_credentials() 재사용 (세션 #27 에서 scope 이미 확장). `wiki/shorts/kpi_log.md` Part B append. |
| 10-04 | `.github/workflows/` 4 YAML + `scripts/schedule/windows_tasks.ps1` + `scripts/schedule/notify_failure.py` | GH Actions cron 4종 + Windows Task Scheduler ps1 + SMTP email 알림. |

**🔴 대표님 액션 필수 (Plan 4 실행 중 터미널이 물어볼 것)**:

#### 액션 A: SMTP app password 생성 (Gmail 또는 Naver)
**Gmail 경우**:
1. [myaccount.google.com](https://myaccount.google.com) → **보안** → **2단계 인증** (켜져있어야 함)
2. **앱 비밀번호** → "앱 선택" = "메일" / "기기 선택" = "Windows 컴퓨터" → 생성
3. 16자리 비밀번호가 나옴 (한번만 표시) → 복사해서 AI 에게 전달

**Naver 경우**:
1. [nid.naver.com](https://nid.naver.com) → 로그인 → **내정보** → **보안설정** → **2단계 인증** (켜져있어야 함)
2. **애플리케이션 비밀번호** → 이름 "shorts-studio" → 생성
3. 비밀번호 복사

#### 액션 B: GitHub Secrets 5개 등록
터미널에 다음 명령 5줄 순서대로 실행 (AI 가 정확한 값을 안내):
```bash
gh secret set YOUTUBE_CLIENT_SECRET < config/client_secret.json
gh secret set YOUTUBE_TOKEN_JSON < config/youtube_token.json
gh secret set RECENT_VIDEO_IDS -b "<Plan 3 이 자동 수집>"
gh secret set SMTP_USER -b "<대표님 email, 예: kanno3@naver.com>"
gh secret set SMTP_APP_PASSWORD -b "<액션 A 에서 생성한 16자리 비밀번호>"
```
(또는 GitHub 웹 → repo Settings → Secrets and variables → Actions → New repository secret)

#### 액션 C: Windows Task Scheduler 등록 (1회만)
1. **시작** 검색창에 `PowerShell` → 우클릭 → **관리자 권한으로 실행**
2. 터미널에 다음 복붙 후 엔터:
```powershell
cd "C:\Users\PC\Desktop\naberal_group\studios\shorts"
& .\scripts\schedule\windows_tasks.ps1
```
3. "작업 3개 등록 완료" 메시지 확인

**돌발 상황**:
- GH Actions 권한 부족 → `gh auth login` 먼저
- Windows Task Scheduler 권한 부족 → 관리자 PowerShell 재시작
- SMTP 인증 실패 → 2단계 인증 ON 재확인 (앱 비밀번호는 2단계 인증이 ON 이어야 생성 가능)

---

### Wave 3 (병렬 3개, 예상 60~90분) — 학습 회로 + 궤도 시각화

| Plan | 파일 | 핵심 액션 |
|------|------|---------|
| 10-05 | `scripts/session_start.py` (30-day rolling, hook 과 별개) | `.claude/hooks/session_start.py` 출력 로그를 `logs/session_audit.jsonl` 에 append. 30일 rolling 평균 점수 ≥ 80 assertion. |
| 10-06 | `scripts/research_loop/monthly_update.py` + template | 상위 3 영상 composite_score 계산 + NotebookLM subprocess query + `wiki/shorts/kpi/monthly_context_YYYY-MM.md` 생성 + 대표님 email reminder. |
| 10-07 | `scripts/analytics/trajectory_append.py` + `wiki/ypp/trajectory.md` 확장 | 월별 구독자/뷰 append + 1차/2차/3차 gate 진행률 계산 + Mermaid line chart. |

**대표님 액션**: **없음**.

---

### Wave 4 (단독 1개, 예상 15~30분) — 안전망 문서

| Plan | 파일 | 핵심 액션 |
|------|------|---------|
| 10-08 | `.planning/phases/10-sustained-operations/ROLLBACK.md` + `scripts/rollback/stop_scheduler.py` | 무인 운영 사고 3 시나리오 (업로드 사고 / scheduler 버그 / 학습 회로 오염) 별 복구 경로 + 긴급 중단 CLI. |

**대표님 액션**: 완료 후 AI 가 전체 요약 + Phase 10 COMPLETE 메시지 출력. 대표님이 1회 읽고 확인.

---

## §2. 전체 예상 소요

| 단계 | AI 시간 | 대표님 시간 |
|------|---------|-----------|
| Wave 1 | 30~60분 | 없음 (모니터링 optional) |
| Wave 2 | 60~90분 | **15~20분** (SMTP + GH Secrets + PowerShell) |
| Wave 3 | 60~90분 | 없음 |
| Wave 4 | 15~30분 | 없음 |
| **합계** | **2.5~4.5 시간** | **15~20분** |

대표님 실제 집중 시간 = Wave 2 의 15~20분. 나머지는 백그라운드 진행.

---

## §3. 실행 중 AI 가 보여줄 터미널 메시지 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► EXECUTING PHASE 10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Wave 1] Spawning executors in parallel...
  ◆ 10-01-skill-patch-counter: task 1/2 — scripts/audit/skill_patch_counter.py 작성
  ◆ 10-02-drift-scan-phase-lock: task 1/2 — deprecated_patterns.json grade 확장 + STATE.md frontmatter smoke
  ...
  [Wave 1 COMPLETE — 42 min]

[Wave 2] Spawning executors...
  ◆ 10-03 task 1/2: scripts/analytics/fetch_kpi.py 작성
  ◆ 10-04 task 1/2: .github/workflows/ 4 YAML 작성
  ...
  ⏸ PAUSE FOR MANUAL DISPATCH
    → 대표님 액션 필요:
      1. SMTP app password 생성 (Gmail 또는 Naver)
      2. GitHub Secrets 5개 등록
      3. Windows PowerShell 관리자 권한 → windows_tasks.ps1 실행
    → 완료 후 "done" 입력하여 재개
  ...
  [Wave 2 COMPLETE — 78 min]

[Wave 3] ...
[Wave 4] ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PHASE 10 COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## §4. 실패 / 중단 시 대응

### 4.1 AI 가 task 중간에 막히면
- 자동으로 `## CHECKPOINT REACHED` 메시지 출력 + 상태 저장
- 대표님이 `/gsd:resume-work` 로 재개 가능
- 또는 `/gsd:debug` 로 디버깅 세션 진입

### 4.2 Plan 중 특정 task 실패 (테스트 fail 등)
- AI 가 gsd-debugger 호출 → 원인 분석 → fix → 재실행
- 3회 fail 시 사람 개입 요청 (대표님께 원인 + 옵션 제시)

### 4.3 대표님이 도중 중단하고 싶으면
- Ctrl+C 1회 → AI 가 "정말 중단?" 확인
- 2회 → 중단 + 현재 상태 WORK_HANDOFF 자동 박제

### 4.4 GH Actions 등록 후 cron 이 안 돌아갈 때
- Plan 8 ROLLBACK.md 시나리오 2 참조
- `gh workflow view` 로 상태 확인
- `drift-scan-weekly.yml` manual trigger: `gh workflow run drift-scan-weekly.yml`

---

## §5. 완료 후 상태

### 생성된 파일 (예상 40+ 파일)
- `scripts/audit/` — 2 Python + 2 test
- `scripts/analytics/` — 2 Python + 2 test
- `scripts/research_loop/` — 2 Python + 1 template + 1 test
- `scripts/schedule/` — 1 Python + 1 PowerShell + 2 test
- `scripts/rollback/` — 1 Python + 1 test
- `scripts/session_start.py` (30-day rolling, hook 과 별개)
- `.github/workflows/` — 4 YAML
- `wiki/ypp/trajectory.md` + `wiki/shorts/kpi/monthly_context_*.md` + `wiki/shorts/kpi_log.md` Part B
- `reports/` + `logs/` 신규 디렉토리 (월간/세션 로그)
- `.planning/phases/10-sustained-operations/ROLLBACK.md`

### 활성화된 자동화
- **매일 새벽**: YouTube Analytics 데이터 수집 + kpi_log Part B append
- **매주 월요일**: drift_scan 전수 검사 + A급 발견 시 phase_lock + gh issue
- **매월 1일**: skill_patch_counter 집계 + monthly_update 상위 3 분석 + 대표님 이메일 reminder + harness_audit + YPP trajectory 월별 append
- **대표님 세션 시작 시**: session_start.py 30-day rolling score 표시
- **대표님 PC on 시 매일 저녁**: 영상 생성 파이프라인 + YouTube 업로드 (publish_lock 48h gating)

### 주 3~4편 자동 운영 시작 가능
Plan 1~4 완료 후 즉시. Plan 5~8 은 learning + 안전망 계층이라 병행 진행해도 운영 시작에 영향 없음.

---

## §6. Phase 10 이후 (Phase 11 candidate, 메모리 박제됨)

- **Mac Mini 서버 이관** (`project_server_infrastructure_plan.md`) — Windows Task Scheduler → macOS launchd
- **auto-route Kling → Veo** — 수동 플래그 → 실패 패턴 기반 자동 fallback
- **Producer AGENT.md monthly_context wikilink** — D-2 Lock 해제 (2026-06-20) 후
- **audienceRetention timeseries 정확도 개선** — 현재 audienceWatchRatio proxy → 실측 오차 확인 후
- **D091-DEF-02 잔여 6항목** batch window cleanup

---

## References

- [WORK_HANDOFF.md](../../../WORK_HANDOFF.md) — 전체 세션 상태
- [SESSION_LOG.md](../../../SESSION_LOG.md) — 역사 박제 (세션 #27 포함)
- [10-CONTEXT.md](./10-CONTEXT.md) — 3 Locked Decision + canonical refs
- [10-RESEARCH.md](./10-RESEARCH.md) — 기술 근거 1204줄
- [10-VALIDATION.md](./10-VALIDATION.md) — Continuous Monitoring + Wave 0 requirements
- [10-01~08-*.md](./) — 8 Plan 실제 실행 명령서
- [PHASE_10_ENTRY_GATE.md](../../PHASE_10_ENTRY_GATE.md) — 진입 게이트 (PASSED)

---

*Generated 2026-04-20 by 나베랄 감마 during session #27, as 3rd handoff artifact for next session smooth execute-phase entry.*
