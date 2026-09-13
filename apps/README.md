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
├── windows_sysadmin/          # Windows System Administrator (AD & User Management)
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── router.py              # FastAPI REST & WebSocket endpoints (/api/v1/windows-admin)
│   ├── tui.py                 # Rich-based AD, user sessions & security events dashboard
│   └── README.md              # Technical documentation & usage guide
│
├── user_assistant/          # User Assistant Desk (Mail, Calendar, Docs & Agenda)
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── config.json            # Application configuration
│   ├── engine.py              # Business logic coordinator
│   ├── router.py              # FastAPI REST endpoints (/api/v1/assistant)
│   ├── tui.py                 # Rich-based daily agenda & triage dashboard
│   ├── README.md              # Technical documentation & usage guide
│   └── src/
│       ├── mail_service.py    # Email integration
│       ├── calendar_service.py# Google Calendar API
│       └── docs_service.py    # Sandboxed storage & RAG indexer
│
├── cloudflared_monitor/       # Cloudflare Tunnel Supervisor & Diagnostics Desk
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── config.json            # Application configuration
│   ├── router.py              # FastAPI REST endpoints (/api/cloudflared)
│   ├── tui.py                 # Rich-based live log stream & tunnel health dashboard
│   ├── README.md              # Technical documentation & usage guide
│   └── src/
│       ├── __init__.py
│       └── state.py           # Daemon telemetry, log parsing, endpoint probe, AI diagnostics
│
├── gcloud_monitor/            # Google Cloud Console & Observability Monitor
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point (TUI, server, logs, metrics, audit)
│   ├── config.json            # Application configuration & alert thresholds
│   ├── router.py              # FastAPI REST endpoints (/api/gcloud)
│   ├── tui.py                 # Rich-based live GCP telemetry & logs dashboard
│   ├── README.md              # Technical documentation & usage guide
│   ├── src/
│   │   ├── __init__.py
│   │   ├── auth.py            # Multi-mode GCP credentials & discovery
│   │   ├── logging_service.py # Cloud Logging query & filter engine
│   │   ├── metrics_service.py # Cloud Monitoring telemetry aggregator
│   │   ├── audit_service.py   # Cloud Audit & IAM security inspector
│   │   ├── error_reporting.py # Exception clustering & stack traces
│   │   ├── alert_engine.py    # Log-based alerts & incident manager
│   │   └── diagnostics.py     # AI health scoring & root cause analysis
│   └── tests/
│       ├── __init__.py
│       └── test_gcloud_monitor.py # Full unit test suite
│
└── website_monitor/           # Website Intelligence Monitor (GA4, GSC & Technical Observability)
    ├── __init__.py
    ├── __main__.py            # CLI entry point (TUI, server, realtime, summary, diagnostic)
    ├── config.json            # Application settings, endpoints & anomaly thresholds
    ├── router.py              # FastAPI REST endpoints (/api/v1/website-monitor)
    ├── tui.py                 # Rich-based interactive live terminal UI dashboard
    ├── README.md              # Technical documentation & usage guide
    ├── src/
    │   ├── __init__.py
    │   ├── auth.py            # Multi-mode auth (OAuth, Service Account, Mock)
    │   ├── ga4_service.py     # GA4 Data API, Realtime API & Admin client
    │   ├── gsc_service.py     # Google Search Console queries & CTR aggregator
    │   ├── technical_service.py # Web probes, availability, latency, 404/5xx & server metrics
    │   ├── normalizer.py      # Cross-layer data normalizer & WoW period deltas
    │   ├── anomaly_detector.py # Drift heuristics & multi-factor alert rule engine
    │   └── diagnostics.py     # AI Root-Cause diagnostics & executive summaries
    └── tests/
        ├── __init__.py
        └── test_website_monitor.py # Full unit test suite
```

---

## 🚀 Applications Summary

| Application | CLI Command | Launcher Script | Port | FastAPI Endpoints | Description |
|---|---|---|---|---|---|
| **Windows System Administrator** | `python -m apps.windows_sysadmin` | `Run-WindowsAdmin.ps1` | `8100` | `/api/v1/windows-admin/*` | Active Directory management, user session monitoring, security event tracking, group policies, and Windows admin operations. |
| **Network Terminal** | `python -m apps.network_terminal` | `Run-NetworkTerminal.ps1` | `8101` | `/api/v1/network/*` | Live TShark packet capture, protocol distribution, security heuristics, and LLM-assisted traffic anomaly detection. |
| **System Inspector** | `python -m apps.system_inspector` | `Run-SystemInspector.ps1` | `8102` | `/api/v1/system/*` | Real-time system telemetry, hardware inspection, AI diagnostics, process monitoring, and performance audit. |
| **Trading Terminal** | `python -m apps.trading_terminal` | `Run-TradingTerminal.ps1` | `8103` | `/api/v1/trading/*` | Interactive exchange desk with real-time tickers, L2 orderbook, position & PnL tracking, kill-switch, and order execution. |
| **Cloudflared Monitor** | `python -m apps.cloudflared_monitor` | `Run-CloudflaredMonitor.ps1` | `8104` | `/api/cloudflared/*` | Cloudflare tunnel supervisor, log analyzer, public endpoint latency probe, and AI health diagnostics. |
| **User Assistant** | `python -m apps.user_assistant` | `Run-UserAssistant.ps1` | `8105` | `/api/v1/assistant/*` | Personal productivity desk: unified daily agenda, email search/triage, Google Calendar scheduling, and personal document search. |
| **Google Cloud Monitor** | `python -m apps.gcloud_monitor` | `Run-GCloudMonitor.ps1` | `8106` | `/api/gcloud/*` | Google Cloud observability monitor: Cloud Logging filters, Cloud Monitoring metrics, IAM audit logs, error clustering, and AI diagnostics. |
| **Website Intelligence Monitor** | `python -m apps.website_monitor` | `Run-WebsiteMonitor.ps1` | `8107` | `/api/v1/website-monitor/*` | Website owner intelligence monitor: GA4 realtime & traffic channels, Google Search Console, server availability/latency, 404/5xx alerts, and AI root-cause diagnostics. |

---

## 🛠️ Standards & Architectural Uniformity

- **FastAPI Integration:** All application engines expose REST and WebSocket endpoints registered under `/api/v1/`.
- **TUI & CLI:** Rich-based terminal user interfaces with interactive hotkeys and fallback support for headless/simple consoles.
- **Fail-Fast & Explicit DI:** Clean dependency injection without hidden globals.
- **Strict English Standard:** All code, docstrings, logging, and documentation are written strictly in English.
