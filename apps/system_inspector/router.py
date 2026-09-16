# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector FastAPI Router
# =============================================================================
# Description:
#   FastAPI endpoints for system telemetry, hardware monitoring, process streams,
#   AI performance diagnostics, and hardware specification queries.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.system_inspector.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for System Inspector."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request
from src.api.router_auth import require_admin_user

from src.system import (
    SystemAIDiagnostician,
    SystemCollector,
)

router = APIRouter(prefix="/api/system", tags=["system"])
_collector: SystemCollector | None = None
_diagnostician: SystemAIDiagnostician | None = None


def get_collector() -> SystemCollector:
    """Get or create the system collector instance."""
    global _collector
    if _collector is None:
        _collector = SystemCollector()
    return _collector


def get_diagnostician() -> SystemAIDiagnostician:
    """Get or create the system diagnostician instance."""
    global _diagnostician
    if _diagnostician is None:
        _diagnostician = SystemAIDiagnostician()
    return _diagnostician


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Get current system status."""
    collector = get_collector()
    snapshot = collector.get_snapshot(process_limit=15)
    
    return {
        "hostname": snapshot.hostname,
        "os_name": snapshot.os_name,
        "uptime_seconds": snapshot.uptime_seconds,
        "cpu": snapshot.cpu.model_dump(),
        "memory": snapshot.memory.model_dump(),
        "process_count": len(snapshot.top_processes),
    }


@router.get("/processes")
async def get_processes(request: Request, limit: int = 20, sort_by: str = "cpu") -> dict:
    """Get top processes."""
    collector = get_collector()
    snapshot = collector.get_snapshot(process_limit=limit)
    
    processes = []
    for p in snapshot.top_processes:
        processes.append({
            "pid": p.pid,
            "name": p.name,
            "status": p.status,
            "cpu_percent": p.cpu_percent,
            "memory_mb": p.memory_mb,
            "memory_percent": p.memory_percent,
            "num_threads": p.num_threads,
            "username": p.username,
        })
    
    return {
        "processes": processes,
        "sort_by": sort_by,
    }


@router.get("/hardware")
async def get_hardware(request: Request) -> dict:
    """Get hardware specification tree."""
    collector = get_collector()
    nodes = collector.get_hardware_tree()
    sensors = collector.get_hardware_sensors()
    
    hardware = []
    for node in nodes:
        hardware.append({
            "category": node.category,
            "name": node.name,
            "properties": node.properties,
        })
    
    sensors_list = []
    for s in sensors:
        sensors_list.append({
            "name": s.name,
            "value": s.value,
            "unit": s.unit,
        })
    
    return {
        "hardware": hardware,
        "sensors": sensors_list,
    }


@router.get("/diagnostic")
async def get_diagnostic(request: Request, process_limit: int = 20) -> dict:
    """Get AI system diagnostic report."""
    collector = get_collector()
    diagnostician = get_diagnostician()
    
    snapshot = collector.get_snapshot(process_limit=process_limit)
    score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)
    
    return {
        "health_score": score,
        "summary": f"System Health: {score}/100. Telemetry stream nominal.",
        "ai_model_used": "Heuristic Monitor",
        "anomalies": [
            {
                "title": a.title,
                "description": a.description,
                "severity": a.severity,
            }
            for a in anomalies
        ],
        "recommendations": recommendations,
    }


@router.get("/hardware/tree")
async def get_hardware_tree(request: Request) -> dict:
    """Get AIDA64-style hardware tree."""
    collector = get_collector()
    nodes = collector.get_hardware_tree()
    
    tree = []
    for node in nodes:
        tree.append({
            "category": node.category,
            "name": node.name,
            "properties": node.properties,
        })
    
    return {"tree": tree}


@router.get("/hardware/sensors")
async def get_hardware_sensors(request: Request) -> dict:
    """Get active hardware sensors."""
    collector = get_collector()
    sensors = collector.get_hardware_sensors()
    
    return {
        "sensors": [
            {
                "name": s.name,
                "value": s.value,
                "unit": s.unit,
            }
            for s in sensors
        ]
    }


@router.post("/trigger-diagnostic")
async def trigger_diagnostic(request: Request, process_limit: int = 20) -> dict:
    """Trigger a one-shot AI diagnostic (admin only)."""
    require_admin_user(request)
    collector = get_collector()
    diagnostician = get_diagnostician()
    
    snapshot = collector.get_snapshot(process_limit=process_limit)
    score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)
    
    return {
        "success": True,
        "health_score": score,
        "anomalies_count": len(anomalies),
        "recommendations_count": len(recommendations),
    }


def init_router() -> APIRouter:
    """Initialize the FastAPI router for System Inspector."""
    return router


__all__ = [
    "init_router",
    "router",
]
