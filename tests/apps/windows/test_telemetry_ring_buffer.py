# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Ring Buffer
# =============================================================================
# Description:
#   Тесты кольцевого буфера телеметрии в оперативной памяти.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_ring_buffer import test_ring_buffer_capacity_and_fifo
#
#     res = test_ring_buffer_capacity_and_fifo()
#
# File: test_telemetry_ring_buffer.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты кольцевого буфера телеметрии в оперативной памяти."""

import time
import pytest
from apps.windows.telemetry.ring_buffer import TelemetryRingBuffer


def test_ring_buffer_capacity_and_fifo():
    """Проверяет соблюдение максимальной емкости и вытеснение старых записей."""
    rb = TelemetryRingBuffer(capacity=5)
    assert rb.capacity == 10  # Минимальный clamp 10

    small_rb = TelemetryRingBuffer(capacity=10)
    for i in range(15):
        small_rb.append({"index": i, "val": i * 10}, epoch_timestamp=100.0 + i)

    assert small_rb.count() == 10
    all_items = small_rb.get_all()
    assert len(all_items) == 10
    assert all_items[0]["index"] == 5
    assert all_items[-1]["index"] == 14


def test_ring_buffer_get_window():
    """Проверяет извлечение окна вокруг заданного момента времени (pre/post window)."""
    rb = TelemetryRingBuffer(capacity=100)
    center_ts = 1000.0

    # Заполняем записи с 900s по 1100s
    for ts in range(900, 1101, 10):
        rb.append({"ts": float(ts), "data": f"sample_{ts}"}, epoch_timestamp=float(ts))

    # Извлекаем окно: 60 секунд до и 30 секунд после
    window = rb.get_window(center_timestamp=center_ts, before_seconds=60.0, after_seconds=30.0)
    assert len(window) > 0
    timestamps = [w["ts"] for w in window]
    assert min(timestamps) >= 940.0
    assert max(timestamps) <= 1030.0
    assert center_ts in timestamps


def test_ring_buffer_get_recent_and_clear():
    """Проверяет получение недавних данных и очистку буфера."""
    rb = TelemetryRingBuffer(capacity=50)
    now = time.time()
    rb.append({"tag": "old"}, epoch_timestamp=now - 500)
    rb.append({"tag": "recent1"}, epoch_timestamp=now - 10)
    rb.append({"tag": "recent2"}, epoch_timestamp=now - 2)

    recent = rb.get_recent(seconds=30)
    assert len(recent) == 2
    assert recent[0]["tag"] == "recent1"
    assert recent[1]["tag"] == "recent2"

    rb.clear()
    assert rb.count() == 0
    assert rb.get_all() == []
