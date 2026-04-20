---
phase: 10-sustained-operations
plan: 08
subsystem: [rollback, operations]
tags: [rollback-runbook, emergency-shutdown, publish-lock-reverse, fail-04-recovery, d-2-lock-safe]
requires: [10-04-scheduler-hybrid, 10-02-drift-scan-phase-lock]
provides: [emergency-cli, 3-scenario-runbook, fail-04-triple-safety-net]
affects: [.planning/phases/10-sustained-operations/ROLLBACK.md, scripts/rollback/, tests/phase10/test_rollback_procedures.py]
phase_success_criteria: [FAIL-04-RECOVERY]
requirements: [FAIL-04]
tech_added: []
patterns: [reverse-use-publish-lock, subprocess-powershell-unregister, dry-run-zero-side-effects, platform-graceful-skip]
key_files_created:
  - .planning/phases/10-sustained-operations/ROLLBACK.md
  - scripts/rollback/__init__.py
  - scripts/rollback/stop_scheduler.py
  - tests/phase10/test_rollback_procedures.py
key_files_modified: []
decisions: []
metrics:
  duration_min: 5
  tasks_completed: 2
  tests_added: 8
  files_created: 4
  files_modified: 0
  commits: 3
completed: 2026-04-20
---

# Phase 10 Plan 08: Rollback Docs Summary

> 무인 운영 사고 3 시나리오 (업로드 사고 / scheduler 버그 / 학습 회로 오염) 별 복구 runbook 185 줄 + 긴급 중단 CLI `scripts/rollback/stop_scheduler.py` 256 줄 + 8 tests GREEN. FAIL-04 삼중 안전망의 3축 (복구) 완성.

**One-liner**: Phase 10 Plan 08 rollback runbook + emergency shutdown CLI — `publish_lock.py` 48h+jitter 역활용 future-timestamp lock + `schtasks -Unregister` via PowerShell subprocess + 3 scenarios × 5 stages Detect/Stop/Diagnose/Recover/Verify.

## Overview

Phase 10 Sustained Operations 는 "예방 (Plan 01-07) + 복구 (Plan 08)" 2축 구조입니다. 본 Plan 은 후자의 관문으로 **FAIL-04 삼중 안전망**을 완성합니다.

- **1축 감지 (Plan 10-01)** — `skill_patch_counter.py` 가 D-2 Lock 위반 count
- **2축 잠금 (Plan 10-02)** — `drift_scan.py` 가 A 급 drift 시 `STATE.md phase_lock: true`
- **3축 복구 (Plan 10-08, 본 Plan)** — `ROLLBACK.md` runbook + `stop_scheduler.py` CLI

핵심 설계 아이디어는 **Phase 8 `publish_lock.py` 의 48h+jitter gate 역활용** — 사고 시 `last_upload_iso` 를 미래 시점 (default 49h) 으로 세팅해서 `assert_can_publish()` 가 `PublishLockViolation` 을 영구 raise 하도록 만드는 것입니다. 기존 규율 메커니즘을 무기화했으므로 신규 injection 없이 복구 경로 확립.

## Tasks Completed

### Task 1: ROLLBACK.md 3 시나리오 × 5 단계 runbook
- **Commit**: `ed1a80a` — `docs(10-08): ROLLBACK.md 3 시나리오 runbook (업로드/scheduler/학습오염)`
- **Files**:
  - `.planning/phases/10-sustained-operations/ROLLBACK.md` (185 lines, 신규): frontmatter 6 fields + `# Phase 10 Rollback Runbook` + `긴급 전체 중단 (2분 이내)` 3 명령 (windows_tasks.ps1 -Unregister + stop_scheduler --block-hours 49 + workflows.disabled/) + `## 시나리오 1: 업로드 사고` (Detect 4 + Stop 4 + Diagnose 5 + Recover 3 + Verify 4 = 20 checkbox) + `## 시나리오 2: Scheduler 버그` (Detect 4 + Stop 3 + Diagnose 2 + Recover 2 + Verify 3 = 14 checkbox) + `## 시나리오 3: 학습 회로 오염` (Detect 4 + Stop 2 + Diagnose 3 + Recover 4 + Verify 5 = 18 checkbox) + `## Audit Trail` + `## Related` + `## Rollback 실행 메타` (pre-flight 검증 체크리스트).
- **Acceptance**: 185 lines ≥ 150; 3 시나리오 + 15 5-stage sections (`### Detect` ×3 / `### Stop` ×3 / `### Diagnose` ×3 / `### Recover` ×3 / `### Verify` ×3); 56 checkboxes ≥ 20; F-OPS-XX 4 hits + F-D2-XX 3 hits ≥ 3; `scripts.rollback.stop_scheduler` + `windows_tasks.ps1 -Unregister` 둘 다 등장 ≥ 2; SKILL_HISTORY 복원 경로 ≥ 1.

### Task 2: stop_scheduler.py CLI + 8 tests (TDD)
- **Commits**:
  - `cce2346` — `test(10-08): RED — 8 failing tests for rollback stop_scheduler` (ModuleNotFoundError 8 test collection fail 확인)
  - `3e2eeb7` — `feat(10-08): stop_scheduler.py — emergency shutdown CLI (256 lines)` (8 tests GREEN)
