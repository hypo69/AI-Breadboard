# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector Router (apps.windows)
# =============================================================================
# Description:
#   FastAPI роутер системного инспектора телеметрии, аппаратного обеспечения
#   и отчетов AI диагностики в составе модуля apps.windows.
#
# File: system_inspector_router.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер системного инспектора в составе пакета apps.windows."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request

from src.api.router_auth import require_admin_user
from apps.common.csv_logger import AppCsvLogger
from apps.windows.telemetry import (
    SystemDiagnosticEngine as SystemAIDiagnostician,
    SystemCollector,
)

router = APIRouter(prefix="/api/system", tags=["system-inspector"])
_csv_logger = AppCsvLogger("system_inspector")
_collector: Optional[SystemCollector] = None
_diagnostician: Optional[SystemAIDiagnostician] = None


def get_collector() -> SystemCollector:
    """Получить или создать объект синглтона сборщика телеметрии."""
    global _collector
    if _collector is None:
        _collector = SystemCollector()
    return _collector


def get_diagnostician() -> SystemAIDiagnostician:
    """Получить или создать объект синглтона AI диагностика."""
    global _diagnostician
    if _diagnostician is None:
        _diagnostician = SystemAIDiagnostician()
    return _diagnostician


@router.get("/status")
async def get_status(request: Request) -> Dict[str, Any]:
    """Получение текущего состояния системы и загрузки ресурсов."""
    collector = get_collector()
    snapshot = await collector.get_snapshot(process_limit=15)

    _csv_logger.log_poll(
        poll_type="status",
        metric_name="system_snapshot",
        value=f"cpu={snapshot.cpu.total_percent}%,mem={snapshot.memory.percent}%",
        unit="summary",
        status="ok",
        details=f"hostname={snapshot.hostname},processes={len(snapshot.top_processes)}",
        filename="system_inspector_polls.csv",
    )

    return {
        "hostname": snapshot.hostname,
        "os_name": snapshot.os_name,
        "uptime_seconds": snapshot.uptime_seconds,
        "cpu": snapshot.cpu.model_dump(),
        "memory": snapshot.memory.model_dump(),
        "process_count": len(snapshot.top_processes),
    }


@router.get("/processes")
async def get_processes(request: Request, limit: int = 20, sort_by: str = "cpu") -> Dict[str, Any]:
    """Получение списка активных процессов с деталями по ресурсам."""
    collector = get_collector()
    snapshot = await collector.get_snapshot(process_limit=limit)

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

    _csv_logger.log_poll(
        poll_type="processes",
        metric_name="top_processes_count",
        value=len(processes),
        unit="count",
        status="ok",
        details=f"limit={limit},sort_by={sort_by}",
        filename="system_inspector_polls.csv",
    )

    return {
        "processes": processes,
        "sort_by": sort_by,
    }


@router.get("/hardware")
async def get_hardware(request: Request) -> Dict[str, Any]:
    """Получение полного дерева спецификации оборудования и активных датчиков."""
    collector = get_collector()
    nodes = await collector.get_hardware_tree_async()
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

    _csv_logger.log_poll(
        poll_type="hardware",
        metric_name="hardware_nodes_count",
        value=len(hardware),
        unit="count",
        status="ok",
        details=f"sensors_count={len(sensors_list)}",
        filename="system_inspector_polls.csv",
    )

    return {
        "hardware": hardware,
        "sensors": sensors_list,
    }


@router.get("/diagnostic")
async def get_diagnostic(request: Request, process_limit: int = 20) -> Dict[str, Any]:
    """Получение AI отчета эвристической диагностики системы."""
    collector = get_collector()
    diagnostician = get_diagnostician()

    snapshot = await collector.get_snapshot(process_limit=process_limit)
    score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)

    _csv_logger.log_event(
        event_type="diagnostic_report",
        status="ok",
        details=f"health_score={score},anomalies={len(anomalies)},recs={len(recommendations)}",
        filename="system_inspector_events.csv",
    )

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
async def get_hardware_tree(request: Request) -> Dict[str, Any]:
    """Получение иерархического дерева оборудования в стиле AIDA64."""
    collector = get_collector()
    nodes = await collector.get_hardware_tree_async()

    tree = []
    for node in nodes:
        tree.append({
            "category": node.category,
            "name": node.name,
            "properties": node.properties,
        })

    return {"tree": tree}


@router.get("/hardware/sensors")
async def get_hardware_sensors(request: Request) -> Dict[str, Any]:
    """Получение мгновенных показаний системных датчиков."""
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
async def trigger_diagnostic(request: Request, process_limit: int = 20) -> Dict[str, Any]:
    """Ручной запуск разовой AI диагностики (требуются права администратора)."""
    require_admin_user(request)
    collector = get_collector()
    diagnostician = get_diagnostician()

    snapshot = await collector.get_snapshot(process_limit=process_limit)
    score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)

    _csv_logger.log_event(
        event_type="trigger_diagnostic",
        status="ok",
        details=f"health_score={score},anomalies_count={len(anomalies)},recommendations_count={len(recommendations)}",
        filename="system_inspector_events.csv",
    )

    return {
        "success": True,
        "health_score": score,
        "anomalies_count": len(anomalies),
        "recommendations_count": len(recommendations),
    }


def init_router() -> APIRouter:
    """Инициализация роутера системного инспектора."""
    return router


__all__ = [
    "init_router",
    "router",
]
