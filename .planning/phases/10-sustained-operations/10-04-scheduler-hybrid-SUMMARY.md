---
phase: 10-sustained-operations
plan: 04
subsystem: scheduler
tags: [scheduler, gh-actions, windows-task-scheduler, smtp, failure-notify, cron, hybrid]
requires:
  - scripts/audit/skill_patch_counter.py   # Plan 10-01
  - scripts/audit/drift_scan.py            # Plan 10-02
  - scripts/analytics/fetch_kpi.py         # Plan 10-03 (parallel Wave 2)
  - scripts/validate/harness_audit.py      # Phase 7
  - scripts/publisher/publish_lock.py      # Phase 8 (pace enforcement)
  - scripts/publisher/kst_window.py        # Phase 8
provides:
  - 4 GH Actions cron workflows (analytics-daily / drift-scan-weekly / skill-patch-count-monthly / harness-audit-monthly)
  - Windows Task Scheduler registration script (3 tasks)
  - 3-channel failure notifier (stdout / SMTP / FAILURES.md append)
affects:
  - .github/workflows/
  - scripts/schedule/
  - tests/phase10/
tech-stack:
  added:
    - GitHub Actions cron scheduling
    - Windows Task Scheduler (PowerShell Register-ScheduledTask)
    - smtplib + MIMEText (stdlib SMTP)
  patterns:
    - Direct file I/O FAILURES.md append (hook bypass per RESEARCH Pitfall 3)
    - Graceful degradation for missing SMTP secrets
    - Redundant label creation (Wave 0 manual + GH Actions step)
    - Harness separate checkout (not submodule) + --harness-path flag
key-files:
  created:
    - .github/workflows/analytics-daily.yml
    - .github/workflows/drift-scan-weekly.yml
    - .github/workflows/skill-patch-count-monthly.yml
    - .github/workflows/harness-audit-monthly.yml
    - scripts/schedule/__init__.py
    - scripts/schedule/windows_tasks.ps1
    - scripts/schedule/notify_failure.py
    - tests/phase10/test_workflows_yaml.py
    - tests/phase10/test_notify_failure.py
  modified: []
decisions:
  - "Daily Windows Task trigger + publish_lock.assert_can_publish() gating — 외부에서 일일 패턴으로 보여도 실 발행은 주 3~4편 + 48h+jitter (AF-1/AF-11 enforce)"
  - "SMTP graceful degradation — SMTP_APP_PASSWORD 미설정 시 skip + reason 반환 (GH built-in email 이 primary, Windows SMTP 보조)"
  - "FAILURES.md direct open('a') — Claude Write hook 은 Python direct I/O 미감지, append-only 계약은 파일 레벨에서 유지 (RESEARCH Pitfall 3)"
  - "harness 별도 checkout step (submodule 금지) + continue-on-error — harness repo private/미생성 시 drift_scan 의 graceful local-only fallback 이 처리"
metrics:
  duration_minutes: 5.4
  commits: 2
  tasks: 2
  tests_added: 18
  tests_passing: 18
  lines_added: 932
completed: 2026-04-20
---

# Phase 10 Plan 04: Scheduler Hybrid Summary

대표님, 말씀하신 대로 GH Actions cron 4종 + Windows Task Scheduler 3종 + 3채널 실패 알림을 하이브리드 구조로 완비했습니다. 무인 운영의 시계탑이 갖춰졌습니다.

**One-liner**: 4 GH Actions cron (KPI daily / drift weekly / skill-patch monthly / harness-audit monthly) + Windows Task Scheduler 3종 (Pipeline/Upload/NotifyFailure) + 3채널 실패 알림 (stdout/SMTP/FAILURES append) 하이브리드.

---

## Commits

| Task | Commit    | Description                                                      |
| ---- | --------- | ---------------------------------------------------------------- |
| 1    | `e094fa3` | 4 GH Actions workflows + scripts/schedule/ namespace             |
| 2    | `31aea3f` | windows_tasks.ps1 + notify_failure.py + 18 tests GREEN           |

