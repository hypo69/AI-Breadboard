# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router System Module
# =============================================================================
# Description:
#   Системный роутер FastAPI для предоставления диагностических и телеметрических эндпоинтов.
#
#   Зачем нужен этот модуль:
#     1. Предоставление системной телеметрии: эндпоинты для получения текущих снимков системы
#        (CPU, память, процессы, сенсоры) и живого WebSocket потока через SystemCollector.
#     2. Интеллектуальная диагностика: интеграция с SystemDiagnosticEngine и GroupedTelemetryBuilder
#        для выявления аномалий, группировки метрик и генерации рекомендаций.
#     3. Единый фасад для UI и агентов: прозрачный доступ фронтенда и LLM к данным о состоянии хоста.
#
# Usage Examples:
#   Python API:
#     from fastapi import FastAPI
#     from src.api.routers.core.router_system import router as system_router
#
#     app = FastAPI()
#     app.include_router(system_router, prefix="/api/v1/system")
#
# File: router_system.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:20:00
# =============================================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from logger import logger
from apps.windows.telemetry import (
    HardwareNode,
    HardwareSensor,
    ProcessMetrics,
    ProcessNetworkActivity,
    SystemCollector,
    SystemDiagnosticReport,
    SystemSnapshot,
)
from apps.windows.telemetry_research.diagnostic_engine import SystemDiagnosticEngine
from apps.windows.telemetry_research.grouped_telemetry import (
    GroupDiagnoseRequest,
    GroupDiagnosticResult,
    GroupedTelemetryBuilder,
    SynthesisDiagnosticResult,
    SynthesisRequest,
    TelemetryGroupInfo,
)

router = APIRouter(prefix="/api/v1/system", tags=["system-diagnostics"])
_collector: Optional[SystemCollector] = None
_diagnostician: Optional[SystemDiagnosticEngine] = None
_builder = GroupedTelemetryBuilder()


def get_collector() -> SystemCollector:
    """Получить экземпляр системного коллектора."""
    global _collector
    if _collector is None:
        _collector = SystemCollector()
    return _collector


def get_diagnostician(chat_model: Optional[Any] = None) -> SystemDiagnosticEngine:
    """Получить экземпляр системного диагноста."""
    global _diagnostician
    if _diagnostician is None or chat_model is not None:
        _diagnostician = SystemDiagnosticEngine(chat_model=chat_model)
    return _diagnostician


@router.get("/router_system/ping", tags=["system-diagnostics"])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {"status": "ok"}


@router.websocket("/stream")
async def stream_telemetry(websocket: WebSocket) -> None:
    """WebSocket поток мгновенных снимков телеметрии в реальном времени."""
    await websocket.accept()
    collector = get_collector()
    logger.info("[RouterSystem] WebSocket клиент подключен к потоку телеметрии /api/v1/system/stream")

    try:
        while True:
            snapshot = await collector.get_snapshot(process_limit=15)
            await websocket.send_text(snapshot.model_dump_json())
            await asyncio.sleep(1.0)

    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.info("[RouterSystem] WebSocket клиент отключен от потока телеметрии.")
    except Exception as ex:
        logger.debug(f"[RouterSystem] Завершение WebSocket соединения: {ex}")


@router.get("/summary", response_model=SystemSnapshot)
async def get_system_summary(
    process_limit: int = Query(default=20, ge=1, le=100, description="Количество Top-процессов")
) -> SystemSnapshot:
    """Получение текущего снимка нагрузки системы, сенсоров и процессов."""
    collector = get_collector()
    return await collector.get_snapshot(process_limit=process_limit)


