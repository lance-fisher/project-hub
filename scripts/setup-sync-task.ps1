# setup-sync-task.ps1 - Creates a Windows Scheduled Task for repo sync
# Must be run as Administrator (or with appropriate privileges)
#
# Creates two triggers:
# 1. Every 5 minutes (repeating)
# 2. On user logon

$taskName = "ProjectsHome-GitSync"
$scriptPath = Join-Path $PSScriptRoot "sync-all.ps1"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing old task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Define action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Define triggers
$triggerRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 365)

$triggerLogon = New-ScheduledTaskTrigger -AtLogOn

# Define settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

# Register
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggerRepeat, $triggerLogon `
    -Settings $settings `
    -Description "Syncs all ProjectsHome git repos with GitHub every 5 minutes" `
    -RunLevel Limited

Write-Host ""
Write-Host "Scheduled task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "  Script: $scriptPath"
Write-Host "  Interval: Every 5 minutes"
Write-Host "  Also runs: On logon"
Write-Host ""
Write-Host "To check status:  Get-ScheduledTask -TaskName '$taskName'"
Write-Host "To run now:       Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To disable:       Disable-ScheduledTask -TaskName '$taskName'"
Write-Host "To remove:        Unregister-ScheduledTask -TaskName '$taskName'"
