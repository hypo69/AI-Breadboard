# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router Memory IO
# =============================================================================
# Description:
#   Тесты эндпоинта GET /api/v1/panel/memory-io (память и дисковый ввод-вывод из БД).
#
# File: test_router_memory_io.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 03:54:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/memory-io."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_memory_io import init_router
from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskIoMetrics,
    MemoryMetrics,
    SystemSnapshot,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


@pytest.fixture
def storage(tmp_path):
    """Временное хранилище телеметрии."""
    return TelemetryStorage(db_path=tmp_path / "t.db", buffer_mode="direct", auto_flush=False)


@pytest.fixture
def client(storage):
    """Тестовый клиент с внедрённым хранилищем."""
    app = FastAPI()
    app.include_router(init_router(storage=storage))
    return TestClient(app)


def _save(storage, used_gb, pct, read_bps, write_bps):
    """Сохраняет снимок с заданными метриками памяти и диска."""
    storage.save_snapshot(SystemSnapshot(
        hostname="T",
        cpu=CpuMetrics(total_percent=1.0),
        memory=MemoryMetrics(total_gb=32.0, used_gb=used_gb, percent=pct),
        disk_io=DiskIoMetrics(read_bytes_per_sec=read_bps, write_bytes_per_sec=write_bps),
    ))
    storage.flush()


def test_empty_db(client):
    """Пустая БД: статус ok, отдаются актуальные fallback метрики или нули, пустая история."""
    data = client.get("/api/v1/panel/memory-io").json()
    assert data["status"] == "ok"
    assert data["memory"]["percent"] >= 0.0
    assert data["history"] == []


def test_latest_and_history(client, storage):
    """Берётся последний снимок; история отдаётся в хронологическом порядке."""
    _save(storage, 8.0, 25.0, 1000.0, 2000.0)
    _save(storage, 16.0, 50.0, 4096.0, 8192.0)

    data = client.get("/api/v1/panel/memory-io?limit=10").json()
    assert data["memory"]["total_gb"] == 32.0
    assert data["memory"]["used_gb"] == 16.0
    assert data["memory"]["percent"] == 50.0
    assert data["disk_io"]["read_bytes_sec"] == 4096.0
    assert data["disk_io"]["write_bytes_sec"] == 8192.0
    assert data["disk_io"]["total_bytes_sec"] == 12288.0
    assert [h["memory_percent"] for h in data["history"]] == [25.0, 50.0]
