# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Real-time File System Changes Watcher (ReadDirectoryChangesW)
# =============================================================================
# Description:
#   Мониторинг изменений файловой системы в реальном времени с использованием
#   нативного WinAPI ReadDirectoryChangesW.
#   Фиксация создания, изменения, переименования и удаления файлов (FILE_ACTION_REMOVED).
#
# File: directory_watcher.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль мониторинга файловой системы в реальном времени через WinAPI."""

from __future__ import annotations

import collections
import ctypes
import os
import platform
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

from src.logger import logger


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


@dataclass
class LiveFileEvent:
    """Событие изменения файла в реальном времени."""

    timestamp: str
    action: str
    path: str
    is_deletion: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class DirectoryWatcher:
    """Потоковый наблюдатель за каталогом на базе WinAPI ReadDirectoryChangesW."""

    def __init__(self, watch_dir: Optional[str] = None, max_history: int = 200) -> None:
        """Инициализация наблюдателя.

        Args:
            watch_dir: Путь к отслеживаемому каталогу.
            max_history: Размер кольцевого буфера истории событий.
        """
        self.watch_dir = watch_dir or str(Path.cwd())
        self.max_history = max_history
        self.events_history: Deque[LiveFileEvent] = collections.deque(maxlen=max_history)
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.is_windows = platform.system() == "Windows"

    def start(self) -> bool:
        """Запустить фоновый поток мониторинга директории.

        Returns:
            bool: True если мониторинг успешно стартовал.
        """
        if not self.is_windows:
            logger.warning("DirectoryWatcher поддерживается только на Windows")
            return False

        if self._is_running:
            return True

        if not os.path.exists(self.watch_dir):
            logger.warning(f"Каталог для мониторинга не существует: {self.watch_dir}")
            return False

        self._is_running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="DirectoryWatcherThread")
        self._thread.start()
        logger.info(f"DirectoryWatcher запущен для: {self.watch_dir}")
        return True

    def stop(self) -> None:
        """Остановить мониторинг."""
        self._is_running = False

    def get_recent_events(self, limit: int = 50) -> List[LiveFileEvent]:
        """Получить недавние события из кольцевого буфера.

        Args:
            limit: Максимальное количество событий.

        Returns:
            List[LiveFileEvent]: Список недавних событий.
        """
        with self._lock:
            items = list(self.events_history)
        return items[-limit:][::-1]

    def _watch_loop(self) -> None:
        """Основной цикл ожидания изменений через ReadDirectoryChangesW."""
        kernel32 = ctypes.windll.kernel32

        h_dir = kernel32.CreateFileW(
            self.watch_dir,
            0x0001,  # FILE_LIST_DIRECTORY
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )

        if h_dir == -1 or h_dir == 0xFFFFFFFF:
            logger.error(f"Не удалось открыть дескриптор каталога {self.watch_dir}")
            self._is_running = False
            return

        buffer = ctypes.create_string_buffer(65536)
        bytes_returned = ctypes.c_ulong()

        flags = (
            FILE_NOTIFY_CHANGE_FILE_NAME
            | FILE_NOTIFY_CHANGE_DIR_NAME
            | FILE_NOTIFY_CHANGE_LAST_WRITE
            | FILE_NOTIFY_CHANGE_SIZE
        )

        try:
            while self._is_running:
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

                self._process_notifications(buffer.raw, bytes_returned.value)
        except Exception as e:
            logger.error(f"Ошибка в цикле DirectoryWatcher: {e}")
        finally:
            kernel32.CloseHandle(h_dir)
            self._is_running = False

    def _process_notifications(self, raw_data: bytes, total_bytes: int) -> None:
        """Разобрать структуры FILE_NOTIFY_INFORMATION из буфера.

        Args:
            raw_data: Сырой буфер памяти.
            total_bytes: Количество возвращенных байт.
        """
        offset = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        while offset < total_bytes:
            # Структура FILE_NOTIFY_INFORMATION:
            # DWORD NextEntryOffset;
            # DWORD Action;
            # DWORD FileNameLength;
            # WCHAR FileName[1];
            next_offset = int.from_bytes(raw_data[offset : offset + 4], byteorder="little")
            action_code = int.from_bytes(raw_data[offset + 4 : offset + 8], byteorder="little")
            file_name_len = int.from_bytes(raw_data[offset + 8 : offset + 12], byteorder="little")

            fn_start = offset + 12
            fn_end = fn_start + file_name_len
            file_name_raw = raw_data[fn_start:fn_end]
            file_name = file_name_raw.decode("utf-16le", errors="ignore")

            full_path = os.path.join(self.watch_dir, file_name)
            action_str = ACTION_NAMES.get(action_code, f"Action_{action_code}")
            is_del = action_code in (FILE_ACTION_REMOVED, FILE_ACTION_RENAMED_OLD_NAME)

            event = LiveFileEvent(
                timestamp=now_str,
                action=action_str,
                path=full_path,
                is_deletion=is_del,
                details={"action_code": action_code, "relative_path": file_name},
            )

            with self._lock:
                self.events_history.append(event)

            if next_offset == 0:
                break
            offset += next_offset


# Глобальный инстанс вотчера для AI-Breadboard
_global_watcher: Optional[DirectoryWatcher] = None


def get_directory_watcher(watch_dir: Optional[str] = None) -> DirectoryWatcher:
    """Получить глобальный экземпляр DirectoryWatcher.

    Args:
        watch_dir: Путь для мониторинга.

    Returns:
        DirectoryWatcher: Экземпляр наблюдателя.
    """
    global _global_watcher
    if _global_watcher is None:
        _global_watcher = DirectoryWatcher(watch_dir=watch_dir)
        _global_watcher.start()
    return _global_watcher
