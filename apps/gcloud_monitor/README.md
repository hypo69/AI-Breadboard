# Google Cloud Console & Observability Monitor (pps/gcloud_monitor)

**Status:** ✅ Active  
**Language:** English  
**Author:** hypo69  

---

## 📋 Overview

The pps/gcloud_monitor module is an enterprise-grade Google Cloud Observability and Administration monitor for AI Breadboard. It connects directly to Google Cloud Platform (GCP) APIs (Cloud Logging, Cloud Monitoring, Cloud Audit Logs, Error Reporting, and Pub/Sub) to provide real-time metrics telemetry, log stream filtering, security audit inspections, error clustering, and AI-driven root cause diagnostics.

---

## 🏛️ Directory Structure

`
apps/gcloud_monitor/
├── __init__.py                # Package exports & public API
├── __main__.py                # CLI entry point (TUI, server, logs, metrics, audit)
├── config.json                # App settings, filters, and alert thresholds
├── README.md                  # Comprehensive documentation in English
├── router.py                  # FastAPI REST endpoints (/api/gcloud/*)
├── tui.py                     # Rich-based interactive live terminal UI dashboard
├── src/
│   ├── __init__.py            # Engine package exports
│   ├── auth.py                # Multi-mode auth (Service Account, OAuth, ADC, Mock)
│   ├── logging_service.py     # Cloud Logging query engine & log parsers
│   ├── metrics_service.py     # Cloud Monitoring time series aggregator
│   ├── audit_service.py       # Cloud Audit & IAM security inspector
│   ├── error_reporting.py     # Exception clustering & traceback analyzer
│   ├── alert_engine.py        # Log-based alert rules & incident manager
│   └── diagnostics.py         # AI root-cause analysis & health scoring
└── tests/
    ├── __init__.py
    ├── test_auth.py           # Unit tests for credentials resolution
    ├── test_services.py       # Unit tests for logging, metrics, and audit
    └── test_router.py         # Unit tests for FastAPI REST endpoints
`

---

## 🚀 Usage & Common Commands

### 1. Interactive Live TUI Dashboard
Launch the full terminal monitoring dashboard:
`powershell
python -m apps.gcloud_monitor
`

### 2. Standalone FastAPI Microservice
Run as an independent API server:
`powershell
python -m apps.gcloud_monitor --mode server --port 8105
`

### 3. One-Shot CLI Inspection
`powershell
# Check GCP connection and auth status
python -m apps.gcloud_monitor --status

# Output status in JSON
python -m apps.gcloud_monitor --status --json

# Query recent logs
python -m apps.gcloud_monitor --logs --limit 20

# Query logs with filter
python -m apps.gcloud_monitor --logs --filter "severity >= ERROR"

# View telemetry metrics summary
python -m apps.gcloud_monitor --metrics

# Inspect recent IAM security & audit events
python -m apps.gcloud_monitor --audit

# View clustered error groups
python -m apps.gcloud_monitor --errors

# Run AI health assessment & root cause diagnostics
python -m apps.gcloud_monitor --diagnostic
`

---

## 🌐 FastAPI REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/gcloud/status | Current GCP authentication state, project ID, and mode |
| GET | /api/gcloud/logs | Fetch parsed Cloud Logging entries with filter query |
| POST | /api/gcloud/logs/query | Structured log query with JSON body |
| GET | /api/gcloud/metrics | Cloud Monitoring telemetry summary & time-series data |
| GET | /api/gcloud/audit | Cloud Audit Logs for IAM mutations & admin events |
| GET | /api/gcloud/errors | Clustered exception groups and stack traces |
| GET | /api/gcloud/incidents | Active alert incidents and threshold violations |
| GET | /api/gcloud/diagnostic | AI-assisted root cause analysis & recommendations |
