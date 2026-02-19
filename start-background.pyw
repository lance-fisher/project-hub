"""
Silent background launcher for the full ProjectsHome stack.
.pyw extension = Python runs this with pythonw automatically (no console window).

Boot order:
  1. Ollama (LLM inference server — needed by OpenClaw and MoltBot)
  2. OpenClaw Gateway (AI agent on port 18800)
  3. Hub Server (dashboard on port 8090)

Each service is idempotent — skips if already running.
"""
import subprocess
import sys
import os
import socket
import shutil
import time
from datetime import datetime

HUB_DIR = r"D:\ProjectsHome\project-hub"
LOG_FILE = os.path.join(HUB_DIR, "hub.log")
BOOT_LOG = os.path.join(HUB_DIR, "boot.log")
HUB_PORT = 8090
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
    subprocess.Popen(
        [ollama_cmd, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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


if __name__ == "__main__":
    log_boot("=== Boot sequence starting ===")

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

    log_boot("=== Boot sequence complete ===")
