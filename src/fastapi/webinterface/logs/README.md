# Logs Webinterface Tab

## Overview
This directory contains the user interface components for the **System Logs & AI Analysis** tab in the AI Breadboard web interface.

## Components
- `index.html`: Layout containing log metrics, filter toolbar (log level, search, tail size, auto-refresh switch), terminal view, and AI analysis report modal.
- `main.js`: Interactive client logic connecting to the backend endpoints under `/api/logs`:
  - `GET /api/logs/files`: Lists available server log files.
  - `GET /api/logs/read`: Fetches log lines with customizable tail window.
  - `GET /api/logs/stats`: Returns overall storage metrics and file count.
  - `DELETE /api/logs/clear`: Truncates log file on demand.
  - `POST /api/logs/analyze`: Triggers asynchronous Gemini-driven log analysis.
  - `GET /api/logs/reports`: Fetches AI diagnostic reports.
