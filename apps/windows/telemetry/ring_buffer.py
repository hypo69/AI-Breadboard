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
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Потокобезопасный кольцевой буфер в оперативной памяти для удержания"""

import collections
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class TelemetryRingBuffer:
    """Потокобезопасный кольцевой буфер для хранения сырых метрик телеметрии в RAM."""

    def __init__(self, capacity: int = 600) -> None:
        """Инициализирует кольцевой буфер заданной емкости.

        Args:
            capacity: Максимальное количество удерживаемых записей (по умолчанию 600 = 10 мин при 1с).
        """
        self._capacity = max(10, capacity)
        self._buffer: collections.deque[Tuple[float, Dict[str, Any]]] = collections.deque(maxlen=self._capacity)
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        """Возвращает максимальную емкость буфера."""
        return self._capacity

    def append(self, item: Dict[str, Any], epoch_timestamp: Optional[float] = None) -> None:
        """Добавляет запись телеметрии в кольцевой буфер.

        Args:
            item: Словарь с телеметрией или системным снимком.
            epoch_timestamp: Unix epoch timestamp в секундах (если None, берется текущее время).
        """
        ts = epoch_timestamp if epoch_timestamp is not None else time.time()
        with self._lock:
            self._buffer.append((ts, item))

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
            return [item for ts, item in self._buffer if ts >= cutoff]

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
            return [item for ts, item in self._buffer if start_ts <= ts <= end_ts]

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все текущие записи в буфере.

        Returns:
            List[Dict[str, Any]]: Полный текущий срез буфера.
        """
        with self._lock:
            return [item for _, item in self._buffer]

    def count(self) -> int:
        """Возвращает текущее число записей в буфере."""
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """Очищает буфер."""
        with self._lock:
            self._buffer.clear()