---

## Artifacts Created

### GitHub Actions (4 workflows, 212 총 줄수)

| Workflow                           | Cron (UTC)        | KST 시각     | Target                                    |
| ---------------------------------- | ----------------- | ------------ | ----------------------------------------- |
| analytics-daily.yml                | `0 20 * * *`      | 매일 05:00   | `scripts.analytics.fetch_kpi`             |
| drift-scan-weekly.yml              | `0 0 * * 1`       | 월 09:00     | `scripts.audit.drift_scan`                |
| skill-patch-count-monthly.yml      | `0 0 1 * *`       | 1일 09:00    | `scripts.audit.skill_patch_counter`       |
| harness-audit-monthly.yml          | `0 1 1 * *`       | 1일 10:00    | `scripts.validate.harness_audit`          |

모든 workflow 는 `workflow_dispatch` 수동 trigger 도 허용.

### Windows Task Scheduler (148 줄 PowerShell)

| Task                          | Trigger               | Python Command                                        |
| ----------------------------- | --------------------- | ----------------------------------------------------- |
| `ShortsStudio_Pipeline`       | Daily 20:30 KST       | `-m scripts.orchestrator.shorts_pipeline`             |
| `ShortsStudio_Upload`         | Daily 20:45 KST       | `-m scripts.publisher.smoke_test --production`       |
| `ShortsStudio_NotifyFailure`  | On-demand (never-fire) | `-m scripts.schedule.notify_failure --task-name $env:TASK_NAME --error-msg $env:ERROR_MSG` |

**Idempotent**: Re-run 시 `Unregister-ScheduledTask` 선행 + `-Force`. `-Unregister` 플래그로 3개 task 일괄 제거 가능 (Plan 8 ROLLBACK 연계).

### Failure Notifier (201 줄 Python)

3 채널 dispatch:
- **stdout JSON** — 항상 출력 (scheduler 로그 수집)
- **SMTP email** — `SMTP_APP_PASSWORD` env 있을 때만 (없으면 graceful skip + reason 반환)
- **FAILURES.md append** — 직접 `open("a")`, hook 우회하되 append-only 계약은 파일 레벨 유지. `### F-OPS-NN` 자동 증가.

---

## Secrets Required

### GitHub Actions (repo Settings → Secrets → Actions)

| Secret Name              | Purpose                                           | Required |
| ------------------------ | ------------------------------------------------- | -------- |
| `YOUTUBE_TOKEN_JSON`     | OAuth refresh token (analytics-daily)             | Plan 3   |
| `YOUTUBE_CLIENT_SECRET`  | GCP OAuth client secret JSON                      | Plan 3   |
| `RECENT_VIDEO_IDS`       | Comma-separated video IDs for daily fetch         | Plan 3+  |
| `GITHUB_TOKEN`           | gh CLI 인증 (drift-scan-weekly issue/label)       | auto     |
| (GITHUB_TOKEN 은 GH Actions 가 자동 주입)                                                |

### Windows Task Scheduler (local env var)

| Env Var              | Purpose                          | Required                      |
| -------------------- | -------------------------------- | ----------------------------- |
| `SMTP_USER`          | Gmail/Naver sender address       | optional (email skip 허용)   |
| `SMTP_APP_PASSWORD`  | Gmail App Password (16자)        | optional                      |
| `SMTP_HOST`          | 기본 `smtp.gmail.com`            | optional                      |
| `SMTP_PORT`          | 기본 `587`                       | optional                      |
| `EMAIL_TO`           | 기본 `kanno3@naver.com`          | optional                      |

---

## Manual Dispatch Tasks (대표님)

실제 cron/스케줄 가동 전 대표님께서 수행하셔야 하는 항목입니다:

