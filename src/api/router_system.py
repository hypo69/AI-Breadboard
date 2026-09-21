# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI System and Hardware Telemetry Router
# =============================================================================
# Description:
#   FastAPI REST and WebSocket endpoints for live system snapshots, hardware
#   trees, process monitoring, and AI diagnostic reports.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from src.api.router_system import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router_system.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router for system telemetry, hardware inspection, and AI diagnosis."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.logger import logger
from apps.windows.telemetry import (
    # (используйте src.ai.observability.system_engine для SystemDiagnosticEngine)

    HardwareNode,
    HardwareSensor,
    ProcessMetrics,
    SystemDiagnosticEngine,
    SystemCollector,
    SystemDiagnosticReport,
    SystemSnapshot,
    TelemetryLoggerService,
    TelemetryStorage,
)


def init_router(chat_model: Optional[Any] = None) -> APIRouter:
    """Initialize and configure System and Hardware Inspector router.

    Args:
        chat_model: Optional UnifiedChatModel instance for AI telemetry diagnosis.

    Returns:
        APIRouter: Configured FastAPI router instance.
    """
    router = APIRouter(prefix="/api/v1/system", tags=["System & Hardware Inspector"])
    collector = SystemCollector()
    diagnostician = SystemDiagnosticEngine(chat_model=chat_model)
    telemetry_service = TelemetryLoggerService.get_instance()
    storage = telemetry_service.storage

    @router.get("/summary", response_model=SystemSnapshot)
    async def get_system_summary(
        process_limit: int = Query(default=20, ge=1, le=100, description="Top processes count")
    ) -> SystemSnapshot:
        """Retrieve live system load, hardware telemetry, and top processes snapshot."""
        return await collector.get_snapshot(process_limit=process_limit)

    @router.get("/processes", response_model=List[ProcessMetrics])
    async def list_processes(
        limit: int = Query(default=50, ge=1, le=200, description="Max processes count"),
        sort_by: str = Query(default="cpu", pattern="^(cpu|memory)$", description="Sort criteria"),
    ) -> List[ProcessMetrics]:
        """Retrieve active process stream sorted by CPU or memory consumption."""
        return collector.get_top_processes(limit=limit, sort_by=sort_by)

    @router.get("/hardware", response_model=List[HardwareNode])
    async def get_hardware_tree() -> List[HardwareNode]:
        """Retrieve AIDA64-like hierarchical component specification tree."""
        return await collector.get_hardware_tree_async()

    @router.get("/sensors", response_model=List[HardwareSensor])
    async def get_sensors() -> List[HardwareSensor]:
        """Retrieve thermal, fan, and voltage sensor readings."""
        from apps.windows.telemetry.sensors import get_hardware_sensors

        return get_hardware_sensors()

    @router.post("/diagnose", response_model=SystemDiagnosticReport)
    async def run_ai_diagnostics(
        snapshot: Optional[SystemSnapshot] = None,
    ) -> SystemDiagnosticReport:
        """Perform AI and heuristic performance audit on system telemetry."""
        target_snapshot = snapshot or await collector.get_snapshot()
        return await diagnostician.diagnose(target_snapshot)

    # =========================================================================
    # Посекундный логгер телеметрии и история SQLite
    # =========================================================================

    @router.post("/logger/start")
    async def start_telemetry_logger(
        interval_sec: float = Query(default=1.0, ge=0.2, le=60.0, description="Интервал сбора в секундах"),
        top_processes: int = Query(default=20, ge=1, le=100, description="Количество Top-процессов"),
    ) -> Dict[str, Any]:
        """Запуск фонового сбора телеметрии в SQLite."""
        telemetry_service.interval_sec = interval_sec
        telemetry_service.top_processes = top_processes
        started = telemetry_service.start()
        return {
            "success": True,
            "started": started,
            "status": telemetry_service.get_status(),
        }

    @router.post("/logger/stop")
    async def stop_telemetry_logger() -> Dict[str, Any]:
        """Остановка фонового сбора телеметрии."""
        stopped = telemetry_service.stop()
        return {
            "success": True,
            "stopped": stopped,
            "status": telemetry_service.get_status(),
        }

    @router.get("/logger/status")
    async def get_telemetry_logger_status() -> Dict[str, Any]:
        """Получение текущего статуса фонового логгера и базы SQLite."""
        return telemetry_service.get_status()

    @router.get("/logger/history")
    async def get_telemetry_history(
        limit: int = Query(default=60, ge=1, le=1000, description="Максимальное число записей"),
        since_epoch: Optional[float] = Query(default=None, description="Фильтр по времени (Unix epoch)"),
    ) -> List[Dict[str, Any]]:
        """Извлечение истории системных снапшотов из базы SQLite."""
        return storage.get_snapshots(limit=limit, since_epoch=since_epoch)

    @router.get("/logger/processes")
    async def get_telemetry_process_history(
        name: Optional[str] = Query(default=None, description="Имя процесса"),
        pid: Optional[int] = Query(default=None, description="PID процесса"),
        limit: int = Query(default=100, ge=1, le=500, description="Лимит записей"),
    ) -> List[Dict[str, Any]]:
        """Извлечение истории среза процессов из базы SQLite."""
        return storage.get_process_history(name=name, pid=pid, limit=limit)

    @router.delete("/logger/history")
    async def cleanup_telemetry_history(
        days: int = Query(default=7, ge=1, le=365, description="Удалить записи старше N дней"),
    ) -> Dict[str, Any]:
        """Очистка устаревших записей телеметрии из SQLite."""
        deleted = storage.cleanup_old_records(retention_days=days)
        return {
            "success": True,
            "deleted_records": deleted,
            "retention_days": days,
        }

    @router.websocket("/stream")
    async def stream_telemetry(websocket: WebSocket) -> None:
        """Stream real-time system snapshots over WebSocket (Wireshark-style stream)."""
        await websocket.accept()
        interval_sec = 1.0

        try:
            while True:
                # Check if client sent configuration or message without blocking
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if isinstance(data, dict) and "interval" in data:
                        interval_sec = max(0.5, min(10.0, float(data["interval"])))
                except (asyncio.TimeoutError, Exception):
                    pass

                snapshot = collector.get_snapshot(process_limit=15)
                await websocket.send_text(snapshot.model_dump_json())
                await asyncio.sleep(interval_sec)

        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.debug("System telemetry WebSocket client disconnected")
        except Exception as ex:
            logger.debug(f"System telemetry WebSocket error: {ex}")

    return router

