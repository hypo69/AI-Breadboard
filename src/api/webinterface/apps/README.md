# Applications Hub Web Interface (`/apps`)

## Overview
The Applications Hub (`/apps`) provides a focused, dedicated standalone web interface for AI Breadboard microservices and applications located in `/apps`.

## Included Application Desks
1. **Exchange Trading Terminal (`#tab-trading`)**: L2 Orderbook, market data stream, positions, PnL monitoring, and kill-switch execution.
2. **Network Analyzer Terminal (`#tab-network`)**: Packet inspection, live stream telemetry, DPI stats, and network anomaly detection.
3. **System Inspector (`#tab-system-inspector`)**: Host hardware metrics, CPU/RAM/Disk diagnostics, GPU telemetry, and process analysis.
4. **Windows System Administrator (`#tab-windows-admin`)**: Windows OS management, services monitoring, scheduled tasks, and administrative diagnostics.
5. **User Assistant (`#tab-user-assistant`)**: Task scheduling, calendar integration, and personal reminders.
6. **Google Cloud Monitor (`#tab-gcloud`)**: Google Cloud console logs, audit inspection, error reporting, and AI diagnostics.
7. **Website Intelligence Monitor (`#tab-website-monitor`)**: GA4 telemetry, Search Console analytics, endpoint health, and traffic anomaly tracking.
8. **Cloudflare Tunnel Monitor (`#tab-cloudflared`)**: Tunnel status, active connections, routing, and remote accessibility observability.

## Key Features
- Zero code duplication: loads existing modular tab templates and lifecycle scripts.
- Multi-theme support (Dark, Light, System) via `src/api/webinterface/js/theme.js`.
- Internationalization (English, Russian, Hebrew) via `src/api/webinterface/js/i18n.js`.
- Direct hash routing (`/apps#tab-trading`, `/apps#tab-network`, etc.).
