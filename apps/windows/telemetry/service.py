# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry Logger Service (Empty - No Storage)
# =============================================================================
# Description:
#   Фоновый сервис для непрерывного сбора метрик системы без сохранения.
#   Используется для сбора данных в памяти для последующего анализа.
#
# File: service.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Фоновый сервис посекундного сбора системных метрик без сохранения."""

import asyncio
import threading
import time
from typing import Any, Dict, Optional

from logger import logger
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.history_manager import HardwareHistoryManager


class TelemetryLoggerService:
    """Сервис периодического сбора системной телеметрии и аудита оборудования."""

    _instance: Optional[TelemetryLoggerService] = None

    def __init__(
        self,
        interval_sec: float = 1.0,
        top_processes: int = 20,
        collector: Optional[SystemCollector] = None,
        hardware_audit_interval_sec: float = 60.0,
    ) -> None:
        """Инициализирует сервис сбора системных метрик.

        Args:
            interval_sec: Интервал между замерами телеметрии в секундах (по умолчанию 1.0).
            top_processes: Лимит сохраняемых активных процессов (по умолчанию 20).
            collector: Экземпляр сборщика SystemCollector (опционально).
            hardware_audit_interval_sec: Интервал периодического аудита железа (по умолчанию 60.0).
        """
        self.interval_sec = max(0.2, interval_sec)
        self.top_processes = max(1, top_processes)
        self.hardware_audit_interval_sec = max(5.0, hardware_audit_interval_sec)
        self.collector = collector or SystemCollector()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Статистика сессии
        self._ticks_count = 0
        self._start_time: Optional[float] = None
        self._last_tick_time: Optional[float] = None
        self._last_hw_audit_time: Optional[float] = None
        self._last_error: Optional[str] = None
        self._last_snapshot: Optional[Any] = None

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
        """Запускает фоновый поток сбора телеметрии и мониторинга оборудования.

        Returns:
            bool: True если сервис успешно запущен, False если уже работал.
        """
        if self.is_running:
            logger.debug("Сервис сбора телеметрии уже запущен.")
            return False

        self._stop_event.clear()
        self._running = True
        self._start_time = time.time()
        self._ticks_count = 0
        self._last_error = None
        self._last_hw_audit_time = None

        self._thread = threading.Thread(
            target=self._worker_loop,
            name="TelemetryLoggerWorker",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            f"Фоновый сервис телеметрии запущен (интервал: {self.interval_sec}с, "
            f"аудит железа: {self.hardware_audit_interval_sec}с)"
        )
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
        """Основной рабочий цикл фонового сбора метрик и аудита изменений."""
        while not self._stop_event.is_set():
            loop_start = time.time()
            try:
                # 1. Сбор живого моментального снимка
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    task = asyncio.run_coroutine_threadsafe(
                        self.collector.get_snapshot(process_limit=self.top_processes),
                        loop,
                    )
                    snapshot = task.result(timeout=5.0)
                else:
                    snapshot = asyncio.run(self.collector.get_snapshot(process_limit=self.top_processes))

                self._last_snapshot = snapshot
                self._ticks_count += 1
                self._last_tick_time = time.time()

                # 2. Периодический аудит железа и фиксация изменений
                if (
                    self._last_hw_audit_time is None
                    or (loop_start - self._last_hw_audit_time) >= self.hardware_audit_interval_sec
                ):
                    try:
                        self.collector.archive_hardware_state(auto_diff=True)
                        self._last_hw_audit_time = loop_start
                    except Exception as hw_ex:
                        logger.debug(f"Ошибка при периодическом аудите железа: {hw_ex}")

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

        return {
            "is_running": self.is_running,
            "interval_sec": self.interval_sec,
            "top_processes_limit": self.top_processes,
            "hardware_audit_interval_sec": self.hardware_audit_interval_sec,
            "ticks_recorded": self._ticks_count,
            "uptime_seconds": uptime,
            "last_tick_epoch": self._last_tick_time,
            "last_hw_audit_epoch": self._last_hw_audit_time,
            "last_error": self._last_error,
        }

    @property
    def storage(self) -> HardwareHistoryManager:
        """Возвращает менеджер истории и архивов оборудования.

        Returns:
            HardwareHistoryManager: Менеджер архивного хранилища.
        """
        return self.collector.history_manager

    def get_last_snapshot(self) -> Optional[Any]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Any]: Последний снапшот или None.
        """
        return self._last_snapshot

    def record_event(
        self,
        event_type: str,
        event_details: Dict[str, Any],
    ) -> None:
        """Записывает событие в системный логгер.

        Args:
            event_type: Тип события (hardware_change, process_start, driver_update).
            event_details: Детали события.
        """
        logger.info(f"[Событие Telemetry] {event_type}: {event_details}")

