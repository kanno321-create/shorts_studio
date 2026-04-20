---
phase: 10-sustained-operations
plan: 04
type: execute
wave: 2
depends_on: [10-01-skill-patch-counter, 10-02-drift-scan-phase-lock, 10-03-youtube-analytics-fetch]
files_modified:
  - .github/workflows/analytics-daily.yml
  - .github/workflows/drift-scan-weekly.yml
  - .github/workflows/skill-patch-count-monthly.yml
  - .github/workflows/harness-audit-monthly.yml
  - scripts/schedule/__init__.py
  - scripts/schedule/windows_tasks.ps1
  - scripts/schedule/notify_failure.py
  - tests/phase10/test_workflows_yaml.py
  - tests/phase10/test_notify_failure.py
autonomous: true
requirements: [KPI-01, KPI-02, AUDIT-02, AUDIT-03, FAIL-04]
must_haves:
  truths:
    - "4 GH Actions workflows (.github/workflows/) 가 cron 스케줄로 각각 KPI fetch (일), drift scan (주), skill patch count (월), harness audit (월) 를 실행한다"
    - "Windows Task Scheduler PowerShell 스크립트가 영상 파이프라인 + YouTube 업로드 + notify_failure 3개 task 를 등록하는 idempotent 루틴을 제공한다"
    - "notify_failure.py 는 실패 정보를 stdout JSON + (optional) SMTP email + FAILURES.md append (direct file I/O) 3채널로 분산 기록한다"
    - "모든 YAML 이 유효 syntax + cron 표현식 UTC 주석 포함 + GH secrets 참조 (YOUTUBE_TOKEN_JSON / YOUTUBE_CLIENT_SECRET) 명시"
  artifacts:
    - path: .github/workflows/analytics-daily.yml
      provides: "Daily cron: fetch_kpi.py — KPI-01"
      min_lines: 50
    - path: .github/workflows/drift-scan-weekly.yml
      provides: "Weekly cron: drift_scan.py + A급 drift 시 issue create — AUDIT-03"
      min_lines: 45
    - path: .github/workflows/skill-patch-count-monthly.yml
      provides: "Monthly cron: skill_patch_counter.py — FAIL-04"
      min_lines: 40
    - path: .github/workflows/harness-audit-monthly.yml
      provides: "Monthly cron: harness_audit.py (Phase 7 existing) — AUDIT-02 scheduler integration"
      min_lines: 40
    - path: scripts/schedule/windows_tasks.ps1
      provides: "PowerShell Register-ScheduledTask x3 (pipeline/upload/notify)"
      min_lines: 100
    - path: scripts/schedule/notify_failure.py
      provides: "Python notify_failure CLI — SMTP email + FAILURES.md append (direct I/O)"
      min_lines: 120
    - path: tests/phase10/test_workflows_yaml.py
      provides: "YAML syntax + cron expression + secrets reference tests"
      min_lines: 60
    - path: tests/phase10/test_notify_failure.py
      provides: "notify_failure.py unit — smtplib mock + append proof"
      min_lines: 60
  key_links:
    - from: .github/workflows/analytics-daily.yml
      to: scripts/analytics/fetch_kpi.py
      via: "run: python -m scripts.analytics.fetch_kpi --video-ids ${{ secrets.RECENT_VIDEO_IDS }}"
      pattern: "scripts\\.analytics\\.fetch_kpi"
    - from: .github/workflows/drift-scan-weekly.yml
      to: scripts/audit/drift_scan.py
      via: "run: python -m scripts.audit.drift_scan --harness-path=../harness"
      pattern: "scripts\\.audit\\.drift_scan"
    - from: .github/workflows/skill-patch-count-monthly.yml
      to: scripts/audit/skill_patch_counter.py
      via: "run: python -m scripts.audit.skill_patch_counter"
      pattern: "scripts\\.audit\\.skill_patch_counter"
    - from: .github/workflows/harness-audit-monthly.yml
      to: scripts/validate/harness_audit.py
      via: "run: python -m scripts.validate.harness_audit --threshold 80"
      pattern: "scripts\\.validate\\.harness_audit"
    - from: scripts/schedule/windows_tasks.ps1
      to: Register-ScheduledTask
      via: "PowerShell cmdlet — RunLevel Highest, Daily/Weekly triggers"
      pattern: "Register-ScheduledTask"
    - from: scripts/schedule/notify_failure.py
      to: FAILURES.md
      via: "Path.open('a', encoding='utf-8') — direct file I/O bypass Claude Write hook (RESEARCH Pitfall 3)"
      pattern: "open\\(.*FAILURES\\.md.*[\"']a[\"']"
    - from: scripts/schedule/windows_tasks.ps1
      to: scripts/publisher/publish_lock.py
      via: "Daily trigger + publish_lock.assert_can_publish() 조합 — 48h+jitter 실제 gating (AF-1/AF-11 주 3~4편 enforce)"
      pattern: "publish_lock\\.assert_can_publish|AF-1|주 3~4편"
---

<objective>
Phase 10 continuous monitoring 의 실행 엔진을 구축한다. GH Actions cron 4종 (analytics-daily / drift-scan-weekly / skill-patch-count-monthly / harness-audit-monthly) 으로 클라우드 24/7 감시를 가동하고, Windows Task Scheduler PowerShell 스크립트로 대표님 로컬 PC 에 영상 생성 + 업로드 + notify_failure 3 task 를 등록한다. 실패 시 3채널 (GH email + PowerShell SMTP + FAILURES.md append) 분산 기록으로 단일 장애점을 제거한다.

