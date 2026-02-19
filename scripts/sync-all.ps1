# sync-all.ps1 - Git Sync Script for ProjectsHome
# Pulls changes from GitHub for all tracked repos
# Designed to run on a schedule (every 5 minutes) and on login
#
# Usage:
#   .\sync-all.ps1              # Normal sync
#   .\sync-all.ps1 -Verbose     # Verbose output
#   .\sync-all.ps1 -DryRun      # Show what would happen without doing it
#   .\sync-all.ps1 -Push        # Also push after pulling (override config)

param(
    [switch]$Verbose,
    [switch]$DryRun,
    [switch]$Push
)

$ErrorActionPreference = 'Continue'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path $scriptDir -Parent) '_ops\sync-config.json'

# Load config
if (-not (Test-Path $configPath)) {
    Write-Error "Config not found: $configPath"
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$logFile = $config.log_file
$pullStrategy = $config.pull_strategy
$autoStash = $config.auto_stash
$autoPush = if ($Push) { $true } else { $config.auto_push }

# Ensure log directory exists
$logDir = Split-Path $logFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
    if ($Verbose -or $Level -eq "ERROR" -or $Level -eq "WARN") {
        Write-Host $entry
    }
}

function Sync-Repo {
    param([PSObject]$Repo)

    $name = $Repo.name
    $path = $Repo.path

    if (-not $Repo.enabled) {
        Write-Log "$name - SKIPPED (disabled)" "DEBUG"
        return @{ Name=$name; Status="skipped"; Reason="disabled" }
    }

    if (-not (Test-Path $path)) {
        Write-Log "$name - SKIPPED (path not found: $path)" "WARN"
        return @{ Name=$name; Status="error"; Reason="path not found" }
    }

    if (-not (Test-Path (Join-Path $path '.git'))) {
        Write-Log "$name - SKIPPED (not a git repo)" "WARN"
        return @{ Name=$name; Status="error"; Reason="not a git repo" }
    }

    # Check for remote
    $remote = git -C $path remote get-url origin 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "$name - SKIPPED (no remote configured)" "WARN"
        return @{ Name=$name; Status="skipped"; Reason="no remote" }
    }

    # Check for uncommitted changes
    $status = git -C $path status --porcelain 2>&1
    $isDirty = [bool]$status

    if ($isDirty) {
        Write-Log "$name - Has uncommitted changes, skipping pull" "WARN"
        if ($DryRun) {
            return @{ Name=$name; Status="dirty"; Reason="uncommitted changes" }
        }
        # Still fetch so we know about remote changes
        git -C $path fetch origin 2>&1 | Out-Null
        return @{ Name=$name; Status="dirty"; Reason="uncommitted changes (fetched only)" }
    }

    # Get current branch
    $branch = git -C $path branch --show-current 2>&1
    if (-not $branch) {
        Write-Log "$name - SKIPPED (detached HEAD)" "WARN"
        return @{ Name=$name; Status="skipped"; Reason="detached HEAD" }
    }

    # Fetch
    if ($DryRun) {
        Write-Log "$name - DRY RUN: would fetch and pull $branch" "INFO"
        return @{ Name=$name; Status="dry-run"; Reason="would sync" }
    }

    $fetchResult = git -C $path fetch origin 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "$name - Fetch failed: $fetchResult" "ERROR"
        return @{ Name=$name; Status="error"; Reason="fetch failed" }
    }

    # Check if remote branch exists
    $remoteRef = git -C $path rev-parse "origin/$branch" 2>&1
    if ($LASTEXITCODE -ne 0) {
        # Remote branch doesn't exist yet - push if auto_push
        if ($autoPush) {
            $pushResult = git -C $path push -u origin $branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "$name - Pushed new branch $branch to origin" "INFO"
                return @{ Name=$name; Status="pushed"; Reason="new branch pushed" }
            } else {
                Write-Log "$name - Push failed: $pushResult" "ERROR"
                return @{ Name=$name; Status="error"; Reason="push failed" }
            }
        }
        Write-Log "$name - Remote branch origin/$branch not found, skipping" "WARN"
        return @{ Name=$name; Status="skipped"; Reason="no remote branch" }
    }

    # Check ahead/behind
    $localRef = git -C $path rev-parse $branch 2>&1
    if ($localRef -eq $remoteRef) {
        Write-Log "$name - Up to date" "DEBUG"
        return @{ Name=$name; Status="up-to-date"; Reason="" }
    }

    # Check if we can fast-forward
    $mergeBase = git -C $path merge-base $branch "origin/$branch" 2>&1
    $behind = ($mergeBase -eq $localRef)
    $ahead = ($mergeBase -eq $remoteRef)

    if ($behind) {
        # We're behind - pull (fast-forward)
        $pullResult = git -C $path pull --ff-only origin $branch 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "$name - Pulled (ff-only) from origin/$branch" "INFO"
            return @{ Name=$name; Status="pulled"; Reason="fast-forward" }
        } else {
            Write-Log "$name - Pull ff-only failed: $pullResult" "ERROR"
            return @{ Name=$name; Status="error"; Reason="ff-only failed" }
        }
    } elseif ($ahead) {
        # We're ahead - push if auto_push
        if ($autoPush) {
            $pushResult = git -C $path push origin $branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "$name - Pushed to origin/$branch" "INFO"
                return @{ Name=$name; Status="pushed"; Reason="ahead of remote" }
            } else {
                Write-Log "$name - Push failed: $pushResult" "ERROR"
                return @{ Name=$name; Status="error"; Reason="push failed" }
            }
        }
        Write-Log "$name - Ahead of remote (auto_push=false, skipping)" "INFO"
        return @{ Name=$name; Status="ahead"; Reason="auto_push disabled" }
    } else {
        # Diverged
        Write-Log "$name - DIVERGED from origin/$branch (manual resolution needed)" "WARN"
        return @{ Name=$name; Status="diverged"; Reason="needs manual merge" }
    }
}

