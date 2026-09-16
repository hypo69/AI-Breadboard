# Standalone Applications & Terminal Workspaces (`/apps`)

**Status:** ✅ Active  
**Authors:** hypo69  

---

## 📋 Overview

The `/apps` directory hosts standalone domain applications, interactive terminal desks, and specialized monitoring workspaces that run natively on the host system and integrate seamlessly with the AI Breadboard ecosystem and FastAPI backend.

---

## 🏛️ Directory Structure & Domain Separation

```
apps/
├── windows/                   # 🪟 AI Windows Diagnostic, Hardware & Administration Center
│   ├── hardware/              # External hardware diagnostic probers (smartctl, GPU SMI, CPU-Z/AIDA64, Stress)
│   ├── core/                  # Core SafeOps, Root-Cause engine, and 15 OS collectors
│   ├── ai/                    # AI Diagnostician and Incident correlation
│   ├── telemetry/             # Hardware sensors, performance metrics, and tunnels
│   └── router.py              # FastAPI REST endpoints (/api/windows/*)
│
├── trading_terminal/          # 📈 Exchange & Stock Control Desk (CLI, TUI, FastAPI Router)
├── network_terminal/          # 🌐 Network Traffic & Deep Packet Inspection Terminal
├── gcloud_monitor/            # ☁️ Google Cloud Console & Observability Monitor
├── cloudflared_monitor/       # 🔒 Cloudflare Tunnel Supervisor & Diagnostics Desk
├── website_monitor/           # 📊 Website Intelligence Monitor (GA4, GSC & Technical Observability)
├── user_assistant/            # 👤 User Assistant Desk (Mail, Calendar, Docs & Agenda)
├── lawyer_assistant/          # ⚖️ Legal AI Assistant for Contracts and Documents
├── helpdesk/                  # 🎧 IT Support and Helpdesk Ticket System
├── wikipedia_research/        # 📚 Research & Fact-Checking Engine
├── research_and_statistic/    # 📈 Data Analysis & Statistical Research Desk
├── dashboard/                 # 🖥️ Interactive System Dashboard
└── ai_breadboard_admin/       # ⚙️ Platform Administration Workspace
```

---

## 🚀 Applications Summary

| Application | CLI Command | Port | FastAPI Endpoints | Description |
|---|---|---|---|---|
| **AI Windows Diagnostic Center** | `python -m apps.windows` | `8105` | `/api/windows/*` | Комплексная диагностика Windows, аудит драйверов, SMART дисков (`smartctl`), GPU (`nvidia-smi`/`amd-smi`), CPU-Z/AIDA64, стресс-тесты, журналы событий и безопасное администрирование. |
| **Network Terminal** | `python -m apps.network_terminal` | `8101` | `/api/v1/network/*` | Live packet capture, protocol distribution, and traffic anomaly detection. |
| **Trading Terminal** | `python -m apps.trading_terminal` | `8103` | `/api/v1/trading/*` | Interactive exchange desk with real-time tickers, orderbook, position & PnL tracking. |
| **Google Cloud Monitor** | `python -m apps.gcloud_monitor` | `8104` | `/api/gcloud/*` | Cloud Logging, metrics, IAM security audit, and AI diagnostics. |
| **Website Monitor** | `python -m apps.website_monitor` | `8106` | `/api/v1/website-monitor/*` | GA4 Data API, Google Search Console metrics, and latency/uptime probes. |
| **User Assistant** | `python -m apps.user_assistant` | `8107` | `/api/v1/assistant/*` | Personal agenda, Gmail and Google Calendar integration. |
