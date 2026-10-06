# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Ring Buffer
# =============================================================================
# Description:
#   Потокобезопасный кольцевой буфер в оперативной памяти для удержания
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.ring_buffer import TelemetryRingBuffer
#
#     service = TelemetryRingBuffer()
#
# File: ring_buffer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 05:32:00
# =============================================================================

from __future__ import annotations
"""Потокобезопасный кольцевой буфер в оперативной памяти для удержания сырой телеметрии."""

import collections
import json
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class TelemetryRingBuffer:
    """Потокобезопасный кольцевой буфер для хранения сырых метрик телеметрии в RAM с ограничением по объему памяти."""

    def __init__(self, capacity: int = 600, max_bytes: int = 32 * 1024 * 1024) -> None:
        """Инициализирует кольцевой буфер заданной емкости и максимального объема RAM.

        Args:
            capacity: Максимальное количество удерживаемых записей (по умолчанию 600 = 10 мин при 1с).
            max_bytes: Максимальный совокупный объем памяти буфера в байтах (по умолчанию 32 МБ).
        """
        self._capacity = max(10, capacity)
        self._max_bytes = max(1024 * 1024, max_bytes)
        self._current_bytes = 0
        self._buffer: collections.deque[Tuple[float, Dict[str, Any], int]] = collections.deque(maxlen=self._capacity)
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        """Возвращает максимальную емкость буфера в количестве записей."""
        return self._capacity

    @property
    def max_bytes(self) -> int:
        """Возвращает максимальный лимит памяти буфера в байтах."""
        return self._max_bytes

    @property
    def current_bytes(self) -> int:
        """Возвращает текущий ориентировочный объем занимаемой памяти буфера в байтах."""
        with self._lock:
            return self._current_bytes

    def _estimate_size(self, item: Dict[str, Any]) -> int:
        """Оценивает размер словаря с метриками в байтах."""
        try:
            return len(json.dumps(item, ensure_ascii=False, default=str).encode('utf-8')) + 128
        except Exception:
            return sys.getsizeof(item) + 256

    def append(self, item: Dict[str, Any], epoch_timestamp: Optional[float] = None) -> None:
        """Добавляет запись телеметрии в кольцевой буфер с контролем лимитов RAM и количества.

        Args:
            item: Словарь с телеметрией или системным снимком.
            epoch_timestamp: Unix epoch timestamp в секундах (если None, берется текущее время).
        """
        ts = epoch_timestamp if epoch_timestamp is not None else time.time()
        item_size = self._estimate_size(item)
        with self._lock:
            # Если буфер заполнен по длине, deque сам вытеснит старый элемент, но нам нужно учесть его размер
            if len(self._buffer) == self._capacity and self._buffer:
                old_ts, old_item, old_size = self._buffer[0]
                self._current_bytes = max(0, self._current_bytes - old_size)

            self._buffer.append((ts, item, item_size))
            self._current_bytes += item_size

            # Контроль жесткого байтового лимита RAM: вытеснение самых старых записей при переполнении
            while self._current_bytes > self._max_bytes and len(self._buffer) > 1:
                old_ts, old_item, old_size = self._buffer.popleft()
                self._current_bytes = max(0, self._current_bytes - old_size)

    def get_recent(self, seconds: float = 300.0) -> List[Dict[str, Any]]:
        """Возвращает список записей за последние N секунд.

        Args:
            seconds: Длительность временного окна назад от текущего момента.

        Returns:
            List[Dict[str, Any]]: Список замеров от старых к новым.
        """
        now = time.time()
        cutoff = now - max(0.0, seconds)
        with self._lock:
            return [item for ts, item, _ in self._buffer if ts >= cutoff]

    def get_window(
        self,
        center_timestamp: float,
        before_seconds: float = 300.0,
        after_seconds: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Извлекает срез телеметрии вокруг заданного момента времени (например, T-5m .. T+20m).

        Args:
            center_timestamp: Центральный момент времени события (Unix epoch seconds).
            before_seconds: Длительность окна ДО события в секундах.
            after_seconds: Длительность окна ПОСЛЕ события в секундах.

        Returns:
            List[Dict[str, Any]]: Список записей, попавших в интервал.
        """
        start_ts = center_timestamp - max(0.0, before_seconds)
        end_ts = center_timestamp + max(0.0, after_seconds)
        with self._lock:
            return [item for ts, item, _ in self._buffer if start_ts <= ts <= end_ts]

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все текущие записи в буфере.

        Returns:
            List[Dict[str, Any]]: Полный текущий срез буфера.
        """
        with self._lock:
            return [item for _, item, _ in self._buffer]

    def count(self) -> int:
        """Возвращает текущее число записей в буфере."""
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """Очищает буфер."""
        with self._lock:
            self._buffer.clear()
            self._current_bytes = 0