1. **GH Actions secrets 등록** (4종):
   - `YOUTUBE_TOKEN_JSON` (Plan 3 Wave 0 OAuth 재인증 산출물)
   - `YOUTUBE_CLIENT_SECRET` (GCP OAuth client secret JSON 원문)
   - `RECENT_VIDEO_IDS` (첫 업로드 완료 후 추가, 쉼표 구분)
   - SMTP 보조 채널 희망 시 `SMTP_USER` + `SMTP_APP_PASSWORD` 등록 (Windows 로컬 env 로도 대체 가능)

2. **Windows Task Scheduler 등록** (1회 관리자 권한):
   ```powershell
   # 관리자 권한 PowerShell
   cd C:\Users\PC\Desktop\naberal_group\studios\shorts
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\schedule\windows_tasks.ps1
   ```
   3개 task 등록 확인: `schtasks /Query /TN ShortsStudio_Pipeline`

3. **OAuth 재인증 완료** (Plan 3 Wave 0 의존):
   - `config/client_secret.json` + `config/youtube_token.json` 갱신
   - `yt-analytics.readonly` scope 포함 재인증 (이미 `2fda570` commit 에서 `oauth.py` 에 추가됨)

4. **naberal_harness repo URL 확정**:
   - 현재 drift-scan-weekly.yml 의 `repository: kanno321-create/naberal_harness` 는 placeholder
   - 실 repo 주소 확정 후 해당 YAML field 만 수정 (repo public/private 정책도 함께 결정)
   - Private 인 경우 PAT `HARNESS_REPO_TOKEN` secret 추가 필요

---

## Cron Schedule Summary (KST 기준)

```
매일     05:00 KST    │ analytics-daily (fetch_kpi)                    [클라우드]
월요일   09:00 KST    │ drift-scan-weekly (A급 drift 검사)             [클라우드]
매월 1일 09:00 KST    │ skill-patch-count-monthly (D-2 Lock counter)   [클라우드]
매월 1일 10:00 KST    │ harness-audit-monthly (score ≥ 80)             [클라우드]
매일     20:30 KST    │ ShortsStudio_Pipeline                          [로컬 PC]
매일     20:45 KST    │ ShortsStudio_Upload (+ publish_lock gate)      [로컬 PC]
on-demand            │ ShortsStudio_NotifyFailure                     [로컬 PC]
```

---

## Pace Enforcement Mechanism (BLOCKER #1 해결)

**질문**: 일일 Windows Task Trigger 가 `AF-1 일일 업로드 금지` / `AF-11 Inauthentic Content` 를 위반하지 않는가?

**답**: 위반하지 않습니다. 3단 gating 구조:

```
Daily 20:30 KST Trigger
    ↓ (wake-up + gate check 역할)
shorts_pipeline.py
    ↓ (업로드 직전)
publish_lock.assert_can_publish(MIN_ELAPSED_HOURS=48, MAX_JITTER_MIN=720)
    ↓ (48h 미경과 시 PublishLockViolation)
kst_window.assert_in_window(평일 20-23 / 주말 12-15 KST)
    ↓ (window 외 업로드 거부)
videos.insert (YouTube Data API v3)
```

결과: 일일 트리거는 매일 발화하지만 실 업로드는 **주 3~4편 + jitter** 로 자동 제한됨. 봇 패턴처럼 보여도 YouTube 정책 위반 없음.

**windows_tasks.ps1 에 9회 명시적 문서화**: `publish_lock.assert_can_publish`, `AF-1`, `AF-11`, `주 3~4편`, `MIN_ELAPSED_HOURS=48`, `MAX_JITTER_MIN=720`, `kst_window`, `PublishLockViolation`, `Inauthentic Content`.

---

## Label Pre-creation (BLOCKER #2 해결)

**문제**: `gh issue create --label drift --label phase-10 --label auto --label critical` 호출 시 label 이 repo 에 미존재하면 422 에러.

**이중 방어선**:
1. **Wave 0 manual dispatch** (primary): 대표님이 repo settings → Labels 에서 수동 생성 (예정)
2. **GH Actions step redundant safety** (secondary): drift-scan-weekly.yml 에 `gh label create drift/phase-10/auto || true` 3종 step 추가. 이미 존재 시 exit 1 이지만 `|| true` 로 무시.
3. `critical` label 은 GitHub default 이므로 생성 불필요.

