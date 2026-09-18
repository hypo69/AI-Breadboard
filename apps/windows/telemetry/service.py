# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry Logger Service
# =============================================================================
# Description:
#   Фоновый сервис для непрерывного сбора и сохранения метрик системы
#   и Top-20 процессов в SQLite с интервалом в 1 секунду.
#
# Examples:
#   >>> from apps.windows.telemetry.service import TelemetryLoggerService
#   >>> service = TelemetryLoggerService(interval_sec=1.0, top_processes=20)
#   >>> service.start()
#   >>> # ... работа приложения ...
#   >>> service.stop()
#
# File: service.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Фоновый сервис посекундного логгирования телеметрии Windows в SQLite."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from src.logger import logger
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.storage import TelemetryStorage


class TelemetryLoggerService:
    """Сервис периодического сбора и сохранения системной телеметрии."""

    _instance: Optional[TelemetryLoggerService] = None

    def __init__(
        self,
        interval_sec: float = 1.0,
        top_processes: int = 20,
        storage: Optional[TelemetryStorage] = None,
        collector: Optional[SystemCollector] = None,
    ) -> None:
        """Инициализирует сервис сбора системных метрик.

        Args:
            interval_sec: Интервал между замерами в секундах (по умолчанию 1.0).
            top_processes: Лимит сохраняемых активных процессов (по умолчанию 20).
            storage: Экземпляр хранилища TelemetryStorage (опционально).
            collector: Экземпляр сборщика SystemCollector (опционально).
        """
        self.interval_sec = max(0.2, interval_sec)
        self.top_processes = max(1, top_processes)
        self.storage = storage or TelemetryStorage()
        self.collector = collector or SystemCollector()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Статистика сессии
        self._ticks_count = 0
        self._start_time: Optional[float] = None
        self._last_tick_time: Optional[float] = None
        self._last_error: Optional[str] = None

    @classmethod
    def get_instance(cls) -> TelemetryLoggerService:
        """Возвращает глобальный синглтон сервиса телеметрии.

        Returns:
            TelemetryLoggerService: Единственный экземпляр сервиса.
        """
        if cls._instance is None:
            cls._instance = TelemetryLoggerService()
        return cls._instance

    @property
    def is_running(self) -> bool:
        """Проверяет, запущен ли фоновый сбор телеметрии.

        Returns:
            bool: True если сбор активен, иначе False.
        """
        return self._running and self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        """Запускает фоновый поток сбора телеметрии.

        Returns:
            bool: True если сервис успешно запущен, False если уже работал.
        """
        if self.is_running:
            logger.debug("Сервис логирования телеметрии уже запущен.")
            return False

        self._stop_event.clear()
        self._running = True
        self._start_time = time.time()
        self._ticks_count = 0
        self._last_error = None

        self._thread = threading.Thread(
            target=self._worker_loop,
            name="TelemetryLoggerWorker",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Фоновый сервис телеметрии запущен (интервал: {self.interval_sec}с, процессов: {self.top_processes})")
        return True

    def stop(self) -> bool:
        """Останавливает фоновый поток сбора телеметрии.

        Returns:
            bool: True если сервис был остановлен, False если он не работал.
        """
        if not self._running:
            return False

        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        logger.info(f"Фоновый сервис телеметрии остановлен. Всего тиков: {self._ticks_count}")
        return True

    def _worker_loop(self) -> None:
        """Основной рабочий цикл фонового сбора метрик."""
        while not self._stop_event.is_set():
            loop_start = time.time()
            try:
                snapshot = self.collector.get_snapshot(process_limit=self.top_processes)
                self.storage.save_snapshot(snapshot, top_n=self.top_processes)
                self._ticks_count += 1
                self._last_tick_time = time.time()
            except Exception as ex:
                self._last_error = str(ex)
                logger.debug(f"Ошибка при сборе системной телеметрии: {ex}")

            # Рассчитываем точное время сна для сохранения равномерного интервала
            elapsed = time.time() - loop_start
            sleep_time = max(0.01, self.interval_sec - elapsed)
            if self._stop_event.wait(timeout=sleep_time):
                break

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус сервиса телеметрии.

        Returns:
            Dict[str, Any]: Словарь с состоянием и статистикой работы сервиса.
        """
        uptime = round(time.time() - self._start_time, 1) if self._start_time and self.is_running else 0.0
        storage_stats = self.storage.get_storage_stats()

        return {
            "is_running": self.is_running,
            "interval_sec": self.interval_sec,
            "top_processes_limit": self.top_processes,
            "ticks_recorded": self._ticks_count,
            "uptime_seconds": uptime,
            "last_tick_epoch": self._last_tick_time,
            "last_error": self._last_error,
            "storage": storage_stats,
        }
