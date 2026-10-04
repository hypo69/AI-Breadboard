# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - W64 Collector
# =============================================================================
# Description:
#   AI Windows 64-bit Collector - модуль сбора детальных системных событий телеметрии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.w64_collector import AIW64Collector
#
#     service = AIW64Collector()
#
# File: w64_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 04:48:00
# =============================================================================

from __future__ import annotations
"""AI Windows 64-bit Collector - модуль сбора детальных системных событий телеметрии."""

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from logger import logger
from .models import W64CollectorStatus, W64SystemEvent
from .sqlite import TelemetryStorage

_file_write_lock = threading.Lock()

def _append_jsonl_safely(file_path: Path, data: Dict[str, Any], retries: int = 4, retry_delay: float = 0.05) -> bool:
    """Безопасная запись JSONL строки с повторными попытками при блокировке файла.

    Args:
        file_path: Путь к целевому файлу JSONL.
        data: Словарь с данными для сериализации в JSON.
        retries: Количество попыток записи при ошибке доступа.
        retry_delay: Задержка между попытками (сек).

    Returns:
        bool: True если запись успешна, иначе исключение.
    """
    line = json.dumps(data, ensure_ascii=False) + '\n'
    for attempt in range(retries):
        try:
            with _file_write_lock:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(line)
            return True
        except (PermissionError, OSError) as ex:
            if attempt < retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                raise ex
    return False

