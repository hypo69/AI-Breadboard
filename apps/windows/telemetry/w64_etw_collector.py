# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - W64 Etw Collector
# =============================================================================
# Description:
#   ETW Collector для сбора низкоуровневых событий ядра и журналов аудита Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.w64_etw_collector import AIW64ETWCollector
#
#     service = AIW64ETWCollector()
#
# File: w64_etw_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""ETW Collector для сбора низкоуровневых событий ядра и журналов аудита Windows."""

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from logger import logger
from .models import ETWTraceEvent, W64CollectorStatus
from .sqlite import TelemetryStorage

class AIW64ETWCollector:
    """Сборщик низкоуровневых событий через ETW и журналы аудита Windows."""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_process_trace: bool = True,
        enable_disk_trace: bool = True,
        enable_network_trace: bool = True,
        enable_registry_trace: bool = True,
        poll_interval_sec: float = 5.0,
        storage: Optional[TelemetryStorage] = None,
        on_event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """Инициализация ETW сборщика телеметрии.

        Args:
            log_dir: Директория для сохранения JSONL логов ETW.
            enable_process_trace: Трассировка создания/завершения процессов (ID 4688).
            enable_disk_trace: Трассировка операций файлового аудита (ID 4663).
            enable_network_trace: Трассировка сетевых подключений Windows Filtering Platform.
            enable_registry_trace: Трассировка изменений ключей аудита реестра.
            poll_interval_sec: Интервал между выборками событий ETW (сек).
            storage: Экземпляр хранилища TelemetryStorage.
            on_event_callback: Callback-обработчик каждого зафиксированного события.
        """
        if log_dir is None:
            appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
            self.log_dir = str(Path(appdata) / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs' / 'etw')
        else:
            self.log_dir = log_dir

        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        self.enable_process_trace = enable_process_trace
        self.enable_disk_trace = enable_disk_trace
        self.enable_network_trace = enable_network_trace
        self.enable_registry_trace = enable_registry_trace
        self.poll_interval = max(1.0, poll_interval_sec)
        self.storage = storage or TelemetryStorage.get_instance()
        self.on_event_callback = on_event_callback

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_counter = 0
        self._last_event_time: Optional[str] = None
        logger.info(f'AIW64ETWCollector инициализирован. Директория логов: {self.log_dir}')

    def start(self) -> bool:
        """Запустить фоновый поток сбора ETW событий.

        Returns:
            bool: True если сборщик успешно запущен, False если уже работал.
        """
        if self._running:
            logger.warning('AIW64ETWCollector уже запущен')
            return False

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._etw_loop, name='AIW64ETWWorker', daemon=True)
        self._thread.start()
        logger.info('AIW64ETWCollector успешно запущен')
        return True

    def stop(self) -> bool:
        """Остановить фоновый поток ETW сбора.

        Returns:
            bool: True если сборщик остановлен, False если не был активен.
        """
        if not self._running:
            return False

        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info(f'AIW64ETWCollector остановлен. Всего зафиксировано событий: {self._event_counter}')
        return True

    def _etw_loop(self) -> None:
        """Основной рабочий цикл выборки событий ETW."""
        while not self._stop_event.is_set():
            try:
                self._collect_etw_events()
                self._stop_event.wait(timeout=self.poll_interval)
            except Exception as ex:
                logger.error(f'Ошибка в цикле ETW сборщика: {ex}')

    def _collect_etw_events(self) -> None:
        """Собрать порцию событий из включенных провайдеров."""
        if os.name != 'nt':
            return

        if self.enable_process_trace:
            self._collect_process_events()
        if self.enable_disk_trace:
            self._collect_file_events()
        if self.enable_network_trace:
            self._collect_network_events()
        if self.enable_registry_trace:
            self._collect_registry_events()

    def _collect_process_events(self) -> None:
        """Собрать события создания процессов (Security ID 4688)."""
        try:
            ps_script = """
            $startTime = (Get-Date).AddMinutes(-1)
            $events = Get-WinEvent -FilterHashtable @{
                LogName = 'Security'
                Id = 4688
                StartTime = $startTime
            } -MaxEvents 50 -ErrorAction SilentlyContinue

            foreach ($e in $events) {
                $xml = [xml]$e.ToXml()
                $data = @{}
                foreach ($d in $xml.Event.EventData.Data) {
                    $data[$d.Name] = $d.'#text'
                }
                $data | ConvertTo-Json -Compress
            }
            """
            res = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', f'& {{ {ps_script} }}'],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_process_create', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий процессов ETW: {ex}')

    def _collect_file_events(self) -> None:
        """Собрать события файловых операций (Security ID 4663)."""
        try:
            ps_script = """
            $startTime = (Get-Date).AddMinutes(-1)
            $events = Get-WinEvent -FilterHashtable @{
                LogName = 'Security'
                Id = 4663
                StartTime = $startTime
            } -MaxEvents 50 -ErrorAction SilentlyContinue

            foreach ($e in $events) {
                $xml = [xml]$e.ToXml()
                $data = @{}
                foreach ($d in $xml.Event.EventData.Data) {
                    $data[$d.Name] = $d.'#text'
                }
                $data | ConvertTo-Json -Compress
            }
            """
            res = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', f'& {{ {ps_script} }}'],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_file_access', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий файлов ETW: {ex}')

    def _collect_network_events(self) -> None:
        """Собрать события сетевых блокировок/подключений WFP (Security ID 5156/5158)."""
        try:
            ps_script = """
            $startTime = (Get-Date).AddMinutes(-1)
            $events = Get-WinEvent -FilterHashtable @{
                LogName = 'Security'
                Id = 5156,5158
                StartTime = $startTime
            } -MaxEvents 50 -ErrorAction SilentlyContinue

            foreach ($e in $events) {
                $xml = [xml]$e.ToXml()
                $data = @{}
                foreach ($d in $xml.Event.EventData.Data) {
                    $data[$d.Name] = $d.'#text'
                }
                $data | ConvertTo-Json -Compress
            }
            """
            res = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', f'& {{ {ps_script} }}'],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_network_connection', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора сетевых событий ETW: {ex}')

    def _collect_registry_events(self) -> None:
        """Собрать события аудита реестра (Security ID 4657)."""
        try:
            ps_script = """
            $startTime = (Get-Date).AddMinutes(-1)
            $events = Get-WinEvent -FilterHashtable @{
                LogName = 'Security'
                Id = 4657
                StartTime = $startTime
            } -MaxEvents 50 -ErrorAction SilentlyContinue

            foreach ($e in $events) {
                $xml = [xml]$e.ToXml()
                $data = @{}
                foreach ($d in $xml.Event.EventData.Data) {
                    $data[$d.Name] = $d.'#text'
                }
                $data | ConvertTo-Json -Compress
            }
            """
            res = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', f'& {{ {ps_script} }}'],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_registry_access', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий реестра ETW: {ex}')

    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Записать событие в потоковый JSONL файл и базу данных SQLite.

        Args:
            event_type: Тип события ETW.
            event_data: Словарь с полями из журнала событий.
        """
        self._event_counter += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        log_file = Path(self.log_dir) / f'{event_type}_{date_str}.jsonl'

        payload = {
            'event_id': f'etw_{int(time.time())}_{self._event_counter}',
            'timestamp': now_iso,
            'event_type': event_type,
            'provider': 'Microsoft-Windows-Security-Auditing',
            'data': event_data,
        }
        self._last_event_time = now_iso

        # 1. Запись в JSONL
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(payload, ensure_ascii=False) + '\n')
        except Exception as ex:
            logger.warning(f'Не удалось записать JSONL лог ETW {event_type}: {ex}')

        # 2. Сохранение в SQLite TelemetryStorage
        if self.storage:
            try:
                db_record = {
                    'event_id': payload['event_id'],
                    'timestamp': now_iso,
                    'event_type': event_type,
                    'path': event_data.get('ObjectName') or event_data.get('NewProcessName'),
                    'pid': event_data.get('ProcessId') or event_data.get('NewProcessId'),
                    'name': event_data.get('ProcessName') or event_data.get('SubjectUserName'),
                    'details': event_data,
                }
                self.storage.save_w64_event(db_record, provider='w64_etw_collector')
            except Exception as ex:
                logger.debug(f'Ошибка сохранения ETW события в БД: {ex}')

        # 3. Передача в callback
        if self.on_event_callback:
            try:
                self.on_event_callback(payload)
            except Exception as ex:
                logger.debug(f'Ошибка в ETW on_event_callback: {ex}')

    def get_status(self) -> Dict[str, Any]:
        """Получить диагностический статус ETW сборщика.

        Returns:
            Dict[str, Any]: Словарь со статусом и счетчиками.
        """
        status = W64CollectorStatus(
            running=self._running,
            events_count=self._event_counter,
            log_dir=self.log_dir,
            last_event_time=self._last_event_time,
        )
        return status.model_dump()

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить список последних событий ETW из SQLite хранилища.

        Args:
            event_type: Фильтр по типу события.
            limit: Максимальное число записей.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        if self.storage:
            return self.storage.get_w64_events(event_type=event_type, provider='w64_etw_collector', limit=limit)
        return []
