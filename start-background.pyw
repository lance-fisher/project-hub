"""
Silent background launcher for the full ProjectsHome stack.
.pyw extension = Python runs this with pythonw automatically (no console window).

Boot order:
  1. Ollama (LLM inference server — needed by OpenClaw, Auton, MoltBot)
  2. OpenClaw Gateway (AI agent on port 18800)
  3. Hub Server (dashboard on port 8090)
  4. Home Hub (home network dashboard on port 3210)
  5. Auton (autonomous background worker on port 8095)

Each service is idempotent — skips if already running.
"""
import subprocess
import sys
import os
import socket
import shutil
import time
from datetime import datetime

PROJECTS_ROOT = r"D:\ProjectsHome"
HUB_DIR = os.path.join(PROJECTS_ROOT, "project-hub")
HOME_HUB_DIR = os.path.join(PROJECTS_ROOT, "home-hub")
AUTON_DIR = os.path.join(PROJECTS_ROOT, "auton")
LOG_FILE = os.path.join(HUB_DIR, "hub.log")
BOOT_LOG = os.path.join(HUB_DIR, "boot.log")
HUB_PORT = 8090
HOME_HUB_PORT = 3210
AUTON_PORT = 8095
OLLAMA_PORT = 11434
OPENCLAW_PORT = 18800
NO_WINDOW = subprocess.CREATE_NO_WINDOW


