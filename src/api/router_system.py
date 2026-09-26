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
    ForensicsActivityReport,
    HardwareArchiveEntry,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
    HardwareNode,
    HardwareSensor,
    KernelThrottlingReport,
    PeripheralsNetworkReport,
    ProcessLeakDiagnosticsReport,
    ProcessMetrics,
    ProcessNetworkActivity,
    StorageBatteryWearReport,
    SystemCoreMetrics,
    SystemDiagnosticEngine,
    SystemCollector,
    SystemDiagnosticReport,
    SystemHardwareQuick,
    SystemSnapshot,
    TelemetryLoggerService,
)
from apps.windows.telemetry.deep_diagnostics import DeepDiagnosticsEngine
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
    router = APIRouter(prefix="/tc/system", tags=["System & Hardware Inspector"])
    alias_v1 = APIRouter(prefix="/api/v1/system", include_in_schema=False)
    alias_tc_v1 = APIRouter(prefix="/tc/api/v1/system", include_in_schema=False)
    collector = SystemCollector()
    diagnostician = SystemDiagnosticEngine(chat_model=chat_model)
    telemetry_service = TelemetryLoggerService.get_instance()

    @router.get("/metrics/core", response_model=SystemCoreMetrics)
    async def get_core_metrics() -> SystemCoreMetrics:
        """Сверхбыстрый сбор базовых показателей хоста (CPU, RAM, GPU, Disk I/O, Battery)."""
        return await collector.get_core_metrics()

    @router.get("/hardware/quick", response_model=SystemHardwareQuick)
    async def get_hardware_quick() -> SystemHardwareQuick:
        """Сводка состояния накопителей, планок RAM и сетевых сокетов с кэшированием."""
        return await collector.get_hardware_quick()

    @router.get("/summary", response_model=SystemSnapshot)
    async def get_system_summary(
        process_limit: int = Query(default=25, ge=0, le=5000, description="Top processes count (0 for all active processes)")
    ) -> SystemSnapshot:
        """Retrieve live system load, hardware telemetry, and top processes snapshot."""
        return await collector.get_snapshot(process_limit=process_limit)

    @router.get("/processes", response_model=List[ProcessMetrics])
    async def list_processes(
        limit: int = Query(default=50, ge=0, le=5000, description="Max processes count (0 for all)"),
        sort_by: str = Query(default="cpu", pattern="^(cpu|memory|ram|handles|descriptors)$", description="Sort criteria"),
        mode: Optional[str] = Query(default=None, pattern="^(top_n|all)$", description="Mode: top_n or all (if all, returns all active processes)"),
        source: str = Query(default="db", pattern="^(db|live)$", description="Data source: db (SQLite) or live"),
    ) -> List[ProcessMetrics]:
        """Получение последнего замера активных процессов из базы данных SQLite (по умолчанию) или psutil."""
        effective_limit = 0 if mode == "all" else limit

        if source == "db":
            procs = await asyncio.to_thread(telemetry_service.storage.get_latest_processes, limit=effective_limit, sort_by=sort_by)
            if not procs:
                # Fallback: если БД ещё пуста, фиксируем первый срез в БД и возвращаем
                snapshot = await collector.get_snapshot(process_limit=effective_limit)
                await asyncio.to_thread(telemetry_service.storage.save_snapshot, snapshot, top_n=effective_limit)
                procs = await asyncio.to_thread(telemetry_service.storage.get_latest_processes, limit=effective_limit, sort_by=sort_by)
            return [ProcessMetrics(**p) for p in procs]

        return await asyncio.to_thread(collector.get_top_processes, limit=effective_limit, sort_by=sort_by)

    @router.get("/processes/stats")
    async def get_processes_stats(
        name: Optional[str] = Query(default=None, description="Фильтр по имени процесса"),
        limit: int = Query(default=50, ge=1, le=200, description="Лимит записей"),
    ) -> Dict[str, Any]:
        """Получение статистики процессов: 2-минутные агрегаты, суточная статистика и зафиксированные выбросы."""
        return await asyncio.to_thread(telemetry_service.storage.get_process_stats, name=name, limit=limit)

    @router.post("/processes/rollup")
    async def trigger_processes_rollup(
        cutoff_seconds: int = Query(default=120, ge=10, le=86400, description="Порог обобщения в секундах (по умолчанию 120 с)"),
        outlier_cpu_threshold: float = Query(default=30.0, ge=0.0, le=100.0, description="Порог выброса по CPU %"),
    ) -> Dict[str, Any]:
        """Принудительный запуск обобщения устаревших метрик процессов (> 2 мин со средними/выбросами и > 1 дня)."""
        short_res = await asyncio.to_thread(
            telemetry_service.storage.aggregate_process_metrics_2min,
            cutoff_seconds=cutoff_seconds,
            outlier_cpu_threshold=outlier_cpu_threshold,
        )
        daily_res = await asyncio.to_thread(
            telemetry_service.storage.aggregate_process_metrics_daily,
            cutoff_days=1,
        )
        return {
            "success": True,
            "rollup_2min": short_res,
            "rollup_daily": daily_res,
        }

    @router.get("/network-activity", response_model=List[ProcessNetworkActivity])
    async def get_process_network_activity(
        limit: int = Query(default=50, ge=1, le=200, description="Max active network connections"),
        only_internet: bool = Query(default=False, description="Filter only external Internet addresses"),
    ) -> List[ProcessNetworkActivity]:
        """Сетевая активность процессов: программы в сети, адреса, протоколы, отправка и прием."""
        return await asyncio.to_thread(collector.get_process_network_activity, limit=limit, only_internet=only_internet)

    @router.get("/hardware", response_model=List[HardwareNode])
    async def get_hardware_tree() -> List[HardwareNode]:
        """Retrieve AIDA64-like hierarchical component specification tree."""
        return await collector.get_hardware_tree_async()

    @router.get("/hardware/audit", response_model=HardwareAuditReport)
    async def get_hardware_audit() -> HardwareAuditReport:
        """Retrieve full hardware and driver audit report with attached sensors."""
        return await asyncio.to_thread(collector.get_hardware_audit)

    @router.get("/hardware/history")
    async def get_hardware_history(
        limit: int = Query(default=50, ge=1, le=200, description="Max history count")
    ) -> List[Dict[str, Any]]:
        """Retrieve list of saved historical hardware archive snapshots."""
        return await asyncio.to_thread(collector.get_hardware_history, limit=limit)

    @router.get("/hardware/changes", response_model=List[HardwareChangeItem])
    async def get_hardware_changes(
        limit: int = Query(default=100, ge=1, le=500, description="Max changes count")
    ) -> List[HardwareChangeItem]:
        """Retrieve historical timeline of hardware configuration changes."""
        return await asyncio.to_thread(collector.get_hardware_changes, limit=limit)

    @router.post("/hardware/archive", response_model=HardwareArchiveEntry)
    async def create_hardware_archive() -> HardwareArchiveEntry:
        """Force capturing and archiving current hardware audit state."""
        return await asyncio.to_thread(collector.archive_hardware_state, auto_diff=True)

    @router.get("/sensors")
    async def get_sensors(
        source: str = Query(default="db", pattern="^(db|live)$", description="Источник данных: db (SQLite) или live (прямой вызов)"),
    ) -> List[Dict[str, Any]]:
        """Получение показаний тепловых, вентиляторных и нагрузочных сенсоров хоста.

        Параметры:
            source: Источник данных — ``db`` читает последний актуальный замер из БД
                    (аналогично панели «Топ процессов»), ``live`` делает прямой вызов сенсоров.
        """
        if source == "db":
            rows = await asyncio.to_thread(telemetry_service.storage.get_latest_sensors)
            if rows:
                # Нормализуем поля БД в формат HardwareSensor для совместимости с UI
                return [
                    {
                        "id": r.get("sensor_id", ""),
                        "hardware_name": r.get("hardware_name", "System"),
                        "hardware_type": r.get("hardware_type", "cpu"),
                        "sensor_category": r.get("sensor_category", "General"),
                        "sensor_name": r.get("sensor_name", "Unknown"),
                        "value_raw": f"{r.get('value', 0.0)} {r.get('unit', '')}".strip(),
                        "value_numeric": r.get("value", 0.0),
                        "unit": r.get("unit", ""),
                        "timestamp": r.get("timestamp"),
                    }
                    for r in rows
                ]
            # Fallback: если БД ещё пуста — возвращаем live
            logger.info("[router_system] БД сенсоров пуста, fallback на live-вызов")

        from apps.windows.telemetry.sensors import get_hardware_sensors
        sensors = await asyncio.to_thread(get_hardware_sensors)
        return [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in sensors]

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
        from apps.windows.hardware.lhm_auditor import LhmSensorAuditor
        auditor = LhmSensorAuditor()
        return await auditor.audit_sensors_with_ai(chat_model=chat_model)

    # =========================================================================
    # Глубокая системная диагностика, форензика, троттлинг и износ
    # =========================================================================

    _deep_engine = DeepDiagnosticsEngine()

    @router.get("/diagnostics/leaks", response_model=ProcessLeakDiagnosticsReport)
    async def get_process_leaks(
        limit: int = Query(default=50, ge=1, le=200, description="Максимум процессов")
    ) -> ProcessLeakDiagnosticsReport:
        """Скрытая диагностика процессов (дескрипторы Handles, GDI/USER объекты, Hard Page Faults)."""
        return await asyncio.to_thread(_deep_engine.collect_process_leaks, limit=limit)

    @router.get("/diagnostics/forensics", response_model=ForensicsActivityReport)
    async def get_activity_forensics() -> ForensicsActivityReport:
        """Поведенческая телеметрия (активное окно, Idle Time, камера/микрофон, UserAssist)."""
        return await asyncio.to_thread(_deep_engine.collect_forensics_activity)

    @router.get("/diagnostics/throttling", response_model=KernelThrottlingReport)
    async def get_kernel_throttling() -> KernelThrottlingReport:
        """Качество работы ядра, прерывания DPC/ISR, троттлинг PROCHOT/Power, Uptime и BSOD."""
        return await asyncio.to_thread(_deep_engine.collect_kernel_throttling)

    @router.get("/diagnostics/storage-battery", response_model=StorageBatteryWearReport)
    async def get_storage_battery_wear() -> StorageBatteryWearReport:
        """Телеметрия износа накопителей SSD/NVMe (SMART, TBW) и батареи питания."""
        return await asyncio.to_thread(_deep_engine.collect_storage_battery_wear)

    @router.get("/diagnostics/peripherals", response_model=PeripheralsNetworkReport)
    async def get_peripherals_network() -> PeripheralsNetworkReport:
        """Телеметрия сети (Wi-Fi RSSI/BSSID), USB PnP устройств и аудио."""
        return await asyncio.to_thread(_deep_engine.collect_peripherals_network)


    @router.websocket("/stream")
    async def stream_telemetry(websocket: WebSocket) -> None:
        """Потоковая передача системных замеров через WebSocket каждые 5 секунд."""
        await websocket.accept()
        interval_sec = 5.0
        logger.info("Системная телеметрия: WebSocket клиент успешно подключен к потоку (интервал: 5 сек).")

        try:
            while True:
                # Проверка конфигурационных сообщений от клиента без блокировки
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if isinstance(data, dict) and "interval" in data:
                        interval_sec = max(1.0, min(60.0, float(data["interval"])))
                except (asyncio.TimeoutError, Exception):
                    pass

                snapshot = await collector.get_snapshot(process_limit=20)
                # Если фоновый логгер не запущен, сохраняем снимок в БД прямо здесь
                if not telemetry_service.is_running:
                    try:
                        await asyncio.to_thread(telemetry_service.storage.save_snapshot, snapshot, top_n=20)
                    except Exception as save_err:
                        logger.debug(f"Ошибка сохранения снимка через WebSocket: {save_err}")

                await websocket.send_text(snapshot.model_dump_json())
                await asyncio.sleep(interval_sec)

        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.info("Системная телеметрия: WebSocket клиент отключился.")
        except RuntimeError as ex:
            if "websocket.close" in str(ex) or "websocket.send" in str(ex):
                logger.warning(
                    f"Системная телеметрия: WebSocket соединение закрыто ({ex}). Ожидание переподключения..."
                )
            else:
                logger.warning(f"Системная телеметрия: ошибка цикла WebSocket: {ex}")
        except Exception as ex:
            logger.warning(
                f"Системная телеметрия: разрыв WebSocket соединения ({ex}). Ожидание повторного подключения..."
            )

    # Автозапуск фоновой службы сбора телеметрии каждые 5 секунд
    try:
        if not telemetry_service.is_running:
            telemetry_service.interval_sec = 5.0
            telemetry_service.start()
            logger.info("Автоматический запуск службы сбора телеметрии TelemetryLoggerService (каждые 5 сек).")
    except Exception as auto_start_err:
        logger.warning(f"Не удалось автоматически запустить службу сбора телеметрии: {auto_start_err}")

    return router
