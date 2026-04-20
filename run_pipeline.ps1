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

  세션 ID 이중 생성: .ps1 가 Get-Date 로 명시적 banner 를 출력하고 Python 에
  --session-id 로 전달. Plan 11-03 argparse 도 auto-default 를 가지므로 .ps1
  를 거치지 않는 scheduler 직접 호출 경로에서도 timestamp 가 자동 생성됨.
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
            # Strip matched surrounding quotes (single or double)
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
        Write-Host ""
        Write-Host "[done] 파이프라인 성공 (대표님)" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[fail] 파이프라인 실패 rc=$rc (대표님 — 위 로그 확인)" -ForegroundColor Red
        throw "pipeline returned $rc"
    }
}
catch {
    Write-Host ""
    Write-Host "[error] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[error] 스택: $($_.ScriptStackTrace)" -ForegroundColor DarkRed
}
finally {
    Write-Host ""
    Read-Host "완료. 엔터로 창 닫기 (대표님)"
}
