# System & Hardware Telemetry Engine (`src/system`)

A unified telemetry collection, sensor probing, and AI diagnostics subsystem for **AI-Breadboard**.

## Overview
- **Zero-Dependency Baseline**: Extracts comprehensive CPU, RAM, Disk I/O, Network, and Process table telemetry via `psutil` and standard Windows WMI/CIM.
- **Deep Sensor Integration**: Dynamically attaches to LibreHardwareMonitor/OpenHardwareMonitor WMI namespaces and NVIDIA SMI without requiring proprietary drivers.
- **AIDA64-Grade Device Tree**: Constructs hierarchical hardware specifications for CPU, Motherboard, GPU, RAM, Storage volumes, and Network adapters.
- **AI Performance Copilot**: Heuristic anomaly analysis with local/cloud LLM diagnosis for identifying system lag, thermal spikes, and runaway processes.

## Components
| Module | Description |
| :--- | :--- |
| `models.py` | Pydantic data schemas for hardware metrics, snapshots, and diagnostic reports. |
| `sensors.py` | Multi-backend hardware sensor prober (NVIDIA SMI, WMI ACPI, LibreHardwareMonitor). |
| `collector.py` | `SystemCollector` for gathering live point-in-time snapshots and hardware trees. |
| `ai_diagnostics.py` | `SystemAIDiagnostician` for rule-based and AI-driven performance audits. |

## Usage
```python
from src.system import SystemCollector, SystemAIDiagnostician

collector = SystemCollector()
snapshot = collector.get_snapshot()

print(f"CPU Load: {snapshot.cpu.total_percent}%")
print(f"RAM Used: {snapshot.memory.used_gb} / {snapshot.memory.total_gb} GB")

diagnostician = SystemAIDiagnostician()
score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)
print(f"Health Score: {score}/100")
```
