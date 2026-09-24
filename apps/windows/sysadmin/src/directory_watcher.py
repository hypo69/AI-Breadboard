# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Real-time File System Changes Watcher (ReadDirectoryChangesW)
# =============================================================================
# Description:
#   Мониторинг изменений файловой системы в реальном времени с использованием
#   нативного WinAPI ReadDirectoryChangesW с поддержкой одновременного
#   отслеживания нескольких папок (Multi-Directory Monitoring) и определением
#   программы-инициатора изменений через Windows Restart Manager (rstrtmgr.dll).
#   Фиксация создания, изменения, переименования и удаления файлов.
#
# File: directory_watcher.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль мониторинга файловой системы в реальном времени через WinAPI (Multi-Directory & Process Resolver)."""

from __future__ import annotations

import collections
import ctypes
from ctypes import wintypes
import fnmatch
import os
import platform
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger


# Windows API константы
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
FILE_NOTIFY_CHANGE_SECURITY = 0x00000100

FILE_ACTION_ADDED = 1
FILE_ACTION_REMOVED = 2
FILE_ACTION_MODIFIED = 3
FILE_ACTION_RENAMED_OLD_NAME = 4
FILE_ACTION_RENAMED_NEW_NAME = 5

ACTION_NAMES = {
    FILE_ACTION_ADDED: "Created",
    FILE_ACTION_REMOVED: "Deleted",
    FILE_ACTION_MODIFIED: "Modified",
    FILE_ACTION_RENAMED_OLD_NAME: "Renamed (Old Name)",
    FILE_ACTION_RENAMED_NEW_NAME: "Renamed (New Name)",
}


class RM_UNIQUE_PROCESS(ctypes.Structure):
    """Уникальный идентификатор процесса Windows Restart Manager."""

    _fields_ = [
        ("dwProcessId", wintypes.DWORD),
        ("ProcessStartTime", wintypes.FILETIME),
    ]


CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63


class RM_PROCESS_INFO(ctypes.Structure):
    """Информация о процессе, блокирующем или изменившем файл."""

    _fields_ = [
        ("Process", RM_UNIQUE_PROCESS),
        ("strAppName", wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", wintypes.UINT),
        ("AppStatus", wintypes.ULONG),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL),
    ]


def get_process_for_file(file_path: str) -> Tuple[str, Optional[int]]:
    """Определить имя исполняемого файла и PID процесса, изменившего файл.

    Args:
        file_path: Абсолютный путь к файлу.

    Returns:
        Tuple[str, Optional[int]]: Имя программы (например, 'python.exe') и PID.
    """
    if platform.system() != "Windows" or not file_path:
        return ("", None)

    try:
        rstrtmgr = ctypes.windll.rstrtmgr
        session_handle = wintypes.DWORD()
        session_key = (wintypes.WCHAR * 33)()

        res = rstrtmgr.RmStartSession(ctypes.byref(session_handle), 0, session_key)
        if res != 0:
            return ("", None)

        try:
            file_paths = (wintypes.LPCWSTR * 1)(file_path)
            res = rstrtmgr.RmRegisterResources(
                session_handle,
                1,
                file_paths,
                0,
                None,
                0,
                None,
            )
            if res != 0:
                return ("", None)

            n_proc_info_needed = wintypes.UINT(0)
            n_proc_info = wintypes.UINT(10)
            reboot_reasons = wintypes.DWORD()
            proc_info = (RM_PROCESS_INFO * 10)()

            res = rstrtmgr.RmGetList(
                session_handle,
                ctypes.byref(n_proc_info_needed),
                ctypes.byref(n_proc_info),
                proc_info,
                ctypes.byref(reboot_reasons),
            )

            if res == 0 and n_proc_info.value > 0:
                p = proc_info[0]
                pid = int(p.Process.dwProcessId)
                app_name = str(p.strAppName).strip()
                if not app_name or app_name.lower().endswith(".exe") is False:
                    try:
                        import psutil

                        proc = psutil.Process(pid)
                        app_name = proc.name()
                    except Exception:
                        if not app_name:
                            app_name = f"Process [{pid}]"
                return (app_name, pid)
        finally:
            rstrtmgr.RmEndSession(session_handle)
    except Exception as e:
        logger.debug(f"Ошибка Restart Manager для файла {file_path}: {e}")

    return ("", None)


