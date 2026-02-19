#!/usr/bin/env python3
"""
ProjectsHome Hub — Unified project dashboard for Claude Code projects.
Launch: python server.py [port]
Opens: http://localhost:8090
"""

import json
import os
import sys
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse
import urllib.request
import urllib.error

# --- Configuration ---
MOLTBOT_URL = "http://127.0.0.1:8002"
OPENCLAW_WS_PORT = 18800
OPENCLAW_TOKEN = os.environ.get("OPENCLAW_TOKEN", "")
OPENCLAW_CONFIG = Path(r"C:\Users\lance\.openclaw\openclaw.json")
OPENCLAW_SESSIONS = Path(r"C:\Users\lance\.openclaw\agents\main\sessions")
OPENCLAW_WORKSPACE = Path(r"C:\Users\lance\.openclaw\workspace")
PROJECTS_ROOT = Path(r"D:\ProjectsHome")
PROJECTS_JSON = PROJECTS_ROOT / "PROJECTS.json"
CLAUDE_DATA = PROJECTS_ROOT / ".claude-data"
HISTORY_FILE = CLAUDE_DATA / "history.jsonl"
DEFAULT_PORT = 8090


def load_projects():
    if PROJECTS_JSON.exists():
        with open(PROJECTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"projects": [], "metadata": {}}


