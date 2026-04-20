"""PIPELINE-04 wrapper tests — file existence + .ps1 parse dry-run.

Phase 11 Plan 04. D-09/D-10/D-11/D-12 (run_pipeline.cmd bootstrap + run_pipeline.ps1
engine) contract guard. These tests verify wrapper files are placed at studio repo
root with the exact markers the 대표님 double-click UX depends on.

Test 1 — file existence + grep contract (exact strings from D-10/D-11)
Test 2 — PowerShell Parser.ParseFile() dry-run (syntax validity, skips when pwsh
         not available on the machine)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def test_wrapper_files_exist_at_repo_root(repo_root: Path):
    """Both wrapper files exist at studio repo root with expected markers."""
    cmd_path = repo_root / "run_pipeline.cmd"
    ps1_path = repo_root / "run_pipeline.ps1"

    assert cmd_path.exists(), (
        f"{cmd_path} must exist at repo root (PIPELINE-04 D-09 .cmd bootstrap)"
    )
    assert ps1_path.exists(), (
        f"{ps1_path} must exist at repo root (PIPELINE-04 D-09 .ps1 engine)"
    )

    cmd_text = cmd_path.read_text(encoding="utf-8", errors="replace")
    assert "ExecutionPolicy Bypass" in cmd_text, (
        ".cmd must use `-ExecutionPolicy Bypass` (D-10 admin-free per-invocation override)"
    )
    assert "run_pipeline.ps1" in cmd_text, (
        ".cmd must reference run_pipeline.ps1 as the engine file"
    )
    assert "%~dp0" in cmd_text, (
        "`.cmd` must resolve its own directory via %~dp0 (Windows cmd builtin)"
    )

    ps1_text = ps1_path.read_text(encoding="utf-8", errors="replace")
    assert "$PSScriptRoot" in ps1_text, (
        ".ps1 must use $PSScriptRoot (PS 3.0+ canonical path resolution)"
    )
    assert "Get-Date" in ps1_text, (
        ".ps1 must auto-generate session-id via Get-Date (D-11 human-readable banner)"
    )
    assert "py -3.11" in ps1_text, (
        ".ps1 must invoke `py -3.11` launcher (Windows Python launcher)"
    )
    assert "scripts.orchestrator.shorts_pipeline" in ps1_text, (
        ".ps1 must launch the orchestrator entry module"
    )
    assert "Read-Host" in ps1_text, (
        ".ps1 must pause-on-exit via Read-Host (D-11 window-stays-open contract)"
    )
    assert "chcp 65001" in ps1_text, (
        ".ps1 must enable UTF-8 console via chcp 65001 (한국어 Write-Host)"
    )
    assert "대표님" in ps1_text, (
        ".ps1 must address 대표님 (나베랄 감마 identity — CLAUDE.md Korean-first)"
    )


def test_ps1_syntax_parses_via_pwsh(repo_root: Path):
    """PowerShell Parser.ParseFile dry-run — validates .ps1 syntax without execution.

    Skips gracefully when neither powershell.exe nor pwsh is available on PATH
    (CI Linux containers, macOS without PS Core, etc.).
    """
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("powershell / pwsh not available on this machine")

    ps1_path = repo_root / "run_pipeline.ps1"
    if not ps1_path.exists():
        pytest.fail("run_pipeline.ps1 must exist before parse test (Task 1 precondition)")

    # Ask PowerShell to parse the file without executing it.
    parse_cmd = (
        "$errors = $null; $tokens = $null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{ps1_path}', "
        "[ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 } "
        "else { exit 0 }"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", parse_cmd],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"PowerShell parse errors in run_pipeline.ps1:\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
