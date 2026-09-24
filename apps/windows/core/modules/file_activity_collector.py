# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from logger import logger
from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider
from apps.windows.core.models import DomainAuditResult
from apps.windows.sysadmin.src.file_auditor import WindowsFileAuditor
from apps.windows.telemetry.service import TelemetryLoggerService

class FileActivityCollector(TelemetryProvider):
    """Коллектор активности файловой системы на основе аудита событий Windows."""

    def __init__(self, monitored_paths: List[str]) -> None:
        """Инициализация коллектора с аудитором и списком отслеживаемых путей."""
        self._auditor = WindowsFileAuditor()
        self._monitored_paths = monitored_paths
        self._log_dir = __root__ / "data" / "file_activity_logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._last_result: Optional[DomainAuditResult] = None
        
        # Автоматическая настройка SACL для путей, если их нет
        for path in monitored_paths:
            if os.path.exists(path):
                status = self._auditor.get_folder_sacl(path)
                if not status.exists:
                    logger.info(f"Настройка SACL для {path}...")
                    self._auditor.configure_folder_sacl(path)

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели сетевых подключений как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            metrics = self._last_result.metrics
            sensors.append(HardwareSensor(
                sensor_id="file_activity_writes",
                name="Записей файлов (событий)",
                category="file_activity",
                value=float(metrics.get("writes_count", 0)),
                unit="count"
            ))
            sensors.append(HardwareSensor(
                sensor_id="file_activity_deletes",
                name="Удалений файлов (событий)",
                category="file_activity",
                value=float(metrics.get("deletes_count", 0)),
                unit="count"
            ))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор событий аудита и запись в JSONL-логи."""
        events = self._auditor.fetch_deletion_events(hours=1, max_events=500)
        
        writes = 0
        deletes = 0
        log_file = self._log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        # Получаем сервис телеметрии для записи корреляций
        telemetry_service = TelemetryLoggerService.get_instance()

        with open(log_file, "a", encoding="utf-8") as f:
            for ev in events:
                if ev.is_deletion:
                    deletes += 1
                    # Записываем корреляцию удаления файла
                    try:
                        telemetry_service.record_event(
                            event_type="file_delete",
                            event_details={
                                "file_path": ev.object_name,
                                "process_name": ev.process_name,
                                "user": ev.subject_user_name,
                            },
                        )
                    except Exception as ex:
                        logger.debug(f"Не удалось записать корреляцию удаления: {ex}")
                else:
                    writes += 1
                    # Записываем корреляцию записи в файл
                    try:
                        telemetry_service.record_event(
                            event_type="file_write",
                            event_details={
                                "file_path": ev.object_name,
                                "process_name": ev.process_name,
                                "user": ev.subject_user_name,
                            },
                        )
                    except Exception as ex:
                        logger.debug(f"Не удалось записать корреляцию записи: {ex}")
                
                # Запись события в JSONL
                f.write(json.dumps(ev.__dict__, default=str, ensure_ascii=False) + "\n")

        metrics = {
            "writes_count": writes,
            "deletes_count": deletes,
            "log_file": str(log_file),
        }

        result = DomainAuditResult(
            domain_name="file_activity",
            title_ru="Активность файловой системы",
            status="ok",
            findings=[],
            metrics=metrics,
            scan_duration_ms=0.0,
        )
        self._last_result = result
        return result
