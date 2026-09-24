# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Stream Aggregator
# =============================================================================
# Description:
#   Централизованный агрегатор телеметрии, синхронизирующий фоновый сбор данных
#   со всех сенсоров и запись в JSON с инкрементальным контролем.
#
# File: aggregator.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Центральный агрегатор телеметрии для сбора данных со всех сенсоров."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.file_collector import FileCollector
from apps.windows.telemetry.json_logger import TelemetryJsonLogger
from apps.windows.telemetry.storage import TelemetryStorage


class TelemetryAggregator:
    """Централизованный агрегатор телеметрии и сенсорного сбора в базу данных и лог."""

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
        """Возвращает минимальный интервал среди всех сенсоров.

        Returns:
            float: Минимальный интервал в секундах.
        """
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

        # Сбор данных от всех сенсоров
        hardware_data = self.sensor_collector.get_hardware_snapshot()
        file_events = self.file_collector.get_recent_events()

        sensors_list = hardware_data.get("sensors", [])

        try:
            if sensors_list:
                self.logger.record_sensors(sensors_list, timestamp=now_iso)
                self.storage.save_sensor_polls_batch(sensors_list, timestamp=now_iso)
            else:
                self.logger.log({
                    "timestamp": now_iso,
                    "measurement_number": self._measurement_count,
                    "hardware": hardware_data,
                    "file_events": file_events,
                })
            logger.debug(f"Записана телеметрия #{self._measurement_count} ({len(sensors_list)} сенсоров в БД и лог)")
        except Exception as e:
            logger.error(f"Ошибка при записи телеметрии: {e}")

        self._last_measurements = {
            "timestamp": now_iso,
            "sensors": sensors_list,
            "hardware": hardware_data,
            "file_events": file_events,
        }

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус агрегатора.

        Returns:
            Dict[str, Any]: Состояние агрегатора.
        """
        return {
            "is_running": self._running,
            "measurement_count": self._measurement_count,
            "log_dir": self.log_dir,
            "log_filename": self.logger.filename,
            "enabled_sensors": self.config_manager.get_enabled_sensors(),
        }

    def get_last_measurement(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнюю записанную телеметрию.

        Returns:
            Optional[Dict[str, Any]]: Последняя телеметрия или None.
        """
        return self._last_measurements