@dataclass
class WatcherExclusions:
    """Правила фильтрации и исключения файлов и процессов из мониторинга в реальном времени."""

    enabled: bool = True
    paths: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    processes: List[str] = field(default_factory=list)

    def is_excluded(self, file_path: str, proc_name: str = "", watch_dir: str = "") -> bool:
        """Проверить, попадает ли путь к файлу или имя процесса под правило исключения.

        Args:
            file_path: Абсолютный или относительный путь к файлу.
            proc_name: Имя исполняемого файла процесса (например, SearchIndexer.exe).
            watch_dir: Отслеживаемый корневой каталог (если известен). Позволяет не исключать
                       файлы, если пользователь явно выбрал отслеживать подпапку внутри
                       обычно исключаемого каталога (например, AppData\\Local\\Temp).

        Returns:
            bool: True если событие должно быть отфильтровано/проигнорировано.
        """
        if not self.enabled:
            return False

        # 1. Проверка по имени процесса (если передано)
        if proc_name and self.processes:
            clean_proc = proc_name.lower().strip()
            for p in self.processes:
                if p and p.lower().strip() == clean_proc:
                    return True

        if not file_path:
            return False

        norm_path = os.path.normpath(file_path).lower()
        file_name = os.path.basename(norm_path)
        norm_watch_dir = os.path.normpath(watch_dir).lower() if watch_dir else ""

        # 2. Проверка расширений файлов (.tmp, .log, .csv, .db-wal, etc.)
        if self.extensions:
            ext = os.path.splitext(file_name)[1].lower()
            for e in self.extensions:
                clean_e = e.lower().strip()
                if not clean_e.startswith("."):
                    clean_e = f".{clean_e}"
                if ext == clean_e:
                    return True

        # 3. Проверка фрагментов путей и каталогов
        if self.paths:
            rel_path = ""
            if norm_watch_dir:
                try:
                    rel_candidate = os.path.relpath(norm_path, norm_watch_dir)
                    if not rel_candidate.startswith(".."):
                        rel_path = rel_candidate.lower()
                except Exception:
                    rel_path = ""

            for p in self.paths:
                clean_p = os.path.normpath(p.strip()).lower()
                if not clean_p:
                    continue

                if os.path.isabs(clean_p):
                    if norm_watch_dir and (norm_watch_dir == clean_p or norm_watch_dir.startswith(clean_p + os.sep)):
                        # Пользователь явно отслеживает эту папку или ее подпапку
                        pass
                    elif norm_path == clean_p or norm_path.startswith(clean_p + os.sep) or clean_p in norm_path:
                        return True
                else:
                    if rel_path:
                        if clean_p in rel_path:
                            return True
                    else:
                        if clean_p in norm_path:
                            return True

        # 4. Проверка шаблонов подстановок (wildcards: fnmatch)
        if self.patterns:
            for pat in self.patterns:
                clean_pat = pat.lower().strip()
                if not clean_pat:
                    continue
                if fnmatch.fnmatch(file_name, clean_pat) or fnmatch.fnmatch(norm_path, clean_pat):
                    return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать правила исключений в словарь."""
        return {
            "enabled": self.enabled,
            "paths": list(self.paths),
            "extensions": list(self.extensions),
            "patterns": list(self.patterns),
            "processes": list(self.processes),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "WatcherExclusions":
        """Создать экземпляр правил из словаря."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            paths=[str(p) for p in data.get("paths", []) if p],
            extensions=[str(e) for e in data.get("extensions", []) if e],
            patterns=[str(pat) for pat in data.get("patterns", []) if pat],
            processes=[str(proc) for proc in data.get("processes", []) if proc],
        )


@dataclass
class LiveFileEvent:
    """Событие изменения файла в реальном времени."""

    timestamp: str
    action: str
    path: str
    is_deletion: bool = False
    watch_dir: str = ""
    process_name: str = ""
    process_id: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


