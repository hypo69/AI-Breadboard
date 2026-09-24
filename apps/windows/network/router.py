# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal FastAPI Router
# =============================================================================
# Description:
#   FastAPI endpoints for Windows network monitoring, real-time packet capture,
#   active connections, network adapters, traffic statistics, and AI anomaly detection.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.network.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Network Terminal."""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import psutil

from logger import logger
from src.api.router_auth import require_admin_user
from apps.common.csv_logger import AppCsvLogger
from apps.tshark import AIDetector, TSharkWrapper, TrafficAnalyzer
from .sensors import NetworkTerminalSensor
from .speedtest import NetworkSpeedTester
from .tui import NetworkTerminalState

router = APIRouter(prefix="/api/network", tags=["network"])
_csv_logger = AppCsvLogger("network_terminal")
_sensor = NetworkTerminalSensor()
_speedtester = NetworkSpeedTester()
_state: NetworkTerminalState | None = None
_latest_speedtest: Dict[str, Any] | None = None


def get_state() -> NetworkTerminalState:
    """Get or create the network terminal state instance."""
    global _state
    if _state is None:
        _state = NetworkTerminalState()
    return _state


def _get_process_name(pid: Optional[int]) -> str:
    """Safely resolve process name by PID."""
    if not pid or pid <= 4:
        return "System" if pid == 4 else "Idle"
    try:
        proc = psutil.Process(pid)
        return proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return f"PID {pid}"


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Get current network terminal status and summary."""
    state = get_state()
    state.evaluate_security()
    stats = state.compute_stats()
    
    tshark_avail = TSharkWrapper().is_available()
    
    # Active connections count
    conn_count = 0
    listen_count = 0
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.status == psutil.CONN_LISTEN:
                listen_count += 1
            elif c.status == psutil.CONN_ESTABLISHED:
                conn_count += 1
    except Exception:
        pass

    # Adapters count
    adapter_count = len(psutil.net_if_addrs())

    _csv_logger.log_poll(
        poll_type="network_status",
        metric_name="total_packets",
        value=state.total_packets_captured,
        unit="packets",
        status="OK",
        details={
            "interface": state.interface,
            "bytes": state.total_bytes_captured,
            "adapters": adapter_count,
            "established": conn_count,
            "listening": listen_count,
        },
        filename="network_terminal_status_polls.csv",
    )

    return {
        "available": True,
        "tshark_available": tshark_avail,
        "interface": state.interface,
        "filter": state.display_filter,
        "total_packets": state.total_packets_captured,
        "total_bytes": state.total_bytes_captured,
        "protocol_counts": state.protocol_counts,
        "latest_ai_report": state.latest_ai_report.model_dump() if state.latest_ai_report else None,
        "latest_heuristics": state.latest_heuristics,
        "total_adapters": adapter_count,
        "active_connections_count": conn_count,
        "listening_ports_count": listen_count,
    }


@router.get("/interfaces")
async def get_interfaces(request: Request) -> List[dict]:
    """Get detailed list of host network interfaces and adapters."""
    interfaces: List[dict] = []
    
    # 1. Native PowerShell/IP Helper adapters
    native_adapters = _sensor.get_network_adapters_native()
    native_map = {a.get("name", "").lower(): a for a in native_adapters if a.get("name")}
    
    # 2. psutil interface stats and addresses
    if_addrs = psutil.net_if_addrs()
    if_stats = psutil.net_if_stats()
    net_io = psutil.net_io_counters(pernic=True)

    idx = 1
    for iface_name, addrs in if_addrs.items():
        ipv4_list = []
        ipv6_list = []
        mac_addr = ""

        for addr in addrs:
            if addr.family == psutil.AF_LINK or str(addr.family).endswith("AF_LINK"):
                mac_addr = addr.address
            elif str(addr.family) in ("AddressFamily.AF_INET", "2"):
                ipv4_list.append(addr.address)
            elif str(addr.family) in ("AddressFamily.AF_INET6", "23"):
                ipv6_list.append(addr.address)

        stat = if_stats.get(iface_name)
        io = net_io.get(iface_name)
        native_item = native_map.get(iface_name.lower(), {})

        is_up = stat.isup if stat else True
        speed_mbps = stat.speed if stat and stat.speed > 0 else native_item.get("speed_mbps", 0)
        description = native_item.get("description") or iface_name

        interfaces.append({
            "id": str(idx),
            "name": iface_name,
            "description": description,
            "status": "Up" if is_up else "Down",
            "is_up": is_up,
            "speed_mbps": speed_mbps,
            "mac": mac_addr or native_item.get("mac", ""),
            "ipv4": ipv4_list,
            "ipv6": ipv6_list,
            "bytes_sent": io.bytes_sent if io else 0,
            "bytes_recv": io.bytes_recv if io else 0,
            "packets_sent": io.packets_sent if io else 0,
            "packets_recv": io.packets_recv if io else 0,
        })
        idx += 1

    return interfaces


@router.get("/connections")
async def get_connections(request: Request, limit: int = 150) -> dict:
    """Get active network connections and listening ports with process info."""
    connections: List[dict] = []
    listening_ports: List[dict] = []

    try:
        raw_conns = psutil.net_connections(kind="inet")
        for c in raw_conns:
            laddr_str = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
            raddr_str = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
            proto = "TCP" if c.type == 1 else ("UDP" if c.type == 2 else "RAW")
            proc_name = _get_process_name(c.pid)

            item = {
                "fd": c.fd,
                "protocol": proto,
                "local_address": laddr_str,
                "remote_address": raddr_str,
                "status": c.status,
                "pid": c.pid,
                "process_name": proc_name,
            }

            if c.status == psutil.CONN_LISTEN:
                listening_ports.append(item)
            else:
                connections.append(item)
    except Exception as ex:
        logger.debug(f"psutil net_connections error: {ex}")
        # Fallback to sensor native powershell
        native_listening = _sensor.get_listening_ports_native()
        for p in native_listening:
            listening_ports.append({
                "protocol": "TCP",
                "local_address": f"{p.get('ip', '0.0.0.0')}:{p.get('port', 0)}",
                "remote_address": "-",
                "status": "LISTEN",
                "pid": p.get("pid"),
                "process_name": p.get("process") or _get_process_name(p.get("pid")),
            })

    return {
        "connections": connections[:limit],
        "listening_ports": listening_ports[:limit],
        "total_connections": len(connections),
        "total_listening": len(listening_ports),
    }


@router.get("/telemetry")
async def get_telemetry(request: Request) -> dict:
    """Get real-time network throughput and sensor rates."""
    sensors = _sensor.get_network_sensors()
    return {
        "sensors": [
            {
                "sensor_id": s.sensor_id,
                "name": s.name,
                "category": s.category,
                "value": s.value,
                "unit": s.unit,
            }
            for s in sensors
        ]
    }


@router.get("/packets")
async def get_packets(request: Request, limit: int = 50) -> dict:
    """Get last captured packets from the buffer."""
    state = get_state()
    packets = list(state.packet_buffer)[-limit:]
    
    return {
        "packets": [
            {
                "packet_number": p.packet_number,
                "timestamp": p.timestamp,
                "source": p.source,
                "destination": p.destination,
                "protocol": p.protocol,
                "length": p.length,
                "source_port": p.source_port,
                "destination_port": p.destination_port,
                "info": p.info,
            }
            for p in packets
        ]
    }


@router.get("/packets/stream")
async def stream_packets(request: Request):
    """Stream packets in real-time via SSE."""
    state = get_state()
    
    async def event_generator():
        while True:
            packets = list(state.packet_buffer)[-10:]
            if packets:
                yield f"data: {len(packets)} new packets\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/stats")
async def get_stats(request: Request) -> dict:
    """Get traffic statistics."""
    state = get_state()
    stats = state.compute_stats()
    avg_packet_size = round(stats.total_bytes / stats.total_packets, 2) if stats.total_packets > 0 else 0.0

    return {
        "total_packets": stats.total_packets,
        "total_bytes": stats.total_bytes,
        "avg_packet_size": avg_packet_size,
        "avg_bps": 0.0,
        "avg_pps": 0.0,
        "top_protocols": stats.protocol_distribution,
        "top_sources": stats.top_sources,
        "top_destinations": stats.top_destinations,
    }


@router.get("/security")
async def get_security(request: Request) -> dict:
    """Get security analysis results."""
    state = get_state()
    state.evaluate_security()
    
    return {
        "heuristics": state.latest_heuristics,
        "ai_report": state.latest_ai_report.model_dump() if state.latest_ai_report else None,
    }


@router.post("/speedtest/run")
@router.get("/speedtest/run")
async def run_speedtest(request: Request) -> dict:
    """Run full internet speed, ping, jitter, download, and upload benchmark."""
    global _latest_speedtest
    report = await _speedtester.run_full_speedtest()
    _latest_speedtest = report
    return report


@router.get("/speedtest/latest")
async def get_latest_speedtest(request: Request) -> dict:
    """Get latest cached speedtest report."""
    global _latest_speedtest
    if _latest_speedtest is None:
        return {"status": "NO_DATA", "message": "Тест скорости еще не запускался."}
    return _latest_speedtest


@router.get("/speedtest/ping")
async def ping_servers(request: Request) -> dict:
    """Quick ping latency probe to global DNS and CDN edge servers."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        servers = await _speedtester.measure_ping_servers(client)
        meta = await _speedtester.get_meta_info(client)
        return {
            "timestamp": time.time(),
            "meta": meta,
            "servers": servers,
        }


