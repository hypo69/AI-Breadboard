# Website Intelligence Monitor (pps/website_monitor)

**Status:** ✅ Active  
**Language:** English  
**Author:** hypo69  

---

## 📋 Overview

The pps/website_monitor module is a high-performance observability and intelligence monitor built specifically for website owners and webmasters. It eliminates the silo between business, search, and technical infrastructure by unifying 3 vital observation layers:

1. **Business Layer (Google Analytics 4):** Live visitor stream via GA4 Realtime API (active users right now, geo breakdown, device categories), traffic acquisition channels (Organic, Direct, Referral, Social, Paid), top-performing pages, conversion counts, and period-over-period comparison (WoW / MoM).
2. **Search Visibility Layer (Google Search Console):** Total impressions, organic clicks, average CTR, average Google Search SERP rankings, and top query keyword performance.
3. **Technical & Security Layer:** Web endpoint latency probes, availability (uptime SLA %), HTTP status codes (200, 404, 5xx), server resource consumption (CPU, RAM, Disk), and WAF/security incident tracking.
4. **AI Root-Cause Diagnostics & Anomaly Engine:** Automatically correlates metrics across layers (e.g. distinguishing whether a drop in checkout conversion is due to server latency vs frontend UI friction or traffic source shifts) and synthesizes actionable executive summaries.

---

## 🏛️ Directory Structure

`
apps/website_monitor/
├── __init__.py                # Package exports & public API
├── __main__.py                # CLI entry point (TUI, server, realtime, summary, diagnostics)
├── config.json                # Application configuration & alert thresholds
├── README.md                  # Technical documentation in English
├── router.py                  # FastAPI REST endpoints (/api/v1/website-monitor/*)
├── tui.py                     # Rich-based interactive live terminal UI dashboard
├── src/
│   ├── __init__.py            # Engine package exports
│   ├── auth.py                # GA4 & Search Console auth manager (OAuth, Service Account, Mock)
│   ├── ga4_service.py         # GA4 Data API (runReport, runRealtimeReport) & Admin client
│   ├── gsc_service.py         # Google Search Console API query engine
│   ├── technical_service.py   # HTTP probes, availability, latency, 404/5xx & server metrics
│   ├── normalizer.py          # Cross-layer data aggregator & period comparison (WoW, MoM)
│   ├── anomaly_detector.py    # Anomaly heuristics & multi-factor alert rule engine
│   └── diagnostics.py         # AI Root Cause & executive summary generator
└── tests/
    ├── __init__.py
    └── test_website_monitor.py # Full unit test suite (pytest)
`

---

## 🚀 Usage & Common Commands

### 1. Interactive Live TUI Dashboard
Launch the full live terminal monitoring desk:
`powershell
python -m apps.website_monitor
`

### 2. Standalone FastAPI Server
Run as an independent microservice desk:
`powershell
python -m apps.website_monitor --mode server --port 8107
`

### 3. One-Shot CLI Inspection
`powershell
# Check connection & authentication status
python -m apps.website_monitor --status

# Output status in JSON
python -m apps.website_monitor --status --json

# Realtime active visitors snapshot (last 30 min)
python -m apps.website_monitor --realtime

# View unified 3-layer report & WoW deltas
python -m apps.website_monitor --summary

# Inspect server health & technical telemetry
python -m apps.website_monitor --technical

# Run AI root-cause diagnosis & health assessment
python -m apps.website_monitor --diagnostic
`

---

## 🌐 FastAPI REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/website-monitor/status | Connection state, property ID, target site URL, and auth mode |
| GET | /api/v1/website-monitor/realtime | Live visitors count, active pages, geo breakdown (last 30m) |
| GET | /api/v1/website-monitor/summary | Complete 3-layer normalized report with period deltas (WoW) |
| GET | /api/v1/website-monitor/pages | Top pages with views, users, engagement, and conversion stats |
| GET | /api/v1/website-monitor/traffic-sources | Acquisition channel breakdown and conversion rates |
| GET | /api/v1/website-monitor/search-console | Search Console clicks, impressions, CTR, and top queries |
| GET | /api/v1/website-monitor/technical | Availability %, avg latency, 404/5xx error counts, system load |
| GET | /api/v1/website-monitor/alerts | Active anomaly alerts (traffic drop, conversion drop, error spike) |
| GET | /api/v1/website-monitor/diagnostic | AI-assisted root cause analysis, health score & recommendations |
