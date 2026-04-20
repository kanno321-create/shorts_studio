---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 04
type: execute
wave: 2
depends_on: [11-01-invoker-stdin-fix-PLAN, 11-02-dotenv-loader-PLAN, 11-03-adapter-graceful-degrade-PLAN]
files_modified:
  - run_pipeline.cmd
  - run_pipeline.ps1
  - tests/phase11/test_wrapper_smoke.py
autonomous: true
requirements: [PIPELINE-04]
must_haves:
  truths:
    - "대표님 double-clicks `run_pipeline.cmd` → PowerShell window opens, `.env` loads, pipeline starts, window stays open on success AND on error (pause-on-error via try/catch/finally Read-Host)"
    - "No administrator privileges required — `.cmd` bootstrap uses `-ExecutionPolicy Bypass` per-invocation (does NOT mutate machine policy)"
    - "UTF-8 console via `chcp 65001` — Korean Write-Host output renders correctly"
    - "`.ps1` auto-generates `--session-id` via `Get-Date -Format yyyyMMdd_HHmmss` for explicit wrapper UX (Python-side auto-default from Plan 11-03 also works; wrapper-side provides human-readable banner)"
    - "Windows Task Scheduler existing ShortsStudio_Pipeline task UNTOUCHED — dual entry path (scheduler direct Python, human `.cmd` wrapper)"
    - "STRUCTURE.md whitelist: studio has no STRUCTURE.md → root files allowed (RESEARCH §STRUCTURE Whitelist Verification)"
  artifacts:
    - path: "run_pipeline.cmd"
      provides: "Windows double-click bootstrap (3 lines)"
      min_lines: 3
      contains: "ExecutionPolicy Bypass"
    - path: "run_pipeline.ps1"
      provides: "UTF-8 console + .env regex parse + py -3.11 launcher + try/catch/finally Read-Host"
      min_lines: 50
      contains: "PSScriptRoot, Get-Date, py -3.11, Read-Host"
    - path: "tests/phase11/test_wrapper_smoke.py"
      provides: "2 tests: file existence + PowerShell dry-run parse (no actual pipeline launch)"
      min_lines: 60
  key_links:
    - from: "run_pipeline.cmd (double-click entry)"
      to: "run_pipeline.ps1 (engine)"
      via: "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0run_pipeline.ps1\""
      pattern: "%~dp0run_pipeline\\.ps1"
    - from: "run_pipeline.ps1"
      to: ".env (regex parse) + py -3.11 -m scripts.orchestrator.shorts_pipeline"
      via: "Set-Item env:$key + Get-Date timestamp"
      pattern: "py -3\\.11 -m scripts\\.orchestrator\\.shorts_pipeline"
---

<objective>
PIPELINE-04: Create 2-file double-click wrapper at studio repo root. `run_pipeline.cmd` is the 3-line bootstrap that bypasses Windows ExecutionPolicy Restricted via `-ExecutionPolicy Bypass` per-invocation; `run_pipeline.ps1` is the engine that loads `.env` (second layer of defense; Plan 11-02 already auto-loads at Python import), generates session-id, calls `py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id ...`, and wraps everything in try/catch/finally Read-Host so the window stays open on success AND error (대표님 never sees a window flash-close).

Purpose: 대표님 ("비개발자") executes the pipeline with one double-click — no PowerShell command entry, no admin rights, no "PS1 file opens in Notepad" Restricted-policy trap, no window-flash-close on error.

Design per D-09 / D-10 / D-11 / D-12:
- `.cmd` + `.ps1` split (not single `.bat`) because `.bat` `for /f` parser breaks on `=` inside API-key values (Runway key has `:` and `=`)
- `-NoProfile` avoids hostile $PROFILE pollution
- `$PSScriptRoot` for path resolution (PS 3.0+; all Win11)
- try/catch + `finally { Read-Host }` keeps the window open even on unhandled error
- `chcp 65001` for UTF-8 Korean console rendering
- Follows `scripts/schedule/windows_tasks.ps1` conventions (Korean block comments, `-NoProfile`, absolute paths)

Output:
- `run_pipeline.cmd` at studio repo root
- `run_pipeline.ps1` at studio repo root
- `tests/phase11/test_wrapper_smoke.py` with 2 tests (file existence + PowerShell dry-run parse validation)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md
@scripts/schedule/windows_tasks.ps1

<interfaces>
<!-- Existing PS convention reference (Plan 10-04 windows_tasks.ps1 L1-45) -->

From scripts/schedule/windows_tasks.ps1:
- Block comment headers with .SYNOPSIS / .DESCRIPTION / .NOTES / .PARAMETER sections
- `$ErrorActionPreference = "Stop"`
- `[CmdletBinding()]` param() block
- Korean block comments with technical references
- `-NoProfile -ExecutionPolicy Bypass` for security