Purpose: 코드만 있고 cron 이 없으면 continuous pass 는 허상. 이 Plan 이 Phase 10 을 "영구 지속 phase" 로 만드는 유일한 실행 계층.
Output: 4 YAML + 2 schedule scripts + 2 test files + FAILURES.md append 계약 증명.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/STATE.md
@.planning/phases/10-sustained-operations/10-CONTEXT.md
@.planning/phases/10-sustained-operations/10-RESEARCH.md
@.planning/phases/10-sustained-operations/10-VALIDATION.md
@CLAUDE.md
@scripts/audit/skill_patch_counter.py
@scripts/audit/drift_scan.py
@scripts/analytics/fetch_kpi.py
@scripts/analytics/monthly_aggregate.py
@scripts/validate/harness_audit.py
@scripts/publisher/publish_lock.py

<interfaces>
<!-- GH Actions workflow + PowerShell + SMTP 계약 -->

From RESEARCH.md §Pattern 2 — GH Actions cron skeleton (KST → UTC 변환):
```yaml
name: <workflow-name>
on:
  schedule:
    - cron: '0 20 * * *'       # KST 05:00 = UTC 20:00 전일 (daily)
    - cron: '0 0 * * 1'        # KST 09:00 Monday = UTC 00:00 Monday (weekly)
    - cron: '0 0 1 * *'        # KST 09:00 day-1 = UTC 00:00 day-1 (monthly)
  workflow_dispatch: {}        # 수동 trigger 허용 (테스트용)

jobs:
  run:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # git push for kpi_log
      issues: write     # gh issue create for drift_scan
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install google-api-python-client google-auth-oauthlib
      - name: Run
        env:
          YOUTUBE_TOKEN_JSON: ${{ secrets.YOUTUBE_TOKEN_JSON }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          mkdir -p config
          echo "$YOUTUBE_CLIENT_SECRET" > config/client_secret.json
          echo "$YOUTUBE_TOKEN_JSON" > config/youtube_token.json
          python -m scripts.analytics.fetch_kpi  # etc.
```

From RESEARCH.md §Pattern 3 — Windows PowerShell:
```powershell
$scriptRoot = "C:\Users\PC\Desktop\naberal_group\studios\shorts"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"cd $scriptRoot; python -m scripts.orchestrator.shorts_pipeline`""
$trigger = New-ScheduledTaskTrigger -Daily -At "20:30"
Register-ScheduledTask -TaskName "ShortsStudio_Pipeline" -Action $action -Trigger $trigger `
    -RunLevel Highest -User "$env:USERNAME" -Force
```

From RESEARCH.md §Pitfall 3 — FAILURES.md append hook bypass (Claude Write tool 만 감지; Python 직접 I/O 는 허용):
```python
with open("FAILURES.md", "a", encoding="utf-8") as f:
    f.write(f"\n\n### F-OPS-{next_id}: {summary}\n...")
# Hook check_failures_append_only 은 Claude Write/Edit tool 만 검사 — Python open('a') 는 통과
```

