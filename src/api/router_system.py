# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI System and Hardware Telemetry Router
# =============================================================================

"""FastAPI router for system telemetry, hardware inspection, and AI diagnosis."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from logger import logger
from apps.windows.telemetry import (
    HardwareArchiveEntry,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
    HardwareNode,
    HardwareSensor,
    ProcessMetrics,
    SystemDiagnosticEngine,
    SystemCollector,
    SystemDiagnosticReport,
    SystemSnapshot,
    TelemetryLoggerService,
)
from src.ai.observability.grouped_telemetry import (
    GroupDiagnoseRequest,
    GroupDiagnosticResult,
    SynthesisDiagnosticResult,
    SynthesisRequest,
    TelemetryGroupInfo,
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

    @router.get("/hardware/audit", response_model=HardwareAuditReport)
    async def get_hardware_audit() -> HardwareAuditReport:
        """Retrieve full hardware and driver audit report with attached sensors."""
        return collector.get_hardware_audit()

    @router.get("/hardware/history")
    async def get_hardware_history(
        limit: int = Query(default=50, ge=1, le=200, description="Max history count")
    ) -> List[Dict[str, Any]]:
        """Retrieve list of saved historical hardware archive snapshots."""
        return collector.get_hardware_history(limit=limit)

    @router.get("/hardware/changes", response_model=List[HardwareChangeItem])
    async def get_hardware_changes(
        limit: int = Query(default=100, ge=1, le=500, description="Max changes count")
    ) -> List[HardwareChangeItem]:
        """Retrieve historical timeline of hardware configuration changes."""
        return collector.get_hardware_changes(limit=limit)

    @router.post("/hardware/archive", response_model=HardwareArchiveEntry)
    async def create_hardware_archive() -> HardwareArchiveEntry:
        """Force capturing and archiving current hardware audit state."""
        return collector.archive_hardware_state(auto_diff=True)

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
        try:
            target_snapshot = snapshot or await collector.get_snapshot()
            return await diagnostician.diagnose(target_snapshot)
        except Exception as e:
            logger.error(f"Error in run_ai_diagnostics: {e}", exc_info=True)
            return SystemDiagnosticReport(
                health_score=85,
                status="warning",
                summary=f"Базовая диагностика: телеметрия хоста получена (AI-модель недоступна: {e})",
                anomalies=[],
                recommendations=["Проверьте журнал событий Windows."],
                ai_model_used="Fallback Heuristic",
            )

    @router.get("/diagnose/groups", response_model=List[TelemetryGroupInfo])
    async def get_diagnostic_groups() -> List[TelemetryGroupInfo]:
        """Формирует и возвращает 4 сфокусированные группы телеметрии для поэтапного анализа."""
        try:
            snapshot = await collector.get_snapshot()
            return diagnostician.get_diagnostic_groups(snapshot)
        except Exception as e:
            logger.error(f"Failed to generate live diagnostic groups: {e}", exc_info=True)
            try:
                fallback_snapshot = SystemSnapshot()
                return diagnostician.get_diagnostic_groups(fallback_snapshot)
            except Exception as e2:
                logger.error(f"Fallback diagnostic groups generation failed: {e2}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Ошибка генерации групп телеметрии: {e}")

    @router.post("/diagnose/group", response_model=GroupDiagnosticResult)
    async def diagnose_single_group(req: GroupDiagnoseRequest) -> GroupDiagnosticResult:
        """Выполняет целевой AI-анализ одной конкретной группы телеметрии."""
        try:
            return await diagnostician.diagnose_group(
                group_id=req.group_id,
                payload=req.payload,
                title=req.title or "",
            )
        except Exception as e:
            logger.error(f"Error in diagnose_single_group ({req.group_id}): {e}", exc_info=True)
            return GroupDiagnosticResult(
                group_id=req.group_id,
                title=req.title or req.group_id,
                status="warning",
                summary=f"Телеметрия группы получена (ошибка AI-анализа: {e})",
                anomalies=[],
                recommendations=[],
                key_metrics={},
                ai_model_used="Fallback Heuristic",
            )

    @router.post("/diagnose/synthesize", response_model=SynthesisDiagnosticResult)
    async def synthesize_diagnostics(req: SynthesisRequest) -> SynthesisDiagnosticResult:
        """Формирует итоговый синтез и общий Health Score на основе результатов всех завершенных групп."""
        try:
            return await diagnostician.synthesize_final_report(req.groups)
        except Exception as e:
            logger.error(f"Error in synthesize_diagnostics: {e}", exc_info=True)
            return SynthesisDiagnosticResult(
                health_score=80,
                status_label="Внимание",
                executive_summary=f"Поэтапный аудит подсистем хоста завершен (ошибка синтеза: {e}).",
                critical_actions=["Проверьте системные службы и журналы событий."],
                ai_model_used="Fallback Heuristic",
                groups_evaluated=len(req.groups),
            )

    @router.post("/lhm-audit")
    async def run_lhm_sensor_hardware_audit() -> Dict[str, Any]:
        """Сбор залогированных данных LHM, усреднение и AI-аудит сравнения с реальным железом."""
        from apps.librehardwaremonitor.core.lhm_auditor import LhmSensorAuditor
        auditor = LhmSensorAuditor()
        return await auditor.audit_sensors_with_ai(chat_model=chat_model)


    # =========================================================================
    # Посекундный логгер телеметрии (CSV)
    # =========================================================================

    @router.post("/logger/start")
    async def start_telemetry_logger(
        interval_sec: float = Query(default=1.0, ge=0.2, le=60.0, description="Интервал сбора в секундах"),
        top_processes: int = Query(default=20, ge=1, le=100, description="Количество Top-процессов"),
    ) -> Dict[str, Any]:
        """Запуск фонового сбора телеметрии в CSV-файлы."""
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
        """Получение текущего статуса фонового логгера."""
        return telemetry_service.get_status()

    @router.websocket("/stream")
    async def stream_telemetry(websocket: WebSocket) -> None:
        """Stream real-time system snapshots over WebSocket (Wireshark-style stream)."""
        await websocket.accept()
        interval_sec = 1.0
        logger.info("Системная телеметрия: WebSocket клиент успешно подключен к потоку.")

        try:
            while True:
                # Check if client sent configuration or message without blocking
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if isinstance(data, dict) and "interval" in data:
                        interval_sec = max(0.5, min(10.0, float(data["interval"])))
                except (asyncio.TimeoutError, Exception):
                    pass

                snapshot = await collector.get_snapshot(process_limit=15)
                await websocket.send_text(snapshot.model_dump_json())
                await asyncio.sleep(interval_sec)

        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.info("Системная телеметрия: WebSocket клиент отключился.")
        except RuntimeError as ex:
            if "websocket.close" in str(ex) or "websocket.send" in str(ex):
                logger.warning(
                    f"Системная телеметрия: WebSocket соединение закрыто со стороны сервера/таймаута ({ex}). Ожидание переподключения клиента..."
                )
            else:
                logger.warning(f"Системная телеметрия: ошибка цикла WebSocket: {ex}")
        except Exception as ex:
            logger.warning(
                f"Системная телеметрия: разрыв WebSocket соединения ({ex}). Ожидание повторного подключения клиента..."
            )

    return router
