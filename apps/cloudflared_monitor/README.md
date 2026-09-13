# Cloudflared Tunnel Monitor (`apps/cloudflared_monitor`)

**Status:** ✅ Active  
**Language:** English  
**Author:** hypo69  

---

## 📋 Overview

The `apps/cloudflared_monitor` module is a standalone monitoring workspace and supervisor for Cloudflare Tunnel (`cloudflared`). It provides real-time daemon process supervision, live log streaming and parsing (`logs/cloudflared.log`), public endpoint latency probes (`https://kino.davidka.net`), and AI/heuristic health diagnostics.

---

## 🏛️ Directory Structure

```
apps/cloudflared_monitor/
├── __init__.py                # Package initialization and public exports
├── __main__.py                # CLI entry point (dashboard, server, health, logs)
├── config.json                # Application configuration (ports, endpoints)
├── router.py                  # FastAPI REST endpoints (/api/cloudflared/*)
├── tui.py                     # Rich-based interactive live terminal UI dashboard
├── README.md                  # Documentation and usage guide
└── src/
    ├── __init__.py            # Internal engine exports
    └── state.py               # Process supervision, log parsing, endpoint prober, AI diagnostics
```

---

## 🚀 Usage & Common Commands

### 1. Interactive TUI Dashboard
Launch the Rich-based full terminal monitoring dashboard:
```powershell
python -m apps.cloudflared_monitor
```

### 2. Standalone FastAPI Microservice
Run as an independent FastAPI server:
```powershell
python -m apps.cloudflared_monitor --mode server --port 8104
```

### 3. One-Shot CLI Inspection
```powershell
# Check tunnel status
python -m apps.cloudflared_monitor --status

# Get status in JSON format
python -m apps.cloudflared_monitor --status --json

# Run AI/heuristic health diagnostics
python -m apps.cloudflared_monitor --health

# View recent tail logs
python -m apps.cloudflared_monitor --logs --limit 30

# Start / Restart / Stop tunnel
python -m apps.cloudflared_monitor --restart
python -m apps.cloudflared_monitor --stop
```

---

## 🌐 FastAPI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cloudflared/status` | Process state, token presence, endpoint status, and summary |
| `GET` | `/api/cloudflared/logs` | Parsed log records with optional level and text filtering |
| `GET` | `/api/cloudflared/metrics` | CPU, RAM, uptime, and network latency metrics |
| `GET` | `/api/cloudflared/diagnostic` | AI/heuristic health assessment, anomaly list, and recommendations |
| `POST` | `/api/cloudflared/test-endpoint` | Trigger immediate HTTP health probe to the public tunnel URL |
| `POST` | `/api/cloudflared/start` | Start daemon (admin auth required) |
| `POST` | `/api/cloudflared/stop` | Stop daemon (admin auth required) |
| `POST` | `/api/cloudflared/restart` | Restart daemon (admin auth required) |

---

## ⚙️ Configuration (`config.json`)

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8104,
    "use_ssl": false,
    "workers": 1
  },
  "cloudflared": {
    "public_url": "https://kino.davidka.net",
    "log_file": "logs/cloudflared.log",
    "poll_interval_seconds": 2.0,
    "metrics_port": 20241,
    "max_log_lines": 500
  }
}
```
