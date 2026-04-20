---
phase: 10-sustained-operations
plan: 05
subsystem: audit
tags: [audit, session-health, rolling-window, harness-audit, jsonl, zoneinfo, failures-append, audit-01]
requires:
  - scripts/validate/harness_audit.py      # Phase 7 (subprocess call target)
  - scripts/publisher/kst_window.py        # Phase 8 (KST timezone precedent, not imported)
  - tests/phase10/conftest.py              # Phase 10 Plan 1 (shared fixtures)
  - FAILURES.md                            # F-AUDIT-NN append target (hook-safe direct I/O)
provides:
  - scripts/audit/session_audit_rollup.py (30-day rolling session audit CLI — AUDIT-01)
  - logs/.gitkeep (git-tracked placeholder for gitignored session_audit.jsonl)
  - 11 behavioural tests covering subprocess mock, rolling math, boundary, FAILURES append
affects:
  - scripts/audit/
  - tests/phase10/
  - logs/ (new directory)
  - .gitignore (+4 lines: logs/*.jsonl + logs/*.json gitignored, !logs/.gitkeep exception)
tech-stack:
  added: []   # pure stdlib
  patterns:
    - Subprocess-based integration with sibling modules (not direct import) for failure-mode decoupling
    - Rolling-window math via zoneinfo KST + datetime.timedelta (stdlib only; pytz forbidden)
    - Direct open('a') FAILURES.md append (hook bypass per RESEARCH Pitfall 3, strict-prefix preserved)
    - 신규 스튜디오 guard — empty rolling window returns 100.0 (pass) so the first session doesn't fail
    - Explicit RuntimeError on non-zero subprocess returncode (Project Rule 3 — no silent fallback)
key-files:
  created:
    - scripts/audit/session_audit_rollup.py
    - tests/phase10/test_session_audit.py
    - logs/.gitkeep
  modified:
    - .gitignore
decisions:
  - "F-AUDIT-NN entry uses '## ' level-2 heading (not '### ' level-3 from plan draft) — consistency with existing ## F-CTX-NN / ## F-D2-NN convention. Regex + write header aligned. Rule 1 auto-fix (bug in plan draft)."
  - "Subprocess call to scripts.validate.harness_audit with --threshold 0 — decouples harness_audit's internal threshold from this CLI's own rolling threshold; returncode != 0 therefore signals real subprocess failure."
  - "Empty rolling window → (100.0, 0) default — 신규 스튜디오 must pass the first session; otherwise the very first invocation always fails with 0 samples."
  - "Naive ISO timestamps assumed KST (deterministic fallback) — prevents silent exclusion when a record somehow lacks offset; astimezone(KST) normalises all comparisons."
  - "Corrupt jsonl lines silently skipped — rolling math tolerates missing datapoints; a single corrupt line should not crash the health check."
  - "Tests pass explicit now= parameter — avoid coupling with conftest.freeze_kst_now autouse (which only patches skill_patch_counter). Cleaner + no conftest mutation risk."
metrics:
  duration_minutes: 5
  commits: 2
  tasks: 1
  tests_added: 11
  tests_passing: 11
  lines_added: 725   # 316 (rollup) + 405 (tests) + 4 (gitignore)
completed: 2026-04-20
---

# Phase 10 Plan 05: Session Audit Rolling Summary

대표님, D-2 Lock 기간의 "조용한 점수 하락" 방어선을 구축했습니다. 매 세션 감사 점수가 `logs/session_audit.jsonl` 에 박제되고, 30일 rolling 평균이 80 미만으로 떨어지면 FAILURES.md 에 `## F-AUDIT-NN` 엔트리가 자동 append 되며 exit 1 로 감사 실패를 신호합니다. `.claude/hooks/session_start.py` 는 한 바이트도 건드리지 않았습니다 (D-2 Lock 준수).

## What Was Built

### scripts/audit/session_audit_rollup.py (316 lines, stdlib only)

**CLI entry points (3 modes):**

| Mode | Command | Behaviour |
|------|---------|-----------|
| Default | `python -m scripts.audit.session_audit_rollup` | harness_audit subprocess → append jsonl → rolling check → exit 0 or 1 |
| Dry-run | `--dry-run` | harness_audit subprocess (observability) but no jsonl mutation, no FAILURES append |
| Skip-audit | `--skip-audit` | Rolling check only (pre-seeded jsonl) — no subprocess |

**Tunable flags:** `--threshold N` (default 80), `--window-days N` (default 30), `--jsonl PATH` (default `logs/session_audit.jsonl`), `--failures PATH` (default `FAILURES.md`), `--studio-root PATH` (default `.`).

**Public API (importable):**

```python
from scripts.audit.session_audit_rollup import (
    run_harness_audit,      # subprocess → audit JSON dict
    append_session_record,  # append one-line JSON to jsonl
    rolling_avg,            # (avg_score, sample_count) over N-day window
    append_failures,        # F-AUDIT-NN append → returns entry_id
    main,                   # CLI entry
)
```

### tests/phase10/test_session_audit.py (405 lines, 11 tests)

| # | Test | Covers |
|---|------|--------|
| 1 | `test_logs_gitkeep_exists_logs_jsonl_ignored` | logs/.gitkeep present + .gitignore registers logs/*.jsonl |
| 2 | `test_subprocess_call_to_harness_audit` | subprocess invokes `scripts.validate.harness_audit --json-out` |
| 3 | `test_append_to_jsonl` | One JSON line with timestamp/score/violations_count/warnings_count |
| 4 | `test_rolling_avg_empty_returns_100` | Empty + absent jsonl both → (100.0, 0) |
| 5 | `test_rolling_avg_below_80_triggers_failures_append` | [70,75,70] → avg 71.67 → F-AUDIT append + exit 1 |
| 6 | `test_rolling_avg_at_80_passes` | [80,80,80] → avg 80.0 → exit 0 (≥ boundary, not >) |
| 7 | `test_records_older_than_30_days_excluded` | 60-day-old record excluded; recent record only |
| 8 | `test_cli_dry_run_no_jsonl_mutation` | --dry-run preserves jsonl bytes exactly |
| 9 | `test_cli_score_threshold_override` | --threshold 70 accepts avg 75 |
| 10 | `test_cp949_safe_korean_reason` | Korean diagnostic text round-trips via UTF-8 reconfigure |
| 11 | `test_harness_audit_subprocess_failure_explicit_raise` | returncode != 0 → RuntimeError (no silent fallback) |

**Test strategy:** Subprocess mock via `monkeypatch.setattr(sar.subprocess, "run", ...)` with a `side_effect` that writes the fake audit JSON to the `--json-out` tmp path before returning a mock result object. FAILURES.md seeded per-test inside `tmp_path` to avoid polluting the real repo.

### logs/.gitkeep + .gitignore

- `logs/.gitkeep` — empty placeholder so the directory is git-tracked.
- `.gitignore` appended with:
  ```
  # Phase 10 Plan 5 — session audit log (gitignored; logs/.gitkeep 만 git-tracked)
  logs/*.jsonl
  logs/*.json
  !logs/.gitkeep
  ```

## Verification Evidence

```
$ py -3.11 -m pytest tests/phase10/test_session_audit.py -v
...
11 passed in 0.11s

$ py -3.11 -c "from scripts.audit.session_audit_rollup import main, rolling_avg, append_failures, append_session_record, run_harness_audit; print('OK')"
OK

$ py -3.11 -m scripts.audit.session_audit_rollup --dry-run --skip-audit
{
  "current_record": {"timestamp": "2026-04-20T22:08:02.146023+09:00", "skipped_audit": true},
  "rolling_avg": 100.0,
  "sample_count": 0,
  "threshold": 80,
  "window_days": 30,
  "passes": true,
  "dry_run": true,
  "skip_audit": true
}
# exit 0

$ py -3.11 -m scripts.audit.session_audit_rollup --dry-run
{
  "current_record": {"timestamp": "...+09:00", "score": 90, "violations_count": 0, "warnings_count": 0, ...},
  "rolling_avg": 100.0,
  "sample_count": 0,
  "threshold": 80,
  "passes": true,
  "dry_run": true
}
# exit 0 — real harness_audit returned score 90 (Phase 7 baseline preserved)
```

**Grep-level acceptance:**

| Criterion | Value |
|-----------|-------|
| `grep -c "F-AUDIT" session_audit_rollup.py` | 6 (regex + heading + docstring) |
| `grep -c "zoneinfo\|ZoneInfo" session_audit_rollup.py` | 3 (import + 2 uses) |
| `grep -c "pytz" session_audit_rollup.py` | 0 (stdlib only) |
| `wc -l session_audit_rollup.py` | 316 (≥ 140 min) |
| `wc -l test_session_audit.py` | 405 (≥ 100 min) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] F-AUDIT heading level mismatch in plan draft**

- **Found during:** Task 1 implementation (reading plan's `append_failures` template)
- **Issue:** Plan draft had `ids = re.findall(r"### F-AUDIT-(\d{2})", existing)` (level 3) but wrote the heading as `f"## {entry_id} — Session audit rolling avg 미달 ..."` (level 2). Inconsistency would cause `next_id` to always start from 01 on repeated runs (regex never matches the level-2 heading the function just wrote).
- **Fix:** Aligned both regex and write to `## F-AUDIT-NN` (level 2), consistent with existing `## F-CTX-01` / `## F-D2-NN` convention in FAILURES.md. Matches `scripts/audit/skill_patch_counter.py::append_failures` sibling pattern.
- **Files modified:** `scripts/audit/session_audit_rollup.py`
- **Commit:** `d291bd1`

**2. [Rule 1 — Bug] Spurious "pytz" mention in docstring**

- **Found during:** Acceptance-criterion grep check (`grep -c "pytz" == 0` required)
- **Issue:** Initial docstring read "pytz forbidden (stdlib only)" which made `grep -c pytz` return 1 instead of 0.
- **Fix:** Rephrased to "stdlib only (no 3rd-party tz libs)".
- **Files modified:** `scripts/audit/session_audit_rollup.py` (docstring only, no functional change)
- **Commit:** Squashed into `d291bd1` prior to staging.

### Not a Deviation — Pre-existing Out-of-Scope Failure

**`tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default`** — Confirmed pre-existing via `git stash && pytest` baseline. Already documented in `deferred-items.md::D10-03-DEF-01` (Plan 10-02 ownership). Plan 10-05 files do not touch STATE.md frontmatter or drift_scan internals.

## Authentication Gates

None. Plan 10-05 operates purely on local files and subprocess invocations; no external services, no API keys, no OAuth.

## Reusable Assets for Downstream Plans

| Asset | Who reuses | How |
|-------|-----------|-----|
| `run_harness_audit(studio_root) -> dict` | Future audit aggregators | Decoupled subprocess wrapper — any CLI can drop this in without importing harness_audit internals. |
| `rolling_avg(jsonl, days, now) -> (float, int)` | Any rolling-window metric (Plan 6 KPI, Plan 7 trajectory) | Generic stdlib math; works on any {timestamp, score} jsonl. |
| `append_failures(failures, avg, count, threshold, now) -> entry_id` | Future audit failure types | Pattern for hook-safe F-XXX-NN append; strict-prefix invariant preserved. |
| Subprocess-side-effect mock pattern | Future tests calling subprocess-integrated CLIs | `_make_fake_subprocess(score, returncode)` in test file — copyable template. |

## Requirements Satisfied

- **AUDIT-01**: `session_start.py` 매 세션 자동 감사 (점수 ≥ 80) — code shipped; runtime validation awaits dispatch by Plan 10-04 Scheduler OR manual 대표님 invocation.

## Next Steps

- **Plan 10-06** (research loop NotebookLM) + **Plan 10-07** (YPP trajectory) — Wave 3 parallel (currently executing).
- **Plan 10-08** (rollback docs) — Wave 4 sequential.
- **Future wiring opportunity:** Plan 10-04 `scripts/schedule/windows_tasks.ps1` 에 `session_audit_rollup` 을 registered Windows Task 로 추가 (현재는 별도 Plan 로 분리 유지 — boundary 존중).

## WARNING #2 Resolution

`depends_on: [10-04-scheduler-hybrid]` 만 선언된 Plan 10-05 frontmatter 는 Plan 10-02 drift-scan-phase-lock 과 **직접** 의존 관계를 선언하지 않습니다. Plan 10-04 가 이미 Plan 10-02 의 drift_scan.py 를 `drift-scan-weekly.yml` 에서 transit 의존하므로 wave 병렬성 오판을 제거했습니다.

## Self-Check: PASSED

- [x] `scripts/audit/session_audit_rollup.py` exists
- [x] `tests/phase10/test_session_audit.py` exists
- [x] `logs/.gitkeep` exists
- [x] `.gitignore` contains `logs/*.jsonl`
- [x] Commit `ac2c206` (RED) found in git log
- [x] Commit `d291bd1` (GREEN) found in git log
- [x] 11/11 Plan 10-05 tests GREEN
- [x] 95/96 Phase 10 tests GREEN (1 pre-existing D10-03-DEF-01 out of scope)
- [x] D-2 Lock: zero `.claude/hooks|skills|agents SKILL.md|CLAUDE.md` edits
