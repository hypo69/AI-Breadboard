# 🛠️ System Control Center Web Interface Tab

**Path:** `src/api/webinterface/system_control_tab/`  
**Status:** ✅ Active (English Standard)

---

## 📋 Overview

The **System Control Center Tab** provides an intuitive administrative web dashboard integrated into the AI Breadboard single-page application (SPA).

---

## 🏛️ Architecture & Panes

The tab consists of `index.html` and `main.js`, exposing `window.initSystemControlTab()` for administrative tab switching and real-time lifecycle management.

### Sub-panes:
1. **📊 1. Monitoring:** Real-time host telemetry, Windows Defender status, Firewall profile states, UAC mode, and partition metrics.
2. **⚡ 2. Post-Install Wizard:** Sequential checklist execution for post-installation setup presets (*Windows Post-Install Baseline*, *Security Hardening*, *Developer Workstation*).
3. **🛠️ 3. Maintenance & Recovery:** Temporary cache purging, System File Checker (SFC) verification, DISM component store health checking, and Windows System Restore Point creation.
4. **📸 4. System Snapshots & Drift:** Point-in-time configuration snapshots with parameter drift comparison (`MATCH` / `DRIFT`) against live state.
5. **📋 Activity Log:** Historical audit trail of all actions and maintenance operations executed through the UI.

---

## 🔗 Backend API

Interacts with the FastAPI backend at `/api/system-control`:
- `GET /api/system-control/status`
- `GET /api/system-control/profiles`
- `POST /api/system-control/profiles/apply`
- `GET /api/system-control/snapshots`
- `POST /api/system-control/snapshots`
- `POST /api/system-control/snapshots/compare`
- `POST /api/system-control/maintenance/cleanup`
- `POST /api/system-control/maintenance/sfc`
- `POST /api/system-control/maintenance/dism`
- `GET /api/system-control/restore-points`
- `POST /api/system-control/restore-points`
- `GET /api/system-control/logs`