class AIW64Collector:
    """Максимально детальный сборщик событий Windows 64-bit для подсистемы телеметрии.

    Фиксирует непрерывные изменения системного состояния:
    - Процессы (создание, завершение, активность)
    - Файловая система (изменения в отслеживаемых путях)
    - Реестр Windows (модификации ключей)
    - Сетевая активность (новые соединения и открытые порты)
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_file_monitoring: bool = True,
        enable_process_monitoring: bool = True,
        enable_registry_monitoring: bool = True,
        enable_network_monitoring: bool = True,
        enable_event_log_monitoring: bool = True,
        monitored_paths: Optional[List[str]] = None,
        poll_interval_sec: float = 1.0,
        storage: Optional[TelemetryStorage] = None,
        on_event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """Инициализация сборщика системных событий W64.

        Args:
            log_dir: Директория для сохранения JSONL логов (по умолчанию logs/ai_w64_logs).
            enable_file_monitoring: Флаг мониторинга изменений файлов.
            enable_process_monitoring: Флаг мониторинга процессов.
            enable_registry_monitoring: Флаг мониторинга реестра.
            enable_network_monitoring: Флаг мониторинга сетевых соединений.
            enable_event_log_monitoring: Флаг мониторинга журналов Windows.
            monitored_paths: Список путей файловой системы для отслеживания.
            poll_interval_sec: Интервал между циклами сканирования изменений (сек).
            storage: Экземпляр хранилища TelemetryStorage для сохранения в SQLite.
            on_event_callback: Опциональный callback-обработчик каждого зафиксированного события.
        """
        if log_dir is None:
            appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
            self.log_dir = str(Path(appdata) / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs' / 'w64')
        else:
            self.log_dir = log_dir

        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        self.enable_file_monitoring = enable_file_monitoring
        self.enable_process_monitoring = enable_process_monitoring
        self.enable_registry_monitoring = enable_registry_monitoring
        self.enable_network_monitoring = enable_network_monitoring
        self.enable_event_log_monitoring = enable_event_log_monitoring
        self.poll_interval = max(0.1, poll_interval_sec)
        self.storage = storage or TelemetryStorage.get_instance()
        self.on_event_callback = on_event_callback

        self.monitored_paths = monitored_paths or [
            os.path.expandvars(r'%USERPROFILE%\Documents'),
            os.path.expandvars(r'%USERPROFILE%\Downloads'),
            os.path.expandvars(r'%USERPROFILE%\Desktop'),
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            r'C:\Windows\System32',
            r'C:\Windows\SysWOW64',
        ]

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_counter = 0
        self._last_event_time: Optional[str] = None
        self._last_baseline: Dict[str, Any] = {}
        logger.debug(f'AIW64Collector инициализирован. Директория логов: {self.log_dir}')

    def _get_log_file(self, event_type: str) -> Path:
        """Получить путь к файлу ротации лога для типа события.

        Args:
            event_type: Название категории/типа события.

        Returns:
            Path: Путь к JSONL файлу.
        """
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return Path(self.log_dir) / f'{event_type}_{date_str}.jsonl'

    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Записать событие в потоковый JSONL файл и базу данных SQLite.

        Args:
            event_type: Тип события.
            event_data: Словарь с атрибутами события.
        """
        self._event_counter += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        event_data['event_id'] = f'evt_{int(time.time())}_{self._event_counter}'
        event_data['timestamp'] = now_iso
        event_data['event_type'] = event_type
        self._last_event_time = now_iso

        # 1. Запись в JSONL
        try:
            log_file = self._get_log_file(event_type)
            _append_jsonl_safely(log_file, event_data)
        except Exception as ex:
            logger.debug(f'Не удалось записать JSONL лог события {event_type}: {ex}')

        # 2. Сохранение в SQLite TelemetryStorage
        if self.storage:
            try:
                self.storage.save_w64_event(event_data, provider='w64_collector')
            except Exception as ex:
                logger.debug(f'Ошибка сохранения W64 события в БД: {ex}')

        # 3. Передача в callback при наличии
        if self.on_event_callback:
            try:
                self.on_event_callback(event_data)
            except Exception as ex:
                logger.debug(f'Ошибка в on_event_callback: {ex}')

    def start(self) -> bool:
        """Запустить фоновый поток мониторинга событий.

        Returns:
            bool: True если сборщик успешно запущен, False если уже работал.
        """
        if self._running:
            logger.warning('AIW64Collector уже запущен')
            return False

        self._running = True
        self._stop_event.clear()
        self._update_baseline()
        self._thread = threading.Thread(target=self._monitoring_loop, name='AIW64CollectorWorker', daemon=True)
        self._thread.start()
        logger.info('AIW64Collector успешно запущен')
        return True

    def stop(self) -> bool:
        """Остановить фоновый поток мониторинга.

        Returns:
            bool: True если сборщик остановлен, False если не был активен.
        """
        if not self._running:
            return False

        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info(f'AIW64Collector остановлен. Всего зафиксировано событий: {self._event_counter}')
        return True

    def _update_baseline(self) -> None:
        """Сформировать начальный снимок состояния системы для сравнения."""
        self._last_baseline = {
            'processes': self._get_current_processes(),
            'network_connections': self._get_current_network_connections(),
            'registry_keys': self._get_registry_keys(),
            'file_hashes': self._get_file_hashes(),
        }

    def _monitoring_loop(self) -> None:
        """Основной рабочий цикл мониторинга и выявления изменений."""
        last_check = time.time()
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - last_check >= self.poll_interval:
                    current_state = {
                        'processes': self._get_current_processes(),
                        'network_connections': self._get_current_network_connections(),
                        'registry_keys': self._get_registry_keys(),
                        'file_hashes': self._get_file_hashes(),
                    }
                    self._detect_changes(self._last_baseline, current_state)
                    self._last_baseline = current_state
                    last_check = current_time

                self._stop_event.wait(timeout=min(0.5, self.poll_interval))
            except Exception as ex:
                logger.error(f'Ошибка в цикле мониторинга AIW64Collector: {ex}')

    def _detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Сравнить предыдущее и текущее состояние и залогировать изменения.

        Args:
            old_state: Предыдущий системный срез.
            new_state: Текущий системный срез.
        """
        # Мониторинг процессов
        if self.enable_process_monitoring:
            old_procs = {p['pid']: p for p in old_state.get('processes', [])}
            new_procs = {p['pid']: p for p in new_state.get('processes', [])}

            for pid, proc in new_procs.items():
                if pid not in old_procs:
                    self._log_event('process_start', proc)

            for pid, proc in old_procs.items():
                if pid not in new_procs:
                    self._log_event('process_stop', proc)

        # Мониторинг сетевых соединений
        if self.enable_network_monitoring:
            old_conns = {c.get('key'): c for c in old_state.get('network_connections', []) if c.get('key')}
            new_conns = {c.get('key'): c for c in new_state.get('network_connections', []) if c.get('key')}

            for key, conn in new_conns.items():
                if key not in old_conns:
                    self._log_event('network_open', conn)

            for key, conn in old_conns.items():
                if key not in new_conns:
                    self._log_event('network_close', conn)

        # Мониторинг файлов
        if self.enable_file_monitoring:
            old_files = old_state.get('file_hashes', {})
            new_files = new_state.get('file_hashes', {})

            for path, h in new_files.items():
                if path not in old_files:
                    self._log_event('file_created', {'path': path, 'hash': h})
                elif old_files[path] != h:
                    self._log_event('file_modified', {'path': path, 'old_hash': old_files[path], 'new_hash': h})

            for path, h in old_files.items():
                if path not in new_files:
                    self._log_event('file_deleted', {'path': path, 'hash': h})

        # Мониторинг реестра
        if self.enable_registry_monitoring:
            old_reg = old_state.get('registry_keys', {})
            new_reg = new_state.get('registry_keys', {})

            for key, val in new_reg.items():
                if key not in old_reg:
                    self._log_event('registry_created', {'key': key, 'value': val})
                elif old_reg[key] != val:
                    self._log_event('registry_modified', {'key': key, 'old_value': old_reg[key], 'new_value': val})

            for key, val in old_reg.items():
                if key not in new_reg:
                    self._log_event('registry_deleted', {'key': key, 'value': val})

    def _get_current_processes(self) -> List[Dict[str, Any]]:
        """Получить текущий список активных процессов в системе."""
        processes = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time']):
                try:
                    info = proc.info
                    processes.append({
                        'pid': info.get('pid'),
                        'name': info.get('name') or '',
                        'path': info.get('exe') or '',
                        'cmdline': ' '.join(info.get('cmdline') or []) if info.get('cmdline') else '',
                        'username': info.get('username') or '',
                        'create_time': info.get('create_time') or 0.0,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as ex:
            logger.debug(f'Ошибка при получении списка процессов: {ex}')
        return processes

    def _get_current_network_connections(self) -> List[Dict[str, Any]]:
        """Получить текущие активные сетевые подключения."""
        connections = []
        try:
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                try:
                    laddr = f'{conn.laddr.ip}:{conn.laddr.port}' if conn.laddr else ''
                    raddr = f'{conn.raddr.ip}:{conn.raddr.port}' if conn.raddr else ''
                    key = f'{conn.type}_{laddr}_{raddr}_{conn.pid}'
                    connections.append({
                        'key': key,
                        'fd': conn.fd,
                        'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family),
                        'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                        'laddr': laddr,
                        'raddr': raddr,
                        'status': conn.status,
                        'pid': conn.pid,
                    })
                except Exception:
                    continue
        except Exception as ex:
            logger.debug(f'Ошибка при получении сетевых соединений: {ex}')
        return connections

    def _get_registry_keys(self) -> Dict[str, Any]:
        """Получить контрольные ключи реестра автозагрузки и системных политик."""
        keys = {}
        if os.name != 'nt':
            return keys
        try:
            import winreg
            hives = [
                (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
                (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run'),
                (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\RunOnce'),
            ]
            for hive, subkey in hives:
                try:
                    with winreg.OpenKey(hive, subkey) as k:
                        idx = 0
                        while True:
                            try:
                                name, val, _ = winreg.EnumValue(k, idx)
                                key_path = f'{subkey}\\{name}'
                                keys[key_path] = str(val)
                                idx += 1
                            except OSError:
                                break
                except OSError:
                    continue
        except Exception as ex:
            logger.debug(f'Ошибка при чтении ключей реестра: {ex}')
        return keys

    def _get_file_hashes(self) -> Dict[str, str]:
        """Получить отпечатки и размеры отслеживаемых файлов для быстрого детекта изменений."""
        hashes = {}
        for root_path in self.monitored_paths:
            p = Path(root_path)
            if not p.exists():
                continue
            try:
                # Ограничиваем сканирование первыми 100 файлами для предотвращения перегрузки
                count = 0
                for item in p.rglob('*'):
                    if count > 100:
                        break
                    if item.is_file():
                        try:
                            stat = item.stat()
                            hashes[str(item)] = f'{stat.st_size}_{stat.st_mtime}'
                            count += 1
                        except OSError:
                            continue
            except Exception as ex:
                logger.debug(f'Ошибка при проверке файлов в {root_path}: {ex}')
        return hashes

    def get_status(self) -> Dict[str, Any]:
        """Получить диагностический статус сборщика.

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
        """Получить список последних событий из SQLite хранилища или JSONL файлов.

        Args:
            event_type: Фильтр по типу события.
            limit: Максимальное число записей.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        if self.storage:
            return self.storage.get_w64_events(event_type=event_type, provider='w64_collector', limit=limit)
        return []


_global_w64_collector: Optional[AIW64Collector] = None
_lock = threading.Lock()

def get_w64_collector(**kwargs: Any) -> AIW64Collector:
    """Получить глобальный синглтон сборщика AIW64Collector.

    Args:
        **kwargs: Аргументы инициализации при первом создании.

    Returns:
        AIW64Collector: Синглтон сборщика.
    """
    global _global_w64_collector
    with _lock:
        if _global_w64_collector is None:
            _global_w64_collector = AIW64Collector(**kwargs)
        return _global_w64_collector

def start_w64_collector(**kwargs: Any) -> bool:
    """Запустить глобальный сборщик AIW64Collector."""
    collector = get_w64_collector(**kwargs)
    return collector.start()

def stop_w64_collector() -> bool:
    """Остановить глобальный сборщик AIW64Collector."""
    global _global_w64_collector
    with _lock:
        if _global_w64_collector:
            res = _global_w64_collector.stop()
            _global_w64_collector = None
            return res
        return False