Phase 11-01/02/03 dependency artifacts (must exist before this plan):
- `scripts/orchestrator/invokers.py` uses stdin piping (Plan 11-01)
- `scripts/orchestrator/__init__.py` has `_load_dotenv_if_present()` (Plan 11-02)
- `scripts/orchestrator/shorts_pipeline.py` has optional `--session-id` (Plan 11-03)

`.env` file contents (current, do not modify): 12 keys present per RESEARCH §Environment Availability.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wave 0 tests — wrapper file existence + .ps1 dry-run parse validation</name>
  <files>tests/phase11/test_wrapper_smoke.py</files>
  <read_first>
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 4 + §STRUCTURE Whitelist Verification
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-09, D-10, D-11, D-12
    - scripts/schedule/windows_tasks.ps1 (convention reference)
    - tests/phase10/test_windows_tasks.py if it exists — Plan 10-04's PS1 test patterns (if any)
  </read_first>
  <behavior>
    - Test 1 `test_wrapper_files_exist_at_repo_root`: both `run_pipeline.cmd` and `run_pipeline.ps1` exist at repo root; `.cmd` contains `ExecutionPolicy Bypass`; `.ps1` contains `PSScriptRoot`, `Get-Date`, `py -3.11`, `Read-Host`
    - Test 2 `test_ps1_syntax_parses_via_pwsh_noexecute`: invoke `powershell -NoProfile -Command "&{ . {Get-Content ...} | Out-Null }"` against the .ps1 using `[System.Management.Automation.Language.Parser]::ParseFile` — no parse errors. If PowerShell not installed (CI edge case), skip with `pytest.skip`.
    - Both tests use `repo_root` fixture (already exists in tests/phase10/conftest.py — may need to add to tests/phase11/conftest.py)
  </behavior>
  <action>
    First, add a `repo_root` fixture to `tests/phase11/conftest.py` if not already there. Check current conftest.py (from Plan 11-01) and APPEND if missing:

    ```python
    @pytest.fixture
    def repo_root() -> Path:
        """Absolute path to studio repo root."""
        # conftest.py lives at tests/phase11/; parents[2] = repo root
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root
    ```

    Append this fixture to `tests/phase11/conftest.py` (do not overwrite — use Edit/append).

    Now create `tests/phase11/test_wrapper_smoke.py`:
    ```python
    """PIPELINE-04 wrapper tests — file existence + .ps1 parse dry-run."""
    from __future__ import annotations

    import shutil
    import subprocess
    from pathlib import Path

    import pytest


    def test_wrapper_files_exist_at_repo_root(repo_root: Path):
        cmd_path = repo_root / "run_pipeline.cmd"
        ps1_path = repo_root / "run_pipeline.ps1"
        assert cmd_path.exists(), f"{cmd_path} must exist at repo root (PIPELINE-04)"
        assert ps1_path.exists(), f"{ps1_path} must exist at repo root (PIPELINE-04)"

        cmd_text = cmd_path.read_text(encoding="utf-8", errors="replace")
        assert "ExecutionPolicy Bypass" in cmd_text, (
            ".cmd must use `-ExecutionPolicy Bypass` (D-10 admin-free policy override)"
        )
        assert "run_pipeline.ps1" in cmd_text
        assert "%~dp0" in cmd_text, "`.cmd` must resolve its own directory via %~dp0"

        ps1_text = ps1_path.read_text(encoding="utf-8", errors="replace")
        assert "$PSScriptRoot" in ps1_text, ".ps1 must use $PSScriptRoot (PS 3.0+ convention)"
        assert "Get-Date" in ps1_text, ".ps1 must auto-generate session-id via Get-Date"
        assert "py -3.11" in ps1_text, ".ps1 must invoke `py -3.11` launcher"
        assert "scripts.orchestrator.shorts_pipeline" in ps1_text
        assert "Read-Host" in ps1_text, ".ps1 must pause-on-exit via Read-Host"
        assert "chcp 65001" in ps1_text, ".ps1 must enable UTF-8 console (한국어)"
        assert "대표님" in ps1_text, ".ps1 must address 대표님 (나베랄 감마 identity)"


    def test_ps1_syntax_parses_via_pwsh(repo_root: Path):
        """Parse-only PowerShell syntax validation. Skips if powershell not available."""
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            pytest.skip("powershell / pwsh not available on this machine")
        ps1_path = repo_root / "run_pipeline.ps1"
        if not ps1_path.exists():
            pytest.fail("run_pipeline.ps1 must exist before parse test")
        # Ask PowerShell to parse the file without executing.
        parse_cmd = (
            "$errors = $null; $tokens = $null; "
            f"[System.Management.Automation.Language.Parser]::ParseFile('{ps1_path}', "
            "[ref]$tokens, [ref]$errors) | Out-Null; "
            "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 } "
            "else { exit 0 }"
        )
        result = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", parse_cmd],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, (
            f"PowerShell parse errors in run_pipeline.ps1:\n{result.stdout}\n{result.stderr}"
        )
    ```
  </action>
  <verify>
    <automated>pytest tests/phase11/test_wrapper_smoke.py --collect-only -q 2>&1 | tail -10</automated>
  </verify>
  <acceptance_criteria>
    - `tests/phase11/test_wrapper_smoke.py` exists with 2 test functions
    - `tests/phase11/conftest.py` contains a `repo_root` fixture
    - Tests RED: `pytest tests/phase11/test_wrapper_smoke.py -v 2>&1 | grep -E "FAILED|ERROR"` returns ≥1 (files don't exist yet)
  </acceptance_criteria>
  <done>2 RED wrapper tests seeded; repo_root fixture added to conftest.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create run_pipeline.cmd + run_pipeline.ps1 at repo root — GREEN both tests</name>
  <files>run_pipeline.cmd, run_pipeline.ps1</files>
  <read_first>
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 4 (L690-763 full .ps1 skeleton)
    - scripts/schedule/windows_tasks.ps1 (convention verbatim — block comments, -NoProfile, $ErrorActionPreference)
    - tests/phase11/test_wrapper_smoke.py (from Task 1 — exact contract strings)
  </read_first>
  <behavior>
    - Both Task 1 tests GREEN
    - `.cmd` is 3 lines: `@echo off` + powershell invocation + `pause`
    - `.ps1` is ~50-70 lines following the §Pattern 4 skeleton verbatim, with Korean block-comment header, try/catch/finally Read-Host, colored Write-Host banner
    - PowerShell parse-file test GREEN (syntax valid)
  </behavior>
  <action>
    **Create `run_pipeline.cmd`** at studio repo root (`c:/Users/PC/Desktop/naberal_group/studios/shorts/run_pipeline.cmd`). EXACT content (3 lines):

    ```
    @echo off
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"
    pause
    ```

    Save with UTF-8 encoding (no BOM needed — `.cmd` uses ASCII only).

    **Create `run_pipeline.ps1`** at studio repo root (`c:/Users/PC/Desktop/naberal_group/studios/shorts/run_pipeline.ps1`). EXACT content:

    ```powershell
    <#
    .SYNOPSIS
      shorts_studio 파이프라인 실행 — 대표님 더블클릭 진입점.

    .DESCRIPTION
      .env 자동 로드 + session-id 자동 생성 + Python 실행 + 창 유지.
      관리자 권한 불필요 (run_pipeline.cmd 가 -ExecutionPolicy Bypass 로 진입).

    .NOTES
      Phase 11 PIPELINE-04. 기존 scripts/schedule/windows_tasks.ps1 컨벤션 준수
      (Korean block-comments, -NoProfile, absolute $PSScriptRoot).

      이중 로드 설계: scripts/orchestrator/__init__.py 의 _load_dotenv_if_present 가
      Python import 시점에 .env 를 다시 로드하므로 .ps1 의 Set-Item 은 "subprocess
      환경 변수 명시 전파" 역할을 담당 (중복 로드는 setdefault 로 idempotent).
    #>
    [CmdletBinding()]
    param()

    $ErrorActionPreference = "Stop"
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null  # UTF-8 console — 한국어 Write-Host

    $ScriptRoot = $PSScriptRoot
    Set-Location $ScriptRoot

    function Load-DotEnv {
        param([string]$Path)
        if (-not (Test-Path $Path)) {
            Write-Host "[env] .env 파일 없음 (대표님 — 기존 환경변수로 진행)" -ForegroundColor Yellow
            return
        }
        Get-Content $Path -Encoding UTF8 | ForEach-Object {
            $line = $_.TrimEnd("`r")
            $stripped = $line.Trim()
            if ($stripped -eq "" -or $stripped.StartsWith("#")) { return }
            if ($line -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
                $key   = $Matches[1]
                $value = $Matches[2]
                # Strip matched surrounding quotes
                if ($value.Length -ge 2) {
                    $first = $value.Substring(0, 1)
                    $last  = $value.Substring($value.Length - 1, 1)
                    if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                }
                Set-Item -Path "env:$key" -Value $value
            }
        }
        Write-Host "[env] .env 로드 완료 (대표님)" -ForegroundColor Green
    }

    try {
        Write-Host "===================================================" -ForegroundColor Cyan
        Write-Host " shorts_studio 파이프라인 실행 (대표님 — 나베랄 감마)" -ForegroundColor Cyan
        Write-Host "===================================================" -ForegroundColor Cyan

        Load-DotEnv -Path "$ScriptRoot\.env"

        $sessionId = Get-Date -Format "yyyyMMdd_HHmmss"
        Write-Host "[session] $sessionId" -ForegroundColor Cyan
        Write-Host "[launch]  py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id $sessionId" -ForegroundColor DarkCyan

        & py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id $sessionId
        $rc = $LASTEXITCODE

        if ($rc -eq 0) {
            Write-Host "" -ForegroundColor Green
            Write-Host "[done] 파이프라인 성공 (대표님)" -ForegroundColor Green
        } else {
            Write-Host "" -ForegroundColor Red
            Write-Host "[fail] 파이프라인 실패 rc=$rc (대표님 — 위 로그 확인)" -ForegroundColor Red
            throw "pipeline returned $rc"
        }
    }
    catch {
        Write-Host "" -ForegroundColor Red
        Write-Host "[error] $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "[error] 스택: $($_.ScriptStackTrace)" -ForegroundColor DarkRed
    }
    finally {
        Write-Host ""
        Read-Host "완료. 엔터로 창 닫기 (대표님)"
    }
    ```

    Save both files at the studio repo root.

    **Verification sweep:**
    ```
    pytest tests/phase11/test_wrapper_smoke.py -v      # 2 GREEN
    pytest tests/phase11/ -q                            # all Phase 11 tests so far
    pytest tests/phase04/ -q                            # baseline preserved
    ```

    **Manual smoke hint (NOT part of automated verify — documented for execute-phase):**
    - 대표님 opens Windows Explorer → navigates to studio repo root → double-clicks `run_pipeline.cmd` → PowerShell window opens, reads `.env`, generates session-id, invokes Python. On error, window stays open with the error; on success, window stays open until Enter. This is **SC#5 manual verification** recorded in VERIFICATION.md by Plan 11-06.
  </action>
  <verify>
    <automated>pytest tests/phase11/test_wrapper_smoke.py tests/phase11/test_invoker_stdin.py tests/phase11/test_dotenv_loader.py tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `test -f run_pipeline.cmd && test -f run_pipeline.ps1` (both exist at repo root) — verify via `ls` in studio root
    - `grep -c "ExecutionPolicy Bypass" run_pipeline.cmd` returns 1
    - `grep -c "%~dp0run_pipeline.ps1" run_pipeline.cmd` returns 1
    - `grep -c "PSScriptRoot" run_pipeline.ps1` returns ≥1
    - `grep -c "py -3.11" run_pipeline.ps1` returns 1
    - `grep -c "Read-Host" run_pipeline.ps1` returns ≥1
    - `grep -c "chcp 65001" run_pipeline.ps1` returns 1
    - `grep -c "대표님" run_pipeline.ps1` returns ≥3 (Korean-first messaging)
    - `pytest tests/phase11/test_wrapper_smoke.py -v` → 2 passed
    - PowerShell parse-file returns 0 errors (Test 2 GREEN)
    - All prior Phase 11 tests still GREEN (regression check)
  </acceptance_criteria>
  <done>Wrapper files exist at repo root with verified grep markers; both wrapper tests GREEN; Phase 11 cumulative tests (Plans 01+02+03+04 = 22 tests) all GREEN.</done>
</task>

</tasks>

<verification>
**Per-plan verify:**
```bash
pytest tests/phase11/ -q                                   # 22 tests GREEN (01+02+03+04 cumulative)
pytest tests/phase04/ -q                                   # 244/244 baseline
ls run_pipeline.cmd run_pipeline.ps1                        # both exist at repo root
powershell -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('run_pipeline.ps1', [ref]$null, [ref]$null)"
```

**PIPELINE-04 / SC#5 linkage:** Automated: wrapper tests GREEN + file existence. Manual: 대표님 double-click confirm → captured in VERIFICATION.md by Plan 11-06.
</verification>

<success_criteria>
- [ ] `run_pipeline.cmd` at studio repo root with `-ExecutionPolicy Bypass` + `%~dp0` path resolution + `pause`
- [ ] `run_pipeline.ps1` at studio repo root with $PSScriptRoot, chcp 65001, .env regex parse, session-id via Get-Date, `py -3.11` invocation, try/catch/finally Read-Host, Korean Write-Host with 대표님 appellation
- [ ] `.ps1` passes PowerShell syntax parse check
- [ ] No STRUCTURE.md change needed (studio has no STRUCTURE.md — harness whitelist doesn't constrain studio, per RESEARCH §STRUCTURE Whitelist Verification)
- [ ] 22 Phase 11 cumulative tests GREEN
- [ ] 244/244 phase04 preserved
- [ ] Existing scripts/schedule/windows_tasks.ps1 UNTOUCHED (scheduler path unchanged)
</success_criteria>

<output>
After completion, create `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-04-SUMMARY.md` with:
- Files created (run_pipeline.cmd 3 lines, run_pipeline.ps1 ~70 lines)
- Test count cumulative: 272 → 274
- Manual verification hint for SC#5 recorded for Plan 11-06 consumption
</output>