@router.get("/processes", response_model=List[ProcessMetrics])
async def list_processes(
    limit: int = Query(default=50, ge=1, le=500, description="Лимит процессов"),
    sort_by: str = Query(default="cpu", description="Сортировка (cpu, memory, handles)"),
    source: Optional[str] = Query(default="db", description="Источник (db или live)"),
) -> List[ProcessMetrics]:
    """Получение списка процессов из SQLite базы данных (telemetry.db) или оперативной памяти."""
    lim = limit.default if hasattr(limit, "default") else (int(limit) if isinstance(limit, (int, float, str)) and str(limit).isdigit() else 50)
    sort_str = sort_by.default if hasattr(sort_by, "default") else (str(sort_by) if sort_by else "cpu")
    src_str = source.default if hasattr(source, "default") else (str(source) if source else "db")

    if src_str != "live":
        try:
            from apps.windows.telemetry.sqlite import TelemetryStorage
            storage = TelemetryStorage.get_instance(read_only=True)
            raw_procs = storage.get_latest_processes(limit=lim, sort_by=sort_str)
            if raw_procs:
                result = []
                for p in raw_procs:
                    result.append(
                        ProcessMetrics(
                            pid=p.get("pid", 0),
                            name=p.get("name", "unknown"),
                            cpu_percent=float(p.get("cpu_percent") or 0.0),
                            memory_mb=float(p.get("memory_mb") or 0.0),
                            memory_percent=float(p.get("memory_percent") or 0.0),
                            num_threads=int(p.get("num_threads") or 1),
                            num_handles=int(p.get("num_handles") or 0),
                            status=p.get("status") or "running",
                            username=p.get("username"),
                        )
                    )
                return result
        except Exception as ex:
            logger.warning(f"[RouterSystem] Ошибка чтения процессов из SQLite: {ex}")
    collector = get_collector()
    return await asyncio.to_thread(collector.get_top_processes, limit=lim, sort_by=sort_str)


@router.get("/processes/stats")
async def get_processes_stats(
    limit: int = Query(default=10, ge=1, le=100, description="Количество записей")
) -> Dict[str, Any]:
    """Получение аналитической статистики процессов (роллапы, суточная статистика, аномалии)."""
    try:
        from apps.windows.telemetry.sqlite import TelemetryStorage
        storage = TelemetryStorage.get_instance(read_only=True)
        stats = storage.get_process_stats(limit=limit)
        return {
            "rollups_2min": stats.get("rollups_2min", []),
            "daily_stats": stats.get("daily_stats", []),
            "outliers": stats.get("outliers", []),
        }
    except Exception as ex:
        logger.warning(f"[RouterSystem] Ошибка получения статистики процессов: {ex}")
        return {"rollups_2min": [], "daily_stats": [], "outliers": []}


@router.post("/processes/rollup")
async def trigger_process_rollup(
    cutoff_seconds: int = Query(default=120, description="Окно отсечки в секундах"),
    outlier_cpu_threshold: float = Query(default=30.0, description="Порог CPU для аномалий"),
) -> Dict[str, Any]:
    """Запуск фонового уплотнения (rollup) телеметрии процессов в базе данных."""
    try:
        from apps.windows.telemetry.sqlite import TelemetryMaintenance
        maint = TelemetryMaintenance.get_instance()
        res = maint.run_process_rollup(cutoff_seconds=cutoff_seconds, outlier_cpu_threshold=outlier_cpu_threshold)
        return {"success": True, **res}
    except Exception as ex:
        logger.warning(f"[RouterSystem] Ошибка rollup процессов: {ex}")
        return {"success": True, "rollup_2min": 0, "rollup_daily": 0, "message": str(ex)}


@router.get("/metrics/core")
async def get_core_metrics() -> Dict[str, Any]:
    """Экспресс-получение базовых метрик хоста (CPU, RAM, Disk I/O, Battery, Uptime)."""
    collector = get_collector()
    core = await collector.get_core_metrics()
    return core.model_dump()


@router.get("/hardware/quick")
async def get_hardware_quick() -> Dict[str, Any]:
    """Экспресс-сводка аппаратных модулей (SMART дисков, планки RAM, порты, алерты)."""
    collector = get_collector()
    quick = await collector.get_hardware_quick()
    return quick.model_dump()


@router.get("/network-activity", response_model=List[ProcessNetworkActivity])
async def get_process_network_activity_endpoint(
    limit: int = 100,
    only_internet: bool = False,
) -> List[ProcessNetworkActivity]:
    """Возвращает список активных сетевых соединений программ и процессов."""
    try:
        collector = get_collector()
        return collector.get_process_network_activity(limit=limit, only_internet=only_internet)
    except Exception as exc:
        logger.error(f"[RouterSystem] Ошибка получения сетевой активности процессов: {exc}", exc_info=True)
        return []


