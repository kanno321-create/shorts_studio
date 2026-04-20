---
phase: 10-sustained-operations
plan: 08
type: execute
wave: 4
depends_on: [10-04-scheduler-hybrid, 10-02-drift-scan-phase-lock]
files_modified:
  - .planning/phases/10-sustained-operations/ROLLBACK.md
  - scripts/rollback/__init__.py
  - scripts/rollback/stop_scheduler.py
  - tests/phase10/test_rollback_procedures.py
autonomous: true
requirements: [FAIL-04]
must_haves:
  truths:
    - ".planning/phases/10-sustained-operations/ROLLBACK.md 가 3 무인 운영 사고 시나리오 (업로드 사고 / scheduler 버그 / 학습 회로 오염) 별 복구 경로를 명시한다"
    - "scripts/rollback/stop_scheduler.py 가 Windows Task 3종 unregister + publish_lock.json 을 미래 시점으로 만들어 48시간 block 을 강제하는 CLI 를 제공한다"
    - "각 시나리오마다 detect / stop / diagnose / recover / verify 5단계 procedure 가 markdown 체크박스로 문서화된다"
    - "--dry-run 모드 + 전수 시나리오 시뮬레이션 tests 로 실 production 중단 없이 검증 가능"
  artifacts:
    - path: .planning/phases/10-sustained-operations/ROLLBACK.md
      provides: "3 시나리오 rollback runbook (detect/stop/diagnose/recover/verify)"
      min_lines: 150
    - path: scripts/rollback/__init__.py
      provides: "scripts.rollback namespace"
    - path: scripts/rollback/stop_scheduler.py
      provides: "Emergency stop CLI — publish_lock + Windows Task unregister"
      min_lines: 120
    - path: tests/phase10/test_rollback_procedures.py
      provides: "FAIL-04 지원 단위 테스트 (publish_lock future time + schtasks subprocess mock)"
      min_lines: 80
  key_links:
    - from: scripts/rollback/stop_scheduler.py
      to: .planning/publish_lock.json
      via: "future-timestamped last_upload_iso to force PublishLockViolation next call"
      pattern: "publish_lock\\.json"
    - from: scripts/rollback/stop_scheduler.py
      to: schtasks.exe (Windows)
      via: "subprocess.run(['schtasks','/End','/TN','ShortsStudio_*'])"
      pattern: "schtasks.*End\\|Unregister-ScheduledTask"
    - from: .planning/phases/10-sustained-operations/ROLLBACK.md
      to: scripts/rollback/stop_scheduler.py
      via: "runbook code block invokes stop_scheduler CLI"
      pattern: "scripts\\.rollback\\.stop_scheduler"
---

<objective>
무인 운영 중 발생 가능한 3 시나리오 (업로드 사고 / scheduler 버그 / 학습 회로 오염) 별 복구 runbook + 긴급 중단 CLI 를 구축한다. 기존 `publish_lock.py` 의 48시간 메커니즘을 역으로 활용하여 future timestamp 로 lock 파일을 세팅, `schtasks /End` + `Unregister-ScheduledTask` 로 Windows Task 를 중단한다. 모든 절차는 markdown 체크박스로 문서화하여 대표님이 실 사고 시 copy-paste 로 복구 가능하도록 한다.

Purpose: cron 이 돌기 시작하면 사고는 시간 문제. 예방보다 복구 경로 명시가 D-2 Lock 규율의 완성.
Output: ROLLBACK.md (3 시나리오 × 5단계) + stop_scheduler.py + 테스트.
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
@scripts/publisher/publish_lock.py
@scripts/schedule/windows_tasks.ps1
@scripts/audit/drift_scan.py
@CLAUDE.md

<interfaces>
<!-- publish_lock + Windows schtasks 긴급 중단 계약 -->

From RESEARCH.md §Plan 8 Open Q1 — publish_lock.json 수동 중단:
```python
import json
from datetime import datetime, timedelta, timezone
future = (datetime.now(timezone.utc) + timedelta(hours=49)).isoformat()
with open('.planning/publish_lock.json', 'w') as f:
    json.dump({'last_upload_iso': future, 'jitter_applied_min': 0, '_schema': 1}, f)
# Next assert_can_publish() call raises PublishLockViolation for 49 hours
```

