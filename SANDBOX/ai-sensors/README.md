# AI-Sensors — Centralized Telemetry Aggregator

Autonomous application for collecting telemetry from all `/apps/` modules with JSON logging and incremental writes.

## Overview

AI-Sensors is designed to collect comprehensive telemetry data from the AI-Breadboard system:

- **Hardware telemetry** — CPU, RAM, GPU, Disk, Network, Sensors (through `HardwareMonitor`)
- **Serial numbers** — Disk and memory serial numbers (through `SmartProber`)
- **LHM sensors** — Full LibreHardwareMonitor Web API data (CPU/GPU/RAM/Storage sensors)
- **File system events** — Real-time monitoring via `DirectoryWatcher`
- **Event correlation** — File write/delete events with process and user info

All data is logged in JSON format with **incremental writes** — only changed values are recorded to minimize disk I/O.

## Features

- ✅ Collects telemetry from all `/apps/` modules
- ✅ JSON logging with automatic rotation
- ✅ Incremental writes (only changes)
- ✅ Configurable via `config.json`
- ✅ PowerShell launcher for background/service mode
- ✅ Support for Task Scheduler integration

## Installation

The application is located in `SANDBOX/ai-sensors/` directory.

### Prerequisites

- Python 3.8+
- Windows OS (uses `DirectoryWatcher` with WinAPI)
- Virtual environment with required dependencies

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "interval_seconds": 5.0,
  "max_file_size_mb": 100,
  "max_measurements": null,
  "watch_directories": [
    "C:\\Users\\"
  ],
  "log_filename": "ai_sensors_polls.json",
  "collect_serial_numbers": true,
  "collect_hardware_inventory": true,
  "collect_file_events": true
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `interval_seconds` | 5.0 | Interval between telemetry polls (seconds) |
| `max_file_size_mb` | 100 | Maximum log file size before rotation |
| `max_measurements` | null | Maximum measurements before stopping (null = infinite) |
| `watch_directories` | `["C:\\Users\\"]` | Directories to monitor for file events |
| `log_filename` | `ai_sensors_polls.json` | Output log file name |
| `collect_serial_numbers` | true | Collect serial numbers from devices |
| `collect_hardware_inventory` | true | Collect full hardware snapshot and LHM sensors |
| `collect_file_events` | true | Collect file system events |

**Note:** LHM (LibreHardwareMonitor) Web API is automatically detected. If not running, `HardwareMonitor` is used as fallback.

## Usage

### PowerShell Launcher

```powershell
# Start the service (background mode)
.\SANDBOX\ai-sensors\run.ps1

# Start in a separate window
.\SANDBOX\ai-sensors\run.ps1 -NewWindow

# Check status
.\SANDBOX\ai-sensors\run.ps1 -Action status

# Stop the service
.\SANDBOX\ai-sensors\run.ps1 -Action stop

# Restart the service
.\SANDBOX\ai-sensors\run.ps1 -Action restart
```

### Direct Python Execution

```bash
# From the project root
python -m SANDBOX.ai-sensors.ai_sensors

# Or directly
python SANDBOX/ai-sensors/ai_sensors.py
```

## Output

### Log File Location

Logs are stored in: `%APPDATA%\AI-Breadboard\apps\logs\ai_sensors_polls.json`

Each line is a JSON object with the following structure:

```json
{
  "timestamp": "2026-09-19T12:00:00.000000+00:00",
  "measurement_number": 1,
  "hardware": {
    "timestamp": "...",
    "hostname": "...",
    "cpu": {...},
    "memory": {...},
    "gpus": [...],
    "sensors": [...]
  },
  "serial_numbers": {
    "disks": [
      {"device": "C:", "model": "SSD", "serial": "XXXXX", "capacity_gb": 512}
    ],
    "memory": [
      {"bank": "DIMM1", "capacity_gb": 16, "speed_mhz": 3200, "serial": "YYYYY"}
    ]
  },
  "file_events": [
    {
      "timestamp": "...",
      "action": "Created",
      "path": "C:\\Users\\...\\file.txt",
      "watch_dir": "C:\\Users\\"
    }
  ]
}
```

### File Rotation

When the log file exceeds `max_file_size_mb`, it's rotated:
- Current file: `ai_sensors_polls.json`
- Rotated file: `ai_sensors_polls_20260919_120000.json`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Sensors                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  TelemetryAggregator Class                          │   │
│  │  - HardwareMonitor (CPU, RAM, GPU, Disk, Net)      │   │
│  │  - LHM Web API (Full sensor tree)                  │   │
│  │  - DirectoryWatcher (File Events)                  │   │
│  │  - SmartProber (Serial Numbers)                    │   │
│  │  - Incremental Writes (_has_value_changed)         │   │
│  │  - Log Rotation                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
            %APPDATA%/AI-Breadboard/apps/logs/ai_sensors_polls.json
```

**Data Sources:**
- **HardwareMonitor** — Primary hardware telemetry via WMI
- **LHM Web API** (`http://localhost:8085/data.json`) — Alternative sensor data (if LHM running)
- **DirectoryWatcher** — Real-time file system monitoring
- **SmartProber** — SMART data and device serial numbers

## Integration with Existing System

AI-Sensors integrates with the following existing components:

| Component | Purpose |
|-----------|---------|
| `HardwareMonitor` | Full hardware telemetry with serial numbers |
| `LhmService` | LibreHardwareMonitor Web API integration |
| `DirectoryWatcher` | Real-time file system monitoring |
| `TelemetryLoggerService` | Event correlation (file_write, file_delete) |
| `SmartProber` | SMART data and serial numbers |
| `AutoLogEngine._has_value_changed()` | Incremental write logic |

## Performance Considerations

- **Incremental Writes**: Only changed values are recorded
- **File Rotation**: Prevents log files from growing indefinitely
- **Background Processing**: Runs in a separate thread to minimize impact
- **Caching**: Hardware data is cached to reduce WMI calls

## Troubleshooting

### Service Not Starting

1. Check Python path: Ensure `venv\Scripts\python.exe` exists
2. Check logs: View `%APPDATA%\AI-Breadboard\apps\logs\ai_sensors.log`
3. Check permissions: Ensure access to watch directories

### High CPU Usage

1. Increase `interval_seconds` in config
2. Disable unused collectors (e.g., `collect_file_events: false`)
3. Reduce `watch_directories` to minimal required paths

### No Data Being Collected

1. Verify `HardwareMonitor` can access hardware (test via `Get-HardwareSensors`)
2. Check `DirectoryWatcher` can access watch directories
3. Review logs for error messages

## License

© 2026 hypo69 — AI-Breadboard Project

## See Also

- `apps/windows/telemetry/` — System telemetry modules
- `apps/windows/core/modules/` — System collectors
- `apps/windows_sysadmin/src/directory_watcher.py` — File system watcher
- `apps/librehardwaremonitor/core/lhm_service.py` — LibreHardwareMonitor Web API integration
- `launchers/Run-LHM.ps1` — LHM launcher script