def log_boot(msg):
    """Append a timestamped line to boot.log."""
    with open(BOOT_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", port))
        sock.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False


def wait_for_port(port, timeout=15):
    """Block until port opens or timeout (seconds)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(port):
            return True
        time.sleep(1)
    return False


def start_ollama():
    """Ensure Ollama is running (needed by OpenClaw + MoltBot)."""
    if is_port_open(OLLAMA_PORT):
        log_boot(f"Ollama already running on :{OLLAMA_PORT}")
        return

    ollama_cmd = shutil.which("ollama")
    if not ollama_cmd:
        # Common install location
        default = r"C:\Users\lance\AppData\Local\Programs\Ollama\ollama.exe"
        if os.path.exists(default):
            ollama_cmd = default

    if not ollama_cmd:
        log_boot("Ollama not found on PATH — skipping")
        return

    log_boot(f"Starting Ollama: {ollama_cmd}")
    env = os.environ.copy()
    env["OLLAMA_HOST"] = "0.0.0.0:11434"
    subprocess.Popen(
        [ollama_cmd, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        creationflags=NO_WINDOW,
    )
    if wait_for_port(OLLAMA_PORT, timeout=20):
        log_boot(f"Ollama started on :{OLLAMA_PORT}")
    else:
        log_boot("Ollama failed to start within 20s")


def start_openclaw_gateway():
    """Start OpenClaw gateway if not already running."""
    if is_port_open(OPENCLAW_PORT):
        log_boot(f"OpenClaw already running on :{OPENCLAW_PORT}")
        return

    openclaw_cmd = shutil.which("openclaw")
    if not openclaw_cmd:
        npm_openclaw = os.path.join(os.environ.get("APPDATA", ""), "npm", "openclaw.cmd")
        if os.path.exists(npm_openclaw):
            openclaw_cmd = npm_openclaw

    if not openclaw_cmd:
        log_boot("OpenClaw not found — skipping")
        return

    log_boot(f"Starting OpenClaw gateway: {openclaw_cmd}")
    gw_log = open(os.path.join(HUB_DIR, "openclaw-gateway.log"), "a", encoding="utf-8")
    gw_log.write(f"\n--- Gateway starting at {datetime.now().isoformat()} ---\n")
    gw_log.flush()

    subprocess.Popen(
        [openclaw_cmd, "gateway", "run", "--port", str(OPENCLAW_PORT), "--bind", "loopback"],
        stdout=gw_log,
        stderr=gw_log,
        creationflags=NO_WINDOW,
    )
    if wait_for_port(OPENCLAW_PORT, timeout=15):
        log_boot(f"OpenClaw gateway started on :{OPENCLAW_PORT}")
    else:
        log_boot("OpenClaw gateway may still be loading (didn't bind within 15s)")


def start_hub_server():
    """Start the dashboard hub server."""
    if is_port_open(HUB_PORT):
        log_boot(f"Hub already running on :{HUB_PORT}")
        return

    log_boot(f"Starting hub server on :{HUB_PORT}")
    hub_log = open(LOG_FILE, "a", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, os.path.join(HUB_DIR, "server.py"), "--silent"],
        cwd=HUB_DIR,
        stdout=hub_log,
        stderr=hub_log,
        creationflags=NO_WINDOW,
    )
    if wait_for_port(HUB_PORT, timeout=10):
        log_boot(f"Hub server started on :{HUB_PORT}")
    else:
        log_boot("Hub server may still be loading")


def start_home_hub():
    """Start Home Hub (home network dashboard) on port 3210."""
    if is_port_open(HOME_HUB_PORT):
        log_boot(f"Home Hub already running on :{HOME_HUB_PORT}")
        return

    server_entry = os.path.join(HOME_HUB_DIR, "server", "dist", "index.js")
    if not os.path.exists(server_entry):
        log_boot("Home Hub server not built (server/dist/index.js missing) — skipping")
        return

    node_cmd = shutil.which("node")
    if not node_cmd:
        log_boot("Node.js not found — skipping Home Hub")
        return

    log_boot(f"Starting Home Hub on :{HOME_HUB_PORT}")
    hh_log = open(os.path.join(HOME_HUB_DIR, "logs", "server.log"), "a", encoding="utf-8")
    hh_log.write(f"\n--- Home Hub starting at {datetime.now().isoformat()} ---\n")
    hh_log.flush()

    # Ensure logs dir exists
    os.makedirs(os.path.join(HOME_HUB_DIR, "logs"), exist_ok=True)

    subprocess.Popen(
        [node_cmd, server_entry],
        cwd=HOME_HUB_DIR,
        stdout=hh_log,
        stderr=hh_log,
        creationflags=NO_WINDOW,
    )
    if wait_for_port(HOME_HUB_PORT, timeout=15):
        log_boot(f"Home Hub started on :{HOME_HUB_PORT}")
    else:
        log_boot("Home Hub may still be loading (didn't bind within 15s)")


def start_auton():
    """Start Auton (autonomous background worker) on port 8095."""
    if is_port_open(AUTON_PORT):
        log_boot(f"Auton already running on :{AUTON_PORT}")
        return

    run_py = os.path.join(AUTON_DIR, "run.py")
    if not os.path.exists(run_py):
        log_boot("Auton run.py not found — skipping")
        return

    # Find pythonw.exe for windowless execution
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    log_boot(f"Starting Auton on :{AUTON_PORT}")

    # Ensure runtime dirs exist
    for d in ["tasks", "tasks/proposals", "tasks/results", "tasks/backups",
              "journal", "logs", "memory", "vault"]:
        os.makedirs(os.path.join(AUTON_DIR, d), exist_ok=True)

    stderr_log = open(os.path.join(AUTON_DIR, "logs", "stderr.log"), "a", encoding="utf-8")
    proc = subprocess.Popen(
        [pythonw, run_py],
        cwd=AUTON_DIR,
        stdout=subprocess.DEVNULL,
        stderr=stderr_log,
        creationflags=subprocess.DETACHED_PROCESS | NO_WINDOW,
    )

    # Write PID file
    pid_file = os.path.join(AUTON_DIR, "auton.pid")
    with open(pid_file, "w") as f:
        f.write(str(proc.pid))

    if wait_for_port(AUTON_PORT, timeout=10):
        log_boot(f"Auton started on :{AUTON_PORT} (PID {proc.pid})")
    else:
        log_boot(f"Auton may still be loading (PID {proc.pid})")


if __name__ == "__main__":
    log_boot("=== Boot sequence starting (5 services) ===")

    # 1. Ollama first (LLM inference — everything else depends on it)
    try:
        start_ollama()
    except Exception as e:
        log_boot(f"Ollama error: {e}")

    # 2. OpenClaw gateway (AI agent — needs Ollama)
    try:
        start_openclaw_gateway()
    except Exception as e:
        log_boot(f"OpenClaw error: {e}")

    # 3. Hub dashboard server
    try:
        start_hub_server()
    except Exception as e:
        log_boot(f"Hub error: {e}")

    # 4. Home Hub (home network dashboard — independent)
    try:
        start_home_hub()
    except Exception as e:
        log_boot(f"Home Hub error: {e}")

    # 5. Auton (autonomous worker — needs Ollama for planning)
    try:
        start_auton()
    except Exception as e:
        log_boot(f"Auton error: {e}")

    # 6. Run initial sync (moved from startup.bat)
    try:
        sync_script = os.path.join(HUB_DIR, "scripts", "sync-all.ps1")
        if os.path.exists(sync_script):
            log_boot("Running initial sync...")
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", sync_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW,
            )
            log_boot("Initial sync launched")
        else:
            log_boot("sync-all.ps1 not found — skipping initial sync")
    except Exception as e:
        log_boot(f"Sync error: {e}")

    log_boot("=== Boot sequence complete (5 services + sync) ===")
