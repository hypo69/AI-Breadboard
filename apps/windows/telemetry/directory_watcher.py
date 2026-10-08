# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Directory Watch Engine
# =============================================================================
# Description:
#   Движок фонового мониторинга файловой активности в контролируемых директориях
#   с привязкой к PID процессов (Win32 ReadDirectoryChangesW + Restart Manager / ETW).
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.directory_watcher import DirectoryWatchEngine
#
#     engine = DirectoryWatchEngine.get_instance()
#     engine.add_directory("C:\\Data\\Projects")
#     engine.start()
#
# File: directory_watcher.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 11:57:00
# =============================================================================

from __future__ import annotations

"""Движок мониторинга файловой активности в целевых директориях с привязкой к процессам по PID."""

import ctypes
from ctypes import wintypes
import json
import os
import platform
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.sqlite import TelemetryStorage

# Win32 Константы для ReadDirectoryChangesW
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
FILE_NOTIFY_CHANGE_DIR_NAME = 0x00000002
FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x00000004
FILE_NOTIFY_CHANGE_SIZE = 0x00000008
FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010

FILE_ACTION_ADDED = 1
FILE_ACTION_REMOVED = 2
FILE_ACTION_MODIFIED = 3
FILE_ACTION_RENAMED_OLD_NAME = 4
FILE_ACTION_RENAMED_NEW_NAME = 5

ACTION_MAP = {
    FILE_ACTION_ADDED: 'CREATE',
    FILE_ACTION_REMOVED: 'DELETE',
    FILE_ACTION_MODIFIED: 'MODIFY',
    FILE_ACTION_RENAMED_OLD_NAME: 'RENAME',
    FILE_ACTION_RENAMED_NEW_NAME: 'RENAME',
}


class RM_UNIQUE_PROCESS(ctypes.Structure):
    """Идентификатор процесса Restart Manager."""
    _fields_ = [
        ('dwProcessId', wintypes.DWORD),
        ('ProcessStartTime', wintypes.FILETIME)
    ]


class RM_PROCESS_INFO(ctypes.Structure):
    """Информация о процессе Restart Manager."""
    _fields_ = [
        ('Process', RM_UNIQUE_PROCESS),
        ('strAppName', wintypes.WCHAR * 256),
        ('strServiceShortName', wintypes.WCHAR * 64),
        ('ApplicationType', wintypes.UINT),
        ('AppStatus', wintypes.ULONG),
        ('TSSessionId', wintypes.DWORD),
        ('bRestartable', wintypes.BOOL)
    ]


def resolve_pid_for_file(file_path: str) -> Tuple[int, str]:
    """Определяет PID и имя процесса, взаимодействующего с файлом через Restart Manager Win32.

    Args:
        file_path: Абсолютный путь к файлу.

    Returns:
        Tuple[int, str]: Кортеж (PID, имя_процесса).
    """
    if platform.system() != 'Windows' or not file_path:
        return (0, 'system')
    try:
        rstrtmgr = ctypes.windll.rstrtmgr
        session_handle = wintypes.DWORD()
        session_key = (wintypes.WCHAR * 33)()
        if rstrtmgr.RmStartSession(ctypes.byref(session_handle), 0, session_key) != 0:
            return (0, 'system')
        try:
            paths = (wintypes.LPCWSTR * 1)(file_path)
            if rstrtmgr.RmRegisterResources(session_handle, 1, paths, 0, None, 0, None) == 0:
                n_proc_needed = wintypes.UINT(0)
                n_proc = wintypes.UINT(5)
                reboot_reasons = wintypes.DWORD()
                proc_info = (RM_PROCESS_INFO * 5)()
                if rstrtmgr.RmGetList(
                    session_handle,
                    ctypes.byref(n_proc_needed),
                    ctypes.byref(n_proc),
                    proc_info,
                    ctypes.byref(reboot_reasons)
                ) == 0 and n_proc.value > 0:
                    p = proc_info[0]
                    pid = int(p.Process.dwProcessId)
                    name = str(p.strAppName).strip() or f'Process [{pid}]'
                    return (pid, name)
        finally:
            rstrtmgr.RmEndSession(session_handle)
    except Exception as exc:
        logger.debug(f'Ошибка определения процесса для файла {file_path}: {exc}')
    return (0, 'system')