def save_projects(data):
    with open(PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def scan_directory():
    data = load_projects()
    known_paths = {(p.get("path") or "").lower() for p in data.get("projects", [])}
    new_projects = []
    for entry in PROJECTS_ROOT.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name == "project-hub":
            continue
        entry_str = str(entry)
        if entry_str.lower() not in known_paths:
            tech = detect_tech(entry)
            new_projects.append({
                "name": entry.name.replace("-", " ").replace("_", " ").title(),
                "path": entry_str,
                "tech": tech,
                "status": "unknown",
                "source": "auto-detected",
                "description": f"Auto-detected project in {entry.name}/",
                "last_active": datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat(),
                "pinned": False,
                "tags": [],
            })
    return new_projects


def detect_tech(path: Path):
    markers = {
        "package.json": "Node.js", "tsconfig.json": "TypeScript",
        "pyproject.toml": "Python", "requirements.txt": "Python",
        "Cargo.toml": "Rust", "go.mod": "Go", "setup.py": "Python",
    }
    techs = []
    for marker, tech in markers.items():
        if (path / marker).exists() and tech not in techs:
            techs.append(tech)
    return ", ".join(techs) if techs else "Unknown"


def load_session_history():
    sessions = []
    if not HISTORY_FILE.exists():
        return sessions
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", 0)
                    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                    sessions.append({
                        "sessionId": entry.get("sessionId", "unknown"),
                        "project": entry.get("project", "unknown"),
                        "display": entry.get("display", "")[:200],
                        "timestamp": dt.isoformat(),
                        "date": dt.strftime("%Y-%m-%d %H:%M"),
                    })
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception as e:
        print(f"Warning: Could not read history: {e}")
    return sessions


def get_session_summary():
    raw = load_session_history()
    grouped = {}
    for entry in raw:
        sid = entry["sessionId"]
        if sid not in grouped:
            grouped[sid] = {
                "sessionId": sid, "project": entry["project"],
                "firstMessage": entry["display"], "messageCount": 0,
                "firstTimestamp": entry["timestamp"], "lastTimestamp": entry["timestamp"],
                "firstDate": entry["date"], "lastDate": entry["date"],
            }
        grouped[sid]["messageCount"] += 1
        grouped[sid]["lastTimestamp"] = entry["timestamp"]
        grouped[sid]["lastDate"] = entry["date"]
    return sorted(grouped.values(), key=lambda x: x["lastTimestamp"], reverse=True)


def get_project_stats(projects_data):
    projects = projects_data.get("projects", [])
    sessions = get_session_summary()
    return {
        "totalProjects": len(projects),
        "activeProjects": sum(1 for p in projects if p.get("status") in ("active", "in_progress")),
        "pinnedProjects": sum(1 for p in projects if p.get("pinned")),
        "totalSessions": len(sessions),
        "totalMessages": sum(s["messageCount"] for s in sessions),
    }


def get_disk_info():
    try:
        import shutil
        usage = shutil.disk_usage(str(PROJECTS_ROOT))
        return {"total_gb": round(usage.total / (1024**3), 1), "used_gb": round(usage.used / (1024**3), 1), "free_gb": round(usage.free / (1024**3), 1), "percent_used": round(usage.used / usage.total * 100, 1)}
    except Exception:
        return None


def openclaw_health():
    """Check OpenClaw gateway health by probing the WS port and reading config."""
    import socket
    result = {
        "status": "offline",
        "port": OPENCLAW_WS_PORT,
        "version": None,
        "model": None,
        "plugins": [],
        "telegram": None,
        "uptime": None,
        "workspace": str(OPENCLAW_WORKSPACE),
    }

    # Check if port is open
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(2)
        sock.connect(("127.0.0.1", OPENCLAW_WS_PORT))
        sock.close()
        result["status"] = "online"
    except (ConnectionRefusedError, OSError):
        return result

    # Read version from config
    if OPENCLAW_CONFIG.exists():
        try:
            with open(OPENCLAW_CONFIG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            result["version"] = cfg.get("meta", {}).get("lastTouchedVersion")
            # Get primary model
            defaults = cfg.get("agents", {}).get("defaults", {})
            result["model"] = defaults.get("model", {}).get("primary", "unknown")
            # Get enabled plugins
            plugins = cfg.get("plugins", {}).get("entries", {})
            result["plugins"] = [k for k, v in plugins.items() if v.get("enabled")]
            # Telegram status
            tg = cfg.get("channels", {}).get("telegram", {})
            result["telegram"] = "enabled" if tg.get("enabled") else "disabled"
        except Exception:
            pass

    return result


def openclaw_activity():
    """Read recent OpenClaw activity from session logs and daily notes."""
    activity = {"sessions": [], "daily_notes": [], "overnight_tasks": [], "heartbeat": None}

    # Read sessions
    sessions_file = OPENCLAW_SESSIONS / "sessions.json"
    if sessions_file.exists():
        try:
            with open(sessions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for sid, sdata in list(data.items())[:10]:
                    activity["sessions"].append({
                        "id": sid,
                        "updated": sdata.get("updatedAt"),
                        "messages": sdata.get("messageCount", 0),
                    })
            elif isinstance(data, list):
                for s in data[:10]:
                    activity["sessions"].append({
                        "id": s.get("id", "?"),
                        "updated": s.get("updatedAt"),
                        "messages": s.get("messageCount", 0),
                    })
        except Exception:
            pass

    # Read today's daily note
    today = datetime.now().strftime("%Y-%m-%d")
    daily_note = OPENCLAW_WORKSPACE / "memory" / f"{today}.md"
    if daily_note.exists():
        try:
            content = daily_note.read_text(encoding="utf-8")
            # Extract bullet points
            lines = [l.strip() for l in content.splitlines() if l.strip().startswith("- ")]
            activity["daily_notes"] = lines[-10:]  # Last 10 entries
        except Exception:
            pass

    # Read overnight tasks
    overnight = OPENCLAW_WORKSPACE / "OVERNIGHT.md"
    if overnight.exists():
        try:
            content = overnight.read_text(encoding="utf-8")
            lines = [l.strip() for l in content.splitlines() if l.strip().startswith("- [")]
            activity["overnight_tasks"] = lines[:10]
        except Exception:
            pass

    # Read heartbeat state
    hb_state = OPENCLAW_WORKSPACE / "memory" / "heartbeat-state.json"
    if hb_state.exists():
        try:
            with open(hb_state, "r", encoding="utf-8") as f:
                activity["heartbeat"] = json.load(f)
        except Exception:
            pass

    return activity


def openclaw_send_message(message):
    """Send a message to OpenClaw via its chat completions HTTP endpoint."""
    try:
        body = json.dumps({
            "model": "qwen2.5:14b-instruct",
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{OPENCLAW_WS_PORT}/v1/chat/completions",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {OPENCLAW_TOKEN}")
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"error": str(e)}


def get_systems_overview():
    """Get live status of all integrated systems — the nerve center."""
    import socket
    systems = []

    def port_check(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except (ConnectionRefusedError, OSError):
            return False

    # 1. OpenClaw Agent
    claw_online = port_check(OPENCLAW_WS_PORT)
    claw_model = None
    claw_plugins = []
    if claw_online and OPENCLAW_CONFIG.exists():
        try:
            with open(OPENCLAW_CONFIG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            claw_model = cfg.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "")
            claw_plugins = [k for k, v in cfg.get("plugins", {}).get("entries", {}).items() if v.get("enabled")]
        except Exception:
            pass
    systems.append({
        "id": "openclaw", "name": "OpenClaw Agent", "icon": "🦞",
        "status": "online" if claw_online else "offline",
        "port": OPENCLAW_WS_PORT, "url": f"http://127.0.0.1:{OPENCLAW_WS_PORT}/",
        "detail": f"Model: {(claw_model or '').replace('ollama/', '')} | {len(claw_plugins)} plugins" if claw_online else "Gateway not running",
        "tags": ["ai-agent", "local", "telegram"],
    })

    # 2. MoltBot Hub
    moltbot_online = port_check(8002)
    moltbot_detail = "Docker container"
    if moltbot_online:
        try:
            req = urllib.request.Request(f"{MOLTBOT_URL}/health")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            moltbot_detail = f"Model: {d.get('model', '?')} | {d.get('status', '?')}"
        except Exception:
            moltbot_detail = "Port open, health check failed"
    systems.append({
        "id": "moltbot", "name": "MoltBot Hub", "icon": "🤖",
        "status": "online" if moltbot_online else "offline",
        "port": 8002, "url": None,
        "detail": moltbot_detail if moltbot_online else "Docker container not running",
        "tags": ["ai-agent", "docker", "wsl"],
    })

    # 3. Ollama
    ollama_online = port_check(11434)
    ollama_detail = "Local LLM inference"
    if ollama_online:
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "?") for m in d.get("models", [])]
            ollama_detail = f"{len(models)} models: {', '.join(models[:4])}"
        except Exception:
            pass
    systems.append({
        "id": "ollama", "name": "Ollama", "icon": "🧠",
        "status": "online" if ollama_online else "offline",
        "port": 11434, "url": None,
        "detail": ollama_detail if ollama_online else "Not running — start with: ollama serve",
        "tags": ["inference", "local", "gpu"],
    })

    # 4. Profit Desk
    profit_desk_path = PROJECTS_ROOT / "profit-desk"
    pd_status = "installed"
    pd_detail = "Multi-agent trading desk (6 agents)"
    pd_journal = profit_desk_path / "journal" / "journal.jsonl"
    pd_entries = 0
    if pd_journal.exists():
        try:
            pd_entries = sum(1 for _ in open(pd_journal, "r", encoding="utf-8") if _.strip())
            pd_detail = f"6 agents | {pd_entries} journal entries | PAPER mode"
        except Exception:
            pass
    systems.append({
        "id": "profit-desk", "name": "Profit Desk", "icon": "📊",
        "status": "installed" if profit_desk_path.exists() else "missing",
        "port": None, "url": None,
        "detail": pd_detail,
        "tags": ["trading", "multi-agent", "python"],
    })

    # 5. SCLS (Exo Scratchpad)
    exo_path = PROJECTS_ROOT / "exo"
    scls_detail = "Scratchpad Continual Learning System"
    scls_files = 0
    memory_dir = exo_path / "memory"
    if memory_dir.exists():
        scls_files = len(list(memory_dir.glob("*.md")))
        scls_detail = f"{scls_files} memory files | File-based learning across sessions"
    systems.append({
        "id": "scls", "name": "SCLS (Scratchpad)", "icon": "📝",
        "status": "installed" if exo_path.exists() else "missing",
        "port": None, "url": None,
        "detail": scls_detail,
        "tags": ["learning", "memory", "framework"],
    })

    # 6. Master Trade Bot
    mtb_path = PROJECTS_ROOT / "master-trade-bot"
    mtb_online = port_check(4000)
    systems.append({
        "id": "master-trade-bot", "name": "Master Trade Bot", "icon": "💹",
        "status": "online" if mtb_online else ("installed" if mtb_path.exists() else "missing"),
        "port": 4000 if mtb_online else None, "url": "http://localhost:4000" if mtb_online else None,
        "detail": "Dashboard live on :4000" if mtb_online else "5 engines (Solana, Polymarket, Binance, Coinbase, ETH DeFi)",
        "tags": ["trading", "typescript", "websocket"],
    })

    # 7. Auton (Autonomous Background Worker)
    auton_path = PROJECTS_ROOT / "auton"
    auton_online = port_check(8095)
    auton_detail = "Autonomous background worker"
    auton_url = "http://localhost:8095"
    if auton_online:
        try:
            req = urllib.request.Request("http://127.0.0.1:8095/health")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            mode = d.get("mode", "?")
            active = d.get("active_tasks", 0)
            completed = d.get("completed_today", 0)
            failed = d.get("failed_today", 0)
            auton_detail = f"Mode: {mode} | {active} active, {completed} done, {failed} failed today"
            if d.get("status") == "killed":
                auton_detail = f"KILLED | {d.get('active_tasks', 0)} tasks paused"
        except Exception:
            auton_detail = "Port open, health check failed"
    systems.append({
        "id": "auton", "name": "Auton", "icon": "⚙️",
        "status": "online" if auton_online else ("installed" if auton_path.exists() else "missing"),
        "port": 8095 if auton_online else None,
        "url": auton_url if auton_online else None,
        "detail": auton_detail if auton_online else "Background worker (not running)",
        "tags": ["background-worker", "autonomous", "python"],
    })

    # 8. Hub itself
    systems.append({
        "id": "project-hub", "name": "Mission Control", "icon": "🎛️",
        "status": "online",
        "port": DEFAULT_PORT, "url": f"http://localhost:{DEFAULT_PORT}",
        "detail": "This dashboard — nerve center for all systems",
        "tags": ["dashboard", "python", "always-on"],
    })

    return systems


def get_active_sessions():
    """Get recent Claude Code sessions + active projects, merged into one view."""
    LABEL_MAP = {
        "profit-desk": "Multi-Agent Trading System",
        "exo": "Scratchpad Learning System",
        "project-hub": "Mission Control Dashboard",
        "openclaw": "OpenClaw Agent Setup",
        "master-trade-bot": "Master Trade Bot",
        "tax-prep-system": "Tax Prep System",
        "harmony-medspa": "Harmony Medspa App",
        "jumpquest": "Jump Quest Game",
        "frontier-bastion": "Crown & Conquest RTS",
        "solana-bot": "Solana Token Sniper",
        "polymarket-sniper": "Polymarket Sniper",
        "polymarketbtc15massistant": "Polymarket BTC 15m Assistant",
        "e2ee-messenger": "E2EE P2P Messenger",
        "trading-shared": "Trading Shared Foundation",
        "lancewfisher-splash": "Lance Fisher Splash Page",
        "market-dashboard": "Market Dashboard",
        "auton": "Auton Background Worker",
    }

    def label_for(proj_path, first_msg=""):
        slug = proj_path.replace("\\", "/").rstrip("/").split("/")[-1].lower() if proj_path else ""
        for key, lbl in LABEL_MAP.items():
            if key in slug:
                return lbl
        if "security" in first_msg.lower() or "harden" in first_msg.lower():
            return "Security Hardening"
        return slug.replace("-", " ").replace("_", " ").title() if slug else "Unknown"

    results = []
    seen_projects = set()

    # 1. Claude Code session history (last 48 hours)
    sessions = get_session_summary()
    now = datetime.now(timezone.utc)
    for s in sessions:
        try:
            ts = datetime.fromisoformat(s["lastTimestamp"])
            if (now - ts).total_seconds() < 172800:
                proj = s.get("project", "")
                s["label"] = label_for(proj, s.get("firstMessage", ""))
                s["projectName"] = proj.replace("\\", "/").rstrip("/").split("/")[-1] if proj else "unknown"
                results.append(s)
                seen_projects.add(s["projectName"].lower())
        except Exception:
            continue

    # 2. Fill in from PROJECTS.json for recently active projects not in history
    data = load_projects()
    for p in data.get("projects", []):
        la = p.get("last_active", "")
        slug = ((p.get("path") or "").replace("\\", "/").rstrip("/").split("/")[-1] or "").lower()
        if slug in seen_projects:
            continue
        try:
            if la:
                if len(la) <= 10:
                    la_dt = datetime.fromisoformat(la + "T23:59:59+00:00")
                else:
                    la_dt = datetime.fromisoformat(la)
                    if la_dt.tzinfo is None:
                        la_dt = la_dt.replace(tzinfo=timezone.utc)
                if (now - la_dt).total_seconds() < 172800:
                    results.append({
                        "sessionId": slug,
                        "project": p.get("path", ""),
                        "firstMessage": p.get("description", ""),
                        "messageCount": 0,
                        "firstTimestamp": la,
                        "lastTimestamp": la,
                        "firstDate": la[:16] if la else "",
                        "lastDate": la[:16] if la else "",
                        "label": label_for(p.get("path", "")),
                        "projectName": slug,
                    })
                    seen_projects.add(slug)
        except Exception:
            continue

    results.sort(key=lambda x: x.get("lastTimestamp", ""), reverse=True)
    return results


def bot_proxy_get(path):
    """Proxy a GET request to moltbot-hub. Returns parsed JSON or error dict."""
    try:
        req = urllib.request.Request(f"{MOLTBOT_URL}{path}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"error": str(e)}


def bot_proxy_post(path, data):
    """Proxy a POST request to moltbot-hub. Returns parsed JSON or error dict."""
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(f"{MOLTBOT_URL}{path}", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"error": str(e)}


AUTON_URL = "http://127.0.0.1:8095"


def auton_proxy_get(path):
    """Proxy a GET request to Auton. Returns parsed JSON or error dict."""
    try:
        req = urllib.request.Request(f"{AUTON_URL}{path}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"error": str(e)}


def auton_proxy_post(path, data=None):
    """Proxy a POST request to Auton. Returns parsed JSON or error dict."""
    try:
        body = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(f"{AUTON_URL}{path}", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"error": str(e)}


class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if args and isinstance(args[0], str) and "/api/" in args[0]:
            return
        super().log_message(format, *args)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_dashboard()
        elif self.path == "/api/projects":
            self.send_json(load_projects())
        elif self.path == "/api/sessions":
            self.send_json(get_session_summary())
        elif self.path == "/api/stats":
            self.send_json(get_project_stats(load_projects()))
        elif self.path == "/api/scan":
            self.send_json({"new_projects": scan_directory()})
        elif self.path == "/api/disk":
            self.send_json(get_disk_info())
        elif self.path == "/api/systems":
            self.send_json(get_systems_overview())
        elif self.path == "/api/active-sessions":
            self.send_json(get_active_sessions())
        elif self.path == "/api/openclaw/health":
            self.send_json(openclaw_health())
        elif self.path == "/api/openclaw/activity":
            self.send_json(openclaw_activity())
        elif self.path == "/api/bot/health":
            self.send_json(bot_proxy_get("/health"))
        elif self.path == "/api/bot/capabilities":
            self.send_json(bot_proxy_get("/api/capabilities"))
        elif self.path.startswith("/api/bot/tasks"):
            # Forward task queries: /api/bot/tasks?status=X&limit=N or /api/bot/tasks/123
            bot_path = self.path.replace("/api/bot/tasks", "/api/tasks", 1)
            # For single task GET: /api/bot/tasks/123 -> /tasks/123
            if "/api/tasks/" in bot_path and "?" not in bot_path.split("/api/tasks/")[1]:
                bot_path = bot_path.replace("/api/tasks/", "/tasks/")
            self.send_json(bot_proxy_get(bot_path))
        # --- Auton proxy routes ---
        elif self.path == "/api/auton/health":
            self.send_json(auton_proxy_get("/health"))
        elif self.path == "/api/auton/status":
            self.send_json(auton_proxy_get("/api/status"))
        elif self.path.startswith("/api/auton/tasks"):
            auton_path = self.path.replace("/api/auton/tasks", "/api/tasks", 1)
            self.send_json(auton_proxy_get(auton_path))
        elif self.path == "/api/auton/knowledge":
            self.send_json(auton_proxy_get("/api/knowledge"))
        elif self.path == "/api/auton/journal":
            self.send_json(auton_proxy_get("/api/journal?n=20"))
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/api/projects/add":
            try:
                new_project = json.loads(body)
                data = load_projects()
                new_project.setdefault("pinned", False)
                new_project.setdefault("tags", [])
                new_project.setdefault("status", "active")
                new_project.setdefault("source", "manual")
                new_project.setdefault("last_active", datetime.now(timezone.utc).isoformat())
                data.setdefault("projects", []).append(new_project)
                save_projects(data)
                self.send_json({"ok": True, "projects": data})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/projects/update":
            try:
                update = json.loads(body)
                idx = update.get("index")
                fields = update.get("fields", {})
                data = load_projects()
                if 0 <= idx < len(data["projects"]):
                    data["projects"][idx].update(fields)
                    save_projects(data)
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False, "error": "Invalid index"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/projects/delete":
            try:
                req = json.loads(body)
                idx = req.get("index")
                data = load_projects()
                if 0 <= idx < len(data["projects"]):
                    removed = data["projects"].pop(idx)
                    save_projects(data)
                    self.send_json({"ok": True, "removed": removed["name"]})
                else:
                    self.send_json({"ok": False, "error": "Invalid index"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/projects/import-scan":
            try:
                req = json.loads(body)
                new_projects = req.get("projects", [])
                data = load_projects()
                data.setdefault("projects", []).extend(new_projects)
                save_projects(data)
                self.send_json({"ok": True, "imported": len(new_projects)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/open-terminal":
            try:
                req = json.loads(body)
                project_path = req.get("path", "")
                if os.path.isdir(project_path):
                    subprocess.Popen(["cmd", "/c", "start", "wt", "-d", project_path], shell=False)
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False, "error": "Path not found"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/open-explorer":
            try:
                req = json.loads(body)
                project_path = req.get("path", "")
                if os.path.isdir(project_path):
                    os.startfile(project_path)
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False, "error": "Path not found"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/bot/dispatch":
            try:
                req = json.loads(body)
                # Dispatch task to moltbot-hub via /run (synchronous) or /tasks (async)
                mode = req.pop("mode", "sync")
                endpoint = "/run" if mode == "sync" else "/tasks"
                result = bot_proxy_post(endpoint, req)
                self.send_json(result)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path.startswith("/api/bot/tasks/") and self.path.endswith("/run"):
            try:
                task_id = self.path.split("/")[-2]
                result = bot_proxy_post(f"/tasks/{task_id}/run", {})
                self.send_json(result)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path.startswith("/api/bot/tasks/") and self.path.endswith("/approve"):
            try:
                task_id = self.path.split("/")[-2]
                result = bot_proxy_post(f"/api/tasks/{task_id}/approve", {})
                self.send_json(result)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path.startswith("/api/bot/tasks/") and self.path.endswith("/handoff"):
            try:
                task_id = self.path.split("/")[-2]
                result = bot_proxy_post(f"/api/tasks/{task_id}/handoff", {})
                self.send_json(result)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/openclaw/send":
            try:
                req = json.loads(body)
                message = req.get("message", "")
                if not message:
                    self.send_json({"error": "message required"}, code=400)
                    return
                result = openclaw_send_message(message)
                self.send_json(result)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        elif self.path == "/api/openclaw/overnight":
            try:
                req = json.loads(body)
                task = req.get("task", "").strip()
                if not task:
                    self.send_json({"error": "task required"}, code=400)
                    return
                overnight = OPENCLAW_WORKSPACE / "OVERNIGHT.md"
                overnight.parent.mkdir(parents=True, exist_ok=True)
                existing = overnight.read_text(encoding="utf-8") if overnight.exists() else "# Overnight Tasks\n\n"
                line = f"- [ ] {task}\n"
                if line not in existing:
                    existing += line
                    overnight.write_text(existing, encoding="utf-8")
                self.send_json({"ok": True, "task": task})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        # --- Auton POST proxy routes ---
        elif self.path.startswith("/api/auton/tasks/") and "/approve" in self.path:
            auton_path = self.path.replace("/api/auton/tasks/", "/api/tasks/", 1)
            self.send_json(auton_proxy_post(auton_path))
        elif self.path.startswith("/api/auton/tasks/") and "/reject" in self.path:
            auton_path = self.path.replace("/api/auton/tasks/", "/api/tasks/", 1)
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            self.send_json(auton_proxy_post(auton_path, data))
        elif self.path == "/api/auton/tasks/approve-all":
            self.send_json(auton_proxy_post("/api/tasks/approve-all"))
        elif self.path == "/api/auton/kill":
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            self.send_json(auton_proxy_post("/api/kill", data))
        elif self.path == "/api/auton/resume":
            self.send_json(auton_proxy_post("/api/resume"))
        elif self.path == "/api/launch-claude":
            try:
                req = json.loads(body)
                project_path = req.get("path", "")
                prompt = req.get("prompt", "")
                create = req.get("create", False)
                name = req.get("name", "")
                # Create directory if needed
                if create and not os.path.isdir(project_path):
                    os.makedirs(project_path, exist_ok=True)
                    # Add to PROJECTS.json
                    data = load_projects()
                    data.setdefault("projects", []).append({
                        "name": name or os.path.basename(project_path),
                        "path": project_path,
                        "tech_stack": [],
                        "status": "active",
                        "source": "computer",
                        "description": prompt,
                        "last_active": datetime.now(timezone.utc).isoformat(),
                        "pinned": False,
                        "tags": [],
                    })
                    save_projects(data)
                if os.path.isdir(project_path):
                    # Open Windows Terminal with claude ready to go
                    cmd_prompt = f'cd /d "{project_path}" && claude "{prompt}"' if prompt else f'cd /d "{project_path}" && claude'
                    subprocess.Popen(
                        ["cmd", "/c", "start", "wt", "cmd", "/k", cmd_prompt],
                        shell=False,
                    )
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False, "error": "Path not found"}, code=400)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, code=400)
        else:
            self.send_error(404)

    def send_json(self, data, code=200):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response)

    def serve_dashboard(self):
        html = get_dashboard_html()
        encoded = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(encoded))
        self.end_headers()
        self.wfile.write(encoded)


def get_dashboard_html():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ProjectsHome Hub</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-deep: #0a0c10;
    --bg-primary: #0f1117;
    --bg-card: #161822;
    --bg-card-hover: #1c1f2e;
    --bg-input: #1a1d2a;
    --border: #252836;
    --border-hover: #3a3f55;
    --text-primary: #e2e4ea;
    --text-secondary: #8b8fa3;
    --text-muted: #5c6078;
    --accent-cyan: #36d8c2;
    --accent-cyan-dim: rgba(54, 216, 194, 0.12);
    --accent-orange: #f0883e;
    --accent-orange-dim: rgba(240, 136, 62, 0.12);
    --accent-blue: #4d9fff;
    --accent-blue-dim: rgba(77, 159, 255, 0.12);
    --accent-purple: #b07aff;
    --accent-purple-dim: rgba(176, 122, 255, 0.12);
    --accent-green: #3dd68c;
    --accent-green-dim: rgba(61, 214, 140, 0.12);
    --accent-red: #f85149;
    --accent-red-dim: rgba(248, 81, 73, 0.12);
    --accent-yellow: #e3b341;
    --accent-yellow-dim: rgba(227, 179, 65, 0.12);
    --radius: 8px;
    --radius-lg: 12px;
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --font-mono: 'JetBrains Mono', 'Cascadia Code', monospace;
    --font-sans: 'DM Sans', -apple-system, sans-serif;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg-deep); color: var(--text-primary); font-family: var(--font-sans); min-height: 100vh; overflow-x: hidden; }
  body::before { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E"); pointer-events: none; z-index: 0; }
  .app { position: relative; z-index: 1; max-width: 1400px; margin: 0 auto; padding: 24px 32px; }
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .logo { font-family: var(--font-mono); font-size: 22px; font-weight: 700; color: var(--accent-cyan); letter-spacing: -0.5px; }
  .logo span { color: var(--text-muted); font-weight: 400; }
  .header-stats { display: flex; gap: 20px; font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }
  .header-stats .stat-val { color: var(--text-secondary); font-weight: 600; }
  .header-actions { display: flex; gap: 8px; }
  .btn { font-family: var(--font-mono); font-size: 12px; font-weight: 500; padding: 8px 14px; border-radius: var(--radius); border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); cursor: pointer; transition: all 0.15s; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
  .btn:hover { border-color: var(--border-hover); color: var(--text-primary); background: var(--bg-card-hover); }
  .btn-accent { background: var(--accent-cyan-dim); border-color: rgba(54, 216, 194, 0.25); color: var(--accent-cyan); }
  .btn-accent:hover { background: rgba(54, 216, 194, 0.2); border-color: var(--accent-cyan); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
  .btn-icon { padding: 6px 8px; font-size: 14px; border: none; background: transparent; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius); transition: all 0.15s; }
  .btn-icon:hover { background: var(--bg-card-hover); }
  .btn-danger { color: var(--accent-red); }
  .btn-danger:hover { background: var(--accent-red-dim); }
  .toolbar { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }
  .search-box { flex: 1; min-width: 200px; font-family: var(--font-mono); font-size: 13px; padding: 9px 14px 9px 36px; background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text-primary); outline: none; transition: border-color 0.15s; }
  .search-box:focus { border-color: var(--accent-cyan); }
  .search-box::placeholder { color: var(--text-muted); }
  .search-wrap { position: relative; flex: 1; min-width: 200px; }
  .search-wrap::before { content: '\2315'; position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 15px; pointer-events: none; }
  .filter-tabs { display: flex; gap: 2px; background: var(--bg-input); border-radius: var(--radius); padding: 2px; }
  .filter-tab { font-family: var(--font-mono); font-size: 11px; padding: 6px 12px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; border-radius: 6px; transition: all 0.15s; }
  .filter-tab:hover { color: var(--text-secondary); }
  .filter-tab.active { background: var(--bg-card); color: var(--text-primary); box-shadow: var(--shadow); }
  .view-toggle { display: flex; gap: 2px; background: var(--bg-input); border-radius: var(--radius); padding: 2px; }
  .view-btn { padding: 6px 10px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; border-radius: 6px; font-size: 14px; transition: all 0.15s; }
  .view-btn:hover { color: var(--text-secondary); }
  .view-btn.active { background: var(--bg-card); color: var(--text-primary); }
  .projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 14px; margin-bottom: 32px; }
  .projects-grid.list-view { grid-template-columns: 1fr; }
  .project-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 18px 20px; cursor: default; transition: all 0.2s; position: relative; animation: cardIn 0.3s ease both; }
  .project-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); transform: translateY(-1px); box-shadow: var(--shadow); }
  @keyframes cardIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .project-card.pinned { border-left: 3px solid var(--accent-yellow); }
  .card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px; }
  .card-title-row { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
  .card-title { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .pin-indicator { color: var(--accent-yellow); font-size: 12px; flex-shrink: 0; }
  .card-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
  .project-card:hover .card-actions { opacity: 1; }
  .card-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .card-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
  .badge { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.3px; text-transform: uppercase; }
  .badge-tech { background: var(--accent-blue-dim); color: var(--accent-blue); }
  .badge-source-ios { background: var(--accent-purple-dim); color: var(--accent-purple); }
  .badge-source-computer { background: var(--accent-orange-dim); color: var(--accent-orange); }
  .badge-source-manual { background: var(--accent-cyan-dim); color: var(--accent-cyan); }
  .badge-source-auto-detected { background: var(--accent-yellow-dim); color: var(--accent-yellow); }
  .status-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  .status-active { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
  .status-in_progress { background: var(--accent-blue); box-shadow: 0 0 6px var(--accent-blue); }
  .status-paused { background: var(--accent-yellow); }
  .status-completed { background: var(--text-muted); }
  .status-unknown { background: var(--text-muted); }
  .status-concept { background: var(--accent-purple); }
  .card-path { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); background: var(--bg-deep); padding: 6px 10px; border-radius: 5px; display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
  .card-path code { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .card-path .copy-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 12px; padding: 2px 4px; border-radius: 3px; flex-shrink: 0; }
  .card-path .copy-btn:hover { color: var(--accent-cyan); background: var(--accent-cyan-dim); }
  .card-footer { display: flex; gap: 6px; flex-wrap: wrap; }
  .card-footer .btn { font-size: 11px; padding: 5px 10px; }
  .tag { font-family: var(--font-mono); font-size: 10px; padding: 2px 7px; border-radius: 3px; background: var(--bg-deep); color: var(--text-muted); border: 1px solid var(--border); }
  .card-timestamp { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); margin-left: auto; }
  .sessions-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 32px; }
  .sessions-title { font-family: var(--font-mono); font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
  .sessions-title span { color: var(--text-muted); font-weight: 400; font-size: 12px; }
  .session-list { display: flex; flex-direction: column; gap: 6px; max-height: 320px; overflow-y: auto; }
  .session-item { display: grid; grid-template-columns: 100px 1fr 80px auto; gap: 12px; align-items: center; padding: 8px 12px; border-radius: var(--radius); font-size: 12px; transition: background 0.1s; }
  .session-item:hover { background: var(--bg-card-hover); }
  .session-date { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; }
  .session-msg { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .session-count { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; text-align: right; }
  .session-project { font-family: var(--font-mono); color: var(--text-muted); font-size: 10px; }
  .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); z-index: 100; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.15s ease; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .modal { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; width: 480px; max-width: 90vw; box-shadow: 0 8px 40px rgba(0,0,0,0.5); animation: slideUp 0.2s ease; }
  @keyframes slideUp { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .modal h2 { font-family: var(--font-mono); font-size: 16px; font-weight: 600; margin-bottom: 18px; color: var(--text-primary); }
  .form-group { margin-bottom: 14px; }
  .form-group label { display: block; font-family: var(--font-mono); font-size: 11px; font-weight: 500; color: var(--text-secondary); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
  .form-group input, .form-group textarea, .form-group select { width: 100%; font-family: var(--font-mono); font-size: 13px; padding: 9px 12px; background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text-primary); outline: none; transition: border-color 0.15s; }
  .form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: var(--accent-cyan); }
  .form-group textarea { resize: vertical; min-height: 60px; }
  .form-group select { cursor: pointer; }
  .form-group select option { background: var(--bg-primary); }
  .modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }
  .toast { position: fixed; bottom: 24px; right: 24px; background: var(--bg-card); border: 1px solid var(--accent-cyan); border-radius: var(--radius); padding: 12px 18px; font-family: var(--font-mono); font-size: 12px; color: var(--accent-cyan); box-shadow: var(--shadow); z-index: 200; animation: toastIn 0.2s ease, toastOut 0.2s ease 2.5s forwards; }
  @keyframes toastIn { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  @keyframes toastOut { from { opacity: 1; } to { opacity: 0; } }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }
  .empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); font-family: var(--font-mono); font-size: 13px; }
  .empty-state .big { font-size: 32px; margin-bottom: 12px; }
  .command-bar { position: relative; margin-bottom: 20px; }
  .command-input { width: 100%; font-family: var(--font-mono); font-size: 15px; padding: 16px 20px 16px 48px; background: linear-gradient(135deg, rgba(54, 216, 194, 0.06), rgba(77, 159, 255, 0.04)); border: 1px solid rgba(54, 216, 194, 0.2); border-radius: var(--radius-lg); color: var(--text-primary); outline: none; transition: all 0.2s; }
  .command-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 0 3px rgba(54, 216, 194, 0.1), 0 4px 20px rgba(0,0,0,0.3); background: linear-gradient(135deg, rgba(54, 216, 194, 0.1), rgba(77, 159, 255, 0.06)); }
  .command-input::placeholder { color: var(--text-muted); font-style: italic; }
  .command-icon { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: var(--accent-cyan); font-size: 18px; pointer-events: none; opacity: 0.7; }
  .command-hint { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); pointer-events: none; display: flex; gap: 6px; align-items: center; }
  .command-hint kbd { background: var(--bg-card); border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; font-size: 10px; }
  .command-dropdown { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: var(--bg-primary); border: 1px solid var(--border-hover); border-radius: var(--radius); box-shadow: 0 8px 32px rgba(0,0,0,0.5); z-index: 50; max-height: 260px; overflow-y: auto; display: none; }
  .command-dropdown.visible { display: block; animation: slideUp 0.15s ease; }
  .command-option { display: flex; align-items: center; gap: 12px; padding: 10px 16px; cursor: pointer; transition: background 0.1s; }
  .command-option:hover, .command-option.selected { background: var(--bg-card-hover); }
  .command-option-icon { font-size: 16px; width: 24px; text-align: center; flex-shrink: 0; }
  .command-option-text { flex: 1; min-width: 0; }
  .command-option-name { font-family: var(--font-mono); font-size: 13px; font-weight: 500; color: var(--text-primary); }
  .command-option-desc { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .command-option-action { font-family: var(--font-mono); font-size: 10px; color: var(--accent-cyan); padding: 2px 8px; background: var(--accent-cyan-dim); border-radius: 3px; flex-shrink: 0; }
  .command-status { margin-top: 8px; font-family: var(--font-mono); font-size: 11px; color: var(--accent-cyan); padding: 8px 14px; background: var(--accent-cyan-dim); border-radius: var(--radius); display: none; animation: fadeIn 0.15s ease; }
  .btn-bot { background: var(--accent-purple-dim); border-color: rgba(176, 122, 255, 0.25); color: var(--accent-purple); }
  .btn-bot:hover { background: rgba(176, 122, 255, 0.2); border-color: var(--accent-purple); }
  .bot-indicator { display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-mono); font-size: 11px; padding: 4px 10px; border-radius: var(--radius); background: var(--bg-card); border: 1px solid var(--border); }
  .bot-indicator .dot { width: 6px; height: 6px; border-radius: 50%; }
  .bot-indicator .dot.online { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
  .bot-indicator .dot.offline { background: var(--accent-red); }
  .tasks-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 32px; }
  .tasks-panel .task-item { display: grid; grid-template-columns: 60px 1fr 100px 80px auto; gap: 10px; align-items: center; padding: 8px 12px; border-radius: var(--radius); font-size: 12px; transition: background 0.1s; }
  .tasks-panel .task-item:hover { background: var(--bg-card-hover); }
  .task-id { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; }
  .task-prompt { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .task-project { font-family: var(--font-mono); color: var(--accent-purple); font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .task-status { font-family: var(--font-mono); font-size: 10px; padding: 2px 8px; border-radius: 4px; text-align: center; }
  .task-status.completed { background: var(--accent-green-dim); color: var(--accent-green); }
  .task-status.running { background: var(--accent-blue-dim); color: var(--accent-blue); }
  .task-status.queued { background: var(--accent-yellow-dim); color: var(--accent-yellow); }
  .task-status.failed { background: var(--accent-red-dim); color: var(--accent-red); }
  .task-status.pending_approval { background: var(--accent-orange-dim); color: var(--accent-orange); }
  .dispatch-modal textarea { min-height: 100px; }
  .target-toggle { display: flex; align-items: center; gap: 0; background: var(--bg-input); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; flex-shrink: 0; height: 44px; }
  .target-btn { font-family: var(--font-mono); font-size: 12px; font-weight: 500; padding: 0 14px; height: 100%; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.15s; white-space: nowrap; display: flex; align-items: center; gap: 6px; }
  .target-btn:hover { color: var(--text-secondary); background: var(--bg-card-hover); }
  .target-btn.active-bot { background: var(--accent-purple-dim); color: var(--accent-purple); font-weight: 600; }
  .target-btn.active-claude { background: var(--accent-cyan-dim); color: var(--accent-cyan); font-weight: 600; }
  .target-btn .tgt-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .target-btn.active-bot .tgt-dot { background: var(--accent-purple); box-shadow: 0 0 6px var(--accent-purple); }
  .target-btn.active-claude .tgt-dot { background: var(--accent-cyan); box-shadow: 0 0 6px var(--accent-cyan); }
  .target-btn:not(.active-bot):not(.active-claude) .tgt-dot { background: var(--text-muted); }
  .command-result { margin-top: 8px; font-family: var(--font-mono); font-size: 11px; padding: 12px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); display: none; max-height: 300px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; line-height: 1.6; }
  .command-result.visible { display: block; animation: fadeIn 0.15s ease; }
  .command-result .result-header { color: var(--accent-purple); font-weight: 600; margin-bottom: 6px; }
  .command-result .result-ok { color: var(--accent-green); }
  .command-result .result-err { color: var(--accent-red); }
  .command-result .result-info { color: var(--text-secondary); }
  /* --- Systems Status Panel --- */
  .systems-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 20px; }
  .systems-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .systems-panel-title { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
  .systems-panel-title .sys-count { font-size: 11px; font-weight: 400; color: var(--text-muted); }
  .systems-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; }
  .sys-card { background: var(--bg-deep); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; display: flex; align-items: flex-start; gap: 12px; transition: all 0.15s; }
  .sys-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); }
  .sys-card.online { border-left: 3px solid var(--accent-green); }
  .sys-card.installed { border-left: 3px solid var(--accent-blue); }
  .sys-card.offline { border-left: 3px solid var(--accent-red); opacity: 0.7; }
  .sys-card.missing { border-left: 3px solid var(--text-muted); opacity: 0.5; }
  .sys-icon { font-size: 22px; flex-shrink: 0; line-height: 1; }
  .sys-info { flex: 1; min-width: 0; }
  .sys-name { font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
  .sys-name .sys-status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .sys-name .sys-status-dot.online { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
  .sys-name .sys-status-dot.installed { background: var(--accent-blue); }
  .sys-name .sys-status-dot.offline { background: var(--accent-red); }
  .sys-name .sys-status-dot.missing { background: var(--text-muted); }
  .sys-detail { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); margin-top: 4px; line-height: 1.4; }
  .sys-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px; }
  .sys-tag { font-family: var(--font-mono); font-size: 9px; padding: 1px 6px; border-radius: 3px; background: var(--bg-card); color: var(--text-muted); border: 1px solid var(--border); }
  .sys-port { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); flex-shrink: 0; }
  .sys-port a { color: var(--accent-cyan); text-decoration: none; }
  .sys-port a:hover { text-decoration: underline; }
  /* --- Active Sessions Panel --- */
  .active-sessions-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 20px; }
  .active-sessions-title { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
  .active-sessions-title .sess-count { font-size: 11px; font-weight: 400; color: var(--text-muted); }
  .active-session-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; }
  .session-card { background: var(--bg-deep); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 16px; transition: all 0.15s; cursor: default; }
  .session-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); }
  .session-card-label { font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: var(--accent-cyan); margin-bottom: 4px; }
  .session-card-project { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); margin-bottom: 6px; }
  .session-card-msg { font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .session-card-meta { display: flex; justify-content: space-between; align-items: center; }
  .session-card-time { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); }
  .session-card-msgs { font-family: var(--font-mono); font-size: 10px; color: var(--accent-purple); background: var(--accent-purple-dim); padding: 2px 8px; border-radius: 3px; }
  /* --- OpenClaw Panel --- */
  .openclaw-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 24px; }
  .openclaw-panel.online { border-color: rgba(61, 214, 140, 0.3); }
  .openclaw-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .openclaw-title { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 10px; }
  .openclaw-title .claw-icon { font-size: 18px; }
  .openclaw-title .claw-version { font-size: 11px; font-weight: 400; color: var(--text-muted); }
  .openclaw-status-badge { font-family: var(--font-mono); font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 12px; display: flex; align-items: center; gap: 6px; }
  .openclaw-status-badge.online { background: var(--accent-green-dim); color: var(--accent-green); }
  .openclaw-status-badge.offline { background: var(--accent-red-dim); color: var(--accent-red); }
  .openclaw-status-badge .pulse { width: 8px; height: 8px; border-radius: 50%; }
  .openclaw-status-badge.online .pulse { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); animation: pulse 2s ease-in-out infinite; }
  .openclaw-status-badge.offline .pulse { background: var(--accent-red); }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  .openclaw-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .openclaw-info-card { background: var(--bg-deep); border-radius: var(--radius); padding: 14px 16px; }
  .openclaw-info-label { font-family: var(--font-mono); font-size: 10px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .openclaw-info-value { font-family: var(--font-mono); font-size: 13px; color: var(--text-primary); line-height: 1.4; }
  .openclaw-info-value .plugin-tag { display: inline-block; font-size: 10px; padding: 2px 7px; background: var(--accent-purple-dim); color: var(--accent-purple); border-radius: 3px; margin: 2px 3px 2px 0; }
  .openclaw-info-value .tg-tag { display: inline-block; font-size: 10px; padding: 2px 7px; background: var(--accent-blue-dim); color: var(--accent-blue); border-radius: 3px; }
  .openclaw-activity { margin-top: 14px; }
  .openclaw-activity-title { font-family: var(--font-mono); font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
  .openclaw-activity-list { display: flex; flex-direction: column; gap: 4px; max-height: 180px; overflow-y: auto; }
  .openclaw-activity-item { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); padding: 5px 10px; background: var(--bg-deep); border-radius: 4px; line-height: 1.4; }
  .openclaw-input-bar { margin-top: 14px; display: flex; gap: 8px; }
  .openclaw-input { flex: 1; font-family: var(--font-mono); font-size: 12px; padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text-primary); outline: none; transition: border-color 0.15s; }
  .openclaw-input:focus { border-color: var(--accent-purple); }
  .openclaw-input::placeholder { color: var(--text-muted); }
  .btn-claw { background: var(--accent-purple-dim); border-color: rgba(176, 122, 255, 0.25); color: var(--accent-purple); }
  .btn-claw:hover { background: rgba(176, 122, 255, 0.2); border-color: var(--accent-purple); }
  .openclaw-actions { display: flex; gap: 6px; }
  .openclaw-response { margin-top: 10px; font-family: var(--font-mono); font-size: 11px; padding: 12px 14px; background: var(--bg-deep); border: 1px solid var(--border); border-radius: var(--radius); display: none; max-height: 250px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; line-height: 1.6; color: var(--text-secondary); }
  .openclaw-response.visible { display: block; animation: fadeIn 0.15s ease; }
  @media (max-width: 768px) { .app { padding: 16px; } .header { flex-direction: column; gap: 12px; align-items: flex-start; } .projects-grid { grid-template-columns: 1fr; } .session-item { grid-template-columns: 80px 1fr auto; } .session-project { display: none; } .command-hint { display: none; } .tasks-panel .task-item { grid-template-columns: 50px 1fr auto; } .task-project, .task-id { display: none; } .openclaw-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="app" id="app">
  <header class="header">
    <div class="header-left">
      <div class="logo">ProjectsHome<span> /hub</span></div>
      <div class="header-stats" id="headerStats"></div>
    </div>
    <div class="header-actions">
      <div class="bot-indicator" id="clawIndicator" title="OpenClaw Agent Status"><span class="dot offline" id="clawDot"></span><span id="clawLabel">Claw: checking...</span></div>
      <div class="bot-indicator" id="botIndicator" title="MoltBot Status"><span class="dot offline" id="botDot"></span><span id="botLabel">Bot: checking...</span></div>
      <div class="bot-indicator" id="autonIndicator" title="Auton Status"><span class="dot offline" id="autonDot"></span><span id="autonLabel">Auton: checking...</span></div>
      <button class="btn" onclick="scanForNew()" title="Scan for new projects">&#x27F3; Scan</button>
      <button class="btn btn-accent" onclick="openAddModal()">+ Add Project</button>
    </div>
  </header>
  <div class="command-bar">
    <div style="display:flex;gap:8px;align-items:stretch;">
      <div class="target-toggle" id="targetToggle">
        <button class="target-btn active-bot" id="tgtBot" onclick="setTarget('bot')" title="Send to local offline bot (Moltbot)"><span class="tgt-dot"></span>Local Bot</button>
        <button class="target-btn" id="tgtClaude" onclick="setTarget('claude')" title="Open in Claude Code terminal"><span class="tgt-dot"></span>Claude Code</button>
      </div>
      <div style="position:relative;flex:1;">
        <span class="command-icon">&#9889;</span>
        <input type="text" class="command-input" id="commandInput" placeholder="Describe a task for the local bot... (e.g. create a hello world python script)" autocomplete="off" spellcheck="false">
        <div class="command-hint"><kbd>Enter</kbd> to send</div>
        <div class="command-dropdown" id="commandDropdown"></div>
      </div>
    </div>
    <div class="command-status" id="commandStatus"></div>
    <div class="command-result" id="commandResult"></div>
  </div>
  <!-- Systems Status Panel -->
  <div class="systems-panel" id="systemsPanel">
    <div class="systems-panel-header">
      <div class="systems-panel-title">&#127918; Systems Status <span class="sys-count" id="sysCount"></span></div>
      <button class="btn btn-sm" onclick="loadSystems()" title="Refresh">&#x27F3; Refresh</button>
    </div>
    <div class="systems-grid" id="systemsGrid">
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--text-muted);padding:20px;text-align:center">Loading systems...</div>
    </div>
  </div>

  <!-- Active Sessions Panel -->
  <div class="active-sessions-panel" id="activeSessionsPanel" style="display:none">
    <div class="active-sessions-title">&#128260; Tonight's Sessions <span class="sess-count" id="activeSessionCount"></span></div>
    <div class="active-session-cards" id="activeSessionCards"></div>
  </div>

  <!-- OpenClaw Agent Panel -->
  <div class="openclaw-panel" id="openclawPanel">
    <div class="openclaw-header">
      <div class="openclaw-title">
        <span class="claw-icon">&#129438;</span>
        OpenClaw Agent
        <span class="claw-version" id="clawVersion"></span>
      </div>
      <div class="openclaw-status-badge offline" id="clawStatusBadge">
        <span class="pulse"></span>
        <span id="clawStatusText">Checking...</span>
      </div>
    </div>
    <div class="openclaw-grid" id="clawInfoGrid">
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Model</div>
        <div class="openclaw-info-value" id="clawModel">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Plugins</div>
        <div class="openclaw-info-value" id="clawPlugins">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Telegram</div>
        <div class="openclaw-info-value" id="clawTelegram">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Gateway</div>
        <div class="openclaw-info-value" id="clawGateway">ws://127.0.0.1:18800</div>
      </div>
    </div>
    <div class="openclaw-activity" id="clawActivitySection" style="display:none">
      <div class="openclaw-activity-title">Recent Activity</div>
      <div class="openclaw-activity-list" id="clawActivityList"></div>
    </div>
    <div class="openclaw-activity" id="clawOvernightSection" style="display:none">
      <div class="openclaw-activity-title">Overnight Queue</div>
      <div class="openclaw-activity-list" id="clawOvernightList"></div>
    </div>
    <div class="openclaw-input-bar">
      <input type="text" class="openclaw-input" id="clawInput" placeholder="Send a task to OpenClaw agent..." autocomplete="off" spellcheck="false">
      <div class="openclaw-actions">
        <button class="btn btn-sm btn-claw" onclick="sendToOpenClaw()" title="Send task">&#9889; Send</button>
        <button class="btn btn-sm" onclick="addOvernightTask()" title="Add to overnight queue">&#127769; Overnight</button>
        <button class="btn btn-sm" onclick="openClawDashboard()" title="Open Control UI">&#128203; Control UI</button>
      </div>
    </div>
    <div class="openclaw-response" id="clawResponse"></div>
  </div>

  <!-- Auton Background Worker Panel -->
  <div class="openclaw-panel" id="autonPanel" style="display:none">
    <div class="openclaw-header">
      <div class="openclaw-title">
        <span class="claw-icon">&#9881;</span>
        Auton
        <span class="claw-version" id="autonMode"></span>
      </div>
      <div class="openclaw-status-badge offline" id="autonStatusBadge">
        <span class="pulse"></span>
        <span id="autonStatusText">Checking...</span>
      </div>
    </div>
    <div class="openclaw-grid" id="autonInfoGrid">
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Active Tasks</div>
        <div class="openclaw-info-value" id="autonActive">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Completed Today</div>
        <div class="openclaw-info-value" id="autonCompleted">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Failed Today</div>
        <div class="openclaw-info-value" id="autonFailed">--</div>
      </div>
      <div class="openclaw-info-card">
        <div class="openclaw-info-label">Known Projects</div>
        <div class="openclaw-info-value" id="autonProjects">--</div>
      </div>
    </div>
    <div class="openclaw-activity" id="autonTaskSection" style="display:none">
      <div class="openclaw-activity-title">Awaiting Review <span id="autonReviewCount" style="color:var(--accent-yellow)"></span></div>
      <div class="openclaw-activity-list" id="autonReviewList"></div>
    </div>
    <div class="openclaw-input-bar">
      <div class="openclaw-actions" style="width:100%;display:flex;gap:8px">
        <button class="btn btn-sm btn-claw" onclick="autonApproveAll()" title="Approve all pending tasks">&#9989; Approve All</button>
        <button class="btn btn-sm" onclick="window.open('http://localhost:8095','_blank')" title="Open full Auton Dashboard">&#128203; Dashboard</button>
        <button class="btn btn-sm" id="autonKillBtn" onclick="autonToggleKill()" title="Kill switch" style="color:var(--accent-red)">&#9724; Kill</button>
      </div>
    </div>
  </div>

  <div class="toolbar">
    <div class="search-wrap">
      <input type="text" class="search-box" id="searchBox" placeholder="Search projects... (press /)" oninput="renderProjects()">
    </div>
    <div class="filter-tabs" id="filterTabs">
      <button class="filter-tab active" onclick="setFilter('all', this)">All</button>
      <button class="filter-tab" onclick="setFilter('active', this)">Active</button>
      <button class="filter-tab" onclick="setFilter('pinned', this)">Pinned</button>
      <button class="filter-tab" onclick="setFilter('computer', this)">&#128187; PC</button>
      <button class="filter-tab" onclick="setFilter('ios', this)">&#128241; iOS</button>
      <button class="filter-tab" onclick="setFilter('concept', this)">&#128173; Ideas</button>
    </div>
    <div class="view-toggle">
      <button class="view-btn active" onclick="setView('grid', this)">&#9638;</button>
      <button class="view-btn" onclick="setView('list', this)">&#8801;</button>
    </div>
  </div>
  <div class="projects-grid" id="projectsGrid"></div>
  <div class="tasks-panel" id="tasksPanel" style="display:none">
    <div class="sessions-title">Bot Tasks <span id="taskCount"></span></div>
    <div class="session-list" id="taskList" style="max-height:400px;overflow-y:auto"></div>
  </div>
  <div class="sessions-panel" id="sessionsPanel" style="display:none">
    <div class="sessions-title">Recent Sessions <span id="sessionCount"></span></div>
    <div class="session-list" id="sessionList"></div>
  </div>
