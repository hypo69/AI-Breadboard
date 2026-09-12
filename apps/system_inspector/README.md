# System & Hardware Inspector Application (`apps/system_inspector`)

An interactive system telemetry monitor combining **AIDA64-grade hardware inspection** with **Wireshark-style real-time process streaming** and **AI performance diagnostics**.

## Features
- **Wireshark-Style Live Process Stream**: Real-time scrolling table tracking PID, process binary, CPU%, Memory MB/%, thread count, user ownership, and disk I/O.
- **AIDA64 Hardware Specification Tree**: Deep breakdown of Host, Motherboard, BIOS, CPU Cores/Threads/Frequencies, GPU Accelerators (CUDA/DirectML), Storage Drives, and Network Adapters.
- **Thermal & Voltage Sensors**: Dynamic integration with NVIDIA SMI, Windows ACPI thermal zones, and LibreHardwareMonitor/OpenHardwareMonitor.
- **AI Performance Copilot**: Heuristic anomaly detector with optional LLM reasoning for bottleneck diagnosis and optimization suggestions.
- **FastAPI REST & WebSocket API**: Full integration with the AI Breadboard web platform.

## CLI Usage

### Interactive Terminal TUI
```powershell
# Launch default live dashboard (1s refresh, sorted by CPU)
py -m apps.system_inspector

# Sort by memory with 2-second interval
py -m apps.system_inspector --sort memory --interval 2.0
```

### One-Shot Commands
```powershell
# AI Performance Diagnosis Audit
py -m apps.system_inspector --diagnose

# Dump AIDA64 Hardware Specification Tree
py -m apps.system_inspector --hardware

# Dump Snapshot JSON
py -m apps.system_inspector --json
```

## REST & WebSocket API
The application is automatically mounted on the FastAPI server:
- `GET /api/v1/system/summary` - Snapshot of system state.
- `GET /api/v1/system/processes` - Active process stream.
- `GET /api/v1/system/hardware` - Complete hardware device tree.
- `GET /api/v1/system/sensors` - Thermal and sensor metrics.
- `POST /api/v1/system/diagnose` - AI performance audit report.
- `WS /api/v1/system/stream` - Live WebSocket telemetry feed.