@router.post("/start-capture")
async def start_capture(
    request: Request,
    interface: str = "1",
    display_filter: str = "",
) -> dict:
    """Start network capture (admin only)."""
    require_admin_user(request)
    global _state
    _state = NetworkTerminalState(interface=interface, display_filter=display_filter)
    _csv_logger.log_event(
        event_type="start_capture",
        status="SUCCESS",
        details={"interface": interface, "filter": display_filter},
        filename="network_terminal_events.csv",
    )
    return {
        "success": True,
        "message": f"Capture started on interface {interface}",
    }


@router.post("/stop-capture")
async def stop_capture(request: Request) -> dict:
    """Stop network capture (admin only)."""
    require_admin_user(request)
    global _state
    _state = None
    _csv_logger.log_event(
        event_type="stop_capture",
        status="SUCCESS",
        details="Capture stopped",
        filename="network_terminal_events.csv",
    )
    return {
        "success": True,
        "message": "Capture stopped",
    }


@router.post("/analyze/pcap")
async def analyze_pcap(
    request: Request,
    file: UploadFile = File(...),
    max_packets: int = 500,
) -> dict:
    """Analyze uploaded PCAP file via TSharkWrapper and AIDetector."""
    wrapper = TSharkWrapper()
    if not wrapper.is_available():
        return {
            "error": "TShark is not installed on this system",
            "stats": {"total_packets": 0, "total_bytes": 0},
            "heuristics": ["TShark executable not available on host"],
            "ai_report": {"health_score": 100, "anomalies": []},
            "sample_packets": [],
        }

    suffix = os.path.splitext(file.filename or "sample.pcap")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        packets = wrapper.read_pcap(tmp_path, max_packets=max_packets)
        analyzer = TrafficAnalyzer()
        stats = analyzer.compute_stats(packets)
        heuristics = analyzer.detect_heuristics(packets)
        
        detector = AIDetector()
        ai_report = await detector.diagnose_traffic(packets, stats, heuristics)

        return {
            "stats": {
                "total_packets": stats.total_packets,
                "total_bytes": stats.total_bytes,
                "protocol_distribution": stats.protocol_distribution,
                "top_sources": stats.top_sources,
                "top_destinations": stats.top_destinations,
            },
            "heuristics": heuristics,
            "ai_report": ai_report.model_dump() if ai_report else None,
            "sample_packets": [
                {
                    "number": p.number,
                    "timestamp": p.timestamp,
                    "source": p.source_ip,
                    "destination": p.destination_ip,
                    "protocol": p.protocol,
                    "length": p.length,
                    "info": p.info,
                }
                for p in packets[:100]
            ],
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def init_router() -> APIRouter:
    """Initialize the FastAPI router for Network Terminal."""
    return router


__all__ = [
    "init_router",
    "router",
]
