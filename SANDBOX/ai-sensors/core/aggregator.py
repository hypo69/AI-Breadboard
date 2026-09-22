# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Sensors Telemetry Aggregator
# =============================================================================
# Description:
#   Централизованный агрегатор телеметрии синхронизирующий сбор данных со всех сенсоров.
#
# File: aggregator.py
# Project: ai-sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Центральный агрегатор телеметрии для сбора данных со всех сенсоров."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logger import logger

from utils.config import ConfigManager
from collectors.sensors import SensorCollector
from collectors.files import FileCollector
from loggers.json_logger import TelemetryJsonLogger


class TelemetryAggregator:
    """Централизованный агрегатор телеметрии с сенсорного сбора."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        log_dir: Optional[str] = None,
    ) -> None:
        """Инициализирует агрегатор телеметрии.

        Args:
            config_manager: Менеджер конфигурации (если None, создается новый).
            log_dir: Директория для логов (по умолчанию: %APPDATA%\\AI-Breadboard\\apps\\logs).
        """
        self.config_manager = config_manager or ConfigManager()
        self.log_dir = log_dir or self._get_default_log_dir()

        # Инициализация коллекторов
        self.sensor_collector = SensorCollector(config_manager=self.config_manager)
        self.file_collector = FileCollector(
            watch_dirs=self.config_manager._config.get("watch_directories", ["C:\\Users\\"])
        )
        self.logger = TelemetryJsonLogger(
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
        import os
        appdata = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return os.path.join(appdata, "AI-Breadboard", "apps", "logs")

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
        logger.info("Агрегатор телеметрии остановлен")
        return True

    def _worker_loop(self) -> None:
        """Основной рабочий цикл агрегатора."""
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Ошибка при сборе телеметрии: {e}")

            # Используем персонализированные интервалы для каждого сенсора
            # Ждем наименьший интервал, чтобы не пропустить ничего
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

        # Сбор данных от всех сенсоров
        hardware_data = self.sensor_collector.get_hardware_snapshot()
        file_events = self.file_collector.get_recent_events()

        # Формирование записи
        measurement = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurement_number": self._measurement_count,
            "hardware": hardware_data,
            "file_events": file_events,
        }

        # Запись в JSON
        try:
            self.logger.log(measurement)
            logger.debug(f"Записана телеметрия #{self._measurement_count}")
        except Exception as e:
            logger.error(f"Ошибка при записи телеметрии: {e}")

        # Сохраняем текущие значения для сравнения в следующий раз
        self._last_measurements = {
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
