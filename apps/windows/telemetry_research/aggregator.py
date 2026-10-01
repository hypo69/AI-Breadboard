# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Aggregator
# =============================================================================
# Description:
#   Централизованный агрегатор телеметрии, синхронизирующий фоновый сбор данных
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.aggregator import TelemetryAggregator
#
#     service = TelemetryAggregator()
#
# File: aggregator.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Централизованный агрегатор телеметрии, синхронизирующий фоновый сбор данных"""

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from logger_ai.logger import logger
except ImportError:
    from logger import logger
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.file_collector import FileCollector
from apps.windows.telemetry.json_logger import TelemetryJsonLogger
from apps.windows.telemetry.sqlite import TelemetryStorage


class TelemetryAggregator:
    """Централизованный агрегатор телеметрии и сенсорного сбора в базу данных и лог.

    Осуществляет периодический сбор аппаратных метрик (через :class:`SensorCollector`)
    и файловых событий (через :class:`FileCollector`) с сохранением сырых измерений
    в базу данных SQLite (:class:`TelemetryStorage`), а также выполняет периодическую
    почасовую агрегацию метрик.

    Примечание:
        Экземпляр :class:`TelemetryJsonLogger` сохранён в `__init__` (атрибут `self.logger`)
        для поддержки явного внедрения зависимостей (DI) и вспомогательного/резервного
        файлового JSON-логирования, в то время как основным постоянным хранилищем
        телеметрии выступает SQLite база данных (:class:`TelemetryStorage`).
    """

    def __init__(
        self,
        config_manager: Optional[TelemetryConfigManager] = None,
        log_dir: Optional[str] = None,
        storage: Optional[TelemetryStorage] = None,
        sensor_collector: Optional[SensorCollector] = None,
        file_collector: Optional[FileCollector] = None,
        telemetry_logger: Optional[TelemetryJsonLogger] = None,
    ) -> None:
        """Инициализирует агрегатор телеметрии.

        Args:
            config_manager: Менеджер конфигурации (если None, создается новый).
            log_dir: Директория для логов (по умолчанию: %APPDATA%\\AI-Breadboard\\apps\\logs).
            storage: Экземпляр постоянного SQLite хранилища TelemetryStorage.
            sensor_collector: Коллектор аппаратных сенсоров.
            file_collector: Коллектор файловых событий.
            telemetry_logger: Логгер JSON-потока телеметрии.
        """
        self.config_manager = config_manager or TelemetryConfigManager()
        self.log_dir = log_dir or self._get_default_log_dir()
        self.storage = storage or TelemetryStorage.get_instance()

        # Инициализация коллекторов с поддержкой явного внедрения зависимостей (DI)
        self.sensor_collector = sensor_collector or SensorCollector(config_manager=self.config_manager)
        self.file_collector = file_collector or FileCollector(
            watch_dirs=self.config_manager._config.get("watch_directories", ["C:\\Users\\"])
        )
        self.logger = telemetry_logger or TelemetryJsonLogger(
            log_dir=self.log_dir,
            filename=self.config_manager._config.get("log_filename", "ai_sensors_polls.json"),
            max_file_size_mb=self.config_manager._config.get("max_file_size_mb", 100),
        )

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._last_measurements: Dict[str, Any] = {}
        self._measurement_count = 0
        self._start_time = datetime.now(timezone.utc)
        self._last_aggregation = self._start_time
        self._last_audit_check = self._start_time
        self._audit_check_interval = 3600.0  # Проверка аудитов раз в час

        # Ленивая инициализация чекера аудитов
        self._audit_checker = None

    @staticmethod
    def _get_default_log_dir() -> str:
        """Возвращает путь к директории логов по умолчанию.

        Returns:
            str: Путь к лог-директории.
        """
        appdata = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return os.path.join(appdata, "AI-Breadboard", "apps", "windows", "telemetry", "logs")

    def start(self) -> bool:
        """Запускает фоновый поток сбора телеметрии.

        Returns:
            bool: True если агрегатор успешно запущен.
        """
        if self._running:
            logger.warning("Агрегатор телеметрии уже запущен.")
            return False

        self._stop_event.clear()
        self._running = True

        self._thread = threading.Thread(
            target=self._worker_loop,
            name="TelemetryAggregatorWorker",
            daemon=True,
        )
        self._thread.start()

        logger.info("Агрегатор телеметрии запущен")
        return True

    def stop(self) -> bool:
        """Останавливает фоновый поток сбора телеметрии.

        Returns:
            bool: True если агрегатор был остановлен.
        """
        if not self._running:
            return False

        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

        self._thread = None
        self.file_collector.stop()
        logger.info("Агрегатор телеметрии остановлен")
        return True

    def _worker_loop(self) -> None:
        """Основной рабочий цикл агрегатора."""
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Ошибка при сборе телеметрии: {e}")

            min_interval = self._get_min_interval()
            sleep_time = max(0.1, min_interval)

            if self._stop_event.wait(timeout=sleep_time):
                break

    def _get_min_interval(self) -> float:
        """Возвращает минимальный интервал среди всех сенсоров, учитывая быстрый режим.

        Если с момента запуска прошло меньше fast_duration_days, используется fast_interval.
        Иначе – обычный минимум среди включенных сенсоров.
        """
        now = datetime.now(timezone.utc)
        fast_days = self.config_manager.get_fast_duration_days()
        if (now - self._start_time).days < fast_days:
            return self.config_manager.get_fast_interval()
        # Обычная логика
        intervals = []
        for sensor_name in self.config_manager.get_enabled_sensors():
            interval = self.config_manager.get_sensor_interval(sensor_name)
            intervals.append(interval)
        if not intervals:
            return self.config_manager._default_interval
        return min(intervals)

    def poll_once(self) -> None:
        """Проводит единовременный сбор всей телеметрии."""
        self._measurement_count += 1
        now_iso = datetime.now(timezone.utc).isoformat()

        hw_snapshot = {}
        file_events = []
        try:
            hw_snapshot = self.sensor_collector.get_hardware_snapshot()
            sensor_items = []
            for s in hw_snapshot.get('sensors', []):
                val_entry = s.get('values', [{}])[0]
                sensor_items.append({
                    'id': s.get('id'),
                    'hardware_name': s.get('hardware_name'),
                    'hardware_type': s.get('hardware_type'),
                    'sensor_category': s.get('sensor_category'),
                    'sensor_name': s.get('sensor_name'),
                    'unit': s.get('unit'),
                    'value': val_entry.get('num')
                })
            if sensor_items:
                self.storage.save_sensor_polls_batch(sensor_items, timestamp=now_iso)
        except Exception as e:
            logger.error(f'Ошибка при сборе и сохранении сенсоров: {e}')

        try:
            file_events = self.file_collector.get_recent_events()
        except Exception as e:
            logger.error(f'Ошибка при сборе файловых событий: {e}')

        self._last_measurements = {
            'hardware': hw_snapshot,
            'file_events': file_events,
            'timestamp': now_iso,
        }

        # После обычного поллинга проверяем необходимость часовой агрегации
        now = datetime.now(timezone.utc)
        fast_days = self.config_manager.get_fast_duration_days()
        if (now - self._start_time).days >= fast_days:
            if (now - self._last_aggregation).total_seconds() >= self.config_manager.get_aggregation_interval():
                self._aggregate_hourly()
                self._last_aggregation = now

        # Периодическая проверка критических аудитов
        if (now - self._last_audit_check).total_seconds() >= self._audit_check_interval:
            self._check_audits_periodic()
            self._last_audit_check = now

    def _check_audits_periodic(self) -> None:
        """Периодическая проверка критических состояний системы.

        Проверяет:
        - Pending reboot (требуется перезагрузка)
        - Критическую загрузку CPU/RAM
        - Проблемные драйверы (опционально)
        """
        try:
            # Ленивая инициализация чекера
            if self._audit_checker is None:
                from .audit_startup_checker import AuditStartupChecker
                self._audit_checker = AuditStartupChecker()

            result = self._audit_checker.check_startup_health(
                check_integrity=True,
                check_performance=True,
                check_drivers=False,
                check_eventlog=False
            )

            if not result.is_healthy:
                logger.error(
                    f"🚨 AUDIT CHECK: Критические проблемы! "
                    f"Critical: {result.critical_count}, Warnings: {result.warning_count}"
                )
                for finding in result.findings:
                    severity = finding.get('severity', 'unknown').upper()
                    domain = finding.get('domain', 'unknown')
                    title = finding.get('title', 'No title')
                    logger.warning(f"  - [{severity}] {domain}: {title}")

                # Сохраняем инцидент в БД
                try:
                    self.storage.save_event(
                        event_type='audit_critical',
                        event_details={
                            'critical_count': result.critical_count,
                            'warning_count': result.warning_count,
                            'findings': result.findings
                        },
                        severity='critical' if result.critical_count > 0 else 'warning'
                    )
                except Exception as save_err:
                    logger.debug(f"Не удалось сохранить инцидент аудита: {save_err}")

            elif result.warning_count > 0:
                logger.info(
                    f"⚠️ AUDIT CHECK: Предупреждения: {result.warning_count} "
                    f"({result.duration_ms}ms)"
                )
            else:
                logger.debug(f"AUDIT CHECK: OK ({result.duration_ms}ms)")

        except Exception as e:
            logger.warning(f"Ошибка при периодической проверке аудитов: {e}")

    def _aggregate_hourly(self) -> None:
        """Агрегирует данные сенсоров за последний полный час и сохраняет их в таблицу агрегатов."""
        # Вычисляем границы последнего полного часа
        now = datetime.now(timezone.utc)
        period_end = now.replace(minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(hours=1)

        # Запрос к базе: агрегируем по sensor_id за указанный период
        query = """
            SELECT sensor_id,
                   AVG(value) as avg_value,
                   MIN(value) as min_value,
                   MAX(value) as max_value,
                   COUNT(*) as count
            FROM sensor_polls
            WHERE timestamp >= ? AND timestamp < ?
            GROUP BY sensor_id
        """
        try:
            with self.storage._lock, self.storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (period_start.isoformat(), period_end.isoformat()))
                rows = cursor.fetchall()
                aggregates = []
                for row in rows:
                    sensor_id, avg_val, min_val, max_val, cnt = row
                    aggregates.append({
                        "sensor_id": sensor_id,
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                        "avg": avg_val,
                        "min": min_val,
                        "max": max_val,
                        "count": cnt,
                    })
                if aggregates:
                    saved = self.storage.save_sensor_aggregates_batch(aggregates)
                    logger.info(f"Сохранено {saved} агрегированных записей за период {period_start} - {period_end}")
        except Exception as e:
            logger.error(f"Ошибка при часовой агрегации телеметрии: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус агрегатора.

        Returns:
            Dict[str, Any]: Состояние агрегатора.
        """
        return {
            "is_running": self._running,
            "measurement_count": self._measurement_count,
            "enabled_sensors": self.config_manager.get_enabled_sensors(),
        }

    def get_last_measurement(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнюю записанную телеметрию.

        Returns:
            Optional[Dict[str, Any]]: Последняя телеметрия или None.
        """
        return self._last_measurements