class DirectoryWatcher:
    """Потоковый наблюдатель за каталогами на базе WinAPI ReadDirectoryChangesW."""

    def __init__(
        self,
        watch_dirs: Optional[Union[str, List[str]]] = None,
        max_history: int = 200,
        exclusions: Optional[Union[WatcherExclusions, Dict[str, Any]]] = None,
    ) -> None:
        """Инициализация наблюдателя файловых изменений.

        Args:
            watch_dirs: Путь или список путей к отслеживаемым каталогам.
            max_history: Размер кольцевого буфера истории событий.
            exclusions: Настройки правил исключений и фильтрации.
        """
        if watch_dirs is None:
            self._watch_dirs: List[str] = [str(Path.cwd().resolve())]
        elif isinstance(watch_dirs, str):
            self._watch_dirs = [str(Path(watch_dirs).resolve())]
        else:
            self._watch_dirs = [str(Path(d).resolve()) for d in watch_dirs if d and d.strip()]
            if not self._watch_dirs:
                self._watch_dirs = [str(Path.cwd().resolve())]

        self.max_history = max_history
        self.events_history: Deque[LiveFileEvent] = collections.deque(maxlen=max_history)
        self._is_running = False
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_events: Dict[str, threading.Event] = {}
        self._handles: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.is_windows = platform.system() == "Windows"

        if isinstance(exclusions, WatcherExclusions):
            self.exclusions = exclusions
        elif isinstance(exclusions, dict):
            self.exclusions = WatcherExclusions.from_dict(exclusions)
        else:
            self.exclusions = WatcherExclusions(
                enabled=True,
                paths=[
                    "AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs",
                    "AppData\\Local\\Temp",
                    "$Recycle.Bin",
                    "System Volume Information",
                    ".git",
                    "__pycache__",
                    "node_modules",
                ],
                extensions=[".tmp", ".log", ".db-wal", ".db-shm"],
                patterns=["*librehardwaremonitor_polls.csv*", "*Windows.db*", "~$*"],
                processes=["SearchIndexer.exe"],
            )

        self.filtered_events_count: int = 0

        from apps.windows.sysadmin.src.watcher_telemetry import get_watcher_telemetry_engine

        self.telemetry = get_watcher_telemetry_engine()

    @property
    def watch_dirs(self) -> List[str]:
        """Список отслеживаемых каталогов."""
        with self._lock:
            return list(self._watch_dirs)

    @property
    def watch_dir(self) -> str:
        """Основной (первый) отслеживаемый каталог для обратной совместимости."""
        with self._lock:
            return self._watch_dirs[0] if self._watch_dirs else str(Path.cwd().resolve())

    def get_watch_dirs(self) -> List[str]:
        """Получить копию списка текущих отслеживаемых каталогов.

        Returns:
            List[str]: Список абсолютных путей к отслеживаемым папкам.
        """
        return self.watch_dirs

    def start(self) -> bool:
        """Запустить фоновые потоки мониторинга для всех настроенных директорий.

        Returns:
            bool: True если хотя бы один поток мониторинга успешно стартовал.
        """
        if not self.is_windows:
            logger.warning("DirectoryWatcher поддерживается только на Windows")
            return False

        with self._lock:
            self._is_running = True
            current_dirs = list(self._watch_dirs)

        started_any = False
        for target_dir in current_dirs:
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                logger.warning(f"Каталог для мониторинга не существует или не является папкой: {target_dir}")
                continue

            if self._start_single_watcher(target_dir):
                started_any = True

        return started_any

    def _start_single_watcher(self, target_dir: str) -> bool:
        """Запустить отдельный фоновый поток наблюдения для указанной директории.

        Args:
            target_dir: Абсолютный путь к каталогу.

        Returns:
            bool: True при успешном запуске потока.
        """
        with self._lock:
            if target_dir in self._threads and self._threads[target_dir].is_alive():
                return True

            stop_event = threading.Event()
            self._stop_events[target_dir] = stop_event
            thread = threading.Thread(
                target=self._watch_loop,
                args=(target_dir, stop_event),
                daemon=True,
                name=f"DirWatcherThread-{Path(target_dir).name}",
            )
            self._threads[target_dir] = thread
            thread.start()

        logger.info(f"DirectoryWatcher запущен для: {target_dir}")
        return True

    def _stop_single_watcher(self, target_dir: str) -> None:
        """Остановить поток наблюдения для конкретной директории.

        Args:
            target_dir: Путь к каталогу.
        """
        with self._lock:
            stop_event = self._stop_events.get(target_dir)
            if stop_event:
                stop_event.set()

            h_dir = self._handles.get(target_dir)
            if h_dir and h_dir != -1 and h_dir != 0xFFFFFFFF:
                try:
                    ctypes.windll.kernel32.CloseHandle(h_dir)
                except Exception as e:
                    logger.debug(f"Ошибка закрытия дескриптора для {target_dir}: {e}")
                self._handles.pop(target_dir, None)

            thread = self._threads.get(target_dir)

        if thread and thread.is_alive() and threading.current_thread() != thread:
            thread.join(timeout=0.8)

        with self._lock:
            self._threads.pop(target_dir, None)
            self._stop_events.pop(target_dir, None)

    def set_watch_dirs(self, new_dirs: List[str]) -> bool:
        """Установить новый список отслеживаемых директорий и перезапустить наблюдение.

        Args:
            new_dirs: Список путей к папкам.

        Returns:
            bool: True если хотя бы одна папка валидна и запущена.
        """
        if not self.is_windows:
            logger.warning("DirectoryWatcher поддерживается только на Windows")
            return False

        resolved_dirs: List[str] = []
        for d in new_dirs:
            if not d or not isinstance(d, str):
                continue
            cleaned = d.strip()
            if not cleaned:
                continue
            resolved = str(Path(cleaned).resolve())
            if os.path.exists(resolved) and os.path.isdir(resolved):
                if resolved not in resolved_dirs:
                    resolved_dirs.append(resolved)
            else:
                logger.warning(f"Пропуск невалидной папки при установке мониторинга: {cleaned}")

        if not resolved_dirs:
            logger.warning("Не передано ни одной существующей директории для мониторинга")
            return False

        self.stop()

        with self._lock:
            self._watch_dirs = resolved_dirs
            self.events_history.clear()

        return self.start()

    def set_watch_dir(self, new_dir: str) -> bool:
        """Сменить отслеживаемую директорию (одиночный режим).

        Args:
            new_dir: Новый путь к папке.

        Returns:
            bool: True если каталог существует и мониторинг успешно переключён.
        """
        return self.set_watch_dirs([new_dir])

    def add_watch_dir(self, new_dir: str) -> bool:
        """Добавить новую директорию в список отслеживаемых на лету.

        Args:
            new_dir: Путь к добавляемой папке.

        Returns:
            bool: True если папка успешно добавлена и мониторинг запущен.
        """
        if not self.is_windows:
            return False

        resolved = str(Path(new_dir.strip()).resolve())
        if not os.path.exists(resolved) or not os.path.isdir(resolved):
            logger.warning(f"Каталог не существует: {new_dir}")
            return False

        with self._lock:
            if resolved in self._watch_dirs:
                return True
            self._watch_dirs.append(resolved)

        if self._is_running:
            return self._start_single_watcher(resolved)
        return True

    def remove_watch_dir(self, dir_path: str) -> bool:
        """Удалить директорию из списка отслеживаемых.

        Args:
            dir_path: Путь к удаляемой из мониторинга папке.

        Returns:
            bool: True если папка удалена.
        """
        resolved = str(Path(dir_path.strip()).resolve())
        with self._lock:
            if resolved not in self._watch_dirs:
                return False
            self._watch_dirs.remove(resolved)

        self._stop_single_watcher(resolved)
        return True

    def stop(self) -> None:
        """Остановить мониторинг всех директорий."""
        self._is_running = False
        with self._lock:
            current_dirs = list(self._watch_dirs)

        for d in current_dirs:
            self._stop_single_watcher(d)

    def get_recent_events(self, limit: int = 50) -> List[LiveFileEvent]:
        """Получить недавние события из кольцевого буфера.

        Args:
            limit: Максимальное количество событий.

        Returns:
            List[LiveFileEvent]: Список недавних событий в обратном хронологическом порядке.
        """
        with self._lock:
            items = list(self.events_history)
        return items[-limit:][::-1]

    def _watch_loop(self, target_dir: str, stop_event: threading.Event) -> None:
        """Основной цикл ожидания изменений через ReadDirectoryChangesW для конкретной папки.

        Args:
            target_dir: Отслеживаемый каталог.
            stop_event: Сигнал остановки цикла.
        """
        kernel32 = ctypes.windll.kernel32

        h_dir = kernel32.CreateFileW(
            target_dir,
            0x0001,  # FILE_LIST_DIRECTORY
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )

        if h_dir == -1 or h_dir == 0xFFFFFFFF:
            logger.error(f"Не удалось открыть дескриптор каталога {target_dir}")
            return

        with self._lock:
            self._handles[target_dir] = h_dir

        buffer = ctypes.create_string_buffer(65536)
        bytes_returned = ctypes.c_ulong()

        flags = (
            FILE_NOTIFY_CHANGE_FILE_NAME
            | FILE_NOTIFY_CHANGE_DIR_NAME
            | FILE_NOTIFY_CHANGE_LAST_WRITE
            | FILE_NOTIFY_CHANGE_SIZE
        )

        try:
            while self._is_running and not stop_event.is_set():
                success = kernel32.ReadDirectoryChangesW(
                    h_dir,
                    ctypes.byref(buffer),
                    len(buffer),
                    True,  # bWatchSubtree
                    flags,
                    ctypes.byref(bytes_returned),
                    None,
                    None,
                )

                if not success or bytes_returned.value == 0:
                    time.sleep(0.5)
                    continue

                self._process_notifications(target_dir, buffer.raw, bytes_returned.value)
        except Exception as e:
            if not stop_event.is_set():
                logger.error(f"Ошибка в цикле DirectoryWatcher для {target_dir}: {e}")
        finally:
            try:
                kernel32.CloseHandle(h_dir)
            except Exception:
                pass
            with self._lock:
                self._handles.pop(target_dir, None)

    def get_exclusions(self) -> Dict[str, Any]:
        """Получить текущие правила исключений и статистику отфильтрованных событий.

        Returns:
            Dict[str, Any]: Словарь с правилами исключений и счетчиком отфильтрованных событий.
        """
        with self._lock:
            data = self.exclusions.to_dict()
            data["filtered_count"] = self.filtered_events_count
            return data

    def set_exclusions(self, data: Dict[str, Any]) -> None:
        """Обновить правила исключений.

        Args:
            data: Словарь с новой конфигурацией исключений.
        """
        with self._lock:
            self.exclusions = WatcherExclusions.from_dict(data)

    def add_exclusion(self, category: str, value: str) -> bool:
        """Добавить элемент в указанную категорию исключений.

        Args:
            category: Категория ('paths', 'extensions', 'patterns', 'processes').
            value: Значение правила.

        Returns:
            bool: True если правило успешно добавлено.
        """
        cat = category.lower().strip()
        val = value.strip()
        if not val:
            return False

        with self._lock:
            if cat in ("paths", "path"):
                if val not in self.exclusions.paths:
                    self.exclusions.paths.append(val)
                    return True
            elif cat in ("extensions", "extension", "ext"):
                clean_ext = val if val.startswith(".") else f".{val}"
                if clean_ext not in self.exclusions.extensions:
                    self.exclusions.extensions.append(clean_ext)
                    return True
            elif cat in ("patterns", "pattern", "pat"):
                if val not in self.exclusions.patterns:
                    self.exclusions.patterns.append(val)
                    return True
            elif cat in ("processes", "process", "proc"):
                if val not in self.exclusions.processes:
                    self.exclusions.processes.append(val)
                    return True
        return False

    def remove_exclusion(self, category: str, value: str) -> bool:
        """Удалить элемент из указанной категории исключений.

        Args:
            category: Категория ('paths', 'extensions', 'patterns', 'processes').
            value: Значение правила.

        Returns:
            bool: True если правило найдено и удалено.
        """
        cat = category.lower().strip()
        val = value.strip()
        with self._lock:
            target_list = None
            if cat in ("paths", "path"):
                target_list = self.exclusions.paths
            elif cat in ("extensions", "extension", "ext"):
                target_list = self.exclusions.extensions
                val = val if val.startswith(".") else f".{val}"
            elif cat in ("patterns", "pattern", "pat"):
                target_list = self.exclusions.patterns
            elif cat in ("processes", "process", "proc"):
                target_list = self.exclusions.processes

            if target_list is not None:
                for idx, item in enumerate(target_list):
                    if item.lower() == val.lower():
                        target_list.pop(idx)
                        return True
        return False

    def toggle_exclusions(self, enabled: Optional[bool] = None) -> bool:
        """Переключить активность фильтрации исключений.

        Args:
            enabled: Опциональное явное состояние включения/отключения.

        Returns:
            bool: Актуальное состояние активности фильтрации.
        """
        with self._lock:
            if enabled is None:
                self.exclusions.enabled = not self.exclusions.enabled
            else:
                self.exclusions.enabled = bool(enabled)
            return self.exclusions.enabled

    def _process_notifications(self, target_dir: str, raw_data: bytes, total_bytes: int) -> None:
        """Разобрать структуры FILE_NOTIFY_INFORMATION из буфера и определить вызывающий процесс.

        Args:
            target_dir: Корневая отслеживаемая папка.
            raw_data: Сырой буфер памяти.
            total_bytes: Количество возвращенных байт.
        """
        offset = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        while offset < total_bytes:
            next_offset = int.from_bytes(raw_data[offset : offset + 4], byteorder="little")
            action_code = int.from_bytes(raw_data[offset + 4 : offset + 8], byteorder="little")
            file_name_len = int.from_bytes(raw_data[offset + 8 : offset + 12], byteorder="little")

            fn_start = offset + 12
            fn_end = fn_start + file_name_len
            file_name_raw = raw_data[fn_start:fn_end]
            file_name = file_name_raw.decode("utf-16le", errors="ignore")

            full_path = os.path.join(target_dir, file_name)

            # Предварительная проверка исключений по пути/расширению/шаблону (до вызова Restart Manager)
            if self.exclusions.is_excluded(full_path, watch_dir=target_dir):
                with self._lock:
                    self.filtered_events_count += 1
                if next_offset == 0:
                    break
                offset += next_offset
                continue

            action_str = ACTION_NAMES.get(action_code, f"Action_{action_code}")
            is_del = action_code in (FILE_ACTION_REMOVED, FILE_ACTION_RENAMED_OLD_NAME)

            # Определение программы / процесса, вызвавшего изменение
            proc_name, proc_id = get_process_for_file(full_path)

            # Проверка исключений с учетом определенного процесса
            if proc_name and self.exclusions.is_excluded(full_path, proc_name=proc_name, watch_dir=target_dir):
                with self._lock:
                    self.filtered_events_count += 1
                if next_offset == 0:
                    break
                offset += next_offset
                continue

            event = LiveFileEvent(
                timestamp=now_str,
                action=action_str,
                path=full_path,
                is_deletion=is_del,
                watch_dir=target_dir,
                process_name=proc_name,
                process_id=proc_id,
                details={
                    "action_code": action_code,
                    "relative_path": file_name,
                    "watch_dir": target_dir,
                    "process_name": proc_name,
                    "process_id": proc_id,
                },
            )

            # Передаем действие в телеметрический движок
            self.telemetry.record_event(action_str, watch_dir=target_dir)

            with self._lock:
                self.events_history.append(event)

            if next_offset == 0:
                break
            offset += next_offset

    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        """Получить актуальный снимок программных и аппаратных сенсоров наблюдателя.

        Returns:
            Dict[str, Any]: Снимок телеметрии в виде словаря.
        """
        with self._lock:
            total_events = len(self.events_history)
            dirs = list(self._watch_dirs)

        snap = self.telemetry.get_telemetry_snapshot(
            watch_dirs=dirs,
            total_history_events=total_events,
        )
        return snap.to_dict()


