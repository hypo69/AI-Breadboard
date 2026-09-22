# TShark Network Packet Analysis App

This app provides packet capture, live streaming inspection, protocol decoding, and AI-driven network anomaly detection for AI-Breadboard using TShark (Wireshark CLI engine).

## Features
- **TShark Engine Wrapper**: Auto-discovers `tshark.exe`, interfaces (`-D`), pcap reading (`-T json`), and async live streaming.
- **Protocol & Traffic Analytics**: Protocol distributions, top talkers, flow bandwidth and error metrics.
- **AI Diagnostics**: Packet explanation and anomaly detection using AI-Breadboard intelligence layers.
- **FastAPI Endpoints & WebSocket**: Real-time traffic ingestion, capture management, and web streaming.
- **Hardware Sensors**: Real-time packet metrics and capture status sensors for system telemetry.

## Requirements
- TShark (Wireshark CLI) installed on the system
- Npcap driver for live packet capture on Windows

## Usage
```python
from apps.tshark import TSharkWrapper, TrafficAnalyzer, AIDetector, get_tshark_sensors, TSharkTelemetryCollector

# Initialize wrapper
tshark = TSharkWrapper()

# List available interfaces
interfaces = tshark.list_interfaces()

# Read PCAP file
packets = tshark.read_pcap("capture.pcap")

# Analyze traffic
analyzer = TrafficAnalyzer()
stats = analyzer.compute_stats(packets)

# AI diagnostics
import asyncio
detector = AIDetector()
report = asyncio.run(detector.diagnose_traffic(packets, stats, []))

# Get hardware sensors
sensors = get_tshark_sensors(packets, wrapper_available=True, interface="1", is_capturing=True)
for sensor in sensors:
    print(f"{sensor.name}: {sensor.value} {sensor.unit}")

# Use telemetry collector
collector = TSharkTelemetryCollector()
collector.set_capture_state(wrapper_available=True, interface="1", is_capturing=True)
collector.set_packets(packets)
snapshot = collector.get_snapshot()
```

## Sensors

The app provides real-time network packet sensors that integrate with AI-Breadboard's telemetry system:

### Packet Metrics Sensors
- `pkt_total` - Total packets captured
- `pkt_bytes_total` - Total bytes captured
- `pkt_avg_size` - Average packet size
- `pkt_rate` - Packet capture rate (pkt/s)
- `pkt_proto_{PROTOCOL}` - Packet count per protocol (e.g., pkt_proto_TCP, pkt_proto_HTTP)

### Capture Status Sensors
- `tshark_available` - TShark binary availability (1.0 = available, 0.0 = not available)
- `capture_interface` - Current capture interface
- `capture_active` - Capture session status (1.0 = active, 0.0 = inactive)

### Integration with System Telemetry
```python
from apps.tshark import get_tshark_sensors
from apps.windows.telemetry.sensors import get_hardware_sensors

# Combine all sensors
all_sensors = get_hardware_sensors()
all_sensors.extend(get_tshark_sensors(packets, wrapper_available=True))
```
