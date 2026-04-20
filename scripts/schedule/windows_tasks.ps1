<#
.SYNOPSIS
  Register 3 Windows Scheduled Tasks for shorts_studio Phase 10 sustained operations.

.DESCRIPTION
  대표님 로컬 Windows PC 에 영상 파이프라인 + 업로드 + 실패 알림 3개 스케줄 task 를 등록.
  idempotent — 재실행 시 기존 task 를 먼저 Unregister 한 후 다시 Register-ScheduledTask.

  Task 목록:
    - ShortsStudio_Pipeline     : Daily 20:30 KST → shorts_pipeline.py 실행 (GATE guard 자체)
    - ShortsStudio_Upload       : Daily 20:45 KST → smoke_test --production (파이프라인 완료 15분 후)
    - ShortsStudio_NotifyFailure: On-demand → notify_failure.py (다른 task 가 실패 시 호출)

.NOTES
  Phase 10 Plan 04. 최초 실행은 반드시 "관리자 권한 PowerShell" 에서 1회 수행 필요.
  재등록은 -Force 로 덮어쓰기 안전.

  [중요 — 페이스 설계 (CLAUDE.md 도메인 절대 규칙 #8, AF-1 / AF-11)]
  Daily trigger 는 "wake-up + gate check" 역할일 뿐, 실제 페이스 gating 은
  scripts/publisher/publish_lock.py (MIN_ELAPSED_HOURS=48, MAX_JITTER_MIN=720) +
  scripts/publisher/kst_window.py (평일 20-23 / 주말 12-15 KST) 가 수행합니다.
  publish_lock.assert_can_publish() 가 48시간 미경과 시 PublishLockViolation 으로
  업로드를 거부 → 주 3~4편 + jitter 자동 enforce. 일일 트리거가 외부에서 봇 패턴처럼
  보여도 실 발행은 주 3~4편으로 제한되므로 Inauthentic Content (AF-11) 리스크 없습니다.

.EXAMPLE
  PS> powershell -NoProfile -ExecutionPolicy Bypass -File scripts/schedule/windows_tasks.ps1
  (관리자 권한 필수) 3개 task 등록.

.EXAMPLE
  PS> powershell -NoProfile -ExecutionPolicy Bypass -File scripts/schedule/windows_tasks.ps1 -Unregister
  3개 task 를 모두 제거. Plan 08 ROLLBACK.md 시나리오 참조.

.PARAMETER ScriptRoot
  shorts_studio 저장소 루트. 기본값 C:\Users\PC\Desktop\naberal_group\studios\shorts.

.PARAMETER Unregister
  스위치. 지정 시 등록 대신 3개 task 모두 제거.
#>
[CmdletBinding()]
param(
    [string]$ScriptRoot = "C:\Users\PC\Desktop\naberal_group\studios\shorts",
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"

function Register-ShortsTask {
    param(
        [Parameter(Mandatory)][string]$TaskName,
        [Parameter(Mandatory)][string]$PythonArgs,
        [Parameter(Mandatory)][ScriptBlock]$TriggerBuilder
    )
    Write-Host "[register] $TaskName"

    # idempotent — 이미 존재하면 먼저 제거 (Pitfall 4 — 재등록 충돌 회피)
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "  (removed existing)"
    } catch {
        # not found — fresh registration, 무시하고 진행
    }

    $argText = "-NoProfile -ExecutionPolicy Bypass -Command `"cd '{0}'; python {1}`"" -f $ScriptRoot, $PythonArgs
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument $argText

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

    Write-Host "  [ok] $TaskName registered (RunLevel Highest)"
}

function Unregister-AllShortsTasks {
    foreach ($tn in @("ShortsStudio_Pipeline", "ShortsStudio_Upload", "ShortsStudio_NotifyFailure")) {
        try {
            Unregister-ScheduledTask -TaskName $tn -Confirm:$false -ErrorAction Stop
            Write-Host "[unregister] $tn"
        } catch {
            Write-Host "[unregister] $tn (not present — skip)"
        }
    }
}

if ($Unregister) {
    Unregister-AllShortsTasks
    Write-Host "[done] All shorts tasks unregistered. See .planning/phases/10-sustained-operations/ROLLBACK.md (Plan 8) for post-rollback checklist."
    exit 0
}

# ---------------------------------------------------------------------------
# 1. Pipeline — daily 20:30 KST
# ---------------------------------------------------------------------------
# NOTE: Daily trigger 이지만 publish_lock.assert_can_publish() (48h+jitter,
# MIN_ELAPSED_HOURS=48, MAX_JITTER_MIN=720) + kst_window.assert_in_window()
# (평일 20-23 / 주말 12-15 KST) 가 파이프라인 내부에서 게이트 역할.
# 48시간 미경과 시 PublishLockViolation 으로 업로드 단계에서 거부됨 →
# AF-1 / AF-11 "주 3~4편" 페이스 자동 enforce.
Register-ShortsTask `
    -TaskName "ShortsStudio_Pipeline" `
    -PythonArgs "-m scripts.orchestrator.shorts_pipeline" `
    -TriggerBuilder { New-ScheduledTaskTrigger -Daily -At "20:30" }

# ---------------------------------------------------------------------------
# 2. Upload — daily 20:45 KST (pipeline 완료 후 15분 여유)
# ---------------------------------------------------------------------------
# NOTE: 일일 실행으로 보이지만 publish_lock.assert_can_publish() 가 48시간 미경과 시
# PublishLockViolation 으로 거부하여 실제 업로드는 주 3~4편 페이스 + jitter 로
# 자동 제한됨. Daily trigger 는 "wake-up + gate check" 역할.
# 대표님 AF-1 / AF-11 Inauthentic Content 리스크 없음 (페이스 enforcement 는
# publish_lock + kst_window 에 위임).
Register-ShortsTask `
    -TaskName "ShortsStudio_Upload" `
    -PythonArgs "-m scripts.publisher.smoke_test --production" `
    -TriggerBuilder { New-ScheduledTaskTrigger -Daily -At "20:45" }

# ---------------------------------------------------------------------------
# 3. NotifyFailure — on-demand trigger (다른 task 의 failure action 에서 Start-ScheduledTask 로 호출)
# ---------------------------------------------------------------------------
# 10년 후 dummy 트리거로 등록 (never-fire) — 실제 실행은 Start-ScheduledTask 를
# 다른 Scheduled Task 의 failure action 에서 호출. 로컬 PowerShell 스크립트가
# notify_failure.py 를 env (TASK_NAME / ERROR_MSG) 와 함께 실행.
Register-ShortsTask `
    -TaskName "ShortsStudio_NotifyFailure" `
    -PythonArgs "-m scripts.schedule.notify_failure --task-name `$env:TASK_NAME --error-msg `$env:ERROR_MSG" `
    -TriggerBuilder { New-ScheduledTaskTrigger -Once -At (Get-Date).AddYears(10) }

Write-Host ""
Write-Host "[done] 3 tasks registered successfully."
Write-Host "       Verify with: schtasks /Query /TN ShortsStudio_Pipeline"
Write-Host "       Rollback with: powershell -File scripts/schedule/windows_tasks.ps1 -Unregister"
Write-Host "       대표님, 관리자 권한 PowerShell 에서 1회 실행하셨는지 확인 부탁드립니다."