@router.get("/hardware", response_model=List[HardwareNode])
async def get_hardware_tree() -> List[HardwareNode]:
    """Иерархическое дерево оборудования и компонентов хоста."""
    collector = get_collector()
    return await collector.get_hardware_tree_async()


@router.get("/sensors", response_model=List[HardwareSensor])
async def get_sensors() -> List[HardwareSensor]:
    """Список текущих показаний аппаратных сенсоров хоста из базы данных SQLite (telemetry.db)."""
    try:
        from apps.windows.telemetry.sqlite import TelemetryStorage
        storage = TelemetryStorage.get_instance(read_only=True)
        db_sensors = storage.get_latest_sensors()
        if db_sensors:
            return [
                HardwareSensor(
                    sensor_id=str(item.get("sensor_id") or item.get("name") or "unknown"),
                    name=str(item.get("name") or item.get("sensor_id") or "sensor"),
                    sensor_type=str(item.get("sensor_type") or "temperature"),
                    value=float(item.get("value") or 0.0),
                    unit=str(item.get("unit") or "°C"),
                )
                for item in db_sensors
            ]
    except Exception as ex:
        logger.debug(f"[RouterSystem] Ошибка чтения сенсоров из SQLite: {ex}")
    from apps.windows.telemetry.sensors import get_hardware_sensors
    return await asyncio.to_thread(get_hardware_sensors)


@router.post("/diagnose", response_model=SystemDiagnosticReport)
async def diagnose_system(snapshot: Optional[SystemSnapshot] = None) -> SystemDiagnosticReport:
    """Запуск диагностики всей системы с использованием эвристик и ИИ."""
    collector = get_collector()
    diagnostician = get_diagnostician()
    if snapshot is None:
        snapshot = await collector.get_snapshot(process_limit=15)
    return await diagnostician.diagnose(snapshot)


@router.post("/lhm-audit")
async def run_lhm_sensor_hardware_audit() -> Dict[str, Any]:
    """Сбор данных LHM и AI-аудит сравнения показаний датчиков с реальным оборудованием."""
    try:
        from apps.librehardwaremonitor.core.lhm_auditor import LhmSensorAuditor
        auditor = LhmSensorAuditor()
        diagnostician = get_diagnostician()
        return await auditor.audit_sensors_with_ai(chat_model=getattr(diagnostician, "chat_model", None))
    except Exception as ex:
        logger.warning(f"[RouterSystem] Ошибка LHM аудита: {ex}")
        return {"status": "error", "message": str(ex)}


@router.get("/diagnose/groups", response_model=List[TelemetryGroupInfo])
async def get_diagnose_groups() -> List[TelemetryGroupInfo]:
    """Возвращает срез телеметрии, разбитый на 4 специализированные группы."""
    collector = get_collector()
    snapshot = await collector.get_snapshot(process_limit=15)
    return _builder.build_all_groups(snapshot)


@router.post("/diagnose/group", response_model=GroupDiagnosticResult)
async def diagnose_group_endpoint(req: GroupDiagnoseRequest) -> GroupDiagnosticResult:
    """Диагностика одной группы телеметрии."""
    diagnostician = get_diagnostician()
    return await diagnostician.diagnose_group(
        group_id=req.group_id,
        payload=req.payload,
        title=req.title or req.group_id,
    )


@router.post("/diagnose/synthesize", response_model=SynthesisDiagnosticResult)
async def synthesize_diagnostics_endpoint(req: SynthesisRequest) -> SynthesisDiagnosticResult:
    """Синтез общего вердикта и индекса здоровья по всем доменам."""
    diagnostician = get_diagnostician()
    return await diagnostician.synthesize_final_report(req.groups)


def init_router(chat_model: Optional[Any] = None, **kwargs: Any) -> APIRouter:
    """Инициализация и возврат системного роутера."""
    if chat_model is not None:
        get_diagnostician(chat_model=chat_model)
    return router