class DirectoryWatchEngine:
    """Движок мониторинга контролируемых папок с привязкой файловых событий к процессам по PID."""

    _instance: Optional[DirectoryWatchEngine] = None
    _lock = threading.RLock()

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Инициализирует наблюдатель за контролируемыми директориями."""
        self._config_path = config_path or (Path(__file__).resolve().parent / 'config.json')
        self._tracked_directories: Set[str] = set()
        self._watch_threads: Dict[str, threading.Thread] = {}
        self._stop_events: Dict[str, threading.Event] = {}
        self._running = False
        self._load_configuration()

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> DirectoryWatchEngine:
        """Возвращает синглтон экземпляр DirectoryWatchEngine."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config_path=config_path)
            return cls._instance

    def _load_configuration(self) -> None:
        """Загружает список отслеживаемых папок из config.json."""
        if self._config_path.is_file():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    dirs = cfg.get('watch_directories', [])
                    for d in dirs:
                        if isinstance(d, str) and d.strip():
                            self._tracked_directories.add(os.path.normpath(d.strip()))
            except Exception as exc:
                logger.warning(f'[DirectoryWatchEngine] Ошибка загрузки watch_directories: {exc}')

    def _save_configuration(self) -> None:
        """Сохраняет актуальный список отслеживаемых директорий в config.json."""
        if self._config_path.is_file():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                cfg['watch_directories'] = sorted(list(self._tracked_directories))
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception as exc:
                logger.warning(f'[DirectoryWatchEngine] Ошибка сохранения watch_directories: {exc}')

    def get_tracked_directories(self) -> List[str]:
        """Возвращает отсортированный список всех активных отслеживаемых директорий."""
        with self._lock:
            return sorted(list(self._tracked_directories))

    def add_directory(self, directory_path: str) -> bool:
        """Добавляет директорию в список активного мониторинга и запускает поток слежения.

        Args:
            directory_path: Путь к отслеживаемой папке.

        Returns:
            bool: True если директория успешно добавлена.
        """
        norm_path = os.path.normpath(directory_path.strip())
        with self._lock:
            if norm_path not in self._tracked_directories:
                self._tracked_directories.add(norm_path)
                self._save_configuration()
                if self._running:
                    self._start_watcher_thread(norm_path)
                logger.info(f'[DirectoryWatchEngine] Добавлена директория для мониторинга: {norm_path}')
                return True
            return False

    def remove_directory(self, directory_path: str) -> bool:
        """Удаляет директорию из списка отслеживания и останавливает поток.

        Args:
            directory_path: Путь к отслеживаемой папке.

        Returns:
            bool: True если директория удалена.
        """
        norm_path = os.path.normpath(directory_path.strip())
        with self._lock:
            if norm_path in self._tracked_directories:
                self._tracked_directories.remove(norm_path)
                self._save_configuration()
                self._stop_watcher_thread(norm_path)
                logger.info(f'[DirectoryWatchEngine] Удалена директория из мониторинга: {norm_path}')
                return True
            return False

    def start(self) -> None:
        """Запускает мониторинг всех зарегистрированных директорий."""
        with self._lock:
            if self._running:
                return
            self._running = True
            for path in list(self._tracked_directories):
                self._start_watcher_thread(path)
            logger.info(f'[DirectoryWatchEngine] Запущен мониторинг {len(self._tracked_directories)} директорий')

    def stop(self) -> None:
        """Останавливает мониторинг всех директорий."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            for path in list(self._watch_threads.keys()):
                self._stop_watcher_thread(path)
            logger.info('[DirectoryWatchEngine] Мониторинг директорий остановлен')

    def _start_watcher_thread(self, path: str) -> None:
        """Запускает поток Win32 ReadDirectoryChangesW для указанной директории."""
        if path in self._watch_threads and self._watch_threads[path].is_alive():
            return
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                pass

        stop_evt = threading.Event()
        self._stop_events[path] = stop_evt
        t = threading.Thread(
            target=self._watch_loop,
            args=(path, stop_evt),
            name=f'DirWatcher_{os.path.basename(path)}',
            daemon=True
        )
        self._watch_threads[path] = t
        t.start()

    def _stop_watcher_thread(self, path: str) -> None:
        """Останавливает фоновый поток слежения за директорией."""
        stop_evt = self._stop_events.pop(path, None)
        if stop_evt:
            stop_evt.set()
        t = self._watch_threads.pop(path, None)
        if t and t.is_alive() and t != threading.current_thread():
            t.join(timeout=1.0)

    def _watch_loop(self, directory: str, stop_evt: threading.Event) -> None:
        """Основной рабочий цикл ReadDirectoryChangesW для директории."""
        if platform.system() != 'Windows':
            return

        kernel32 = ctypes.windll.kernel32
        h_dir = kernel32.CreateFileW(
            directory,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None
        )

        if h_dir == -1 or h_dir == 0xFFFFFFFF:
            logger.debug(f'[DirectoryWatchEngine] Не удалось открыть дескриптор для: {directory}')
            return

        buffer = (ctypes.c_byte * 65536)()
        bytes_returned = wintypes.DWORD()
        flags = (
            FILE_NOTIFY_CHANGE_FILE_NAME
            | FILE_NOTIFY_CHANGE_DIR_NAME
            | FILE_NOTIFY_CHANGE_ATTRIBUTES
            | FILE_NOTIFY_CHANGE_SIZE
            | FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        try:
            while not stop_evt.is_set() and self._running:
                success = kernel32.ReadDirectoryChangesW(
                    h_dir,
                    ctypes.byref(buffer),
                    len(buffer),
                    True,
                    flags,
                    ctypes.byref(bytes_returned),
                    None,
                    None
                )
                if not success or bytes_returned.value == 0:
                    time.sleep(0.5)
                    continue

                self._process_notifications(buffer, bytes_returned.value, directory)
        except Exception as exc:
            logger.debug(f'[DirectoryWatchEngine] Исключение в цикле {directory}: {exc}')
        finally:
            kernel32.CloseHandle(h_dir)

    def _process_notifications(self, buffer: Any, buffer_len: int, target_directory: str) -> None:
        """Парсит структуру FILE_NOTIFY_INFORMATION и записывает события в базу данных."""
        offset = 0
        events_to_save: List[Dict[str, Any]] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        while offset < buffer_len:
            next_entry_offset = int.from_bytes(bytes(buffer[offset:offset + 4]), 'little')
            action = int.from_bytes(bytes(buffer[offset + 4:offset + 8]), 'little')
            file_name_len = int.from_bytes(bytes(buffer[offset + 8:offset + 12]), 'little')
            file_name_bytes = bytes(buffer[offset + 12:offset + 12 + file_name_len])
            file_name = file_name_bytes.decode('utf-16le', errors='ignore')

            full_path = os.path.join(target_directory, file_name)
            action_type = ACTION_MAP.get(action, 'MODIFY')

            # Определение PID и имени процесса
            pid, proc_name = resolve_pid_for_file(full_path)

            # Вычисление затронутого объема байт (если файл доступен)
            bytes_affected = 0
            if action_type != 'DELETE' and os.path.isfile(full_path):
                try:
                    bytes_affected = os.path.getsize(full_path)
                except Exception:
                    pass

            events_to_save.append({
                'pid': pid,
                'process_name': proc_name,
                'action_type': action_type,
                'target_directory': target_directory,
                'file_path': full_path,
                'bytes_affected': bytes_affected,
                'timestamp': now_ts,
                'created_at': time.time(),
            })

            if next_entry_offset == 0:
                break
            offset += next_entry_offset

        if events_to_save:
            try:
                storage = TelemetryStorage.get_instance()
                storage.insert_process_file_events(events_to_save)
            except Exception as exc:
                logger.debug(f'[DirectoryWatchEngine] Ошибка сохранения файловых событий: {exc}')
