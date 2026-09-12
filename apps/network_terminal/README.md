# Network Analyzer Terminal (`apps/network_terminal`)

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  
**Package:** `apps.network_terminal`  

---

## 📋 Overview

The **Network Analyzer Terminal** is an interactive, deep packet inspection (DPI) and live network observability desk. It wraps the native host **TShark (Wireshark CLI)** engine with AI anomaly detection, security heuristics, protocol distribution metrics, and WebSocket streaming.

It operates seamlessly as:
1. **Interactive Rich TUI** for real-time packet inspection in console and Windows Terminal split-pane grids.
2. **FastAPI Microservice** mounted under `/api/v1/network` with PCAP file analysis and live WebSocket streaming (`/ws/live`).

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 apps.network_terminal                       │
├──────────────────────────────┬──────────────────────────────┤
│     Rich TUI Dashboard       │     FastAPI Router           │
│     (tui.py / __main__.py)   │     (router.py)              │
│    • Live DPI packet stream  │    • REST: /status, /analyze │
│    • Protocols & bandwidth   │    • REST: /interfaces       │
│    • Security alerts & AI    │    • WebSocket: /ws/live     │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │         src.network          │
               │  • TSharkWrapper             │
               │  • TrafficAnalyzer           │
               │  • AIDetector (Anomaly LLM)  │
               └──────────────────────────────┘
```

---

## 🚀 CLI Usage

### Launch Interactive TUI
```powershell
# Default interface capture (or simulation if TShark is not installed)
python -m apps.network_terminal

# Custom interface and filter
python -m apps.network_terminal --interface 1 --filter "tcp or udp"

# Force simulation mode for demos/tests
python -m apps.network_terminal --simulate

# List available host network interfaces
python -m apps.network_terminal --list-interfaces
```

### CLI Flags Reference

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--interface` | `-i` | `str` | `1` | Capture interface index or name. |
| `--filter` | `-f` | `str` | `""` | Wireshark display filter expression (e.g. `tcp port 443`, `http`, `dns`). |
| `--simulate` | `-s` | `switch` | `False` | Run synthetic packet generator for demonstration / headless testing. |
| `--list-interfaces` | `-l` | `switch` | `False` | Print available interfaces and exit. |

---

## 🔌 FastAPI REST & WebSocket Endpoints

Base URL: `/api/v1/network`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/network/status` | Verify TShark binary presence and resolve host path. |
| `GET` | `/api/v1/network/interfaces` | List available network capture adapters on the host. |
| `POST` | `/api/v1/network/analyze/pcap` | Upload a `.pcap` / `.pcapng` file for stats, heuristics & AI threat diagnosis. |
| `WS` | `/api/v1/network/ws/live` | WebSocket streaming live captured packets in real-time. |

---

## 🧪 Testing

Run dedicated test suite:
```powershell
pytest tests/test_apps_network.py tests/test_network.py -v
```
