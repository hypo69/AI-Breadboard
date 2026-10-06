# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Service
# =============================================================================
# Description:
#   Фоновый сервис посекундного сбора системных метрик с сохранением в SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.service import TelemetryLoggerService
#
#     instance = TelemetryLoggerService.get_instance()
#
# File: service.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 13:59:00
# =============================================================================

from __future__ import annotations
"""Фоновый сервис периодического сбора системных метрик с сохранением в SQLite."""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional
try:
    from logger import logger
except ImportError:
    from logger import logger
from .collector import SystemCollector
from apps.windows.telemetry_research.hardware_history_manager import HardwareHistoryManager
from .sqlite import TelemetryStorage
from .telemetry_config import TelemetryConfigManager
from .w64_collector import AIW64Collector
from .w64_etw_collector import AIW64ETWCollector

class TelemetryLoggerService:
    """Сервис периодического сбора системной телеметрии, аудита оборудования и W64/ETW событий в SQLite."""
    _instance: Optional[TelemetryLoggerService] = None

    def __init__(
        self,
        interval_sec: Optional[float] = None,
        top_processes: Optional[int] = None,
        collector: Optional[SystemCollector] = None,
        storage: Optional[TelemetryStorage] = None,
        hardware_audit_interval_sec: Optional[float] = None,
        rollup_interval_sec: Optional[float] = None,
        enable_w64: Optional[bool] = None,
        config_manager: Optional[TelemetryConfigManager] = None,
        db_cleanup_interval_sec: Optional[float] = None,
    ) -> None:
        """Инициализирует сервис сбора системных метрик.

        Args:
            interval_sec: Интервал между замерами телеметрии в секундах (по умолчанию из config.json).
            top_processes: Лимит сохраняемых активных процессов (по умолчанию из config.json).
            collector: Экземпляр сборщика SystemCollector (опционально).
            storage: Экземпляр хранилища TelemetryStorage (опционально).
            hardware_audit_interval_sec: Интервал периодического аудита железа (по умолчанию из config.json).
            rollup_interval_sec: Интервал запуска обобщения старых данных (по умолчанию из config.json).
            enable_w64: Включение подсистемы сбора событий W64/ETW (по умолчанию из config.json).
            config_manager: Менеджер конфигурации.
            db_cleanup_interval_sec: Интервал фонового контроля размера базы данных (сек).
        """
        self.config_manager = config_manager or TelemetryConfigManager()
        self._custom_interval_set = (interval_sec is not None)
        self.interval_sec = max(
            0.1,
            interval_sec if interval_sec is not None else self.config_manager.get_interval_seconds()
        )
        self.top_processes = max(
            1,
            top_processes if top_processes is not None else self.config_manager.get_effective_process_limit()
        )
        self.hardware_audit_interval_sec = max(
            1.0,
            hardware_audit_interval_sec if hardware_audit_interval_sec is not None else self.config_manager.get_heavy_interval_seconds()
        )
        self.rollup_interval_sec = max(
            1.0,
            rollup_interval_sec if rollup_interval_sec is not None else self.config_manager.get_aggregation_interval()
        )
        self.collector = collector or SystemCollector()
        self.storage = storage or TelemetryStorage.get_instance()
        self.db_cleanup_interval_sec = max(
            5.0,
            db_cleanup_interval_sec if db_cleanup_interval_sec is not None else self.config_manager.get_db_cleanup_interval_seconds()
        )

        cfg = self.config_manager.get_config()
        w64_cfg = cfg.get('w64_collector', {})
        self.enable_w64 = enable_w64 if enable_w64 is not None else w64_cfg.get('enabled', True)

        self._w64_collector: Optional[AIW64Collector] = None
        self._w64_etw_collector: Optional[AIW64ETWCollector] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ticks_count = 0
        self._start_time: Optional[float] = None
        self._last_tick_time: Optional[float] = None
        self._last_hw_audit_time: Optional[float] = None
        self._last_rollup_time: Optional[float] = None
        self._last_db_cleanup_time: Optional[float] = None
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

    @property
    def w64_collector(self) -> Optional[AIW64Collector]:
        """Возвращает сборщик W64 событий (создается лениво при enable_w64)."""
        if self._w64_collector is None and self.enable_w64:
            self._init_w64_collectors()
        return self._w64_collector

    @w64_collector.setter
    def w64_collector(self, val: Optional[AIW64Collector]) -> None:
        self._w64_collector = val

    @property
    def w64_etw_collector(self) -> Optional[AIW64ETWCollector]:
        """Возвращает сборщик ETW событий (создается лениво при enable_w64)."""
        if self._w64_etw_collector is None and self.enable_w64:
            self._init_w64_collectors()
        return self._w64_etw_collector

    @w64_etw_collector.setter
    def w64_etw_collector(self, val: Optional[AIW64ETWCollector]) -> None:
        self._w64_etw_collector = val

    def _init_w64_collectors(self) -> None:
        """Инициализирует W64 и ETW сборщики при необходимости."""
        if not self.enable_w64:
            return
        cfg = self.config_manager.get_config()
        w64_cfg = cfg.get('w64_collector', {})
        if self._w64_collector is None:
            self._w64_collector = AIW64Collector(
                storage=self.storage,
                enable_file_monitoring=w64_cfg.get('enable_file_monitoring', True),
                enable_process_monitoring=w64_cfg.get('enable_process_monitoring', True),
                enable_registry_monitoring=w64_cfg.get('enable_registry_monitoring', True),
                enable_network_monitoring=w64_cfg.get('enable_network_monitoring', True),
                enable_event_log_monitoring=w64_cfg.get('enable_event_log_monitoring', True),
            )
        if self._w64_etw_collector is None:
            self._w64_etw_collector = AIW64ETWCollector(
                storage=self.storage,
                enable_process_trace=w64_cfg.get('enable_process_trace', True),
                enable_disk_trace=w64_cfg.get('enable_disk_trace', True),
                enable_network_trace=w64_cfg.get('enable_network_trace', True),
                enable_registry_trace=w64_cfg.get('enable_registry_trace', True),
            )

    def start(self) -> bool:
        """Запускает фоновый поток сбора телеметрии, аудита оборудования и W64/ETW сборщиков.

        Returns:
            bool: True если сервис успешно запущен, False если уже работал.
        """
        if self.is_running:
            logger.debug('Сервис сбора телеметрии уже запущен.')
            return False
        self._stop_event.clear()
        self._running = True
        self._start_time = time.time()
        self._ticks_count = 0
        self._last_error = None
        self._last_hw_audit_time = None
        self._last_db_cleanup_time = None

        if self.enable_w64:
            self._init_w64_collectors()
            if self.w64_collector:
                self.w64_collector.start()
            if self.w64_etw_collector:
                self.w64_etw_collector.start()

        # При каждом старте телеметрии фиксируем снимок автозапуска в хранилище
        try:
            startup_entry = self.collector.archive_startup_state(auto_diff=True)
            if startup_entry:
                self.storage.save_startup_archive(startup_entry)
        except Exception as st_init_ex:
            logger.debug(f'Фиксация снимка автозапуска при старте телеметрии: {st_init_ex}')

        self._thread = threading.Thread(target=self._worker_loop, name='TelemetryLoggerWorker', daemon=True)
        self._thread.start()
        logger.info(f'Фоновый сервис телеметрии запущен в БД (интервал: {self.interval_sec}с, аудит железа: {self.hardware_audit_interval_sec}с, W64: {self.enable_w64}, БД: {self.storage.db_path})')
        return True

    def stop(self) -> bool:
        """Останавливает фоновый поток сбора телеметрии и W64/ETW сборщиков.

        Returns:
            bool: True если сервис был остановлен, False если он не работал.
        """
        if not self._running:
            return False
        self._running = False
        self._stop_event.set()

        if self.w64_collector:
            self.w64_collector.stop()
        if self.w64_etw_collector:
            self.w64_etw_collector.stop()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        try:
            self.storage.flush()
        except Exception:
            pass
        logger.info(f'Фоновый сервис телеметрии остановлен. Всего тиков: {self._ticks_count}')
        return True

    def sync_config_from_manager(self) -> bool:
        """Синхронизирует интервалы и настройки сервиса из менеджера конфигурации при их изменении.

        Returns:
            bool: True если конфигурация изменилась и была применена, иначе False.
        """
        self.config_manager.check_tc_mode_auto_switch()
        if self.config_manager.check_and_reload():
            if not self._custom_interval_set:
                self.interval_sec = max(0.1, self.config_manager.get_interval_seconds())
            self.top_processes = max(1, self.config_manager.get_effective_process_limit())
            self.hardware_audit_interval_sec = max(1.0, self.config_manager.get_heavy_interval_seconds())
            self.db_cleanup_interval_sec = max(5.0, self.config_manager.get_db_cleanup_interval_seconds())
            self.rollup_interval_sec = max(1.0, self.config_manager.get_aggregation_interval())
            logger.info(
                f"🔄 [Сервис телеметрии] Конфигурация config.json обновлена 'на лету': "
                f"базовый={self.interval_sec}с, аудит железа={self.hardware_audit_interval_sec}с, "
                f"очистка БД={self.db_cleanup_interval_sec}с, топ процессов={self.top_processes}, mode={self.config_manager.get_telemetry_mode()}"
            )
            return True
        return False

    def _worker_loop(self) -> None:
        """Основной рабочий цикл фонового сбора метрик, записи в БД и аудита изменений."""
        while not self._stop_event.is_set():
            loop_start = time.time()
            try:
                # Проверка изменения config.json 'на лету'
                self.sync_config_from_manager()

                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    task = asyncio.run_coroutine_threadsafe(self.collector.get_snapshot(process_limit=self.top_processes), loop)
                    snapshot = task.result(timeout=30.0)
                else:
                    snapshot = asyncio.run(self.collector.get_snapshot(process_limit=self.top_processes))
                self._last_snapshot = snapshot
                self._ticks_count += 1
                self._last_tick_time = time.time()
                try:
                    self.storage.save_snapshot(snapshot, top_n=self.top_processes)
                except Exception as db_err:
                    logger.warning(f'Ошибка сохранения снимка телеметрии в БД: {db_err}')
                if self._last_hw_audit_time is None or loop_start - self._last_hw_audit_time >= self.hardware_audit_interval_sec:
                    try:
                        archive_entry = self.collector.archive_hardware_state(auto_diff=True)
                        if archive_entry:
                            self.storage.save_hardware_archive(archive_entry)
                    except Exception as hw_ex:
                        logger.debug(f'Ошибка при периодическом аудите железа: {hw_ex}')
                    try:
                        startup_archive = self.collector.archive_startup_state(auto_diff=True)
                        if startup_archive:
                            self.storage.save_startup_archive(startup_archive)
                    except Exception as st_ex:
                        logger.debug(f'Ошибка при периодическом аудите автозапуска: {st_ex}')
                    try:
                        self.collector.get_extended_system_audit()
                    except Exception as ext_ex:
                        logger.debug(f'Ошибка при периодическом расширенном аудите: {ext_ex}')
                    self._last_hw_audit_time = loop_start
                if self._last_rollup_time is None or loop_start - self._last_rollup_time >= self.rollup_interval_sec:
                    try:
                        self.run_rollups()
                        self._last_rollup_time = loop_start
                    except Exception as roll_ex:
                        logger.debug(f'Ошибка при периодическом обобщении процессов: {roll_ex}')
                if self._last_db_cleanup_time is None or loop_start - self._last_db_cleanup_time >= self.db_cleanup_interval_sec:
                    try:
                        self.cleanup_db()
                        self._last_db_cleanup_time = loop_start
                    except Exception as clean_ex:
                        logger.debug(f'Ошибка при периодическом контроле размера БД: {clean_ex}')
            except (RuntimeError, ValueError) as shut_ex:
                if 'shutdown' in str(shut_ex).lower() or 'closed file' in str(shut_ex).lower():
                    break
                self._last_error = str(shut_ex)
                logger.debug(f'Ошибка при сборе системной телеметрии: {shut_ex}')
            except Exception as ex:
                self._last_error = str(ex)
                logger.debug(f'Ошибка при сборе системной телеметрии: {ex}')
            elapsed = time.time() - loop_start
            sleep_time = max(0.01, self.interval_sec - elapsed)
            if self._stop_event.wait(timeout=sleep_time):
                break

    def run_rollups(self) -> Dict[str, Any]:
        """Принудительно запускает процедуры обобщения устаревших метрик процессов.

        Returns:
            Dict[str, Any]: Сводная статистика обобщения за 2 минуты и за 1 день.
        """
        short_res = self.storage.aggregate_process_metrics_2min(cutoff_seconds=120)
        daily_res = self.storage.aggregate_process_metrics_daily(cutoff_days=1)
        return {'rollup_2min': short_res, 'rollup_daily': daily_res}

    def cleanup_db(self) -> Dict[str, Any]:
        """Запускает процедуру контроля размера и усечения базы данных телеметрии.

        Returns:
            Dict[str, Any]: Отчет о результатах контроля размера.
        """
        return self.storage.enforce_size_limit()

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус сервиса телеметрии.

        Returns:
            Dict[str, Any]: Словарь с состоянием и статистикой работы сервиса.
        """
        uptime = round(time.time() - self._start_time, 1) if self._start_time and self.is_running else 0.0
        return {'is_running': self.is_running, 'interval_sec': self.interval_sec, 'top_processes_limit': self.top_processes, 'hardware_audit_interval_sec': self.hardware_audit_interval_sec, 'ticks_recorded': self._ticks_count, 'uptime_seconds': uptime, 'last_tick_epoch': self._last_tick_time, 'last_hw_audit_epoch': self._last_hw_audit_time, 'last_error': self._last_error, 'storage_stats': self.storage.get_storage_stats()}

    def get_last_snapshot(self) -> Optional[Any]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Any]: Последний снапшот или None.
        """
        return self._last_snapshot

    def get_history(self, limit: int=60) -> List[Dict[str, Any]]:
        """Возвращает историю системных снимков из SQLite базы данных.

        Args:
            limit: Количество последних записей.

        Returns:
            List[Dict[str, Any]]: Список исторических срезов.
        """
        return self.storage.get_snapshots(limit=limit)

    def record_event(self, event_type: str, event_details: Dict[str, Any], severity: str='info') -> int:
        """Записывает событие в SQLite базу данных телеметрии.

        Args:
            event_type: Тип события (hardware_change, process_start, driver_update).
            event_details: Детали события.
            severity: Уровень серьезности события.

        Returns:
            int: ID добавленной записи события.
        """
        logger.info(f'[Событие Telemetry] {event_type}: {event_details}')
        try:
            return self.storage.save_event(event_type, event_details, severity=severity)
        except Exception as ex:
            logger.error(f'Не удалось записать событие в базу данных: {ex}')
            return 0