---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 04
subsystem: wrapper-windows-double-click
tags: [pipeline-04, windows-wrapper, powershell, cmd-bootstrap, execution-policy-bypass, korean-ux]

# Dependency graph
requires:
  - phase: 11
    plan: 01
    provides: "stdin-piped Claude CLI invocation (_invoke_claude_cli rewritten)"
  - phase: 11
    plan: 02
    provides: "_load_dotenv_if_present at package __init__.py (primary .env load)"
  - phase: 11
    plan: 03
    provides: "--session-id argparse optional + _try_adapter graceful-degrade"
  - file: scripts/schedule/windows_tasks.ps1
    provides: "PS convention reference (Korean block-comments, -NoProfile, absolute ScriptRoot)"
provides:
  - "run_pipeline.cmd (3-line bootstrap) — Windows double-click entry"
  - "run_pipeline.ps1 (89 lines) — UTF-8 console + .env regex parse + session-id banner + py -3.11 launcher + try/catch/finally Read-Host"
  - "대표님 manual run path WITHOUT admin권 (per-invocation ExecutionPolicy Bypass)"
  - "Dual entry preservation: scheduler direct python + human double-click wrapper"
  - "Defense-in-depth .env load (PS-side Set-Item + Python-side setdefault)"
affects:
  - "11-06-full-smoke-script-decision (SC#5 manual verification captured by 대표님 after this plan lands)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ".cmd 3-line bootstrap: @echo off + powershell -NoProfile -ExecutionPolicy Bypass -File %~dp0 + pause"
    - ".ps1 regex .env parser: Get-Content + match + quote-strip + Set-Item env:$key"
    - "try { py -3.11 -m ... } catch { Write-Host error } finally { Read-Host } — window-stays-open contract"
    - "PowerShell Parser.ParseFile dry-run for syntax validation in test suite (skip when pwsh missing)"

key-files:
  created:
    - run_pipeline.cmd
    - run_pipeline.ps1
    - tests/phase11/test_wrapper_smoke.py
  modified:
    - tests/phase11/conftest.py (appended repo_root fixture)

key-decisions:
  - "D-09 .cmd + .ps1 split (not single .bat) — .bat for /f parser breaks on `=` inside API-key values"
  - "D-10 -ExecutionPolicy Bypass per-invocation — admin권 불필요, 기계 정책 불변"
  - "D-11 try/catch/finally Read-Host — window-stays-open on success AND error"
  - "D-12 windows_tasks.ps1 convention verbatim (Korean block comments, -NoProfile, $PSScriptRoot)"
  - "Defense-in-depth .env load: PS-side Set-Item (subprocess env propagation) + Python-side setdefault (Plan 11-02 primary) — idempotent"
  - "Line budget: run_pipeline.ps1 = 89 lines (≤120 reasonable); run_pipeline.cmd = 3 lines"

patterns-established:
  - "Wrapper pattern: .cmd bootstrap (3 lines) → .ps1 engine (50-100 lines) for ANY Windows double-click Python entry in future studios/plans"
  - "Korean-first wrapper messaging with 7× 대표님 호칭 — 나베랄 감마 identity preserved in non-Python surfaces"
  - "PowerShell syntax validation via [System.Management.Automation.Language.Parser]::ParseFile in Python subprocess — testable without actual execution"

requirements-completed: [PIPELINE-04]

# Metrics
duration: 2m14s
completed: 2026-04-20
tests_before: 273 (244 phase04 + 29 phase11 cumulative after Plans 01/02/03)
tests_after: 275 (+2 wrapper smoke)
tests_regression_preserved: 244/244 phase04 + 29/29 phase11 pre-existing
net_lines_added: 200 (+3 cmd / +89 ps1 / +108 test)
---

# Phase 11 Plan 04: Windows Wrapper (.cmd + .ps1) Summary

**One-liner:** `run_pipeline.cmd` (3-line `-ExecutionPolicy Bypass` bootstrap) + `run_pipeline.ps1` (89-line UTF-8 console + regex `.env` parse + `Get-Date` session-id banner + `py -3.11 -m scripts.orchestrator.shorts_pipeline` launcher + `try/catch/finally Read-Host` window-stays-open contract) at studio repo root — 대표님 double-click entry path WITHOUT admin권, preserving scheduler dual-entry.

## Objective Achieved