From RESEARCH.md §Plan 4 — SMTP:
```python
import smtplib
from email.mime.text import MIMEText
from os import environ

msg = MIMEText(body, _subtype='plain', _charset='utf-8')
msg['Subject'] = f"[shorts_studio] FAILURE — {task_name}"
msg['From'] = environ["SMTP_USER"]
msg['To'] = "kanno3@naver.com"
with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(environ["SMTP_USER"], environ["SMTP_APP_PASSWORD"])
    s.send_message(msg)
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: 4 GH Actions workflows YAML + scripts/schedule/ 네임스페이스 스캐폴드</name>
  <files>
    .github/workflows/analytics-daily.yml,
    .github/workflows/drift-scan-weekly.yml,
    .github/workflows/skill-patch-count-monthly.yml,
    .github/workflows/harness-audit-monthly.yml,
    scripts/schedule/__init__.py
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pattern 2 + §Pitfall 1 (cron 지연)
    - `.planning/phases/10-sustained-operations/10-CONTEXT.md` Scheduler 섹션 (4 workflow 목적 + 각 cron 시각)
    - `scripts/validate/harness_audit.py` (Phase 7 existing, --threshold 80 사용법 확인)
    - `scripts/audit/skill_patch_counter.py` + `scripts/audit/drift_scan.py` (Plan 1+2 산출물, CLI flag 확인)
    - `scripts/analytics/fetch_kpi.py` (Plan 3 산출물, --video-ids 필수 param)
  </read_first>
  <action>
    1. `.github/workflows/analytics-daily.yml` 작성 (50+ lines):
       ```yaml
       name: analytics-daily
       # KPI-01 — YouTube Analytics v2 daily fetch (cron: 05:00 KST = 20:00 UTC 전일)
       # RESEARCH Pitfall 1: cron 10-30분 지연 known issue #156282 — acceptable for daily

       on:
         schedule:
           - cron: '0 20 * * *'   # UTC 20:00 = KST 05:00 (+9h)
         workflow_dispatch:
           inputs:
             video_ids:
               description: 'Comma-separated YouTube video IDs (override secrets)'
               required: false

       permissions:
         contents: write   # kpi_log.md + daily CSV commit

       jobs:
         fetch:
           runs-on: ubuntu-latest
           steps:
             - uses: actions/checkout@v4
             - uses: actions/setup-python@v5
               with:
                 python-version: '3.11'
             - name: Install deps
               run: |
                 python -m pip install --upgrade pip
                 pip install google-api-python-client google-auth-oauthlib
             - name: Restore OAuth token
               env:
                 YOUTUBE_TOKEN_JSON: ${{ secrets.YOUTUBE_TOKEN_JSON }}
                 YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
               run: |
                 mkdir -p config
                 echo "$YOUTUBE_CLIENT_SECRET" > config/client_secret.json
                 echo "$YOUTUBE_TOKEN_JSON" > config/youtube_token.json
             - name: Fetch daily KPI
               env:
                 VIDEO_IDS: ${{ github.event.inputs.video_ids || secrets.RECENT_VIDEO_IDS }}
               run: |
                 if [ -z "$VIDEO_IDS" ]; then
                   echo "::warning::RECENT_VIDEO_IDS secret empty — skipping fetch (expected pre-launch)"
                   exit 0
                 fi
                 python -m scripts.analytics.fetch_kpi --video-ids "$VIDEO_IDS" --output-dir data/kpi_daily
             - name: Commit kpi_log
               run: |
                 git config user.name "github-actions[bot]"
                 git config user.email "github-actions[bot]@users.noreply.github.com"
                 git add data/kpi_daily/ || true
                 git diff --cached --quiet || git commit -m "chore(kpi): daily fetch $(date -u +%Y-%m-%d)"
                 git push
       ```
    2. `.github/workflows/drift-scan-weekly.yml` 작성 (50+ lines) — WARNING #4: harness/ 경로는 submodule 이 아님, 별도 checkout step + graceful `--harness-path` flag 사용. BLOCKER #2: `gh label create` 를 step 에 추가하여 label 422 에러 방지:
       ```yaml
       name: drift-scan-weekly
       # AUDIT-03 + AUDIT-04 — A급 drift 주간 스캔, 발견 시 STATE.md phase_lock + gh issue

       on:
         schedule:
           - cron: '0 0 * * 1'    # UTC Monday 00:00 = KST Monday 09:00
         workflow_dispatch: {}

       permissions:
         contents: write   # STATE.md + CONFLICT_MAP.md commit
         issues: write     # gh issue create

       jobs:
         scan:
           runs-on: ubuntu-latest
           steps:
             - name: Checkout shorts_studio
               uses: actions/checkout@v4
               with:
                 fetch-depth: 0   # drift scan needs full history
                 path: shorts
             - name: Checkout naberal_harness
               uses: actions/checkout@v4
               with:
                 # TBD — 대표님 Plan 4 실행 전 실 repo URL 확정 (예: kanno321-create/naberal_harness)
                 repository: kanno321-create/naberal_harness
                 path: harness
                 ref: main   # or v1.0.1 tag if pinned
               continue-on-error: true   # harness repo private/미생성 시 Plan 2 graceful degradation 이 처리
             - uses: actions/setup-python@v5
               with:
                 python-version: '3.11'
             - name: Ensure labels exist
               working-directory: shorts
               env:
                 GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
               run: |
                 gh label create drift --color "d73a4a" --description "drift detection (auto)" || true
                 gh label create phase-10 --color "0075ca" --description "Phase 10 sustained ops" || true
                 gh label create auto --color "ededed" --description "automated issue" || true
                 # critical 은 GitHub default label 이므로 생성 불필요
             - name: Run drift scan
               working-directory: shorts
               env:
                 GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
               run: |
                 python -m scripts.audit.drift_scan --harness-path=../harness
             - name: Commit STATE.md + CONFLICT_MAP if changed
               if: always()
               working-directory: shorts
               run: |
                 git config user.name "github-actions[bot]"
                 git config user.email "github-actions[bot]@users.noreply.github.com"
                 git add .planning/STATE.md .planning/codebase/CONFLICT_MAP.md .planning/codebase/CONFLICT_HISTORY.jsonl || true
                 git diff --cached --quiet || git commit -m "audit(drift): weekly scan $(date -u +%Y-%m-%d)"
                 git push || true
       ```
       - `GH_TOKEN` 환경변수는 `gh issue create` 및 `gh label create` 둘 다 자동 사용 (gh CLI 1.x+ 규약)
       - harness/ 는 별도 checkout step (shorts_studio 는 submodule 로 관리하지 않음 — CLAUDE.md "독립 git 저장소")
       - `gh label create ... || true` — 이미 존재하면 exit 1 but 무시 (redundant safety; Plan 2 Wave 0 manual dispatch 가 primary)
       - `--harness-path=../harness` — Plan 2 drift_scan.py 가 local-only fallback 지원 (harness/ 부재 시 deprecated_patterns 만 scan)
    3. `.github/workflows/skill-patch-count-monthly.yml` 작성 (40+ lines):
       ```yaml
       name: skill-patch-count-monthly
       # FAIL-04 — D-2 Lock SKILL patch counter (월 1일 09:00 KST = UTC 00:00)

       on:
         schedule:
           - cron: '0 0 1 * *'   # UTC day-1 00:00 = KST day-1 09:00
         workflow_dispatch: {}

       permissions:
         contents: write   # reports/ + FAILURES.md commit

       jobs:
         count:
           runs-on: ubuntu-latest
           steps:
             - uses: actions/checkout@v4
               with:
                 fetch-depth: 0
             - uses: actions/setup-python@v5
               with:
                 python-version: '3.11'
             - name: Run counter
               run: |
                 python -m scripts.audit.skill_patch_counter
             - name: Commit report
               if: always()
               run: |
                 git config user.name "github-actions[bot]"
                 git config user.email "github-actions[bot]@users.noreply.github.com"
                 git add reports/ FAILURES.md || true
                 git diff --cached --quiet || git commit -m "audit(d2-lock): monthly skill patch count $(date -u +%Y-%m)"
                 git push
       ```
    4. `.github/workflows/harness-audit-monthly.yml` 작성 (40+ lines) — AUDIT-02 는 이미 Phase 7 에서 `scripts/validate/harness_audit.py` 280줄 완성. Plan 10 은 cron 호출만 추가:
       ```yaml
       name: harness-audit-monthly
       # AUDIT-02 — Phase 7 existing harness_audit.py 월 1회 재호출 (score ≥ 80)

       on:
         schedule:
           - cron: '0 1 1 * *'   # UTC day-1 01:00 = KST day-1 10:00 (skill-patch-count 1h 후)
         workflow_dispatch: {}

       permissions:
         contents: write

       jobs:
         audit:
           runs-on: ubuntu-latest
           steps:
             - uses: actions/checkout@v4
               with:
                 fetch-depth: 0
             - uses: actions/setup-python@v5
               with:
                 python-version: '3.11'
             - name: Run harness audit (threshold 80)
               run: |
                 python -m scripts.validate.harness_audit --json-out logs/harness_audit_$(date -u +%Y-%m).json --threshold 80
             - name: Upload audit JSON as artifact
               if: always()
               uses: actions/upload-artifact@v4
               with:
                 name: harness-audit-monthly-json
                 path: logs/harness_audit_*.json
                 retention-days: 90
       ```
    5. `scripts/schedule/__init__.py` 작성 (7-line 네임스페이스):
       ```python
       """scripts.schedule — Windows Task Scheduler + SMTP 실패 알림. Phase 10 신규."""
       from __future__ import annotations
       __all__ = []
       ```
  </action>
  <acceptance_criteria>
    - `ls .github/workflows/analytics-daily.yml .github/workflows/drift-scan-weekly.yml .github/workflows/skill-patch-count-monthly.yml .github/workflows/harness-audit-monthly.yml` — 4 파일 존재
    - `python -c "import yaml; [yaml.safe_load(open(p,encoding='utf-8')) for p in ['.github/workflows/analytics-daily.yml','.github/workflows/drift-scan-weekly.yml','.github/workflows/skill-patch-count-monthly.yml','.github/workflows/harness-audit-monthly.yml']]; print('OK')"` prints OK
      (PyYAML 부재 시 stdlib re 로 cron line grep + `on:` `jobs:` key 확인으로 대체)
    - `grep -c "scripts.analytics.fetch_kpi" .github/workflows/analytics-daily.yml` == 1
    - `grep -c "scripts.audit.drift_scan" .github/workflows/drift-scan-weekly.yml` == 1
    - `grep -c "scripts.audit.skill_patch_counter" .github/workflows/skill-patch-count-monthly.yml` == 1
    - `grep -c "scripts.validate.harness_audit" .github/workflows/harness-audit-monthly.yml` == 1
    - `grep -c "workflow_dispatch" .github/workflows/*.yml` == 4 (각 workflow 수동 trigger 가능)
    - `grep -c "cron: '0 20 \\* \\* \\*'\\|cron: '0 0 \\* \\* 1'\\|cron: '0 0 1 \\* \\*'\\|cron: '0 1 1 \\* \\*'" .github/workflows/*.yml` == 4
    - `grep -c "gh label create drift\\|gh label create phase-10\\|gh label create auto" .github/workflows/drift-scan-weekly.yml` >= 3 (BLOCKER #2 — label 사전 생성 redundant safety)
    - `grep -c "Checkout naberal_harness\\|kanno321-create/naberal_harness\\|--harness-path" .github/workflows/drift-scan-weekly.yml` >= 2 (WARNING #4 — harness 별도 checkout + graceful fallback flag)
    - `grep -c "submodules: recursive" .github/workflows/drift-scan-weekly.yml` == 0 (submodule 규약 아님, 별도 checkout step 사용)
    - `ls scripts/schedule/__init__.py` 존재
  </acceptance_criteria>
  <verify>
    <automated>python -c "import re; import pathlib; files=['.github/workflows/analytics-daily.yml','.github/workflows/drift-scan-weekly.yml','.github/workflows/skill-patch-count-monthly.yml','.github/workflows/harness-audit-monthly.yml']; [print(f'{f}: cron_lines={len(re.findall(chr(39)+\"- cron: \"+chr(39), pathlib.Path(f).read_text()))}') for f in files]"</automated>
  </verify>
  <done>4 GH Actions workflow YAML 완비, cron syntax 정확 (UTC), permissions + secrets 참조 명시, scripts/schedule/ namespace 준비, drift-scan-weekly 에 `gh label create` step + harness 별도 checkout + `--harness-path` flag 포함</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: windows_tasks.ps1 + notify_failure.py + 워크플로우/알림 테스트</name>
  <files>
    scripts/schedule/windows_tasks.ps1,
    scripts/schedule/notify_failure.py,
    tests/phase10/test_workflows_yaml.py,
    tests/phase10/test_notify_failure.py
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pattern 3 + §Plan 4 Open Q3-Q4 (PowerShell + SMTP)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 3 (FAILURES.md append hook bypass)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 4 (Windows Task Scheduler 권한)
    - `scripts/audit/skill_patch_counter.py` Task 2 의 `append_failures()` 구현 (direct file I/O 패턴 참조)
    - `scripts/publisher/publish_lock.py` (assert_can_publish — 48h+jitter gating 메커니즘)
    - `scripts/publisher/kst_window.py` (평일 20-23 / 주말 12-15 KST window gating)
    - `tests/phase10/conftest.py` (fixtures, Plan 1 에서 생성)
    - Plan 8 ROLLBACK.md scaffold 전략 (이 PowerShell script 가 Plan 8 에서 unregister 스크립트와 쌍을 이룸)
  </read_first>
  <behavior>
    - Test ps-1 (test_windows_tasks_ps1_contains_three_register): PowerShell script 에 `Register-ScheduledTask` 3회 호출 (Pipeline / Upload / NotifyFailure task)
    - Test ps-2 (test_windows_tasks_ps1_uses_runlevel_highest): 모든 Register-ScheduledTask 에 `-RunLevel Highest` 포함
    - Test ps-3 (test_windows_tasks_ps1_idempotent): `-Force` flag 또는 `Unregister-ScheduledTask -ErrorAction SilentlyContinue` 선행하여 중복 등록 안전
    - Test ps-4 (test_windows_tasks_ps1_documents_publish_lock_pacing): 파일에 `publish_lock.assert_can_publish` OR `AF-1` OR `주 3~4편` 문구 포함 (BLOCKER #1 — pace enforcement 설계 의도 문서화)
    - Test yml-1 (test_workflow_yaml_files_parseable): 4 YAML 파일이 stdlib re 로 cron 1+ line + `jobs:` 블록 존재
    - Test yml-2 (test_workflow_secrets_reference_shape): `secrets.YOUTUBE_TOKEN_JSON` + `secrets.YOUTUBE_CLIENT_SECRET` + `secrets.RECENT_VIDEO_IDS` 각각 1회 이상 참조
    - Test yml-3 (test_workflow_permissions_minimal): drift-scan-weekly 는 `issues: write` 포함, 나머지는 포함 안함 (least-privilege)
    - Test yml-4 (test_drift_scan_weekly_has_label_creation): drift-scan-weekly.yml 에 `gh label create drift` / `gh label create phase-10` / `gh label create auto` 3 호출 포함 (BLOCKER #2)
    - Test notify-1 (test_notify_failure_appends_to_failures_md): tmp FAILURES.md 에 엔트리 append + strict prefix 유지
    - Test notify-2 (test_notify_failure_smtp_skipped_if_env_missing): `SMTP_APP_PASSWORD` env 미설정 → email skip + exit 0 + stderr WARN
    - Test notify-3 (test_notify_failure_smtp_called_when_env_set): monkeypatch env + smtplib.SMTP mock → 1회 send_message 호출
    - Test notify-4 (test_notify_failure_stdout_json_always): dry-run 여부 무관 항상 stdout JSON summary
    - Test notify-5 (test_notify_failure_next_id_increments): 기존 FAILURES.md 에 F-OPS-01 존재 → 다음 호출 시 F-OPS-02 엔트리 추가
    - Test notify-6 (test_notify_failure_cli_task_name_required): `--task-name` 미제공 → argparse error 2
  </behavior>
  <action>
    1. `scripts/schedule/windows_tasks.ps1` 작성 (100+ lines, RESEARCH §Pattern 3 확장). BLOCKER #1: Upload task 블록에 publish_lock pace gating 설계 의도 주석 필수 삽입:
       ```powershell
       <#
       .SYNOPSIS
         Register 3 Windows Scheduled Tasks for shorts_studio Phase 10 sustained operations.
       .DESCRIPTION
         - ShortsStudio_Pipeline: Daily 20:30 KST — runs shorts_pipeline.py (publish_lock + kst_window enforce internal gates)
         - ShortsStudio_Upload:   Daily 20:45 KST — runs smoke_test.py --production (youtube_uploader invoked via pipeline completion)
         - ShortsStudio_NotifyFailure: On-demand (called by failing tasks via Action = notify_failure.py)
         Run as Administrator first time. Re-run is idempotent (-Force overwrites).
       .NOTES
         Phase 10 Plan 4. Pitfall 4: needs RunLevel Highest. Pitfall 5: UTF-8 in -Command 한국어 안전.

         [중요 — 페이스 설계 (CLAUDE.md 도메인 절대 규칙 #8 AF-1/AF-11)]
         Daily trigger 는 "wake-up + gate check" 역할일 뿐, 실제 페이스 gating 은
         publish_lock.py (MIN_ELAPSED_HOURS=48, MAX_JITTER_MIN=720) + kst_window.py (평일 20-23
         / 주말 12-15 KST) 가 수행한다. publish_lock.assert_can_publish() 가 48시간 미경과 시
         PublishLockViolation 으로 업로드를 거부 → 주 3~4편 + jitter 자동 enforce. 일일 트리거가
         봇 패턴처럼 보여도 실 발행은 주 3~4편으로 제한됨.
       #>

       [CmdletBinding()]
       param(
           [string]$ScriptRoot = "C:\Users\PC\Desktop\naberal_group\studios\shorts",
           [switch]$Unregister
       )

       $ErrorActionPreference = "Stop"

       function Register-ShortsTask {
           param(
               [string]$TaskName,
               [string]$PythonArgs,
               [ScriptBlock]$TriggerBuilder
           )
           Write-Host "[register] $TaskName"

           # idempotent: remove existing
           try {
               Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
               Write-Host "  (removed existing)"
           } catch {
               # not found — fresh registration
           }

           $action = New-ScheduledTaskAction `
               -Execute "powershell.exe" `
               -Argument ("-NoProfile -ExecutionPolicy Bypass -Command `"cd '{0}'; python {1}`"" -f $ScriptRoot, $PythonArgs)
           $trigger = & $TriggerBuilder
           $settings = New-ScheduledTaskSettingsSet `
               -AllowStartIfOnBatteries `
               -DontStopIfGoingOnBatteries `
               -StartWhenAvailable `
               -MultipleInstances IgnoreNew `
               -ExecutionTimeLimit (New-TimeSpan -Hours 2)

           Register-ScheduledTask `
               -TaskName $TaskName `
               -Action $action `
               -Trigger $trigger `
               -Settings $settings `
               -RunLevel Highest `
               -User "$env:USERNAME" `
               -Force | Out-Null
           Write-Host "  [ok] $TaskName registered"
       }

       function Unregister-AllShortsTasks {
           foreach ($tn in @("ShortsStudio_Pipeline", "ShortsStudio_Upload", "ShortsStudio_NotifyFailure")) {
               try {
                   Unregister-ScheduledTask -TaskName $tn -Confirm:$false -ErrorAction Stop
                   Write-Host "[unregister] $tn"
               } catch {
                   Write-Host "[unregister] $tn (not present)"
               }
           }
       }

       if ($Unregister) {
           Unregister-AllShortsTasks
           Write-Host "All shorts tasks unregistered."
           exit 0
       }

       # 1. Pipeline — daily 20:30 KST
       # NOTE: Daily trigger 는 publish_lock.py (48h+jitter, MIN_ELAPSED_HOURS=48, MAX_JITTER_MIN=720)
       # + kst_window.py (평일 20-23 / 주말 12-15 KST) 에 의존. 파이프라인은 발행 직전
       # publish_lock.assert_can_publish() 로 gate check → 48h 미경과 시 PublishLockViolation.
       # (CLAUDE.md 도메인 절대 규칙 #8 AF-1/AF-11 주 3~4편 pace enforce 메커니즘)
       Register-ShortsTask `
           -TaskName "ShortsStudio_Pipeline" `
           -PythonArgs "-m scripts.orchestrator.shorts_pipeline" `
           -TriggerBuilder { New-ScheduledTaskTrigger -Daily -At "20:30" }

       # 2. Upload — daily 20:45 KST (pipeline 완료 후 15분 여유)
       # NOTE: 일일 실행으로 보이지만 publish_lock.assert_can_publish() 가 48시간 미경과 시
       # PublishLockViolation 으로 거부하여 실제 업로드는 주 3~4편 페이스 + jitter 로 자동
       # 제한됨. Daily trigger 는 "wake-up + gate check" 역할. 대표님 AF-1/AF-11
       # Inauthentic Content 리스크 없음 (페이스는 publish_lock + kst_window 가 enforce).
       Register-ShortsTask `
           -TaskName "ShortsStudio_Upload" `
           -PythonArgs "-m scripts.publisher.smoke_test --production" `
           -TriggerBuilder { New-ScheduledTaskTrigger -Daily -At "20:45" }

       # 3. NotifyFailure — on-demand (called by other tasks via notify_failure CLI)
       Register-ShortsTask `
           -TaskName "ShortsStudio_NotifyFailure" `
           -PythonArgs "-m scripts.schedule.notify_failure --task-name `$env:TASK_NAME --error-msg `$env:ERROR_MSG" `
           -TriggerBuilder { New-ScheduledTaskTrigger -Once -At (Get-Date).AddYears(10) }
           # (on-demand trigger via Start-ScheduledTask; 10년 후 dummy trigger 는 never-fire)

       Write-Host ""
       Write-Host "[done] 3 tasks registered. Verify with: schtasks /Query /TN ShortsStudio_Pipeline"
       Write-Host "[rollback] Re-run with -Unregister to remove all 3 tasks (Plan 8 ROLLBACK.md 참조)"
       ```
    2. `scripts/schedule/notify_failure.py` 작성 (120+ lines):
       ```python
       """Failure notifier — SMTP email + FAILURES.md append + stdout JSON.

       Called by:
         - Windows Task Scheduler action when a scheduled task fails
         - GH Actions workflow `if: failure()` step (optional, GH built-in email 이 1차)

       Design:
         - stdout JSON 은 항상 출력 (scheduler 로그 수집용)
         - SMTP email 은 SMTP_APP_PASSWORD env 있을 때만 (미설정 = graceful skip)
         - FAILURES.md 는 direct open('a') 로 append — Claude Write hook 우회 (RESEARCH Pitfall 3)
       """
       from __future__ import annotations
       import argparse
       import json
       import os
       import re
       import smtplib
       import sys
       from datetime import datetime
       from email.mime.text import MIMEText
       from pathlib import Path
       from zoneinfo import ZoneInfo

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       SMTP_HOST_DEFAULT = "smtp.gmail.com"
       SMTP_PORT_DEFAULT = 587
       EMAIL_TO_DEFAULT = "kanno3@naver.com"

       def append_failures(task_name: str, error_msg: str, now: datetime,
                           failures_path: Path) -> str:
           """Append F-OPS-NN entry. Returns entry id (e.g., F-OPS-01)."""
           if not failures_path.exists():
               raise FileNotFoundError(f"FAILURES.md not found at {failures_path}")
           existing = failures_path.read_text(encoding="utf-8")
           ids = re.findall(r"### F-OPS-(\d{2})", existing)
           next_id = max((int(i) for i in ids), default=0) + 1
           entry_id = f"F-OPS-{next_id:02d}"
           body = [
               "",
               "",
               f"## {entry_id} — Scheduler 실패 ({now.date().isoformat()}, {task_name})",
               "",
               f"**Task**: `{task_name}`",
               f"**Timestamp**: {now.isoformat()}",
               "",
               "**증상**:",
               "```",
               error_msg[:1500],   # truncate oversize error dumps
               "```",
               "",
               "**조치**: Scheduler 로그 확인 → 원인 분류 (API / network / OAuth / git 권한 / drift) → 재시도 또는 FAILURES 에서 root-cause 추적.",
               "",
               "**관련**: Plan 10-04 scheduler + Plan 10-08 ROLLBACK.md 시나리오",
           ]
           with failures_path.open("a", encoding="utf-8") as f:
               f.write("\n".join(body) + "\n")
           return entry_id

       def send_email(task_name: str, error_msg: str, now: datetime) -> dict:
           """Send SMTP email. Returns {"sent": bool, "reason": str|None}."""
           user = os.environ.get("SMTP_USER")
           password = os.environ.get("SMTP_APP_PASSWORD")
           if not (user and password):
               return {"sent": False, "reason": "SMTP_USER or SMTP_APP_PASSWORD env missing"}
           host = os.environ.get("SMTP_HOST", SMTP_HOST_DEFAULT)
           port = int(os.environ.get("SMTP_PORT", SMTP_PORT_DEFAULT))
           to = os.environ.get("EMAIL_TO", EMAIL_TO_DEFAULT)

           body = f"Task: {task_name}\nTime: {now.isoformat()}\n\nError:\n{error_msg[:2000]}"
           msg = MIMEText(body, _subtype="plain", _charset="utf-8")
           msg["Subject"] = f"[shorts_studio] FAILURE — {task_name}"
           msg["From"] = user
           msg["To"] = to

           with smtplib.SMTP(host, port, timeout=30) as s:
               s.starttls()
               s.login(user, password)
               s.send_message(msg)
           return {"sent": True, "reason": None}

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="Scheduler failure notifier")
           parser.add_argument("--task-name", required=True)
           parser.add_argument("--error-msg", default="(no error message provided)")
           parser.add_argument("--failures-path", type=Path, default=Path("FAILURES.md"))
           parser.add_argument("--skip-email", action="store_true")
           parser.add_argument("--skip-failures-append", action="store_true")
           args = parser.parse_args(argv)

           now = datetime.now(KST)
           result: dict = {
               "task_name": args.task_name,
               "timestamp": now.isoformat(),
               "entry_id": None,
               "email_sent": False,
               "email_reason": None,
           }

           if not args.skip_failures_append:
               entry_id = append_failures(args.task_name, args.error_msg, now, args.failures_path)
               result["entry_id"] = entry_id

           if not args.skip_email:
               email_result = send_email(args.task_name, args.error_msg, now)
               result["email_sent"] = email_result["sent"]
               result["email_reason"] = email_result["reason"]

           print(json.dumps(result, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    3. `tests/phase10/test_workflows_yaml.py` 작성 (60+ lines) — 4 tests yml-1..4:
       - stdlib re 로 YAML parse (PyYAML 부재 허용):
         ```python
         def test_workflow_yaml_files_parseable():
             files = ["analytics-daily", "drift-scan-weekly", "skill-patch-count-monthly", "harness-audit-monthly"]
             for name in files:
                 p = Path(f".github/workflows/{name}.yml")
                 text = p.read_text(encoding="utf-8")
                 assert re.search(r"^on:\s*$", text, re.MULTILINE), f"{name}: missing `on:` block"
                 assert re.search(r"cron:\s*'[0-9 */,-]+'", text), f"{name}: missing cron expression"
                 assert re.search(r"^jobs:\s*$", text, re.MULTILINE), f"{name}: missing `jobs:` block"
         ```
       - yml-2: 각 secret 참조 확인
       - yml-3: drift-scan-weekly 는 `issues: write` 포함, 나머지 3은 부재
       - yml-4 (BLOCKER #2): drift-scan-weekly.yml 에 `gh label create drift` / `gh label create phase-10` / `gh label create auto` 3 호출이 text 에 존재
    4. `tests/phase10/test_notify_failure.py` 작성 (60+ lines) — 6 tests notify-1..6:
       - tmp FAILURES.md 생성 (seed with 1 existing entry) → `main(["--task-name","ShortsStudio_Pipeline","--error-msg","dummy","--skip-email","--failures-path",str(tmp)])` → F-OPS-02 추가 + prefix 보존
       - monkeypatch `smtplib.SMTP` → Mock class with `send_message` counter
       - monkeypatch `os.environ` 으로 SMTP_* 설정/미설정 시나리오
    5. 실행: `pytest tests/phase10/test_workflows_yaml.py tests/phase10/test_notify_failure.py -xvs` → 10+ tests GREEN
    6. PowerShell smoke (Windows 에서만): `powershell -File scripts/schedule/windows_tasks.ps1 -WhatIf` 대안으로 syntax 확인 — 실제 등록은 대표님 로컬 `Run as Administrator` 에서 1회 실행 (manual dispatch)
  </action>
  <acceptance_criteria>
    - `ls scripts/schedule/windows_tasks.ps1 scripts/schedule/notify_failure.py` 존재
    - `grep -c "Register-ScheduledTask" scripts/schedule/windows_tasks.ps1` == 3
    - `grep -c "RunLevel Highest" scripts/schedule/windows_tasks.ps1` ≥ 1 (공유 helper 사용)
    - `grep -c "Unregister-ScheduledTask" scripts/schedule/windows_tasks.ps1` ≥ 1 (idempotent)
    - `grep -c "ShortsStudio_Pipeline\\|ShortsStudio_Upload\\|ShortsStudio_NotifyFailure" scripts/schedule/windows_tasks.ps1` ≥ 3
    - `grep -c "publish_lock.assert_can_publish\\|AF-1\\|주 3~4편" scripts/schedule/windows_tasks.ps1` >= 1 (BLOCKER #1 — pace gating 설계 의도 문서화, CLAUDE.md 도메인 절대 규칙 #8)
    - `wc -l scripts/schedule/windows_tasks.ps1` ≥ 100 lines
    - `python -c "from scripts.schedule.notify_failure import main, append_failures, send_email; print('OK')"` prints OK
    - `python -m scripts.schedule.notify_failure --task-name TEST --error-msg smoke --skip-email --skip-failures-append` exit 0 + stdout JSON
    - `wc -l scripts/schedule/notify_failure.py` ≥ 120 lines
    - `pytest tests/phase10/test_workflows_yaml.py tests/phase10/test_notify_failure.py -q` 10+ tests GREEN
    - Phase 10 Plans 1-3 regression 보존: `pytest tests/phase10/test_skill_patch_counter.py tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py -q --tb=no` GREEN
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_workflows_yaml.py tests/phase10/test_notify_failure.py -q && python -m scripts.schedule.notify_failure --task-name TEST --error-msg smoke --skip-email --skip-failures-append</automated>
  </verify>
  <done>windows_tasks.ps1 3 task Register-ScheduledTask + Unregister 모드 + publish_lock pace 문서화 주석, notify_failure.py 3채널 (stdout / email / FAILURES append), 10+ tests GREEN, Phase 10 Plan 1-3 regression 보존</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_workflows_yaml.py tests/phase10/test_notify_failure.py -v` 10+ tests PASS
