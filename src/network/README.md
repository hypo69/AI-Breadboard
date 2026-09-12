# Network & TShark Packet Analysis Module

This module provides packet capture, live streaming inspection, protocol decoding, and AI-driven network anomaly detection for AI-Breadboard using TShark (Wireshark CLI engine).

## Features
- **TShark Engine Wrapper**: Auto-discovers `tshark.exe`, interfaces (`-D`), pcap reading (`-T json`), and async live streaming.
- **Protocol & Traffic Analytics**: Protocol distributions, top talkers, flow bandwidth and error metrics.
- **AI Diagnostics**: Packet explanation and anomaly detection using AI-Breadboard intelligence layers.
- **FastAPI Endpoints & WebSocket**: Real-time traffic ingestion, capture management, and web streaming.
