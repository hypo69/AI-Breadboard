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

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

try:
    from logger import logger
except ImportError:
    from logger import logger
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.file_collector import FileCollector
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
    ) -> None:
        """Инициализирует агрегатор телеметрии.

        Args:
            config_manager: Менеджер конфигурации (если None, создается новый).
            log_dir: Не используется, оставлен для обратной совместимости.
            storage: Экземпляр постоянного SQLite хранилища TelemetryStorage.
            sensor_collector: Коллектор аппаратных сенсоров.
            file_collector: Коллектор файловых событий.
        """
        self.config_manager = config_manager or TelemetryConfigManager()
        self.log_dir = log_dir
        self.storage = storage or TelemetryStorage.get_instance()

        self.sensor_collector = sensor_collector or SensorCollector(config_manager=self.config_manager)
        self.file_collector = file_collector or FileCollector(
            watch_dirs=self.config_manager._config.get("watch_directories", ["C:\\Users\\"])
        )

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._last_measurements: Dict[str, Any] = {}
        self._measurement_count = 0
        # Время запуска агрегатора и момент последней часовой агрегации
        self._start_time = datetime.now(timezone.utc)
        self._last_aggregation = self._start_time

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

        # Сбор сенсорных данных
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

        # После обычного поллинга проверяем необходимость часовой агрегации
        now = datetime.now(timezone.utc)
        fast_days = self.config_manager.get_fast_duration_days()
        if (now - self._start_time).days >= fast_days:
            if (now - self._last_aggregation).total_seconds() >= self.config_manager.get_aggregation_interval():
                self._aggregate_hourly()
                self._last_aggregation = now

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