# Main execution
Write-Log "===== Sync started =====" "INFO"

$results = @()
foreach ($repo in $config.repos) {
    $result = Sync-Repo -Repo $repo
    $results += $result
}

# Summary
$pulled = ($results | Where-Object { $_.Status -eq 'pulled' }).Count
$pushed = ($results | Where-Object { $_.Status -eq 'pushed' }).Count
$upToDate = ($results | Where-Object { $_.Status -eq 'up-to-date' }).Count
$dirty = ($results | Where-Object { $_.Status -eq 'dirty' }).Count
$errors = ($results | Where-Object { $_.Status -eq 'error' }).Count
$diverged = ($results | Where-Object { $_.Status -eq 'diverged' }).Count
$skipped = ($results | Where-Object { $_.Status -eq 'skipped' }).Count
$total = $results.Count

$summary = "Sync complete: $total repos | $pulled pulled | $pushed pushed | $upToDate current | $dirty dirty | $errors errors | $diverged diverged | $skipped skipped"
Write-Log $summary "INFO"
Write-Log "===== Sync finished =====" "INFO"

if ($Verbose -or $errors -gt 0 -or $diverged -gt 0) {
    Write-Host ""
    Write-Host $summary
    if ($errors -gt 0) {
        Write-Host "  Errors:" -ForegroundColor Red
        $results | Where-Object { $_.Status -eq 'error' } | ForEach-Object { Write-Host "    - $($_.Name): $($_.Reason)" -ForegroundColor Red }
    }
    if ($diverged -gt 0) {
        Write-Host "  Diverged:" -ForegroundColor Yellow
        $results | Where-Object { $_.Status -eq 'diverged' } | ForEach-Object { Write-Host "    - $($_.Name): $($_.Reason)" -ForegroundColor Yellow }
    }
    if ($dirty -gt 0) {
        Write-Host "  Dirty (skipped pull):" -ForegroundColor Yellow
        $results | Where-Object { $_.Status -eq 'dirty' } | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Yellow }
    }
}
