# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cloudflared Monitor FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST endpoints for Cloudflare Tunnel monitoring, telemetry, log tails,
#   public endpoint probing, AI health diagnostics, and daemon lifecycle control.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.cloudflared_monitor.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.cloudflared_monitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Cloudflared Monitor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from src.api.router_auth import require_admin_user
from .src.state import CloudflaredState

router = APIRouter(prefix="/api/cloudflared", tags=["cloudflared"])
_state: Optional[CloudflaredState] = None


def get_state() -> CloudflaredState:
    """Get or create the singleton CloudflaredState instance.

    Returns:
        CloudflaredState: Active state instance.
    """
    global _state
    if _state is None:
        _state = CloudflaredState()
    return _state


@router.get("/status")
async def get_status(request: Request) -> Dict[str, Any]:
    """Get overall status and telemetry of Cloudflare Tunnel.

    Returns:
        Dict[str, Any]: Tunnel process state, token status, endpoint reachability.
    """
    state = get_state()
    state.refresh(probe_network=False)

    return {
        "is_running": state.process.is_running,
        "pid": state.process.pid,
        "uptime_seconds": state.process.uptime_seconds,
        "cpu_percent": state.process.cpu_percent,
        "memory_mb": state.process.memory_mb,
        "memory_percent": state.process.memory_percent,
        "num_threads": state.process.num_threads,
        "has_token": state.has_token,
        "token_preview": state.token_preview,
        "exe_path": state.exe_path,
        "public_url": state.public_url,
        "endpoint_reachable": state.endpoint.is_reachable,
        "endpoint_status_code": state.endpoint.status_code,
        "endpoint_latency_ms": state.endpoint.response_time_ms,
        "active_connections": state.active_connections_count,
        "total_errors": state.total_errors_in_log,
        "total_warnings": state.total_warnings_in_log,
        "health_score": state.report.health_score if state.report else 0,
        "health_status": state.report.status if state.report else "UNKNOWN",
        "last_refreshed": state.last_refreshed,
    }


@router.get("/logs")
async def get_logs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    level: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve recent parsed log records from cloudflared.log.

    Args:
        request: Incoming FastAPI request.
        limit: Max log entries to return.
        level: Optional log level filter (e.g. ERROR, WARN, INFO).
        search: Optional case-insensitive text search.

    Returns:
        Dict[str, Any]: Filtered log records and error summary.
    """
    state = get_state()
    entries = state.tail_logs(limit=limit)

    if level:
        lvl_upper = level.upper()
        entries = [e for e in entries if e.level == lvl_upper]

    if search:
        s_lower = search.lower()
        entries = [e for e in entries if s_lower in e.message.lower() or s_lower in e.raw.lower()]

    return {
        "count": len(entries),
        "total_errors": state.total_errors_in_log,
        "total_warnings": state.total_warnings_in_log,
        "logs": [
            {
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
                "connection_id": e.connection_id,
                "raw": e.raw,
            }
            for e in entries
        ],
    }


@router.get("/metrics")
async def get_metrics(request: Request) -> Dict[str, Any]:
    """Retrieve detailed process and network telemetry metrics.

    Returns:
        Dict[str, Any]: Numerical metrics for graphs and dashboards.
    """
    state = get_state()
    state.refresh(probe_network=False)

    return {
        "process": {
            "is_running": state.process.is_running,
            "pid": state.process.pid,
            "cpu_percent": state.process.cpu_percent,
            "memory_mb": state.process.memory_mb,
            "memory_percent": state.process.memory_percent,
            "threads": state.process.num_threads,
            "uptime_seconds": state.process.uptime_seconds,
        },
        "network": {
            "public_url": state.public_url,
            "is_reachable": state.endpoint.is_reachable,
            "status_code": state.endpoint.status_code,
            "latency_ms": state.endpoint.response_time_ms,
            "last_checked": state.endpoint.last_checked,
        },
        "log_stats": {
            "errors": state.total_errors_in_log,
            "warnings": state.total_warnings_in_log,
            "active_connectors": state.active_connections_count,
        },
    }


@router.get("/diagnostic")
async def get_diagnostic(request: Request) -> Dict[str, Any]:
    """Get AI and heuristic health diagnostics for the Cloudflare tunnel.

    Returns:
        Dict[str, Any]: Health score, status, anomalies, and recommendations.
    """
    state = get_state()
    state.refresh(probe_network=False)
    report = state.evaluate_diagnostics()

    return {
        "health_score": report.health_score,
        "status": report.status,
        "summary": report.summary,
        "anomalies": [
            {
                "title": a.title,
                "description": a.description,
                "severity": a.severity,
            }
            for a in report.anomalies
        ],
        "recommendations": report.recommendations,
        "evaluated_at": report.evaluated_at,
    }


@router.post("/test-endpoint")
async def test_endpoint(request: Request) -> Dict[str, Any]:
    """Perform live HTTP probe against public tunnel URL.

    Returns:
        Dict[str, Any]: Fresh reachability and latency report.
    """
    state = get_state()
    health = state.probe_endpoint()

    return {
        "url": health.url,
        "is_reachable": health.is_reachable,
        "status_code": health.status_code,
        "response_time_ms": health.response_time_ms,
        "error_message": health.error_message,
        "last_checked": health.last_checked,
    }


@router.post("/start")
async def start_tunnel(request: Request) -> Dict[str, Any]:
    """Launch the cloudflared tunnel daemon (admin only)."""
    require_admin_user(request)
    state = get_state()
    success, msg = state.start_tunnel()
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"success": True, "message": msg}


@router.post("/stop")
async def stop_tunnel(request: Request) -> Dict[str, Any]:
    """Stop the cloudflared tunnel daemon (admin only)."""
    require_admin_user(request)
    state = get_state()
    success, msg = state.stop_tunnel()
    return {"success": True, "message": msg}


@router.post("/restart")
async def restart_tunnel(request: Request) -> Dict[str, Any]:
    """Restart the cloudflared tunnel daemon (admin only)."""
    require_admin_user(request)
    state = get_state()
    success, msg = state.restart_tunnel()
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"success": True, "message": msg}


def init_router() -> APIRouter:
    """Initialize and return the FastAPI router for Cloudflared Monitor.

    Returns:
        APIRouter: Configured router instance.
    """
    return router


__all__ = [
    "init_router",
    "router",
    "get_state",
]
