# Standalone Applications & Terminal Workspaces (`/apps`)

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  

---

## 📋 Overview

The `/apps` directory hosts standalone domain applications, interactive terminal desks, and specialized monitoring workspaces that run natively on the host system and integrate seamlessly with the AI Breadboard ecosystem and FastAPI backend.

---

## 🏛️ Directory Structure

```
apps/
├── trading_terminal/          # Exchange & Stock Control Desk (CLI, TUI, FastAPI Router)
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── engine.py              # Exchange engine, orderbook, PnL & state management
│   ├── router.py              # FastAPI REST & WebSocket endpoints (/api/v1/trading)
│   ├── tui.py                 # Rich-based interactive terminal UI
│   └── README.md              # Technical documentation & usage guide
│
├── network_terminal/          # Network Traffic & Deep Packet Inspection Terminal
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── router.py              # Bridge to FastAPI endpoints (/api/v1/network)
│   ├── tui.py                 # Rich-based live packet stream & anomaly dashboard
│   └── README.md              # Technical documentation & usage guide
│
├── system_inspector/          # System & Hardware Inspector (Monitoring & Diagnostics)
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── router.py              # FastAPI REST endpoints (/api/v1/system)
│   ├── tui.py                 # Rich-based hardware & process monitoring dashboard
│   └── README.md              # Technical documentation & usage guide
│
└── windows_sysadmin/          # Windows System Administrator (AD & User Management)
    ├── __init__.py
    ├── __main__.py            # CLI entry point
    ├── router.py              # FastAPI REST & WebSocket endpoints (/api/v1/windows-admin)
    ├── tui.py                 # Rich-based AD, user sessions & security events dashboard
    └── README.md              # Technical documentation & usage guide
```

---

## 🚀 Applications Summary

| Application | CLI Command | FastAPI Endpoints | Description |
|---|---|---|---|
| **Trading Terminal** | `python -m apps.trading_terminal` | `/api/v1/trading/*` | Interactive exchange desk with real-time tickers, L2 orderbook, position & PnL tracking, kill-switch, and order execution. |
| **Network Terminal** | `python -m apps.network_terminal` | `/api/v1/network/*` | Live TShark packet capture, protocol distribution, security heuristics, and LLM-assisted traffic anomaly detection. |
| **System Inspector** | `python -m apps.system_inspector` | `/api/v1/system/*` | Real-time system telemetry, hardware inspection, AI diagnostics, process monitoring, and performance audit. |
| **Windows System Administrator** | `python -m apps.windows_sysadmin` | `/api/v1/windows-admin/*` | Active Directory management, user session monitoring, security event tracking, group policies, and Windows admin operations. |

---

## 🛠️ Standards & Architectural Uniformity

- **FastAPI Integration:** All application engines expose REST and WebSocket endpoints registered under `/api/v1/`.
- **TUI & CLI:** Rich-based terminal user interfaces with interactive hotkeys and fallback support for headless/simple consoles.
- **Fail-Fast & Explicit DI:** Clean dependency injection without hidden globals.
- **Strict English Standard:** All code, docstrings, logging, and documentation are written strictly in English.