From `scripts/publisher/publish_lock.py`:
- `MIN_ELAPSED_HOURS = 48`
- `MAX_JITTER_MIN = 720` (12h)
- Lock path: `.planning/publish_lock.json` (SHORTS_PUBLISH_LOCK_PATH env override 가능)

From RESEARCH.md §Plan 8 Open Q2 — git revert (PRIVATE repo 1인 운영):
```bash
git revert <commit>   # 새 commit 추가 (history 보존)
git push              # force push 불필요
# Phase 10 scheduler 도입 commit 만 revert 하면 GH Actions workflow 파일 삭제 → cron 자동 비활성화
```

From RESEARCH.md §Plan 8 Open Q4 — 학습 회로 오염 복구:
```bash
ls SKILL_HISTORY/<skill_name>/v*.md.bak | tail -1
cp SKILL_HISTORY/<skill_name>/v20260415_103000.md.bak .claude/skills/<skill_name>/SKILL.md
# FAILURES.md append F-D2-XX (이미 skill_patch_counter 가 기록)
# git revert <violation_commit>
```

From Plan 4 `scripts/schedule/windows_tasks.ps1`:
- `ShortsStudio_Pipeline`, `ShortsStudio_Upload`, `ShortsStudio_NotifyFailure` 3 task 이름
- `-Unregister` 모드로 전체 제거 가능
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: ROLLBACK.md 3 시나리오 runbook 작성 (150+ lines)</name>
  <files>
    .planning/phases/10-sustained-operations/ROLLBACK.md
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 8 Open Q1-Q4
    - `.planning/phases/10-sustained-operations/10-CONTEXT.md` Boundary decisions (rollback docs)
    - `.planning/PHASE_10_ENTRY_GATE.md` §4 rollback 개요 (확장 대상)
    - `scripts/publisher/publish_lock.py` (API 확인)
    - `scripts/schedule/windows_tasks.ps1` (Plan 4 — Unregister 모드 재사용)
  </read_first>
  <action>
    `.planning/phases/10-sustained-operations/ROLLBACK.md` 작성 (150+ lines) — 구조:
    ```markdown
    ---
    phase: 10-sustained-operations
    kind: rollback-runbook
    status: ready
    last_updated: 2026-04-20
    ---

    # Phase 10 Rollback Runbook

    > 무인 운영 중 사고 발생 시 대표님이 copy-paste 로 복구할 수 있는 수순서.
    > **모든 명령은 cwd = `C:\Users\PC\Desktop\naberal_group\studios\shorts\` 기준**

    ## 긴급 전체 중단 (2분 이내)

    ```powershell
    # 1. Windows Task 3종 정지 + Unregister
    powershell -File scripts\schedule\windows_tasks.ps1 -Unregister

    # 2. Publish lock 을 미래 49시간으로 세팅 (대안: 즉시 재시작 방지)
    python -m scripts.rollback.stop_scheduler --block-hours 49

    # 3. GH Actions 중단 (workflow 파일을 .github/workflows.disabled/ 로 이동)
    mkdir -p .github/workflows.disabled
    mv .github/workflows/*.yml .github/workflows.disabled/
    git add .github/ && git commit -m "emergency(10): disable all scheduled workflows" && git push
    ```

    ---

    ## 시나리오 1: 업로드 사고 (잘못된 영상 발행됨)

    ### Detect
    - [ ] YouTube Studio 대시보드에서 의도치 않은 업로드 확인
    - [ ] `config/production_log.json` 또는 `.planning/publish_lock.json` 의 `last_upload_iso` 시각 확인
    - [ ] `ShortsStudio_Upload` Task 의 Last Run Result 확인: `schtasks /Query /TN ShortsStudio_Upload /V /FO LIST`

    ### Stop
    - [ ] 긴급 전체 중단 (위 3 명령)
    - [ ] YouTube Studio 에서 해당 영상 **Unlisted** 로 변경 (대표님 browser 수동)
    - [ ] 필요 시 삭제

    ### Diagnose
    - [ ] `scripts/publisher/publish_lock.py` 48h+jitter 이 왜 우회되었는지 분석
    - [ ] `kst_window.py` 가 승인한 시각인지 (평일 20-23 / 주말 12-15) 검증
    - [ ] `ai_disclosure` containsSyntheticMedia=True flag 누락 여부 (Phase 8 ANCHOR A)
    - [ ] `production_metadata` 첨부 여부 (Phase 8 PUB-04)

    ### Recover
    - [ ] FAILURES.md 에 F-OPS-XX append (사고 상세 + 원인)
    - [ ] 원인 수정 commit (D-2 Lock 기간이면 `FAILURES.md` append 만, skill/hook/CLAUDE.md 수정 금지)
    - [ ] `.github/workflows.disabled/` → `.github/workflows/` 복귀 (점진적, 1개씩 재활성화)

    ### Verify
    - [ ] `python -m scripts.rollback.stop_scheduler --dry-run` → 현재 lock 상태 + Task 상태 확인
    - [ ] `python -m scripts.publisher.smoke_test --dry-run` → upload lane 정상
    - [ ] 첫 재활성 workflow = `skill-patch-count-monthly.yml` (가장 안전, 업로드 아님)

    ---

    ## 시나리오 2: Scheduler 버그 (GH Actions cron 실패 반복)

    ### Detect
    - [ ] GH Actions 페이지에서 3회 연속 ❌ 확인 (`https://github.com/kanno321-create/shorts_studio/actions`)
    - [ ] 대표님 email 에 `[shorts_studio] FAILURE` 메일 ≥3건 도착
    - [ ] `FAILURES.md` F-OPS-XX 3건 이상 축적

    ### Stop
    - [ ] 해당 workflow YAML 을 `.github/workflows.disabled/` 로 이동
    - [ ] 의심되는 script 의 최근 commit `git log -5 scripts/<module>/`

    ### Diagnose
    - [ ] Actions 로그 다운로드: `gh run list --workflow <name> --limit 5` + `gh run view <run-id> --log`
    - [ ] 원인 분류: (a) secret 만료 / (b) API rate limit / (c) code bug / (d) Google API 변경
    - [ ] OAuth token 만료 의심 시: `python scripts/publisher/oauth.py --reauth` (대표님 로컬 브라우저)

    ### Recover
    - [ ] 원인별 조치:
      - secret 만료 → GH Settings > Secrets > Update `YOUTUBE_TOKEN_JSON`
      - rate limit → cron 간격 늘리기 (daily → 2-day)
      - code bug → `git revert <commit>` 또는 fix 후 재배포
    - [ ] FAILURES.md F-OPS-XX append (root cause 기록)

    ### Verify
    - [ ] `workflow_dispatch` 로 수동 1회 실행 (` gh workflow run <name> `) → exit 0 확인
    - [ ] 24h 관찰 후 정상 cron 재가동

    ---

    ## 시나리오 3: 학습 회로 오염 (SKILL patch 금지 위반)

    ### Detect
    - [ ] `skill_patch_counter.py` 월간 리포트 `reports/skill_patch_count_YYYY-MM.md` 의 violation_count > 0
    - [ ] `FAILURES.md` 에 F-D2-XX 엔트리 존재
    - [ ] 또는 `drift_scan.py` 가 A급 drift 발견 → STATE.md `phase_lock: true`

    ### Stop
    - [ ] 긴급 전체 중단 (위 3 명령) — D-2 Lock 위반은 운영 지속 불가
    - [ ] 위반 commit 들의 hash 수집: `git log --since=2026-04-20 --name-only --pretty=format:"%H|%s" | grep -B1 -E "^\\.claude/(agents|skills|hooks)|^CLAUDE\\.md"`

    ### Diagnose
    - [ ] 각 위반 commit 을 diff 로 검토: `git show <hash>`
    - [ ] 의도된 수정인지 사고인지 판단:
      - 사고 → revert 필수
      - 의도됐으나 Lock 기간 위반 → 규율 실패, FAILURES append + 기간 재시작

    ### Recover
    - [ ] SKILL_HISTORY 에서 직전 버전 복원:
      ```bash
      ls SKILL_HISTORY/<skill_name>/v*.md.bak | sort | tail -1
      cp SKILL_HISTORY/<skill_name>/v<timestamp>.md.bak .claude/skills/<skill_name>/SKILL.md
      ```
    - [ ] 또는 `git revert <violation_commit>` 로 cleanly revert
    - [ ] FAILURES.md 에 F-D2-XX append (이미 skill_patch_counter 가 자동 기록했을 것)
    - [ ] A급 drift 관련이면 수정 후 `python -m scripts.audit.drift_scan --clear-lock`

    ### Verify
    - [ ] `python -m scripts.audit.skill_patch_counter` → violation_count == 0
    - [ ] `python -m scripts.audit.drift_scan` → exit 0
    - [ ] `grep "phase_lock: false" .planning/STATE.md` 확인
    - [ ] D-2 Lock 기간 **재시작** (2개월 count 를 원위치 — 사실상 기간 연장)

    ---

    ## Audit Trail

    모든 rollback 실행은 FAILURES.md 에 append 로 기록해야 한다 (append-only 규율). 본 runbook 에 항목 추가 시 commit message 는 `docs(10-08): extend rollback scenario N` 형식.

    ## Related

    - Plan 10-01 skill_patch_counter (D-2 Lock 검증)
    - Plan 10-02 drift_scan (phase_lock 토글)
    - Plan 10-04 scheduler (windows_tasks.ps1 -Unregister)
    - Plan 10-05 session_audit_rollup (학습 오염 조기 감지)
    - `.planning/PHASE_10_ENTRY_GATE.md` §4 original rollback skeleton
    ```
  </action>
  <acceptance_criteria>
    - `ls .planning/phases/10-sustained-operations/ROLLBACK.md` 존재
    - `wc -l .planning/phases/10-sustained-operations/ROLLBACK.md` >= 150
    - `grep -c "시나리오 1:\|시나리오 2:\|시나리오 3:" .planning/phases/10-sustained-operations/ROLLBACK.md` == 3
    - `grep -c "### Detect\|### Stop\|### Diagnose\|### Recover\|### Verify" .planning/phases/10-sustained-operations/ROLLBACK.md` >= 15 (3 시나리오 × 5 단계)
    - `grep -c "scripts.rollback.stop_scheduler\|windows_tasks.ps1 -Unregister" .planning/phases/10-sustained-operations/ROLLBACK.md` >= 2
    - `grep -c "SKILL_HISTORY" .planning/phases/10-sustained-operations/ROLLBACK.md` >= 1
    - `grep -c "\[ \]" .planning/phases/10-sustained-operations/ROLLBACK.md` >= 20 (checkbox procedure)
    - `grep -c "F-OPS-XX\|F-D2-XX" .planning/phases/10-sustained-operations/ROLLBACK.md` >= 3
  </acceptance_criteria>
  <verify>
    <automated>python -c "from pathlib import Path; t=Path('.planning/phases/10-sustained-operations/ROLLBACK.md').read_text(encoding='utf-8'); required=['시나리오 1:', '시나리오 2:', '시나리오 3:', '### Detect', '### Stop', '### Diagnose', '### Recover', '### Verify', 'stop_scheduler', 'windows_tasks.ps1', 'SKILL_HISTORY']; [print(f'found: {r!r}') for r in required if r in t]; missing=[r for r in required if r not in t]; assert not missing, f'missing: {missing}'; print(f'OK — {len(t.splitlines())} lines')"</automated>
  </verify>
  <done>ROLLBACK.md 3 시나리오 × 5 단계 runbook 완비, 150+ lines, checkbox procedure 20+, 모든 관련 스크립트 참조</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: stop_scheduler.py CLI + 긴급 중단 단위 테스트</name>
  <files>
    scripts/rollback/__init__.py,
    scripts/rollback/stop_scheduler.py,
    tests/phase10/test_rollback_procedures.py
  </files>
  <read_first>
    - `scripts/publisher/publish_lock.py` — SHORTS_PUBLISH_LOCK_PATH env + json schema
    - `scripts/schedule/windows_tasks.ps1` (Plan 4 — `-Unregister` 플래그)
    - `.planning/phases/10-sustained-operations/ROLLBACK.md` Task 1 산출물 (긴급 전체 중단 섹션 — CLI 호출 포함)
    - `tests/phase10/conftest.py` (`freeze_kst_now`)
    - `scripts/publisher/smoke_test.py` (Phase 8 — `--dry-run` 관례)
  </read_first>
  <behavior>
    - Test 1 (test_block_publish_lock_writes_future_iso): tmp publish_lock.json → `block_publish(hours=49)` → 파일 내 `last_upload_iso` 가 현재+49h 미래
    - Test 2 (test_block_publish_lock_preserves_schema): schema == 1 + jitter_applied_min == 0 + `_schema` field 존재
    - Test 3 (test_unregister_tasks_calls_powershell): monkeypatch subprocess.run → `unregister_windows_tasks()` 가 powershell.exe + windows_tasks.ps1 + `-Unregister` 로 호출
    - Test 4 (test_unregister_tasks_dry_run_no_subprocess): `--dry-run` → subprocess 미호출 + stdout JSON 에 `"would_unregister": [...]`
    - Test 5 (test_stop_scheduler_main_does_both): main 호출 → block_publish + unregister_windows_tasks 둘 다 실행 (subprocess mock counter == 1)
    - Test 6 (test_stop_scheduler_respects_env_override): `SHORTS_PUBLISH_LOCK_PATH=tmp/custom.json` → 그 경로에 lock 작성
    - Test 7 (test_stop_scheduler_platform_warning_on_non_windows): non-Windows → PowerShell step skip + stderr WARN (sys.platform mock)
    - Test 8 (test_stop_scheduler_json_output): stdout JSON 항상 출력, `{"publish_lock_future", "tasks_unregistered", "platform"}` keys
  </behavior>
  <action>
    1. `scripts/rollback/__init__.py` 작성 (네임스페이스, 7-line):
       ```python
       """scripts.rollback — Emergency shutdown + recovery helpers. Phase 10 Plan 08."""
       from __future__ import annotations
       __all__ = []
       ```
    2. `scripts/rollback/stop_scheduler.py` 작성 (≥120 lines):
       ```python
       """Emergency scheduler shutdown — Plan 10-08.

       Usage:
         python -m scripts.rollback.stop_scheduler            # block + unregister + json stdout
         python -m scripts.rollback.stop_scheduler --dry-run  # inspect only
         python -m scripts.rollback.stop_scheduler --block-hours 72 --skip-unregister

       Effects (production mode):
         1. Writes .planning/publish_lock.json with last_upload_iso = now + block_hours
            → next assert_can_publish() raises PublishLockViolation for `block_hours`
         2. Runs PowerShell scripts/schedule/windows_tasks.ps1 -Unregister (Windows only)
            → removes ShortsStudio_Pipeline / ShortsStudio_Upload / ShortsStudio_NotifyFailure
       """
       from __future__ import annotations
       import argparse
       import json
       import os
       import subprocess
       import sys
       from datetime import datetime, timedelta, timezone
       from pathlib import Path

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       DEFAULT_LOCK_PATH = Path(".planning/publish_lock.json")
       DEFAULT_PS1 = Path("scripts/schedule/windows_tasks.ps1")
       WINDOWS_TASKS = ("ShortsStudio_Pipeline", "ShortsStudio_Upload", "ShortsStudio_NotifyFailure")

       def block_publish(lock_path: Path, hours: int = 49,
                         now: datetime | None = None) -> dict:
           """Write publish_lock.json with future last_upload_iso.
           Returns the lock payload written."""
           if now is None:
               now = datetime.now(timezone.utc)
           future = now + timedelta(hours=hours)
           payload = {
               "last_upload_iso": future.isoformat(),
               "jitter_applied_min": 0,
               "_schema": 1,
           }
           lock_path.parent.mkdir(parents=True, exist_ok=True)
           lock_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
           return payload

       def unregister_windows_tasks(ps1: Path = DEFAULT_PS1, dry_run: bool = False) -> dict:
           """Invoke windows_tasks.ps1 -Unregister. Returns summary dict."""
           if sys.platform != "win32":
               return {
                   "platform": sys.platform,
                   "unregistered": False,
                   "reason": "non-Windows platform — PowerShell task unregister skipped",
                   "tasks": list(WINDOWS_TASKS),
               }
           if dry_run:
               return {
                   "platform": sys.platform,
                   "unregistered": False,
                   "dry_run": True,
                   "would_unregister": list(WINDOWS_TASKS),
               }
           if not ps1.exists():
               return {
                   "platform": sys.platform,
                   "unregistered": False,
                   "reason": f"ps1 not found at {ps1}",
                   "tasks": list(WINDOWS_TASKS),
               }
           result = subprocess.run(
               ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(ps1), "-Unregister"],
               capture_output=True, text=True, encoding="utf-8", timeout=60,
           )
           return {
               "platform": sys.platform,
               "unregistered": result.returncode == 0,
               "returncode": result.returncode,
               "stdout": result.stdout[-400:],
               "stderr": result.stderr[-400:],
               "tasks": list(WINDOWS_TASKS),
           }

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="Emergency scheduler shutdown")
           parser.add_argument("--block-hours", type=int, default=49,
                               help="How long publish_lock future-stamps (default 49h)")
           parser.add_argument("--lock-path", type=Path,
                               default=Path(os.environ.get("SHORTS_PUBLISH_LOCK_PATH", DEFAULT_LOCK_PATH)))
           parser.add_argument("--ps1", type=Path, default=DEFAULT_PS1)
           parser.add_argument("--skip-publish-lock", action="store_true")
           parser.add_argument("--skip-unregister", action="store_true")
           parser.add_argument("--dry-run", action="store_true")
           args = parser.parse_args(argv)

           now_utc = datetime.now(timezone.utc)
           summary: dict = {
               "invocation_ts": now_utc.isoformat(),
               "dry_run": args.dry_run,
               "block_hours": args.block_hours,
           }

           if not args.skip_publish_lock:
               if args.dry_run:
                   summary["publish_lock_would_write"] = {
                       "lock_path": str(args.lock_path),
                       "future_iso": (now_utc + timedelta(hours=args.block_hours)).isoformat(),
                   }
               else:
                   summary["publish_lock"] = block_publish(args.lock_path, args.block_hours, now_utc)

           if not args.skip_unregister:
               summary["tasks_unregister"] = unregister_windows_tasks(args.ps1, args.dry_run)
           else:
               summary["tasks_unregister"] = {"skipped": True}

           print(json.dumps(summary, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    3. `tests/phase10/test_rollback_procedures.py` 작성 (≥80 lines) — 8 tests Test 1-8:
       - `block_publish()` 단위 테스트: tmp_path lock + fixed now → future iso 검증
       - monkeypatch `subprocess.run` + `sys.platform` 로 Windows/non-Windows 경로 모두 커버
       - monkeypatch `os.environ["SHORTS_PUBLISH_LOCK_PATH"]` 경로 override 테스트
       - `--dry-run` 에서 subprocess 호출 수 == 0 (mock counter)
       - CLI main() 호출 시 stdout JSON parseable + keys 존재
    4. 실행: `pytest tests/phase10/test_rollback_procedures.py -xvs` → 8 tests GREEN
    5. 수동 실증: `python -m scripts.rollback.stop_scheduler --dry-run` → exit 0 + stdout JSON 에 `"dry_run": true` + `"publish_lock_would_write"` + `"tasks_unregister"` keys
  </action>
  <acceptance_criteria>
    - `ls scripts/rollback/__init__.py scripts/rollback/stop_scheduler.py` 존재
    - `wc -l scripts/rollback/stop_scheduler.py` >= 120
    - `python -c "from scripts.rollback.stop_scheduler import main, block_publish, unregister_windows_tasks; print('OK')"` prints OK
    - `python -m scripts.rollback.stop_scheduler --dry-run` exit 0 + stdout JSON 유효
    - `python -m scripts.rollback.stop_scheduler --dry-run --skip-unregister --skip-publish-lock` exit 0 + summary에 `"skipped": true` 두번
    - `pytest tests/phase10/test_rollback_procedures.py -q` 8 tests GREEN
    - `grep -c "windows_tasks.ps1\|WINDOWS_TASKS" scripts/rollback/stop_scheduler.py` >= 2
    - `grep -c "publish_lock.json\|_schema" scripts/rollback/stop_scheduler.py` >= 2
    - `grep -c "ShortsStudio_Pipeline\|ShortsStudio_Upload\|ShortsStudio_NotifyFailure" scripts/rollback/stop_scheduler.py` >= 3
    - `grep -c "timezone.utc\|zoneinfo" scripts/rollback/stop_scheduler.py` >= 1 (timezone-aware)
    - Phase 10 Plans 1-7 regression 보존: `pytest tests/phase10 --ignore=tests/phase10/test_rollback_procedures.py -q --tb=no` GREEN
    - Phase 8 publish_lock 호환: `pytest tests/phase08 -k "publish_lock or kst_window" -q --tb=no` exit 0
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_rollback_procedures.py -q && python -m scripts.rollback.stop_scheduler --dry-run --skip-unregister --skip-publish-lock</automated>
  </verify>
  <done>stop_scheduler.py 완비 (120+ lines), 8 tests GREEN, ROLLBACK.md 에서 CLI 호출 참조 정확, Phase 10 Plans 1-7 + Phase 8 publish_lock regression 보존</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_rollback_procedures.py -v` 8 tests PASS
- `python -m scripts.rollback.stop_scheduler --dry-run` exit 0
- `.planning/phases/10-sustained-operations/ROLLBACK.md` 150+ lines, 3 시나리오 × 5 단계 완비
- Phase 8 publish_lock regression 보존
- Phase 10 Plans 1-7 regression 보존
- FAIL-04 지원 완성 — 위반 감지 (Plan 1) + phase lock (Plan 2) + rollback runbook (Plan 8) 삼중 안전망
</verification>

<success_criteria>
1. `.planning/phases/10-sustained-operations/ROLLBACK.md` 150+ lines, 3 시나리오 (업로드 사고 / scheduler 버그 / 학습 오염) 각 Detect/Stop/Diagnose/Recover/Verify 5단계
2. `scripts/rollback/stop_scheduler.py` 120+ lines, publish_lock future-stamp + Windows Task unregister + graceful non-Windows + --dry-run
3. 8 tests GREEN covering publish_lock + schtasks + platform 분기 + CLI
4. 모든 CLI 호출이 ROLLBACK.md 에서 copy-paste 가능한 정확한 command 로 문서화
5. FAIL-04 지원 삼중 안전망 (counter + lock + runbook) 완성
6. Phase 10 Plans 1-7 + Phase 8 publish_lock regression 전수 보존
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-08-SUMMARY.md` with:
- Commits: (ROLLBACK.md + rollback CLI + tests)
- 3 시나리오 runbook 완성도
- FAIL-04 삼중 안전망 요약 (Plan 1 counter + Plan 2 lock + Plan 8 runbook)
- Phase 10 전체 완결 후 다음 단계:
  1. 대표님 manual dispatch 리스트 (GH secrets 등록 / OAuth 재인증 / Windows admin PowerShell / NotebookLM 월 업로드)
  2. Plan 4 Scheduler workflow 실제 활성화 (disabled → workflows/ 복귀)
  3. Phase 10 Continuous Monitoring 시작 — nyquist_compliant=true flip 은 `phase10_acceptance.py` 가 6 ledger 파일 (reports/kpi_log/trajectory/CONFLICT_MAP/session_audit/FAILURES) 의 첫 실 데이터 확인 후 수행
- 본 Plan 완료로 Phase 10 의 8 plan 모두 ship — ROADMAP `Phase 10: Sustained Operations` 의 Progress Table 0/8 → 8/8 갱신 가능 (메타 작업)
</output>