- **Files**:
  - `scripts/rollback/__init__.py` (5 lines, 신규): namespace only.
  - `scripts/rollback/stop_scheduler.py` (256 lines, 신규): `block_publish(lock_path, hours=49, now=None) -> dict` + `unregister_windows_tasks(ps1, dry_run=False) -> dict` + `_resolve_lock_path(cli_value) -> Path` + `main(argv=None) -> int`. 상수: `DEFAULT_LOCK_PATH = Path(".planning/publish_lock.json")`, `DEFAULT_PS1 = Path("scripts/schedule/windows_tasks.ps1")`, `WINDOWS_TASKS = ("ShortsStudio_Pipeline", "ShortsStudio_Upload", "ShortsStudio_NotifyFailure")`. CLI flags: `--block-hours` / `--lock-path` / `--ps1` / `--skip-publish-lock` / `--skip-unregister` / `--dry-run`. stdlib-only (argparse + json + os + subprocess + sys + datetime + pathlib).
  - `tests/phase10/test_rollback_procedures.py` (239 lines, 신규): 8 tests. Test 1 (future ISO write) + Test 2 (schema {last_upload_iso, jitter_applied_min, _schema} — matches publish_lock.py contract) + Test 3 (PowerShell subprocess call with exact args on win32) + Test 4 (dry-run zero subprocess + would_unregister list) + Test 5 (main does both with mock counter == 1) + Test 6 (SHORTS_PUBLISH_LOCK_PATH env override) + Test 7 (non-Windows graceful skip + reason) + Test 8 (CLI JSON stdout contract).
- **Acceptance**:
  - `pytest tests/phase10/test_rollback_procedures.py -v` → 8/8 PASS (0.09s)
  - `python -m scripts.rollback.stop_scheduler --dry-run` exit 0, stdout JSON contains `dry_run: true` + `publish_lock_would_write` + `tasks_unregister.would_unregister` (win32) OR `tasks_unregister.reason` (linux/darwin)
  - `python -m scripts.rollback.stop_scheduler --dry-run --skip-unregister --skip-publish-lock` exit 0, both sections `skipped: true`
  - `python -c "from scripts.rollback.stop_scheduler import main, block_publish, unregister_windows_tasks; print('OK')"` prints OK
  - 256 lines ≥ 120; `windows_tasks.ps1` + `WINDOWS_TASKS` ≥ 2 hits; `publish_lock.json` + `_schema` ≥ 2 hits; 3 task names all present; `timezone.utc` ≥ 1 hit.

## Integration Smoke

실 환경 dry-run 검증 (win32):
```json
{
  "invocation_ts": "2026-04-20T13:18:18.173380+00:00",
  "dry_run": true,
  "block_hours": 49,
  "publish_lock_would_write": {
    "lock_path": ".planning/publish_lock.json",
    "future_iso": "2026-04-22T14:18:18.173380+00:00",
    "_schema": 1
  },
  "tasks_unregister": {
    "platform": "win32",
    "unregistered": false,
    "dry_run": true,
    "would_unregister": [
      "ShortsStudio_Pipeline",
      "ShortsStudio_Upload",
      "ShortsStudio_NotifyFailure"
    ]
  }
}
```

ROLLBACK.md 의 "긴급 전체 중단 (2분 이내)" 3 명령 중 명령 2 (`python -m scripts.rollback.stop_scheduler --block-hours 49`) 가 정확히 작동함을 확인. 실제 사고 발생 시 대표님이 copy-paste 하실 수 있는 경로가 end-to-end 검증 완료.

## FAIL-04 삼중 안전망 완성

| 축 | Plan | Mechanism | Effect |
|----|------|-----------|--------|
| 감지 | 10-01 | `skill_patch_counter.py` git log grep | `reports/skill_patch_count_YYYY-MM.md` violation_count + `FAILURES.md` F-D2-XX append |
| 잠금 | 10-02 | `drift_scan.py` deprecated_patterns.json | A 급 drift > 0 시 `.planning/STATE.md phase_lock: true` → 다음 작업 차단 |
| 복구 | **10-08** | `ROLLBACK.md` runbook + `stop_scheduler.py` CLI | 3 시나리오 × 5 단계 copy-paste 복구 + publish_lock future-timestamp + Windows Task Unregister |

Phase 10 Plan 08 완료로 FAIL-04 (ROADMAP §269, REQUIREMENTS line 138) 실증 삼중 안전망 완성. Plan 10-01 + 10-02 감지/잠금은 자동, Plan 10-08 복구는 대표님 judgement loop 포함 — 이는 의도된 분업 (사고 원인 판단은 인간 책임, 기계적 shutdown + data collection 은 CLI 자동화).

## Deviations from Plan

Plan 지시서와의 이탈 사항:

