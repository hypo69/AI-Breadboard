# Log Analyzer Admin Plugin

## Overview
The `log_analyzer` plugin extends the AI Breadboard Admin UI with powerful log diagnostics, error clustering, and Gemini-powered root-cause analysis.

## Features
- **Admin UI Integration**: Automatically rendered in `/api/admin/plugins` with dedicated action controls and configuration forms.
- **Actions Available**:
  - **Full Analysis**: Inspects and counts all events across active logs.
  - **Error Filter**: Isolates and clusters `ERROR` and `CRITICAL` signatures.
  - **AI Diagnostics**: Synthesizes errors with Google Gemini and formats actionable remediation plans.
  - **Rotate & Clean Logs**: Maintains disk space by rotating large or empty log files.
- **Configurable Settings**: Log level filter, tail limit, auto-save reports, and AI toggle.
- **LLM Function Calling**: Exposes `analyze_system_logs` tool for agent workflows.

## Configuration Example
```json
{
  "enabled": true,
  "log_level": "ALL",
  "tail_lines": 500,
  "enable_ai_synthesis": true,
  "auto_save_report": true
}
```
