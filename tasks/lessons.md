# Project Hub - Lessons Learned

## Boot Sequence
- start-background.pyw uses CREATE_NO_WINDOW flag for all subprocesses
- All service starts are idempotent (safe to run multiple times)
- Service order matters: Ollama must be up before OpenClaw (uses Ollama for inference)

## Git Sync
- sync-all.ps1 runs with -WindowStyle Hidden via scheduled task
- Script does fetch+pull per repo, skips dirty repos, handles diverged branches
- Daily trigger with no repeat interval (runs once at scheduled time)