</div>
<div id="modalRoot"></div>
<div id="toastRoot"></div>
<script>
let projects=[], sessions=[], currentFilter='all', currentView='grid', commandTarget='bot';
async function init(){await Promise.all([loadProjects(),loadSessions(),loadStats()]);renderProjects();renderSessions();checkBotHealth();loadBotTasks();setInterval(checkBotHealth,30000);setInterval(loadBotTasks,15000);}
async function loadProjects(){try{const r=await fetch('/api/projects');const d=await r.json();projects=d.projects||[];}catch(e){projects=[];}}
async function loadSessions(){try{const r=await fetch('/api/sessions');sessions=await r.json();}catch(e){sessions=[];}}
async function loadStats(){try{const r=await fetch('/api/stats');const s=await r.json();document.getElementById('headerStats').innerHTML=`<span><span class="stat-val">${s.totalProjects}</span> projects</span><span><span class="stat-val">${s.activeProjects}</span> active</span><span><span class="stat-val">${s.totalSessions}</span> sessions</span><span><span class="stat-val">${s.totalMessages}</span> messages</span>`;}catch(e){}}
function renderProjects(){const grid=document.getElementById('projectsGrid');const query=document.getElementById('searchBox').value.toLowerCase();let filtered=projects.filter((p,i)=>{p._index=i;const text=`${p.name} ${p.description||''} ${p.path||''} ${p.tech||''} ${(p.tags||[]).join(' ')}`.toLowerCase();if(query&&!text.includes(query))return false;if(currentFilter==='all')return true;if(currentFilter==='active')return p.status==='active'||p.status==='in_progress';if(currentFilter==='pinned')return p.pinned;if(currentFilter==='computer')return p.source==='computer'||p.source==='local'||p.source==='auto-detected';if(currentFilter==='ios')return p.source==='ios';if(currentFilter==='concept')return p.status==='concept';return true;});filtered.sort((a,b)=>{if(a.pinned&&!b.pinned)return -1;if(!a.pinned&&b.pinned)return 1;return new Date(b.last_active||0)-new Date(a.last_active||0);});if(!filtered.length){grid.innerHTML='<div class="empty-state"><div class="big">&empty;</div>No projects found.</div>';return;}grid.className=`projects-grid ${currentView==='list'?'list-view':''}`;grid.innerHTML=filtered.map((p,fi)=>{const sc=`status-${(p.status||'unknown').replace(/\s+/g,'_')}`;const sl=(p.status||'unknown').replace(/_/g,' ');const src=p.source==='ios'?'&#128241; iOS':p.source==='computer'?'&#128187; PC':p.source||'manual';const srcC=`badge-source-${(p.source||'manual').replace(/\s+/g,'-')}`;const techs=(p.tech||'').split(',').map(t=>t.trim()).filter(Boolean);const tags=p.tags||[];const la=p.last_active?timeAgo(p.last_active):'';return`<div class="project-card ${p.pinned?'pinned':''}" style="animation-delay:${fi*0.04}s"><div class="card-header"><div class="card-title-row">${p.pinned?'<span class="pin-indicator">&#9733;</span>':''}<span class="card-title">${esc(p.name)}</span></div><div class="card-actions"><button class="btn-icon" onclick="togglePin(${p._index})">${p.pinned?'&#9733;':'&#9734;'}</button><button class="btn-icon" onclick="openEditModal(${p._index})">&#9998;</button><button class="btn-icon btn-danger" onclick="deleteProject(${p._index})">&#10005;</button></div></div>${p.description?`<div class="card-desc">${esc(p.description)}</div>`:''}<div class="card-meta"><span class="status-dot ${sc}"></span><span style="font-family:var(--font-mono);font-size:11px;color:var(--text-muted)">${esc(sl)}</span><span class="badge ${srcC}">${src}</span>${techs.map(t=>`<span class="badge badge-tech">${esc(t)}</span>`).join('')}${tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}${la?`<span class="card-timestamp">${la}</span>`:''}</div>${p.path?`<div class="card-path"><code>${esc(p.path)}</code><button class="copy-btn" onclick="event.stopPropagation();copyText('${escAttr(p.path)}')" title="Copy path">&#128203;</button></div>`:''}<div class="card-footer">${p.path?`<button class="btn btn-sm" onclick="event.stopPropagation();openTerminal('${escAttr(p.path)}')">&#9654; Terminal</button><button class="btn btn-sm" onclick="event.stopPropagation();openExplorer('${escAttr(p.path)}')">&#128193; Explorer</button><button class="btn btn-sm" onclick="event.stopPropagation();copyText('cd ${escAttr(p.path)} && claude')">&#8984; Claude</button><button class="btn btn-sm btn-bot" onclick="event.stopPropagation();openDispatchModal('${escAttr(p.name)}','${escAttr(p.path)}')">&#9881; Bot</button>`:''}</div></div>`;}).join('');}
function renderSessions(){const panel=document.getElementById('sessionsPanel');const list=document.getElementById('sessionList');if(!sessions.length){panel.style.display='none';return;}panel.style.display='block';document.getElementById('sessionCount').textContent=sessions.length+' sessions';list.innerHTML=sessions.slice(0,30).map(s=>`<div class="session-item"><span class="session-date">${esc(s.lastDate)}</span><span class="session-msg" title="${esc(s.firstMessage)}">${esc(s.firstMessage||'(no message)')}</span><span class="session-count">${s.messageCount} msg${s.messageCount>1?'s':''}</span><span class="session-project">${esc(s.project.split('\\\\').pop()||s.project)}</span></div>`).join('');}
async function togglePin(i){await fetch('/api/projects/update',{method:'POST',body:JSON.stringify({index:i,fields:{pinned:!projects[i].pinned}})});projects[i].pinned=!projects[i].pinned;renderProjects();}
async function deleteProject(i){const p=projects[i];if(!confirm(`Remove "${p.name}" from dashboard?\n(Files on disk are NOT deleted.)`))return;await fetch('/api/projects/delete',{method:'POST',body:JSON.stringify({index:i})});projects.splice(i,1);loadStats();renderProjects();toast('Removed '+p.name);}
async function openTerminal(p){await fetch('/api/open-terminal',{method:'POST',body:JSON.stringify({path:p})});toast('Opening terminal...');}
async function openExplorer(p){await fetch('/api/open-explorer',{method:'POST',body:JSON.stringify({path:p})});}
async function scanForNew(){const r=await fetch('/api/scan');const d=await r.json();const n=d.new_projects||[];if(!n.length){toast('No new projects found');return;}if(confirm(`Found ${n.length} new project(s):\n\n${n.map(p=>'- '+p.name).join('\n')}\n\nAdd them?`)){await fetch('/api/projects/import-scan',{method:'POST',body:JSON.stringify({projects:n})});await loadProjects();loadStats();renderProjects();toast(`Added ${n.length} project(s)`);}}
function setFilter(f,el){currentFilter=f;document.querySelectorAll('.filter-tab').forEach(t=>t.classList.remove('active'));el.classList.add('active');renderProjects();}
function setView(v,el){currentView=v;document.querySelectorAll('.view-btn').forEach(t=>t.classList.remove('active'));el.classList.add('active');renderProjects();}
function openAddModal(){showModal('Add Project',{},async d=>{await fetch('/api/projects/add',{method:'POST',body:JSON.stringify(d)});await loadProjects();loadStats();renderProjects();toast('Added '+d.name);});}
function openEditModal(i){showModal('Edit Project',{...projects[i]},async d=>{await fetch('/api/projects/update',{method:'POST',body:JSON.stringify({index:i,fields:d})});Object.assign(projects[i],d);loadStats();renderProjects();toast('Updated '+d.name);});}
function showModal(title,def,onSave){const r=document.getElementById('modalRoot');r.innerHTML=`<div class="modal-overlay" onclick="closeModal()"><div class="modal" onclick="event.stopPropagation()"><h2>${title}</h2><div class="form-group"><label>Name</label><input id="m_name" value="${esc(def.name||'')}" placeholder="My Project"></div><div class="form-group"><label>Path</label><input id="m_path" value="${esc(def.path||'')}" placeholder="D:\\ProjectsHome\\my-project"></div><div class="form-group"><label>Description</label><textarea id="m_desc" placeholder="What this does...">${esc(def.description||'')}</textarea></div><div class="form-group"><label>Tech</label><input id="m_tech" value="${esc(def.tech||'')}" placeholder="Python, Node.js"></div><div class="form-group"><label>Status</label><select id="m_status">${['active','in_progress','paused','completed','concept','unknown'].map(s=>`<option value="${s}" ${def.status===s?'selected':''}>${s.replace(/_/g,' ')}</option>`).join('')}</select></div><div class="form-group"><label>Source</label><select id="m_source">${['computer','ios','manual','auto-detected'].map(s=>`<option value="${s}" ${def.source===s?'selected':''}>${s}</option>`).join('')}</select></div><div class="form-group"><label>Tags (comma-separated)</label><input id="m_tags" value="${esc((def.tags||[]).join(', '))}" placeholder="bot, trading"></div><div class="modal-actions"><button class="btn" onclick="closeModal()">Cancel</button><button class="btn btn-accent" onclick="saveModal()">Save</button></div></div></div>`;r._onSave=onSave;}
function saveModal(){const d={name:document.getElementById('m_name').value.trim(),path:document.getElementById('m_path').value.trim(),description:document.getElementById('m_desc').value.trim(),tech:document.getElementById('m_tech').value.trim(),status:document.getElementById('m_status').value,source:document.getElementById('m_source').value,tags:document.getElementById('m_tags').value.split(',').map(t=>t.trim()).filter(Boolean)};if(!d.name){alert('Name required');return;}document.getElementById('modalRoot')._onSave(d);closeModal();}
function closeModal(){document.getElementById('modalRoot').innerHTML='';}
function copyText(t){navigator.clipboard.writeText(t).then(()=>toast('Copied!')).catch(()=>toast('Copied!'));}
function toast(m){const r=document.getElementById('toastRoot');const e=document.createElement('div');e.className='toast';e.textContent=m;r.appendChild(e);setTimeout(()=>e.remove(),3000);}
function timeAgo(d){const diff=Date.now()-new Date(d).getTime();const m=Math.floor(diff/60000);if(m<1)return'just now';if(m<60)return m+'m ago';const h=Math.floor(m/60);if(h<24)return h+'h ago';const dy=Math.floor(h/24);if(dy<30)return dy+'d ago';return new Date(d).toLocaleDateString();}
function esc(s){if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function escAttr(s){return(s||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
// --- Target Toggle ---
function setTarget(t){
  commandTarget=t;
  const botBtn=document.getElementById('tgtBot');
  const claudeBtn=document.getElementById('tgtClaude');
  const inp=document.getElementById('commandInput');
  const hint=document.querySelector('.command-hint');
  if(t==='bot'){
    botBtn.className='target-btn active-bot';
    claudeBtn.className='target-btn';
    inp.placeholder='Describe a task for the local bot... (e.g. create a hello world python script)';
    if(hint)hint.innerHTML='<kbd>Enter</kbd> to send';
  }else{
    botBtn.className='target-btn';
    claudeBtn.className='target-btn active-claude';
    inp.placeholder='What do you want to work on? Type a project name or describe a new idea...';
    if(hint)hint.innerHTML='<kbd>Enter</kbd> to launch';
  }
  // Re-trigger dropdown if there's text
  if(inp.value.trim())onCommandInput();
}
// --- Command Bar ---
let cmdSelectedIdx=-1, cmdMatches=[];
const cmdInput=()=>document.getElementById('commandInput');
const cmdDrop=()=>document.getElementById('commandDropdown');
const cmdStatus=()=>document.getElementById('commandStatus');
const cmdResult=()=>document.getElementById('commandResult');
function setupCommandBar(){
  const inp=cmdInput();
  inp.addEventListener('input',onCommandInput);
  inp.addEventListener('keydown',onCommandKey);
  inp.addEventListener('focus',()=>{if(inp.value.trim())onCommandInput();});
  document.addEventListener('click',e=>{if(!e.target.closest('.command-bar'))cmdDrop().classList.remove('visible');});
}
function onCommandInput(){
  const q=cmdInput().value.trim().toLowerCase();
  const drop=cmdDrop();
  if(!q){drop.classList.remove('visible');cmdMatches=[];return;}
  cmdMatches=[];
  if(commandTarget==='bot'){
    // Bot mode: show matching projects to scope the task, plus "general" option
    cmdMatches.push({type:'bot-general',name:'Run without project scope',desc:'Execute in default workspace (D:\\ProjectsHome)',path:null,icon:'&#9881;',action:'Send to Bot'});
    projects.forEach((p,i)=>{
      const text=`${p.name} ${p.description||''} ${p.tech||''} ${(p.tags||[]).join(' ')}`.toLowerCase();
      if(text.includes(q)){
        cmdMatches.push({type:'bot-project',index:i,name:p.name,desc:(p.description||'').slice(0,60),path:p.path,icon:'&#128193;',action:'Scoped to project'});
      }
    });
  }else{
    // Claude mode: match existing projects
    projects.forEach((p,i)=>{
      const text=`${p.name} ${p.description||''} ${p.tech||''} ${(p.tags||[]).join(' ')}`.toLowerCase();
      if(text.includes(q)){
        cmdMatches.push({type:'project',index:i,name:p.name,desc:p.description||'',path:p.path,icon:p.source==='ios'?'&#128241;':'&#128187;',action:p.path?'Open in Claude':'No local path'});
      }
    });
    // Always offer "new project" option
    cmdMatches.push({type:'new',name:'Create new project: "'+cmdInput().value.trim()+'"',desc:'Set up a new project directory and launch Claude Code',path:null,icon:'&#10010;',action:'Create'});
  }
  cmdSelectedIdx=0;
  renderCommandDropdown();
  drop.classList.add('visible');
}
function renderCommandDropdown(){
  const drop=cmdDrop();
  drop.innerHTML=cmdMatches.map((m,i)=>`<div class="command-option ${i===cmdSelectedIdx?'selected':''}" onmouseenter="cmdSelectedIdx=${i};renderCommandDropdown()" onclick="executeCommand(${i})"><span class="command-option-icon">${m.icon}</span><div class="command-option-text"><div class="command-option-name">${esc(m.name)}</div><div class="command-option-desc">${esc(m.desc)}</div></div><span class="command-option-action">${m.action}</span></div>`).join('');
}
function onCommandKey(e){
  if(e.key==='Enter'&&!cmdMatches.length&&commandTarget==='bot'){
    // Bot mode: Enter with no dropdown matches sends directly (no project scope)
    e.preventDefault();
    cmdMatches=[{type:'bot-general',name:'general',path:null}];
    cmdSelectedIdx=0;
    executeCommand(0);
    return;
  }
  if(!cmdMatches.length)return;
  if(e.key==='ArrowDown'){e.preventDefault();cmdSelectedIdx=Math.min(cmdSelectedIdx+1,cmdMatches.length-1);renderCommandDropdown();}
  else if(e.key==='ArrowUp'){e.preventDefault();cmdSelectedIdx=Math.max(cmdSelectedIdx-1,0);renderCommandDropdown();}
  else if(e.key==='Enter'){e.preventDefault();executeCommand(cmdSelectedIdx);}
  else if(e.key==='Escape'){cmdDrop().classList.remove('visible');cmdInput().blur();}
}
async function executeCommand(idx){
  const m=cmdMatches[idx];
  const status=cmdStatus();
  const result=cmdResult();
  const drop=cmdDrop();
  drop.classList.remove('visible');
  const prompt=cmdInput().value.trim();

  // --- Bot target ---
  if(m.type==='bot-general'||m.type==='bot-project'){
    if(!prompt){toast('Enter a task description first');return;}
    if(!botOnline){toast('Bot is offline. Start it first.');return;}
    const projName=m.type==='bot-project'?m.name:null;
    const projPath=m.type==='bot-project'?m.path:null;
    status.style.display='block';
    status.textContent='Sending to bot'+(projName?' ['+projName+']':'')+': "'+prompt.slice(0,60)+'..."';
    result.className='command-result';
    result.innerHTML='';
    cmdInput().value='';
    cmdInput().disabled=true;
    try{
      const payload={prompt:prompt,mode:'sync',source:'projectshome',risk_level:'low'};
      if(projName)payload.project_name=projName;
      if(projPath)payload.project_path=projPath;
      const r=await fetch('/api/bot/dispatch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const d=await r.json();
      cmdInput().disabled=false;
      if(d.error){
        status.textContent='Bot error';
        result.className='command-result visible';
        result.innerHTML='<span class="result-err">Error: '+esc(d.error)+'</span>';
      }else{
        const taskStatus=d.status||'?';
        const taskId=d.id||'?';
        const icon=taskStatus.includes('completed')?'&#9989;':taskStatus==='failed'?'&#10060;':'&#9203;';
        status.style.display='none';
        result.className='command-result visible';
        let html='<div class="result-header">'+icon+' Task #'+taskId+': '+esc(taskStatus)+'</div>';
        const res=d.result||{};
        if(d.project_name)html+='<span class="result-info">Project: '+esc(d.project_name)+'</span>\n';
        if(res.plan)html+='<span class="result-info">Plan: '+esc(res.plan.slice(0,300))+'</span>\n';
        if(res.files_touched&&res.files_touched.length)html+='<span class="result-info">Files: '+esc(res.files_touched.join(', '))+'</span>\n';
        if(res.commands_run&&res.commands_run.length){
          const last=res.commands_run[res.commands_run.length-1];
          html+='<span class="result-info">Last cmd (rc='+last.returncode+'): '+esc(last.cmd||'')+'</span>\n';
          if(last.stdout)html+='<span class="result-ok">'+esc(last.stdout.slice(0,500))+'</span>\n';
          if(last.stderr)html+='<span class="result-err">'+esc(last.stderr.slice(0,300))+'</span>\n';
        }
        if(res.errors&&res.errors.length)html+='<span class="result-err">Errors: '+esc(res.errors.join('; ').slice(0,300))+'</span>\n';
        result.innerHTML=html;
        loadBotTasks();
      }
    }catch(e){
      cmdInput().disabled=false;
      status.textContent='Network error';
      result.className='command-result visible';
      result.innerHTML='<span class="result-err">'+esc(e.message)+'</span>';
    }
    setTimeout(()=>{status.style.display='none';},5000);
    return;
  }

  // --- Claude Code target ---
  if(m.type==='project'&&m.path){
    status.style.display='block';
    status.textContent='Launching Claude Code in '+m.name+'...';
    result.className='command-result';
    try{
      await fetch('/api/launch-claude',{method:'POST',body:JSON.stringify({path:m.path,prompt:prompt})});
      status.textContent='Terminal opened for '+m.name+'. Type your prompt in Claude Code!';
    }catch(e){status.textContent='Error: '+e.message;}
    cmdInput().value='';
    setTimeout(()=>{status.style.display='none';},4000);
  } else if(m.type==='project'&&!m.path){
    toast(m.name+' has no local path. Clone it first.');
  } else if(m.type==='new'){
    const name=prompt;
    const slug=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    const projPath='D:\\\\ProjectsHome\\\\'+slug;
    status.style.display='block';
    status.textContent='Creating project "'+name+'" and launching Claude Code...';
    try{
      await fetch('/api/launch-claude',{method:'POST',body:JSON.stringify({path:projPath,prompt:name,create:true,name:name})});
      await loadProjects();loadStats();renderProjects();
      status.textContent='Project created! Claude Code opening in terminal.';
    }catch(e){status.textContent='Error: '+e.message;}
    cmdInput().value='';
    setTimeout(()=>{status.style.display='none';},4000);
  }
}
// --- Bot integration ---
let botOnline=false, botTasks=[];
async function checkBotHealth(){try{const r=await fetch('/api/bot/health');const d=await r.json();botOnline=d.status==='ok'&&!d.error;document.getElementById('botDot').className='dot '+(botOnline?'online':'offline');document.getElementById('botLabel').textContent=botOnline?'Bot: online ('+d.model+')':'Bot: offline';}catch(e){botOnline=false;document.getElementById('botDot').className='dot offline';document.getElementById('botLabel').textContent='Bot: offline';}}
async function loadBotTasks(){try{const r=await fetch('/api/bot/tasks?limit=20');botTasks=await r.json();if(Array.isArray(botTasks))renderBotTasks();}catch(e){botTasks=[];}}
function renderBotTasks(){const panel=document.getElementById('tasksPanel');const list=document.getElementById('taskList');if(!botTasks.length){panel.style.display='none';return;}panel.style.display='block';document.getElementById('taskCount').textContent=botTasks.length+' tasks';list.innerHTML=botTasks.map(t=>{const sc=t.status.replace(/[^a-z_]/g,'');return`<div class="task-item"><span class="task-id">#${t.id}</span><span class="task-prompt" title="${esc(t.prompt)}">${esc(t.prompt.slice(0,120))}</span><span class="task-project">${esc(t.project_name||'-')}</span><span class="task-status ${sc}">${t.status}</span><span style="display:flex;gap:4px">${t.status==='queued'?`<button class="btn btn-sm" onclick="runBotTask(${t.id})">Run</button>`:t.status==='pending_approval'?`<button class="btn btn-sm btn-bot" onclick="approveBotTask(${t.id})">Approve</button>`:t.status==='completed'||t.status==='completed_with_errors'?`<button class="btn btn-sm" onclick="viewHandoff(${t.id})">Handoff</button>`:''}</span></div>`;}).join('');}
function openDispatchModal(projName,projPath){const r=document.getElementById('modalRoot');r.innerHTML=`<div class="modal-overlay" onclick="closeModal()"><div class="modal dispatch-modal" onclick="event.stopPropagation()"><h2>Dispatch to Bot</h2><div class="form-group"><label>Project</label><input id="d_proj" value="${esc(projName)}" readonly style="opacity:0.7"></div><div class="form-group"><label>Task Description</label><textarea id="d_prompt" placeholder="What should the bot do? e.g. Create a test file, add error handling, list project structure..."></textarea></div><div class="form-group"><label>Mode</label><select id="d_mode"><option value="sync">Sync (wait for result)</option><option value="async">Async (queue for later)</option></select></div><div class="form-group"><label>Risk Level</label><select id="d_risk"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High (requires approval)</option></select></div><div class="modal-actions"><button class="btn" onclick="closeModal()">Cancel</button><button class="btn btn-bot" onclick="submitDispatch('${escAttr(projName)}','${escAttr(projPath)}')">Dispatch</button></div></div></div>`;}
async function submitDispatch(projName,projPath){const prompt=document.getElementById('d_prompt').value.trim();if(!prompt){alert('Task description required');return;}const mode=document.getElementById('d_mode').value;const risk=document.getElementById('d_risk').value;closeModal();toast('Dispatching task to bot...');try{const r=await fetch('/api/bot/dispatch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:prompt,project_name:projName,project_path:projPath,mode:mode,risk_level:risk,requires_approval:risk==='high',source:'projectshome'})});const d=await r.json();if(d.error){toast('Bot error: '+d.error);}else{toast('Task #'+d.id+' — '+d.status);loadBotTasks();}}catch(e){toast('Error: '+e.message);}}
async function runBotTask(id){toast('Running task #'+id+'...');try{await fetch('/api/bot/tasks/'+id+'/run',{method:'POST'});setTimeout(loadBotTasks,2000);}catch(e){toast('Error: '+e.message);}}
async function approveBotTask(id){toast('Approving task #'+id+'...');try{await fetch('/api/bot/tasks/'+id+'/approve',{method:'POST'});setTimeout(loadBotTasks,2000);}catch(e){toast('Error: '+e.message);}}
async function viewHandoff(id){try{const r=await fetch('/api/bot/tasks/'+id+'/handoff',{method:'POST'});const d=await r.json();if(d.handoff_md){const blob=new Blob([d.handoff_md],{type:'text/markdown'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='handoff_task_'+id+'.md';a.click();URL.revokeObjectURL(url);toast('Handoff downloaded');}}catch(e){toast('Error: '+e.message);}}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();if((e.key==='/'||e.key==='k'&&(e.ctrlKey||e.metaKey))&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'){e.preventDefault();cmdInput().focus();}});
// --- Systems Status ---
async function loadSystems(){
  try{
    const r=await fetch('/api/systems');
    const systems=await r.json();
    const grid=document.getElementById('systemsGrid');
    const onlineCount=systems.filter(s=>s.status==='online').length;
    document.getElementById('sysCount').textContent=onlineCount+'/'+systems.length+' online';
    grid.innerHTML=systems.map(s=>{
      const portHtml=s.port?(s.url?'<a href="'+s.url+'" target="_blank">:'+s.port+'</a>':':'+s.port):'';
      return'<div class="sys-card '+s.status+'">'
        +'<div class="sys-icon">'+s.icon+'</div>'
        +'<div class="sys-info">'
          +'<div class="sys-name"><span class="sys-status-dot '+s.status+'"></span>'+esc(s.name)+'</div>'
          +'<div class="sys-detail">'+esc(s.detail)+'</div>'
          +'<div class="sys-tags">'+s.tags.map(t=>'<span class="sys-tag">'+esc(t)+'</span>').join('')+'</div>'
        +'</div>'
        +(portHtml?'<div class="sys-port">'+portHtml+'</div>':'')
      +'</div>';
    }).join('');
  }catch(e){
    document.getElementById('systemsGrid').innerHTML='<div style="color:var(--accent-red);font-family:var(--font-mono);font-size:12px">Error loading systems</div>';
  }
}
// --- Active Sessions ---
async function loadActiveSessions(){
  try{
    const r=await fetch('/api/active-sessions');
    const sessions=await r.json();
    const panel=document.getElementById('activeSessionsPanel');
    const cards=document.getElementById('activeSessionCards');
    if(!sessions.length){panel.style.display='none';return;}
    panel.style.display='block';
    document.getElementById('activeSessionCount').textContent=sessions.length+' sessions';
    cards.innerHTML=sessions.map(s=>{
      const ago=timeAgo(s.lastTimestamp);
      return'<div class="session-card">'
        +'<div class="session-card-label">'+esc(s.label||s.projectName)+'</div>'
        +'<div class="session-card-project">'+esc(s.project.replace(/\\\\/g,'/').split('/').pop())+'/ &mdash; '+esc(s.sessionId.slice(0,12))+'</div>'
        +'<div class="session-card-msg">'+esc(s.firstMessage||'(no message)')+'</div>'
        +'<div class="session-card-meta">'
          +'<span class="session-card-time">'+ago+'</span>'
          +'<span class="session-card-msgs">'+s.messageCount+' msg'+(s.messageCount>1?'s':'')+'</span>'
        +'</div>'
      +'</div>';
    }).join('');
  }catch(e){
    document.getElementById('activeSessionsPanel').style.display='none';
  }
}
// --- OpenClaw Agent Integration ---
let clawOnline=false;
async function checkClawHealth(){
  try{
    const r=await fetch('/api/openclaw/health');
    const d=await r.json();
    clawOnline=d.status==='online';
    const badge=document.getElementById('clawStatusBadge');
    const text=document.getElementById('clawStatusText');
    const panel=document.getElementById('openclawPanel');
    document.getElementById('clawDot').className='dot '+(clawOnline?'online':'offline');
    document.getElementById('clawLabel').textContent=clawOnline?'Claw: online':'Claw: offline';
    if(clawOnline){
      badge.className='openclaw-status-badge online';
      text.textContent='Online';
      panel.classList.add('online');
      document.getElementById('clawVersion').textContent=d.version?'v'+d.version:'';
      document.getElementById('clawModel').textContent=(d.model||'--').replace('ollama/','');
      if(d.plugins&&d.plugins.length){
        document.getElementById('clawPlugins').innerHTML=d.plugins.map(p=>'<span class="plugin-tag">'+esc(p)+'</span>').join('');
      }
      document.getElementById('clawTelegram').innerHTML=d.telegram==='enabled'?'<span class="tg-tag">@LanceFisherBot</span> Connected':'Disabled';
    }else{
      badge.className='openclaw-status-badge offline';
      text.textContent='Offline';
      panel.classList.remove('online');
    }
  }catch(e){
    clawOnline=false;
    document.getElementById('clawStatusBadge').className='openclaw-status-badge offline';
    document.getElementById('clawStatusText').textContent='Offline';
  }
}
async function loadClawActivity(){
  try{
    const r=await fetch('/api/openclaw/activity');
    const d=await r.json();
    // Daily notes
    const actSection=document.getElementById('clawActivitySection');
    const actList=document.getElementById('clawActivityList');
    if(d.daily_notes&&d.daily_notes.length){
      actSection.style.display='block';
      actList.innerHTML=d.daily_notes.map(n=>'<div class="openclaw-activity-item">'+esc(n)+'</div>').join('');
    }else{
      actSection.style.display='none';
    }
    // Overnight tasks
    const ovSection=document.getElementById('clawOvernightSection');
    const ovList=document.getElementById('clawOvernightList');
    if(d.overnight_tasks&&d.overnight_tasks.length){
      ovSection.style.display='block';
      ovList.innerHTML=d.overnight_tasks.map(t=>{
        const done=t.includes('[x]')||t.includes('[X]');
        const cl=done?'color:var(--accent-green)':'';
        return'<div class="openclaw-activity-item" style="'+cl+'">'+esc(t)+'</div>';
      }).join('');
    }else{
      ovSection.style.display='none';
    }
  }catch(e){}
}
async function sendToOpenClaw(){
  const inp=document.getElementById('clawInput');
  const resp=document.getElementById('clawResponse');
  const msg=inp.value.trim();
  if(!msg){toast('Enter a message first');return;}
  if(!clawOnline){toast('OpenClaw is offline');return;}
  inp.disabled=true;
  resp.className='openclaw-response visible';
  resp.innerHTML='<span style="color:var(--accent-purple)">Sending to OpenClaw...</span>';
  try{
    const r=await fetch('/api/openclaw/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
    const d=await r.json();
    inp.disabled=false;
    inp.value='';
    if(d.error){
      resp.innerHTML='<span style="color:var(--accent-red)">Error: '+esc(d.error)+'</span>';
    }else{
      const content=d.choices&&d.choices[0]&&d.choices[0].message?d.choices[0].message.content:'(no response)';
      resp.innerHTML='<span style="color:var(--accent-purple);font-weight:600">OpenClaw:</span>\n'+esc(content);
    }
  }catch(e){
    inp.disabled=false;
    resp.innerHTML='<span style="color:var(--accent-red)">Network error: '+esc(e.message)+'</span>';
  }
}
async function addOvernightTask(){
  const inp=document.getElementById('clawInput');
  const task=inp.value.trim();
  if(!task){toast('Enter a task first');return;}
  try{
    const r=await fetch('/api/openclaw/overnight',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:task})});
    const d=await r.json();
    if(d.ok){
      inp.value='';
      toast('Added to overnight queue');
      loadClawActivity();
    }else{
      toast('Error: '+(d.error||'unknown'));
    }
  }catch(e){toast('Error: '+e.message);}
}
function openClawDashboard(){
  window.open('http://127.0.0.1:18800/','_blank');
}
document.getElementById('clawInput').addEventListener('keydown',function(e){
  if(e.key==='Enter'){
    e.preventDefault();
    if(e.shiftKey){addOvernightTask();}else{sendToOpenClaw();}
  }
});
init();
setupCommandBar();
loadSystems();
loadActiveSessions();
checkClawHealth();
loadClawActivity();
checkAutonHealth();
setInterval(loadSystems,30000);
setInterval(loadActiveSessions,60000);
setInterval(checkClawHealth,30000);
setInterval(loadClawActivity,60000);
setInterval(checkAutonHealth,15000);

// --- Auton Background Worker Integration ---
let autonOnline=false;
let autonKilled=false;

async function checkAutonHealth(){
  const panel=document.getElementById('autonPanel');
  const badge=document.getElementById('autonStatusBadge');
  const badgeText=document.getElementById('autonStatusText');
  const dot=document.getElementById('autonDot');
  const label=document.getElementById('autonLabel');
  try{
    const r=await fetch('/api/auton/health');
    const d=await r.json();
    if(d.error){throw new Error(d.error);}
    autonOnline=true;
    autonKilled=d.status==='killed';
    panel.style.display='block';
    badge.className='openclaw-status-badge '+(autonKilled?'offline':'online');
    badgeText.textContent=autonKilled?'KILLED':(d.mode||'SUPERVISED');
    dot.className='dot '+(autonKilled?'offline':'online');
    label.textContent='Auton: '+(autonKilled?'killed':d.mode);
    document.getElementById('autonMode').textContent=d.mode||'';
    document.getElementById('autonActive').textContent=d.active_tasks||0;
    document.getElementById('autonCompleted').textContent=d.completed_today||0;
    document.getElementById('autonFailed').textContent=d.failed_today||0;
    document.getElementById('autonProjects').textContent=d.known_projects||0;
    // Update kill button
    const kb=document.getElementById('autonKillBtn');
    if(autonKilled){kb.innerHTML='&#9654; Resume';kb.style.color='var(--accent-green)';}
    else{kb.innerHTML='&#9724; Kill';kb.style.color='var(--accent-red)';}
    // Load review tasks
    loadAutonReviewTasks(d.tasks_by_status);
  }catch(e){
    autonOnline=false;
    panel.style.display='block';
    badge.className='openclaw-status-badge offline';
    badgeText.textContent='Offline';
    dot.className='dot offline';
    label.textContent='Auton: offline';
    document.getElementById('autonActive').textContent='--';
    document.getElementById('autonCompleted').textContent='--';
    document.getElementById('autonFailed').textContent='--';
    document.getElementById('autonProjects').textContent='--';
    document.getElementById('autonTaskSection').style.display='none';
  }
}

async function loadAutonReviewTasks(tasksByStatus){
  const sec=document.getElementById('autonTaskSection');
  const reviewCount=(tasksByStatus&&tasksByStatus.awaiting_review)||0;
  if(reviewCount===0){sec.style.display='none';return;}
  sec.style.display='block';
  document.getElementById('autonReviewCount').textContent='('+reviewCount+')';
  try{
    const r=await fetch('/api/auton/tasks?status=awaiting_review');
    const d=await r.json();
    const list=document.getElementById('autonReviewList');
    list.innerHTML=(d.tasks||[]).slice(0,8).map(function(t){
      return '<div class="openclaw-activity-item" style="display:flex;justify-content:space-between;align-items:center;padding:6px 0">'
        +'<span style="flex:1;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(t.title)+'</span>'
        +'<span style="display:flex;gap:4px">'
        +'<button class="btn btn-sm" onclick="autonApproveTask(\''+t.task_id+'\')" style="color:var(--accent-green);padding:2px 8px;font-size:10px">&#10003;</button>'
        +'<button class="btn btn-sm" onclick="autonRejectTask(\''+t.task_id+'\')" style="color:var(--accent-red);padding:2px 8px;font-size:10px">&#10007;</button>'
        +'</span></div>';
    }).join('');
  }catch(e){sec.style.display='none';}
}

async function autonApproveTask(taskId){
  try{
    await fetch('/api/auton/tasks/'+taskId+'/approve',{method:'POST'});
    toast('Task approved');
    checkAutonHealth();
  }catch(e){toast('Approve failed');}
}

async function autonRejectTask(taskId){
  try{
    await fetch('/api/auton/tasks/'+taskId+'/reject',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason:'Rejected from hub'})});
    toast('Task rejected');
    checkAutonHealth();
  }catch(e){toast('Reject failed');}
}

async function autonApproveAll(){
  try{
    const r=await fetch('/api/auton/tasks/approve-all',{method:'POST'});
    const d=await r.json();
    toast('Approved '+(d.count||0)+' tasks');
    checkAutonHealth();
  }catch(e){toast('Approve all failed');}
}

async function autonToggleKill(){
  if(autonKilled){
    try{await fetch('/api/auton/resume',{method:'POST'});toast('Auton resumed');checkAutonHealth();}catch(e){toast('Resume failed');}
  }else{
    if(!confirm('Kill Auton? All agents will pause.'))return;
    try{await fetch('/api/auton/kill',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason:'Killed from Project Hub'})});toast('Auton killed');checkAutonHealth();}catch(e){toast('Kill failed');}
  }
}

</script>
</body>
</html>"""


LOG_FILE = PROJECTS_ROOT / "project-hub" / "hub.log"
PID_FILE = PROJECTS_ROOT / "project-hub" / "hub.pid"


def is_already_running():
    """Check if another instance is already serving on the port."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", DEFAULT_PORT))
        sock.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False


def main():
    silent = "--silent" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--silent"]
    port = int(args[0]) if args else DEFAULT_PORT

    if not PROJECTS_ROOT.exists():
        if not silent:
            print(f"Error: {PROJECTS_ROOT} does not exist.")
        sys.exit(1)

    if is_already_running():
        if not silent:
            print(f"  Hub already running on port {port}. Opening browser...")
        webbrowser.open(f"http://localhost:{port}")
        return

    # Redirect output to log file when running silently
    if silent:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log = open(LOG_FILE, "a", encoding="utf-8")
        sys.stdout = log
        sys.stderr = log

    # Write PID file for management
    PID_FILE.write_text(str(os.getpid()))

    print(f"\n  ProjectsHome Hub v1.0")
    print(f"  http://localhost:{port}")
    print(f"  Root: {PROJECTS_ROOT}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'silent/background' if silent else 'interactive'}")
    print(f"  PID: {os.getpid()}\n")

    server = HTTPServer(("127.0.0.1", port), DashboardHandler)

    if not silent:
        webbrowser.open(f"http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


if __name__ == "__main__":
    main()
