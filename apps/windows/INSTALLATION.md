# Installation & Setup Guide

## System Requirements

- **OS:** Windows 7, 8, 10, 11
- **Python:** 3.8 or later
- **Privileges:** Administrator (for full functionality)
- **Disk Space:** ~50 MB

## Installation

### 1. Clone/Download Repository
```bash
cd c:\Users\onela\AppData\Local\AI-Breadboard\apps\windows
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
python -m apps.windows.apps.dashboard
```

## Quick Start

### Run Dashboard
```bash
python -m apps.windows.apps.dashboard
```

### Run Individual Applications
```bash
# Process Explorer
python -m apps.windows.apps.process_explorer

# Memory Monitor
python -m apps.windows.apps.memory_monitor

# Network Diagnostics
python -m apps.windows.apps.network_diagnostics

# Services Manager
python -m apps.windows.apps.services_manager

# Registry Viewer
python -m apps.windows.apps.windows.registry

# Security Analyzer
python -m apps.windows.apps.security_analyzer

# Hardware Explorer
python -m apps.windows.apps.hardware_explorer

# Baseline Detector
python -m apps.windows.apps.baseline_detector

# Real-Time Monitor
python -m apps.windows.apps.realtime_monitor
```

## Configuration

### Command-Line Usage
Each application supports help:
```bash
python -m apps.windows.apps.process_explorer
> help
> help processes
```

### Python API Usage
```python
from apps.windows.apps.process_explorer import ProcessExplorerUI
from apps.windows.apps.memory_monitor import PerformanceMonitor

# Create UI
ui = ProcessExplorerUI()
ui.start()

# Get metrics
monitor = PerformanceMonitor()
monitor.start()
```

## Troubleshooting

### Import Errors
```bash
# Add to PYTHONPATH
set PYTHONPATH=%cd%

# Or use absolute paths
python -m apps.windows...
```

### Permission Denied
- Run Command Prompt as Administrator
- Some operations require elevation

### Module Not Found
- Verify all directories created
- Check __init__.py files present
- Rebuild package: `pip install -e .`

### Performance Issues
- Reduce refresh intervals
- Limit historical data size
- Close other applications

## Uninstallation

Simply delete the directory:
```bash
rmdir /s c:\path\to\windows\diagnostic\engine
```

## Support

For issues:
1. Check TESTING.md for test procedures
2. Review application README files
3. Check system event logs
4. Run diagnostics suite

## License

Part of Windows Diagnostic Engine (Process Explorer implementation)