**1. [Rule 2 — Completeness] `_resolve_lock_path` helper 추가**
- **Found during:** Task 2 GREEN implementation
- **Issue:** Plan 지시는 `args.lock_path` default 를 `Path(os.environ.get("SHORTS_PUBLISH_LOCK_PATH", DEFAULT_LOCK_PATH))` 로 inline evaluation 하는 형태. 이는 argparse 가 default 를 **import time** 에 한 번만 평가하므로, 테스트가 `monkeypatch.setenv` 로 env var 를 변경해도 반영되지 않는 버그 존재 (Phase 8 `publish_lock.py` 의 `_lock_path()` helper 가 이 문제를 이미 회피).
- **Fix:** `--lock-path` default 를 `None` 으로 두고, `main()` 에서 `_resolve_lock_path(args.lock_path)` 헬퍼로 **런타임 평가** 하여 CLI flag > env > DEFAULT 우선순위를 보장. Test 6 `test_stop_scheduler_respects_env_override` 가 이 헬퍼를 통과함으로써 검증.
- **Files modified:** `scripts/rollback/stop_scheduler.py` (신규 `_resolve_lock_path` 5 lines + `main()` 내부 1 line).
- **Commit:** `3e2eeb7`

**2. [Rule 2 — Completeness] `publish_lock` dict 에 `lock_path` 추가 출력**
- **Found during:** Task 2 manual smoke inspection
- **Issue:** Plan 지시는 `summary["publish_lock"] = block_publish(...)` 만 기술. 실제 `block_publish` 는 `{last_upload_iso, jitter_applied_min, _schema}` 만 반환하므로, 대표님이 JSON stdout 을 보고 **어느 경로에 write 됐는지** 알 수 없음.
- **Fix:** `summary["publish_lock"]["lock_path"] = str(resolved_lock)` 한 줄 추가해서 operator 가 실 파일 경로를 확인할 수 있게 함. 본 정보는 rollback 복구 audit trail 의 필수 요소 (어느 파일이 bricked 됐는지 명확해야 복구 수순 진행 가능).
- **Files modified:** `scripts/rollback/stop_scheduler.py` (1 line in `main()`).
- **Commit:** `3e2eeb7`

## Deferred Issues

**D10-03-DEF-01 (pre-existing)** — `tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default` 가 Plan 10-08 작업과 무관하게 실패 중. 이미 `.planning/phases/10-sustained-operations/deferred-items.md` §D10-03-DEF-01 에 기록됨 (Plan 10-02 follow-up: 테스트 조건을 "missing == implicit false" 로 완화 OR `gsd-tools` 가 `phase_lock: false` 를 명시 출력하도록 수정). Plan 10-08 의 scope (`scripts/rollback/` + `ROLLBACK.md` + `tests/phase10/test_rollback_procedures.py`) 와 zero overlap — 범위 밖 고정.

## Regression 보존

- **Phase 10 Plans 1-7**: 109/110 PASS (1 pre-existing D10-03-DEF-01 out-of-scope)
- **Phase 10 Plan 08 본 plan**: 8/8 PASS
- **Phase 10 전체**: 117/118 PASS
- **Phase 8 publish_lock + kst_window**: 36/36 PASS (CLI 가 `publish_lock.py` schema 와 byte-for-byte 호환 확인)

## Self-Check: PASSED

- FOUND: `.planning/phases/10-sustained-operations/ROLLBACK.md` (185 lines)
- FOUND: `scripts/rollback/__init__.py` (5 lines)
- FOUND: `scripts/rollback/stop_scheduler.py` (256 lines)
- FOUND: `tests/phase10/test_rollback_procedures.py` (239 lines)
- FOUND commit: `ed1a80a` (docs ROLLBACK.md)
- FOUND commit: `cce2346` (test RED)
- FOUND commit: `3e2eeb7` (feat GREEN)
- Phase 10 Plan 08 success criteria 6/6 PASS

## Next (Post-Plan 10-08)

Phase 10 의 8 Plans 모두 ship 완료. 다음 단계:

1. **대표님 manual dispatch 리스트** — GH Secrets 등록 (YOUTUBE_TOKEN_JSON) + OAuth 재인증 실행 + Windows admin PowerShell 실 등록 (`powershell -File scripts/schedule/windows_tasks.ps1`) + NotebookLM 월 업로드.
2. **Plan 10-04 Scheduler workflow 실제 활성화** — `.github/workflows.disabled/` → `.github/workflows/` 복귀 1 개씩 점진적.
3. **Phase 10 Continuous Monitoring 시작** — `nyquist_compliant=true` flip 은 `phase10_acceptance.py` 가 6 ledger 파일 (reports/kpi_log/trajectory/CONFLICT_MAP/session_audit/FAILURES) 의 첫 실 데이터 확인 후 수행.
4. **ROADMAP Phase 10 Progress Table 0/8 → 8/8** — 본 Plan 완료로 Phase 10 의 8 Plan 모두 ship, 메타 작업 완결.

---

*Plan 10-08 completed in session #27 by 나베랄 감마 (Opus 4.7 1M context executor). 2 tasks, 3 commits, 4 files created, 0 files modified, 8 tests added, ~5 minutes wall time.*
