# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry File System Events Collector
# =============================================================================
# Description:
#   Сбор событий файловой системы в реальном времени через WinAPI DirectoryWatcher.
#
# File: file_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сбор событий файловой системы через DirectoryWatcher."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

# Импорт DirectoryWatcher из существующих модулей
try:
    from apps.windows.sysadmin.src.directory_watcher import DirectoryWatcher, LiveFileEvent
except ImportError as e:
    logger.warning(f"Не удалось импортировать DirectoryWatcher: {e}")
    DirectoryWatcher = None
    LiveFileEvent = None


class FileCollector:
    """Коллектор событий файловой системы."""

    def __init__(
        self,
        watch_dirs: Optional[List[str]] = None,
        max_history: int = 200,
    ) -> None:
        """Инициализирует коллектор файловых событий.

        Args:
            watch_dirs: Список директорий для мониторинга.
            max_history: Размер истории событий.
        """
        self.watch_dirs = watch_dirs or [str(Path.home() / "Documents")]
        self.max_history = max_history

        self._watchers: Dict[str, DirectoryWatcher] = {}
        self._lock = threading.Lock()

        self._init_watchers()

    def _init_watchers(self) -> None:
        """Инициализирует DirectoryWatcher для каждой директории."""
        if DirectoryWatcher is None:
            logger.warning("DirectoryWatcher недоступен")
            return

        for watch_dir in self.watch_dirs:
            try:
                watcher = DirectoryWatcher(watch_dir=watch_dir, max_history=self.max_history)
                if watcher.start():
                    self._watchers[watch_dir] = watcher
                    logger.info(f"DirectoryWatcher запущен для: {watch_dir}")
            except Exception as e:
                logger.error(f"Ошибка инициализации DirectoryWatcher для {watch_dir}: {e}")

    def _convert_event(self, event: LiveFileEvent) -> Dict[str, Any]:
        """Преобразует LiveFileEvent в словарь для JSON.

        Args:
            event: Событие от DirectoryWatcher.

        Returns:
            Dict[str, Any]: Событие в формате словаря.
        """
        return {
            "timestamp": event.timestamp,
            "action": event.action,
            "path": event.path,
            "is_deletion": event.is_deletion,
            "details": event.details,
        }

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает недавние файловые события.

        Args:
            limit: Максимальное количество событий.

        Returns:
            List[Dict[str, Any]]: Список файловых событий.
        """
        with self._lock:
            events: List[Dict[str, Any]] = []

            for watch_dir, watcher in self._watchers.items():
                try:
                    raw_events = watcher.get_recent_events(limit=limit)
                    for event in raw_events:
                        converted = self._convert_event(event)
                        converted["watch_dir"] = watch_dir
                        events.append(converted)
                except Exception as e:
                    logger.error(f"Ошибка получения событий из {watch_dir}: {e}")

            # Сортируем по времени и берем последние
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return events[:limit]

    def get_events_by_action(self, action: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает события определенного типа.

        Args:
            action: Тип действия (Created, Deleted, Modified).
            limit: Максимальное количество событий.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        all_events = self.get_recent_events(limit=limit * 2)
        return [e for e in all_events if e.get("action") == action][:limit]

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает события определенного типа (Created/Deleted).

        Args:
            event_type: Тип события (Created или Deleted).
            limit: Максимальное количество событий.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        if event_type.lower() == "created":
            return self.get_events_by_action("Created", limit)
        elif event_type.lower() == "deleted":
            return self.get_events_by_action("Deleted", limit)
        return []

    def stop(self) -> None:
        """Останавливает все DirectoryWatcher."""
        with self._lock:
            for watcher in self._watchers.values():
                watcher.stop()
            self._watchers.clear()
            logger.info("FileCollector остановлен")

    def restart(self) -> bool:
        """Перезапускает DirectoryWatcher.

        Returns:
            bool: True если перезапуск успешен.
        """
        self.stop()
        self._init_watchers()
        return True

    def add_watch_dir(self, watch_dir: str) -> bool:
        """Добавляет директорию для мониторинга.

        Args:
            watch_dir: Путь к директории.

        Returns:
            bool: True если директория успешно добавлена.
        """
        if DirectoryWatcher is None:
            logger.warning("DirectoryWatcher недоступен")
            return False

        if watch_dir in self._watchers:
            logger.warning(f"Директория уже отслеживается: {watch_dir}")
            return False

        try:
            watcher = DirectoryWatcher(watch_dir=watch_dir, max_history=self.max_history)
            if watcher.start():
                self._watchers[watch_dir] = watcher
                logger.info(f"Добавлена директория для мониторинга: {watch_dir}")
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления директории {watch_dir}: {e}")

        return False

    def remove_watch_dir(self, watch_dir: str) -> bool:
        """Удаляет директорию из мониторинга.

        Args:
            watch_dir: Путь к директории.

        Returns:
            bool: True если директория успешно удалена.
        """
        with self._lock:
            if watch_dir in self._watchers:
                watcher = self._watchers.pop(watch_dir)
                watcher.stop()
                logger.info(f"Удалена директория из мониторинга: {watch_dir}")
                return True
            else:
                logger.warning(f"Директория не найдена в мониторинге: {watch_dir}")
                return False
