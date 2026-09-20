# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal FastAPI Router
# =============================================================================
# Description:
#   FastAPI endpoints for network monitoring, real-time packet capture,
#   traffic statistics, protocol distribution, and AI security anomaly detection.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.network_terminal.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Network Terminal."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Request
from src.api.router_auth import require_admin_user
from apps.common.csv_logger import AppCsvLogger

from .tui import NetworkTerminalState

router = APIRouter(prefix="/api/network", tags=["network"])
_csv_logger = AppCsvLogger("network_terminal")
_state: NetworkTerminalState | None = None



def get_state() -> NetworkTerminalState:
    """Get or create the network terminal state instance."""
    global _state
    if _state is None:
        _state = NetworkTerminalState()
    return _state


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Get current network terminal status."""
    state = get_state()
    state.evaluate_security()
    stats = state.compute_stats()
    
    _csv_logger.log_poll(
        poll_type="network_status",
        metric_name="total_packets",
        value=state.total_packets_captured,
        unit="packets",
        status="OK",
        details={"interface": state.interface, "bytes": state.total_bytes_captured},
        filename="network_terminal_status_polls.csv",
    )

    return {
        "interface": state.interface,
        "filter": state.display_filter,
        "total_packets": state.total_packets_captured,
        "total_bytes": state.total_bytes_captured,
        "protocol_counts": state.protocol_counts,
        "latest_ai_report": state.latest_ai_report.model_dump() if state.latest_ai_report else None,
        "latest_heuristics": state.latest_heuristics,
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
    
    return {
        "total_packets": stats.total_packets,
        "total_bytes": stats.total_bytes,
        "avg_packet_size": stats.avg_packet_size,
        "avg_bps": stats.avg_bps,
        "avg_pps": stats.avg_pps,
        "top_protocols": stats.top_protocols,
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



def init_router() -> APIRouter:
    """Initialize the FastAPI router for Network Terminal."""
    return router


__all__ = [
    "init_router",
    "router",
]
