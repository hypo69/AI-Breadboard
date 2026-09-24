# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry Logger Service with SQLite Database Storage
# =============================================================================
# Description:
#   Фоновый сервис непрерывного сбора метрик системы и сохранения их в базу данных SQLite.
#   Фиксирует системные снапшоты, активные процессы, события и периодический аудит железа.
#
# Examples:
#   >>> from apps.windows.telemetry.service import TelemetryLoggerService
#   >>> service = TelemetryLoggerService.get_instance()
#   >>> service.start()
#
# File: service.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Фоновый сервис посекундного сбора системных метрик с сохранением в SQLite."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.history_manager import HardwareHistoryManager
from apps.windows.telemetry.storage import TelemetryStorage


class TelemetryLoggerService:
    """Сервис периодического сбора системной телеметрии и аудита оборудования в SQLite."""

    _instance: Optional[TelemetryLoggerService] = None

    def __init__(
        self,
        interval_sec: float = 1.0,
        top_processes: int = 20,
        collector: Optional[SystemCollector] = None,
        storage: Optional[TelemetryStorage] = None,
        hardware_audit_interval_sec: float = 60.0,
    ) -> None:
        """Инициализирует сервис сбора системных метрик.

        Args:
            interval_sec: Интервал между замерами телеметрии в секундах (по умолчанию 1.0).
            top_processes: Лимит сохраняемых активных процессов (по умолчанию 20).
            collector: Экземпляр сборщика SystemCollector (опционально).
            storage: Экземпляр хранилища TelemetryStorage (опционально).
            hardware_audit_interval_sec: Интервал периодического аудита железа (по умолчанию 60.0).
        """
        self.interval_sec = max(0.2, interval_sec)
        self.top_processes = max(1, top_processes)
        self.hardware_audit_interval_sec = max(5.0, hardware_audit_interval_sec)
        self.collector = collector or SystemCollector()
        self.storage = storage or TelemetryStorage.get_instance()

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

    @property
    def history_manager(self) -> HardwareHistoryManager:
        """Возвращает менеджер истории оборудования."""
        return self.collector.history_manager

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
            f"Фоновый сервис телеметрии запущен в БД (интервал: {self.interval_sec}с, "
            f"аудит железа: {self.hardware_audit_interval_sec}с, БД: {self.storage.db_path})"
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
        """Основной рабочий цикл фонового сбора метрик, записи в БД и аудита изменений."""
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

                # Сохранение среза в SQLite базу данных
                try:
                    self.storage.save_snapshot(snapshot, top_n=self.top_processes)
                except Exception as db_err:
                    logger.warning(f"Ошибка сохранения снимка телеметрии в БД: {db_err}")

                # 2. Периодический аудит железа и фиксация изменений
                if (
                    self._last_hw_audit_time is None
                    or (loop_start - self._last_hw_audit_time) >= self.hardware_audit_interval_sec
                ):
                    try:
                        archive_entry = self.collector.archive_hardware_state(auto_diff=True)
                        if archive_entry:
                            self.storage.save_hardware_archive(archive_entry)
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
            "storage_stats": self.storage.get_storage_stats(),
        }

    def get_last_snapshot(self) -> Optional[Any]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Any]: Последний снапшот или None.
        """
        return self._last_snapshot

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        """Возвращает историю системных снимков из SQLite базы данных.

        Args:
            limit: Количество последних записей.

        Returns:
            List[Dict[str, Any]]: Список исторических срезов.
        """
        return self.storage.get_snapshots(limit=limit)

    def record_event(
        self,
        event_type: str,
        event_details: Dict[str, Any],
        severity: str = "info",
    ) -> int:
        """Записывает событие в SQLite базу данных телеметрии.

        Args:
            event_type: Тип события (hardware_change, process_start, driver_update).
            event_details: Детали события.
            severity: Уровень серьезности события.

        Returns:
            int: ID добавленной записи события.
        """
        logger.info(f"[Событие Telemetry] {event_type}: {event_details}")
        try:
            return self.storage.save_event(event_type, event_details, severity=severity)
        except Exception as ex:
            logger.error(f"Не удалось записать событие в базу данных: {ex}")
            return 0
