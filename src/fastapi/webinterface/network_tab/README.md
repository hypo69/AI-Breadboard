# Network Terminal Admin Tab (`src/fastapi/webinterface/network_tab`)

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  

---

## 📋 Overview

The `network_tab` module integrates the standalone **Network Terminal** (`/apps/network_terminal`) into the AI-Breadboard administrative web panel. It offers live packet streaming via TShark, network interface discovery, PCAP capture file uploading and Deep Packet Inspection (DPI), heuristic traffic rules, and AI anomaly detection.

---

## 🚀 Key Features

- **TShark Live Capture:** Real-time packet stream over WebSocket `/api/v1/network/ws/live`.
- **Interface Probing:** Dynamic network interface probing via `/api/v1/network/interfaces`.
- **PCAP Analysis:** File upload and parsing via `/api/v1/network/analyze/pcap`.
- **AI Diagnostics:** Traffic anomaly heuristics and health report generation.