- 4 GH Actions workflows YAML parseable (cron + jobs + permissions)
- drift-scan-weekly.yml 에 `gh label create` 3종 step + `Checkout naberal_harness` step + `--harness-path` flag 포함 (BLOCKER #2 + WARNING #4)
- `grep -c "Register-ScheduledTask" scripts/schedule/windows_tasks.ps1` == 3
- `grep -c "publish_lock.assert_can_publish\|AF-1\|주 3~4편" scripts/schedule/windows_tasks.ps1` >= 1 (BLOCKER #1)
- notify_failure CLI works: `--skip-email --skip-failures-append` exit 0 + stdout JSON
- Phase 10 Plans 1-3 regression 보존 (pytest tests/phase10 -q)
- 대표님 manual dispatch 필요 (기록만, 실행 안 함):
  1. GH secrets 등록 (`YOUTUBE_TOKEN_JSON`, `YOUTUBE_CLIENT_SECRET`, `RECENT_VIDEO_IDS`, `SMTP_USER`, `SMTP_APP_PASSWORD`)
  2. `scripts/schedule/windows_tasks.ps1` 관리자 권한 1회 실행
  3. OAuth 재인증 완료 (Plan 3 Wave 0)
  4. naberal_harness repo URL 확정 (drift-scan-weekly.yml 의 `repository:` field — 현재 placeholder `kanno321-create/naberal_harness`)
</verification>

<success_criteria>
1. `.github/workflows/` 에 4 YAML 파일 (analytics-daily / drift-scan-weekly / skill-patch-count-monthly / harness-audit-monthly) 존재 + 각 cron syntax 정확 + workflow_dispatch 허용 + secrets 참조 명시
2. drift-scan-weekly.yml 에 `gh label create` 3종 step + `Checkout naberal_harness` 별도 step + `--harness-path=../harness` 인자 전달 (BLOCKER #2 + WARNING #4)
3. `scripts/schedule/windows_tasks.ps1` 3 Register-ScheduledTask + Unregister 모드 + `-RunLevel Highest` + idempotent + publish_lock/AF-1/주 3~4편 pace gating 주석 (BLOCKER #1)
4. `scripts/schedule/notify_failure.py` 3채널 (stdout / SMTP / FAILURES append) + graceful degradation
5. 10+ tests GREEN (yml-1..4 + notify-1..6)
6. AUDIT-02 은 이미 완료(Phase 7)지만 cron wrapping 으로 월 1회 호출 보장
7. Phase 10 Plans 1-3 regression 전수 보존
8. 대표님 manual dispatch 사항 명시 (GH secrets 등록 + PowerShell admin 실행 + OAuth 재인증 + harness repo URL 확정)
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-04-SUMMARY.md` with:
- Commits: (4 YAML + 2 schedule scripts + 2 tests)
- Secrets required list (GH 5개 + 로컬 SMTP 2개)
- Manual dispatch tasks for 대표님 (4 items, incl. harness repo URL 확정)
- Cron schedule summary (KST 기준)
- Pace enforcement 메커니즘 문서화 (BLOCKER #1) — publish_lock.py + kst_window.py + Daily trigger 조합
- Label pre-creation 방어선 (BLOCKER #2) — Wave 0 manual dispatch + GH Actions step 이중 방어
- Harness checkout 별도 step (WARNING #4) — submodule 아님, graceful --harness-path fallback
- Next: Plan 5 (session audit rolling) + Plan 6 (research loop) + Plan 7 (trajectory) Wave 3 parallel
</output>