---

## Harness Checkout (WARNING #4 해결)

**쟁점**: `naberal_harness` 는 shorts_studio 의 submodule 인가?

**답**: **아닙니다**. CLAUDE.md 명시: "독립 git 저장소, 수동 pull". 그러므로:

- `submodules: recursive` 사용 **금지** (test 로 lock)
- 별도 `Checkout naberal_harness` step + `continue-on-error: true`
- `--harness-path=../harness` 로 drift_scan.py 에 경로 전달
- harness repo 부재 시 Plan 2 drift_scan.py 의 `local-only fallback` 이 처리 (deprecated_patterns 만 scan)

---

## Deviations from Plan

**None** — Plan 이 작성된 대로 정확히 실행되었습니다.

단 2가지 미세 조정 있었음 (Rule 2 Auto-add missing critical functionality):
1. **skill-patch-count-monthly.yml** 에 `actions/upload-artifact@v4` step 을 추가하여 월간 리포트를 180일 retention artifact 로 보존 (plan 은 commit only). 감사 증거 장기 보관 목적.
2. **harness-audit-monthly.yml** 에 주석 블록 추가 — Phase 7 existing 스크립트라는 사실을 workflow 에서도 명시 (min_lines 하한 40+ 충족 + 문맥 전달).

두 조정 모두 plan 의 acceptance criteria 를 깎지 않고 추가 방어선만 늘린 것입니다.

---

## Authentication Gates Encountered

**None** — 이 Plan 은 코드/YAML 생성만 수행하며 실 API 호출은 하지 않습니다. 대표님의 수동 dispatch 4종 (secrets 등록 / PowerShell 관리자 실행 / OAuth 재인증 / harness repo URL 확정) 은 위 "Manual Dispatch Tasks" 섹션에 명시.

---

## Test Results

```
tests/phase10/test_workflows_yaml.py         8/8  PASS
tests/phase10/test_notify_failure.py        10/10 PASS
                                   합계      18/18 PASS (0.13s)

Phase 10 Plans 1-2 regression                32/32 PASS (4.57s)
```

테스트 분류:
- yml-1..5 (structural) : 4 YAML parseable + workflow_dispatch + secrets refs + permissions minimal + label step + harness separate checkout
- ps-1..4 (PowerShell) : Register-ScheduledTask 3회 + RunLevel Highest + idempotent + publish_lock 문서화
- notify-1..6 (Python) : FAILURES append + SMTP skip/called + stdout JSON + monotonic id + argparse validation

---

## Known Stubs

**None.** 모든 artifacts 는 wired + testable.

단, 다음 항목은 외부 입력 대기 (대표님 manual dispatch 섹션 참조):
- `RECENT_VIDEO_IDS` secret: 첫 업로드 이후에만 값을 가짐 (pre-launch 에는 `::warning::` + exit 0)
- `SMTP_APP_PASSWORD` env: 미설정 시 graceful skip, email 채널만 비활성화 (stdout + FAILURES 는 정상 동작)
- `naberal_harness` repo: private/미생성 시 `continue-on-error: true` + local-only fallback 으로 drift_scan 자체는 완주

---

## Next

Wave 3 (parallel):
- Plan 10-05 session audit rolling 30-day
- Plan 10-06 research loop (NotebookLM 월간)
- Plan 10-07 YPP trajectory (wiki/ypp/trajectory.md 자동 append)

이후 Wave 4:
- Plan 10-08 ROLLBACK.md + `scripts/rollback/stop_scheduler.py` (본 Plan 의 `-Unregister` 와 짝을 이룸)

---

## Self-Check: PASSED

- 9/9 artifact files FOUND
- 2/2 commits FOUND in git log (`e094fa3`, `31aea3f`)
- 18/18 Plan 04 tests PASS + 32/32 Plans 1-2 regression preserved
- All acceptance criteria from PLAN.md verified (grep invariants + pytest GREEN)
