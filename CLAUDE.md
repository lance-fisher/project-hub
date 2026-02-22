# Project Hub

Unified project dashboard for the entire ProjectsHome workspace. Single-file Python HTTP server at http://localhost:8090.

## Stack
- **Language**: Python 3 (stdlib only, zero dependencies)
- **Server**: `http.server.HTTPServer` + `SimpleHTTPRequestHandler`
- **Frontend**: Inline HTML/CSS/JS served from `serve_dashboard()` (no separate files)
- **Data**: `D:\ProjectsHome\PROJECTS.json` (project registry), `.claude-data/history.jsonl` (session history)

## How to Run
```
python server.py           # starts on :8090, opens browser
python server.py 9000      # custom port
python server.py --silent  # no browser auto-open
```

## Architecture
Single file `server.py` (~1800 lines). The dashboard HTML is generated inline by `get_dashboard_html()`. No build step.

### Key Classes / Functions
- `DashboardHandler` — HTTP request handler (GET + POST routes)
- `load_projects()` / `save_projects()` — PROJECTS.json CRUD
- `scan_directory()` — auto-detect new projects in ProjectsHome
- `get_systems_overview()` — live health check of 9+ integrated systems (port probes)
- `get_active_sessions()` — recent Claude Code sessions

### API Endpoints (GET)
- `/api/projects` — all registered projects
- `/api/sessions` — Claude Code session history
- `/api/stats` — project count, active count, session stats
- `/api/scan` — detect unregistered project directories
- `/api/disk` — disk usage info
- `/api/systems` — live system health (port checks for bots, servers, etc.)
- `/api/active-sessions` — recent Claude sessions with project labels
- `/api/openclaw/*` — OpenClaw health, activity, sessions
- `/api/bot/*` — Moltbot proxy (health, tasks, capabilities)
- `/api/auton/*` — Auton proxy (health, status, tasks, journal)

### API Endpoints (POST)
- `/api/projects/add` — register a new project
- `/api/projects/update` — update project metadata
- `/api/projects/delete` — remove a project
- `/api/projects/import-scan` — bulk-import scanned projects
- `/api/open-terminal` — open Windows Terminal at a project path
- `/api/open-explorer` — open Explorer at a project path
- `/api/launch-claude` — launch Claude Code session for a project
- `/api/bot/dispatch` — send task to Moltbot
- `/api/auton/kill` / `/api/auton/resume` — Auton kill switch

## Integrated Systems
Proxies requests to: Moltbot Hub (:8002), Auton (:8095), OpenClaw (:18800).