# Глобальный инстанс вотчера для AI-Breadboard
_global_watcher: Optional[DirectoryWatcher] = None


def get_directory_watcher(
    watch_dirs: Optional[Union[str, List[str]]] = None,
    exclusions: Optional[Union[WatcherExclusions, Dict[str, Any]]] = None,
) -> DirectoryWatcher:
    """Получить глобальный экземпляр DirectoryWatcher.

    Args:
        watch_dirs: Путь или список путей для мониторинга. Если не указаны, используются пути из config.json.
        exclusions: Настройки исключений. Если не указаны, загружаются из config.json.

    Returns:
        DirectoryWatcher: Экземпляр наблюдателя.
    """
    global _global_watcher
    if _global_watcher is None:
        cfg_exclusions = None
        # Если пути или исключения не указаны, пытаемся загрузить их из config.json
        if watch_dirs is None or exclusions is None:
            from pathlib import Path
            import json
            import os
            cfg_file = Path(__file__).resolve().parent.parent / "config.json"
            try:
                if cfg_file.exists():
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                        if watch_dirs is None:
                            custom_paths = cfg_data.get("watch_directories")
                            if isinstance(custom_paths, list) and custom_paths:
                                valid_paths = [p for p in custom_paths if isinstance(p, str) and os.path.isdir(p)]
                                if valid_paths:
                                    watch_dirs = valid_paths
                        if exclusions is None and "exclusions" in cfg_data:
                            cfg_exclusions = cfg_data.get("exclusions")
            except Exception as e:
                logger.debug(f"Не удалось загрузить параметры из config.json при первом создании: {e}")

        active_exclusions = exclusions if exclusions is not None else cfg_exclusions
        _global_watcher = DirectoryWatcher(watch_dirs=watch_dirs, exclusions=active_exclusions)
        _global_watcher.start()
    return _global_watcher
