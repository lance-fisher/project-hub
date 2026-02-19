# Git Sync System

Automatic bidirectional sync between D:\ProjectsHome repos and GitHub.

## How It Works

A PowerShell script (`scripts/sync-all.ps1`) runs every 5 minutes via Windows Task Scheduler. It iterates all repos listed in `_ops/sync-config.json` and:

1. **Fetches** from `origin` for every enabled repo
2. **Pulls** (fast-forward only) if the repo is clean and behind remote
3. **Skips** repos with uncommitted changes (logs a warning, still fetches)
4. **Pushes** only if `auto_push` is enabled in config (default: off)
5. **Logs** all actions to `_logs/sync.log`

## Quick Reference

| Action | Command |
|--------|---------|
| Manual sync (verbose) | `sync-now.bat` on Desktop, or `scripts/sync-now.bat` |
| Check sync log | `type project-hub\_logs\sync.log` |
| Disable auto-sync | `schtasks /Change /TN ProjectsHome-GitSync /Disable` |
| Re-enable auto-sync | `schtasks /Change /TN ProjectsHome-GitSync /Enable` |
| Remove auto-sync | `schtasks /Delete /TN ProjectsHome-GitSync /F` |
| Run sync with push | `scripts/sync-all.bat --push` |
| Dry run | `powershell -File scripts/sync-all.ps1 -DryRun -Verbose` |

## Phone-to-PC Flow

1. You commit and push from your phone (via Claude iOS or git client)
2. Within 5 minutes, the sync script fetches and fast-forward pulls the changes
3. Your local copy is updated without any action needed

## PC-to-GitHub Flow

1. You commit locally on PC
2. Run `sync-now.bat --push` or manually `git push`
3. Or enable `auto_push: true` in sync-config.json for automatic pushing

## Configuration

Edit `_ops/sync-config.json`:

- `sync_interval_minutes`: Change the scheduled task interval (you also need to re-register the task)
- `pull_strategy`: `"ff-only"` (safe) or `"merge"` (riskier, not recommended)
- `auto_push`: `false` (manual push) or `true` (auto-push clean repos)
- `repos[].enabled`: Set to `false` to skip a repo during sync

## Adding a New Repo

1. Add an entry to `_ops/sync-config.json`:
   ```json
   { "name": "my-project", "path": "D:/ProjectsHome/my-project", "enabled": true }
   ```
2. The next sync cycle will pick it up automatically

## Handling Conflicts

If a repo shows "diverged" in the sync log:

1. Navigate to the repo: `cd D:\ProjectsHome\<repo>`
2. Check the situation: `git log --oneline --graph --all -20`
3. Decide: merge or rebase
   - Merge: `git merge origin/main`
   - Rebase: `git rebase origin/main`
4. Resolve conflicts, commit, and push

## Troubleshooting

**Sync not running?**
```
schtasks /Query /TN ProjectsHome-GitSync
```

**Too many dirty warnings?**
Commit your work. The sync script intentionally won't pull over uncommitted changes.

**Want to force-update a specific repo?**
```
cd D:\ProjectsHome\<repo>
git stash
git pull --ff-only
git stash pop
```
