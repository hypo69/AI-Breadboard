# Telemetry Process Inspector

Inspects and reports system process states from the Windows telemetry SQLite database (`telemetry.db`).

## Features
- Connects to persistent telemetry storage.
- Queries the latest system snapshot processes (`process_snapshots`).
- Formats process metrics (CPU %, Memory MB, Threads, User).

## Usage
```bash
python .skills/telemetry-process-inspector/scripts/get_process_state.py
```