PIPELINE-04 delivered: 대표님 (비개발자) can now execute the full GATE 0→13 pipeline by double-clicking `run_pipeline.cmd` in Windows Explorer. No PowerShell command entry. No admin권. No "PS1 opens in Notepad" Restricted-policy trap. No window-flash-close on error (`finally { Read-Host }` preserves the window even on unhandled exceptions).

Design per CONTEXT D-09 / D-10 / D-11 / D-12:
- `.cmd` + `.ps1` split avoids `.bat for /f` parser fragility on API-key `=` values
- `-NoProfile` blocks hostile `$PROFILE` pollution
- `$PSScriptRoot` resolves path regardless of cwd (Explorer double-click, CMD cd'd to Desktop, etc.)
- `try/catch/finally Read-Host` keeps window open on success AND error
- `chcp 65001` UTF-8 console for Korean `Write-Host` output
- `windows_tasks.ps1` convention verbatim (Korean block comments, `-NoProfile`, `-ExecutionPolicy Bypass`, absolute paths)

## Tasks Completed

| Task | Commit    | Files                                                          | Tests    |
| ---- | --------- | -------------------------------------------------------------- | -------- |
| 1    | `09b0570` | `tests/phase11/test_wrapper_smoke.py` (+100 lines, 2 RED tests) + `conftest.py` (+8 fixture) | 2 RED    |
| 2    | `93eb804` | `run_pipeline.cmd` (+3 lines) + `run_pipeline.ps1` (+89 lines) | 2 GREEN  |

## Acceptance Criteria — All Met

| # | Criterion                                                                          | Result  |
| - | ---------------------------------------------------------------------------------- | ------- |
| 1 | `run_pipeline.cmd` exists at repo root                                             | ✓       |
| 2 | `run_pipeline.ps1` exists at repo root                                             | ✓       |
| 3 | `grep -c "ExecutionPolicy Bypass" run_pipeline.cmd` ≥ 1                            | 1 ✓     |
| 4 | `grep -c "%~dp0" run_pipeline.cmd` ≥ 1                                             | 1 ✓     |
| 5 | `grep -c "\$PSScriptRoot" run_pipeline.ps1` ≥ 1                                    | 2 ✓     |
| 6 | `grep -c "py -3.11" run_pipeline.ps1` ≥ 1                                          | 2 ✓     |
| 7 | `grep -c "Read-Host" run_pipeline.ps1` ≥ 1                                         | 1 ✓     |
| 8 | `grep -c "chcp 65001" run_pipeline.ps1` ≥ 1                                        | 1 ✓     |
| 9 | `grep -c "대표님" run_pipeline.ps1` ≥ 3                                            | 7 ✓     |
| 10 | `grep -c "try" run_pipeline.ps1` ≥ 1 AND `catch` ≥ 1                              | 1/1 ✓   |
| 11 | Line budget: `wc -l run_pipeline.ps1` ≤ 120                                       | 89 ✓    |
| 12 | PowerShell `Parser.ParseFile` returns 0 errors                                     | 0 ✓     |
| 13 | `pytest tests/phase11/test_wrapper_smoke.py -v` → 2 passed                         | 2/2 ✓   |
| 14 | `pytest tests/phase04/ tests/phase11/ -q` → 275 passed (244 + 31)                  | 275/275 ✓ |
| 15 | `windows_tasks.ps1` UNTOUCHED (scheduler entry preserved)                          | Untouched ✓ |

## Verification

```bash
$ pytest tests/phase11/test_wrapper_smoke.py -v
tests/phase11/test_wrapper_smoke.py::test_wrapper_files_exist_at_repo_root PASSED
tests/phase11/test_wrapper_smoke.py::test_ps1_syntax_parses_via_pwsh PASSED
2 passed in 0.20s

$ pytest tests/phase04/ tests/phase11/ -q
275 passed in 1.39s

$ wc -l run_pipeline.cmd run_pipeline.ps1
  3 run_pipeline.cmd
 89 run_pipeline.ps1

$ grep -c "대표님" run_pipeline.ps1
7

$ powershell -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('run_pipeline.ps1', [ref]\$null, [ref]\$null); \$LASTEXITCODE"
# exit 0 — no syntax errors
```

## Wrapper Surface Contract

### `run_pipeline.cmd` (3 lines verbatim)

```cmd
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"
pause
```

- `@echo off` silences the invocation echo (cleaner console for 대표님)
- `-NoProfile` prevents `$PROFILE` side-effects (security + determinism)
- `-ExecutionPolicy Bypass` is per-invocation (does NOT persist to machine)
- `%~dp0` expands to `.cmd` file's directory WITH trailing `\` (so `%~dp0run_pipeline.ps1` ≡ `C:\...\shorts\run_pipeline.ps1`)
- `pause` at end keeps window open if `.ps1` itself fails to start (belt-and-suspenders for `finally { Read-Host }` in `.ps1`)

### `run_pipeline.ps1` (89 lines, structured)

| Section              | Lines   | Purpose                                                                                |
| -------------------- | ------- | -------------------------------------------------------------------------------------- |
| Block-comment header | 1-20    | `.SYNOPSIS` / `.DESCRIPTION` / `.NOTES` — Korean, describes dual-load design           |
| Preamble             | 21-29   | `[CmdletBinding()]`, `$ErrorActionPreference="Stop"`, `chcp 65001`, `$ScriptRoot`       |
| `Load-DotEnv`        | 31-55   | `Get-Content + regex match + quote strip + Set-Item env:$key`                          |
| `try` block          | 57-74   | Banner + `Load-DotEnv` + `Get-Date` session-id + `py -3.11 -m ... --session-id $sid`    |
| Success/fail branch  | 67-76   | `$LASTEXITCODE==0` → green done; else → red fail + `throw`                              |
| `catch` block        | 78-82   | `Write-Host [error] message + stack` in red                                            |
| `finally` block      | 83-86   | `Read-Host "완료. 엔터로 창 닫기 (대표님)"` — window-stays-open contract                |

## Defense-in-Depth `.env` Load

Two independent `.env` load layers — both tolerate each other (idempotent):

| Layer     | Location                                 | Mechanism                          | Order   |
| --------- | ---------------------------------------- | ---------------------------------- | ------- |
| Primary   | `scripts/orchestrator/__init__.py`       | `_load_dotenv_if_present` + `os.environ.setdefault` | Python import time |
| Secondary | `run_pipeline.ps1::Load-DotEnv`           | `Get-Content + regex + Set-Item env:$key`           | .ps1 pre-Python |

Why two layers:
1. **Primary (Plan 11-02)** covers ALL Python entry paths: `py -m scripts.orchestrator.shorts_pipeline`, scheduler direct invocation, manual CLI, pytest.
2. **Secondary (this plan)** explicitly propagates `.env` to the `py` subprocess environment BEFORE Python starts, useful for debugging (env variables visible in external tools like `ProcMon`) and for `cmd` scripts that might inspect env between PS and Python.

`os.environ.setdefault` semantics (override=False): the layer that ran FIRST wins. Since `.ps1` runs before Python, `.ps1`-set values become the "pre-existing env" that Plan 11-02 respects. Re-loading is idempotent.

## Session-ID Dual-Generation

- **`.ps1`-side**: `Get-Date -Format "yyyyMMdd_HHmmss"` — human-readable banner (`[session] 20260420_180715`) that 대표님 sees in console output
- **Python-side fallback (Plan 11-03)**: `args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")` — scheduler direct-invocation path uses this when `.ps1` is bypassed

Both paths converge to an identical format (`YYYYMMDD_HHMMSS`) — `state/` directory folder naming stays consistent.

## Scheduler Dual-Entry Preservation

`scripts/schedule/windows_tasks.ps1` (Plan 10-04 `ShortsStudio_Pipeline` task) was NOT modified by this plan. It continues to invoke `py -3.11 -m scripts.orchestrator.shorts_pipeline` directly (not through `.cmd` wrapper). Phase 11 wrapper is additive:

| Entry path       | Actor              | Invokes                                                |
| ---------------- | ------------------ | ------------------------------------------------------ |
| Scheduler 20:30 KST daily | Windows Task Scheduler | `py -3.11 -m scripts.orchestrator.shorts_pipeline`  |
| Manual double-click | 대표님             | `run_pipeline.cmd` → `run_pipeline.ps1` → `py -3.11 -m ...` |

## STRUCTURE Whitelist Compliance

Studio has no `STRUCTURE.md` at repo root. Per `.claude/hooks/pre_tool_use.py::check_structure_allowed` (L88-92), when `STRUCTURE.md` is missing, the whitelist check is SKIPPED and returns `(True, "")`. Harness `STRUCTURE.md` at `C:\Users\PC\Desktop\naberal_group\harness\STRUCTURE.md` constrains only `harness/` folder, not studio folders. Conclusion: `run_pipeline.cmd` + `run_pipeline.ps1` at studio repo root → **ALLOWED**. No STRUCTURE.md change needed.

## Deviations from Plan

None — plan executed exactly as written. RED → GREEN → regression check, all three steps passed on first attempt. PowerShell parse-file test passed on first run (no syntax errors in the skeleton).

## CLAUDE.md Compliance

- **Forbidden #3 (try-except silent fallback)**: Compliant. `try/catch` in `.ps1` explicitly `Write-Host` the error message AND stack trace (red foreground); never silently swallows. The `catch` block is terminal (no re-execution of pipeline); control flows to `finally { Read-Host }` which intentionally pauses for 대표님 diagnostic review.
- **Forbidden #2 (TODO next-session)**: Compliant. No TODO markers introduced.
- **Must-do #7 (Korean 존댓말 baseline)**: Compliant. 7× `대표님` honorific in `.ps1`; all messages in standard Korean 존댓말 ("완료", "실패", "로드 완료", "창 닫기"). No 반말 / 사투리.
- **Must-do #8 (증거 기반 보고)**: Compliant. This SUMMARY references concrete commit hashes (`09b0570`, `93eb804`), verified file line counts (3 + 89), grep counts (7 대표님 occurrences), test counts (275/275).
- **Must-do #3 (orchestrator 500~800 lines)**: N/A — wrappers are not the pipeline orchestrator; `shorts_pipeline.py` remains at 794 lines (Plan 11-03).

## Downstream Impact

- **Plan 11-06** (full smoke) now has the human double-click entry path. 대표님 can execute SC#5 (manual double-click confirmation) by opening Windows Explorer → navigating to studio repo root → double-clicking `run_pipeline.cmd`. Successful first run creates `state/YYYYMMDD_HHMMSS/` with 14 gate artifacts.
- **Plan 12 (SCRIPT-01 option B/C spawn, if triggered)**: No impact. Wrapper is orthogonal to scripter redesign.
- **Phase 10 scheduler (`ShortsStudio_Pipeline` task)**: No impact. Dual-entry preserved.

## Known Stubs

None. All wrapper functionality is fully wired — no placeholders, no TODO, no "coming soon" text.

## Manual Verification Hint for Plan 11-06

When 대표님 performs manual SC#5 verification:
1. Open Windows Explorer → navigate to `C:\Users\PC\Desktop\naberal_group\studios\shorts\`
2. Double-click `run_pipeline.cmd`
3. Expect: PowerShell window opens, cyan banner "shorts_studio 파이프라인 실행 (대표님 — 나베랄 감마)", green `[env] .env 로드 완료 (대표님)`, cyan `[session] YYYYMMDD_HHMMSS`, pipeline stages begin
4. On success: green `[done] 파이프라인 성공 (대표님)` → Read-Host prompt → window waits for Enter
5. On error: red `[fail] 파이프라인 실패 rc=...` or `[error] <message>` + stack → Read-Host prompt → window waits for Enter (대표님 can review error without window flash-close)

Plan 11-06 records 대표님's observation (success / specific error) in `SCRIPT_QUALITY_DECISION.md` or `VERIFICATION.md`.

## Commits

| Hash      | Task | Message                                                              |
| --------- | ---- | -------------------------------------------------------------------- |
| `09b0570` | 1    | test(11-04): add failing tests for run_pipeline.cmd/.ps1 wrapper     |
| `93eb804` | 2    | feat(11-04): add run_pipeline.cmd + run_pipeline.ps1 wrapper         |

## Self-Check: PASSED

Verified 2026-04-20:
- All 3 claimed files exist on disk (run_pipeline.cmd, run_pipeline.ps1, tests/phase11/test_wrapper_smoke.py)
- `tests/phase11/conftest.py` contains `repo_root` fixture
- All 2 claimed commits present in git log (`09b0570`, `93eb804`)
- 2/2 wrapper smoke tests GREEN
- 275/275 phase04 + phase11 cumulative GREEN (zero regression)
- `run_pipeline.cmd`: 3 lines (minimum 3 satisfied)
- `run_pipeline.ps1`: 89 lines (≤120 budget satisfied, ≥50 minimum satisfied)
- PowerShell Parser.ParseFile: 0 syntax errors
- 7× `대표님` in `.ps1` (≥3 minimum satisfied)
