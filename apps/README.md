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
│   ├── hardware/              # External hardware diagnostic probers (Storage WMI, GPU SMI, CPU-Z/AIDA64, Stress)
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
├── windows_startup_auditor/   # 🚀 Windows Startup & Persistence Auditor
├── windows_backup_manager/    # 💾 Windows Backup, Libraries & File History Manager
├── windows_defender/          # 🛡️ Microsoft Defender & AI Security Diagnostic Center
├── dashboard/                 # 🖥️ Interactive System Dashboard
└── ai_breadboard_admin/       # ⚙️ Platform Administration Workspace
```

---

## 🚀 Applications Summary

| Application | CLI Command | Port | FastAPI Endpoints | Description |
|---|---|---|---|---|
| **AI Windows Diagnostic Center** | `python -m apps.windows` | `8105` | `/api/windows/*` | Комплексная диагностика Windows, аудит драйверов, нативная диагностика накопителей, GPU (`nvidia-smi`/`amd-smi`), стресс-тесты, журналы событий и безопасное администрирование. |
| **Microsoft Defender Security Center** | `python -m apps.windows_defender` | `8113` | `/api/v1/defender/*` | Мониторинг и управление Microsoft Defender Antivirus, правила ASR, Controlled Folder Access (Ransomware), аудит исключений, детекция Fileless и корреляция событий. |
| **Windows Startup Auditor** | `python -m apps.windows_startup_auditor` | `8112` | `/api/v1/startup-auditor/*` | Полный поиск всех точек автозагрузки и персистентности Windows (реестр Run/RunOnce, папки Startup, Winlogon, IFEO, службы, задачи), аудит безопасности и оптимизация старта. |
| **Windows Backup Manager** | `python -m apps.windows_backup_manager` | `8114` | `/api/v1/backup-manager/*` | Управление библиотеками Windows, File History, теневыми копиями VSS и RAG-поиском по резервным копиям. |
| **Network Terminal** | `python -m apps.network_terminal` | `8101` | `/api/v1/network/*` | Live packet capture, protocol distribution, and traffic anomaly detection. |
| **Trading Terminal** | `python -m apps.trading_terminal` | `8103` | `/api/v1/trading/*` | Interactive exchange desk with real-time tickers, orderbook, position & PnL tracking. |
| **Google Cloud Monitor** | `python -m apps.gcloud_monitor` | `8104` | `/api/gcloud/*` | Cloud Logging, metrics, IAM security audit, and AI diagnostics. |
| **Website Monitor** | `python -m apps.website_monitor` | `8106` | `/api/v1/website-monitor/*` | GA4 Data API, Google Search Console metrics, and latency/uptime probes. |
| **User Assistant** | `python -m apps.user_assistant` | `8107` | `/api/v1/assistant/*` | Personal agenda, Gmail and Google Calendar integration. |

