# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Network Traffic and Packet Analysis Router
# =============================================================================
# Description:
#   FastAPI HTTP and WebSocket endpoints for listing capture interfaces,
#   reading PCAP captures, streaming live TShark packets, and running AI anomaly analysis.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from src.api.router_network import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router_network.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router for TShark packet capture and traffic analysis."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from src.logger import logger
from src.network import (
    TSharkWrapper,
    TrafficAnalyzer,
    AIDetector,
    NetworkInterface,
    CaptureFilter,
    PacketSummary,
    TrafficStats,
    AnomalyReport,
)


class AnalyzeResponse(BaseModel):
    """Response payload for PCAP file analysis."""

    stats: TrafficStats
    heuristics: List[str]
    ai_report: AnomalyReport
    sample_packets: List[PacketSummary]


def init_router() -> APIRouter:
    """Initialize and configure Network Traffic router.

    Returns:
        APIRouter: Configured FastAPI router instance.
    """
    router = APIRouter(prefix="/api/v1/network", tags=["Network Analyzer"])
    wrapper = TSharkWrapper()
    analyzer = TrafficAnalyzer()
    ai_detector = AIDetector()

    @router.get("/status", response_model=Dict[str, Any])
    async def get_tshark_status() -> Dict[str, Any]:
        """Check availability and resolved binary path of TShark."""
        return {
            "available": wrapper.is_available(),
            "tshark_path": wrapper.tshark_path,
        }

    @router.get("/interfaces", response_model=List[NetworkInterface])
    async def list_interfaces() -> List[NetworkInterface]:
        """Retrieve available network capture interfaces."""
        if not wrapper.is_available():
            raise HTTPException(
                status_code=503,
                detail="TShark executable is not found on host. Please install Wireshark / TShark."
            )
        return wrapper.list_interfaces()

    @router.post("/analyze/pcap", response_model=AnalyzeResponse)
    async def analyze_pcap_file(
        file: UploadFile = File(...),
        display_filter: str = Form(default=""),
        max_packets: int = Form(default=500),
    ) -> AnalyzeResponse:
        """Upload and analyze a .pcap or .pcapng file."""
        if not wrapper.is_available():
            raise HTTPException(
                status_code=503,
                detail="TShark executable is not found on host."
            )

        # Save uploaded file to a temporary location
        suffix = Path(file.filename or "capture.pcap").suffix or ".pcap"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = Path(tmp_file.name)

        try:
            packets = wrapper.read_pcap(
                pcap_path=temp_path,
                display_filter=display_filter,
                max_packets=max_packets,
            )
            stats = analyzer.compute_stats(packets)
            heuristics = analyzer.detect_heuristics(packets)
            ai_report = await ai_detector.diagnose_traffic(packets, stats, heuristics)

            return AnalyzeResponse(
                stats=stats,
                heuristics=heuristics,
                ai_report=ai_report,
                sample_packets=packets[:50],
            )
        finally:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    @router.websocket("/ws/live")
    async def live_capture_ws(websocket: WebSocket) -> None:
        """WebSocket endpoint streaming live captured packets to connected client."""
        await websocket.accept()
        try:
            # Wait for client initial configuration JSON
            config_data = await websocket.receive_json()
            capture_filter = CaptureFilter(**config_data)

            if not wrapper.is_available():
                await websocket.send_json({"error": "TShark is not available on host."})
                await websocket.close()
                return

            async for packet in wrapper.live_capture_stream(capture_filter):
                await websocket.send_text(packet.model_dump_json())

        except WebSocketDisconnect:
            logger.info("Client disconnected from live network capture WebSocket.")
        except Exception as ex:
            logger.error("Error in live capture WebSocket stream", exc_info=True)
            try:
                await websocket.send_json({"error": str(ex)})
            except Exception:
                pass

    return router
