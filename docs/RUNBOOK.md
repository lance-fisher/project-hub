# ProjectHub Runbook

**Last updated**: 2026-02-18
**Author**: Claude Opus 4.6 (Project Consolidation Engineer)

---

## Daily Workflow

### Morning (automatic)
1. Sync task runs on login, pulling any phone changes
2. Check the sync log if needed: `type D:\ProjectsHome\project-hub\_logs\sync.log | tail -30`

### Working on a Project
1. Open the project folder in your editor
2. Work normally. Commit when ready.
3. Push manually: `git push` (or use `sync-now.bat --push`)

### Before Closing the PC
1. Commit any work in progress
2. Push to GitHub: `git push` from each active project
3. Or run: `D:\Lance\Desktop\Bots & Projects\Sync Now.bat` with `--push`

---

## How Phone Changes Appear Locally

1. You work on your phone via Claude iOS or a git client
2. Changes are pushed to GitHub (to the `exo` repo or a project's own repo)
3. Every 5 minutes, `sync-all.ps1` runs via Windows Scheduled Task
4. It fetches all remotes and fast-forward pulls clean repos
5. Your local copy is updated automatically

**If the repo is dirty** (has uncommitted local changes):
- The pull is skipped
- A warning is logged
- You must commit or stash your local changes first, then the next sync cycle will pull

---

## Adding a New Project

### 1. Create the project folder
```
mkdir D:\ProjectsHome\my-new-project
cd D:\ProjectsHome\my-new-project
git init -b main
```

### 2. Create essential files
- `.gitignore` (use `project-hub/_templates/` or write one)
- `README.md` with what it is, how to run, status
- `CLAUDE.md` if you want Claude Code to have project context

### 3. Create GitHub repo
```
gh repo create lance-fisher/my-new-project --private --description "My new project"
git remote add origin https://github.com/lance-fisher/my-new-project.git
git add -A && git commit -m "Initial commit"
git push -u origin main
```

### 4. Register in sync config
Edit `D:\ProjectsHome\project-hub\_ops\sync-config.json`, add:
```json
{ "name": "my-new-project", "path": "D:/ProjectsHome/my-new-project", "enabled": true }
```

### 5. Register in ProjectHub manifest
Edit `D:\ProjectsHome\project-hub\projects\manifest.json`, add an entry.

### 6. Register in PROJECTS.json
Edit `D:\ProjectsHome\PROJECTS.json`, add a project entry.

---

## Handling Conflicts

### Diverged Repo (local and remote both have new commits)

The sync log will say: `DIVERGED from origin/main (manual resolution needed)`

**Resolution:**
```bash
cd D:\ProjectsHome\<repo>
git log --oneline --graph --all -20   # See the situation
git merge origin/main                  # Merge (safe default)
# Resolve any conflicts, then:
git add . && git commit -m "Merge remote changes"
git push
```

### Dirty Repo Blocking Sync

The sync log will say: `Has uncommitted changes, skipping pull`

**Resolution:**
```bash
cd D:\ProjectsHome\<repo>
git stash                              # Stash your work
# Wait for next sync cycle, or run sync manually
git stash pop                          # Restore your work
```

### Failed Fast-Forward

This means the histories diverged. You need to merge manually (see "Diverged Repo" above).

---

## Recovering From a Bad Sync

### Scenario: Sync pulled something that broke your project
```bash
cd D:\ProjectsHome\<repo>
git log --oneline -10                  # Find the last good commit
git revert HEAD                        # Revert the bad commit
# Or reset to a specific commit (careful):
# git reset --hard <commit-hash>       # Destructive! Only if you're sure
```

### Scenario: Accidentally committed sensitive data
```bash
cd D:\ProjectsHome\<repo>
# Don't push! If already pushed, contact GitHub support for force removal
git reset HEAD~1                       # Undo the commit (keeps files)
# Fix the .gitignore, remove the file from tracking
git rm --cached <sensitive-file>
git commit -m "Remove sensitive file from tracking"
```

---

## Disabling or Changing Automation

### Disable auto-sync entirely
```
schtasks /Change /TN ProjectsHome-GitSync /Disable
```

### Re-enable auto-sync
```
schtasks /Change /TN ProjectsHome-GitSync /Enable
```

### Remove the scheduled task
```
schtasks /Delete /TN ProjectsHome-GitSync /F
```

### Change sync interval
1. Remove the existing task: `schtasks /Delete /TN ProjectsHome-GitSync /F`
2. Re-create with new interval: `schtasks /Create /SC MINUTE /MO 2 /TN "ProjectsHome-GitSync" /TR "D:\ProjectsHome\project-hub\scripts\sync-all.bat" /F`

### Disable sync for a specific repo
Edit `_ops/sync-config.json`, set `"enabled": false` for that repo.

### Enable auto-push
Edit `_ops/sync-config.json`, set `"auto_push": true`. This will push clean repos after pulling.

---

## File Locations

| What | Where |
|------|-------|
| Sync script | `project-hub/scripts/sync-all.ps1` |
| Sync batch wrapper | `project-hub/scripts/sync-all.bat` |
| Manual sync | `project-hub/scripts/sync-now.bat` (also on Desktop) |
| Sync config | `project-hub/_ops/sync-config.json` |
| Sync log | `project-hub/_logs/sync.log` |
| Project manifest | `project-hub/projects/manifest.json` |
| Project registry | `PROJECTS.json` (root) |
| Inventory report | `project-hub/_ops/inventory.md` |
| Cleanup report | `project-hub/_ops/cleanup-report.md` |
| Archive | `_archive/YYYY-MM-DD/` |
| Scheduled task setup | `project-hub/scripts/setup-sync-task.ps1` |
| Sync system docs | `project-hub/docs/SYNC_SYSTEM.md` |
| This runbook | `project-hub/docs/RUNBOOK.md` |

---

## Common Commands

```bash
# Run manual sync with verbose output
D:\ProjectsHome\project-hub\scripts\sync-now.bat

# Check sync task status
schtasks /Query /TN ProjectsHome-GitSync

# View recent sync log
type D:\ProjectsHome\project-hub\_logs\sync.log

# List all repos and their remotes
for /d %d in (D:\ProjectsHome\*) do @git -C %d remote get-url origin 2>nul && echo %d

# Quick status of all repos
for /d %d in (D:\ProjectsHome\*) do @echo. & echo === %~nxd === & git -C %d status --short 2>nul
```
