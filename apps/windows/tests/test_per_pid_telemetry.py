# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Per PID Telemetry
# =============================================================================
# Description:
#   Модульные и интеграционные тесты для подсистемы попроцессного мониторинга ресурсов
#   (Per-PID Telemetry Engine): схемы SQLite, сборщика, DirectoryWatchEngine и FastAPI роутера.
#
# Usage Examples:
#   pytest apps/windows/tests/test_per_pid_telemetry.py -v
#
# File: test_per_pid_telemetry.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 11:58:00
# =============================================================================

from __future__ import annotations

"""Модульные тесты канонической подсистемы Per-PID Telemetry Engine и отслеживания файлов."""

import os
import sqlite3
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_telemetry import router as telemetry_router
from apps.windows.telemetry.directory_watcher import DirectoryWatchEngine
from apps.windows.telemetry.models import (
    CpuDetail,
    MemoryDetail,
    GpuDetail,
    IoDetail,
    NetworkDetail,
    ProcessTelemetryResponse,
    ProcessFileEventItem,
    TrackedDirectoryRequest,
)
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.sqlite.connection import TelemetryConnectionManager
from apps.windows.telemetry.sqlite.maintenance import TelemetryMaintenance
from apps.windows.telemetry.sqlite.reader import TelemetryReader
from apps.windows.telemetry.sqlite.schema import init_database_schema
from apps.windows.telemetry.sqlite.writer import TelemetryWriter


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Создает временный путь к файлу базы данных SQLite."""
    return tmp_path / "test_per_pid_telemetry.db"


@pytest.fixture
def connection_manager(temp_db_path: Path) -> Generator[TelemetryConnectionManager, None, None]:
    """Фикстура менеджера подключений SQLite с инициализированной схемой."""
    cm = TelemetryConnectionManager(db_path=temp_db_path)
    init_database_schema(cm.get_connection())
    yield cm


@pytest.fixture
def api_client(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Создает тестовый FastAPI клиент с настроенным хранилищем на временную БД."""
    storage = TelemetryStorage(db_path=temp_db_path, auto_flush=False)
    monkeypatch.setattr(TelemetryStorage, "get_instance", lambda *args, **kwargs: storage)

    app = FastAPI()
    app.include_router(telemetry_router)
    return TestClient(app)


# =============================================================================
# 1. Тесты схемы базы данных и операций записи/чтения
# =============================================================================

def test_sqlite_schema_per_pid_tables_exist(connection_manager: TelemetryConnectionManager) -> None:
    """Проверяет создание канонических таблиц process_pid_snapshots и process_file_events."""
    with connection_manager.lock, connection_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "process_pid_snapshots" in tables
        assert "process_file_events" in tables

        # Проверка индексов
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_proc_pid_time" in indexes
        assert "idx_proc_name_time" in indexes
        assert "idx_file_events_pid" in indexes
        assert "idx_file_events_dir" in indexes


def test_insert_and_get_process_pid_snapshot(connection_manager: TelemetryConnectionManager) -> None:
    """Проверяет запись и быстрое чтение метрик процесса по PID."""
    writer = TelemetryWriter(connection_manager)
    reader = TelemetryReader(connection_manager)

    sample_snapshot = {
        "pid": 1337,
        "process_name": "code.exe",
        "executable_path": "C:\\Program Files\\VSCode\\code.exe",
        "cpu_percent": 12.5,
        "user_time_ms": 4500,
        "kernel_time_ms": 1200,
        "thread_count": 24,
        "working_set_bytes": 256 * 1024 * 1024,
        "private_bytes": 180 * 1024 * 1024,
        "page_faults_count": 3400,
        "gpu_vram_bytes": 64 * 1024 * 1024,
        "gpu_utilization": 5.4,
        "read_bytes_total": 102400,
        "write_bytes_total": 204800,
        "read_ops_total": 45,
        "write_ops_total": 80,
        "net_bytes_sent_total": 5120,
        "net_bytes_recv_total": 10240,
        "handle_count": 520,
        "gdi_objects": 42,
        "user_objects": 28,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    inserted = writer.insert_process_pid_snapshots([sample_snapshot])
    assert inserted == 1

    start_time = time.perf_counter()
    retrieved = reader.get_process_pid_snapshot(pid=1337)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert retrieved is not None
    assert retrieved["pid"] == 1337
    assert retrieved["process_name"] == "code.exe"
    assert retrieved["cpu_percent"] == 12.5
    assert retrieved["user_time_ms"] == 4500
    assert retrieved["kernel_time_ms"] == 1200
    assert retrieved["thread_count"] == 24
    assert retrieved["working_set_bytes"] == 256 * 1024 * 1024
    assert retrieved["handle_count"] == 520
    assert elapsed_ms < 50.0  # Гарантия быстрого отклика


def test_insert_and_get_process_file_events(connection_manager: TelemetryConnectionManager) -> None:
    """Проверяет сохранение и фильтрацию событий файловой активности."""
    writer = TelemetryWriter(connection_manager)
    reader = TelemetryReader(connection_manager)

    events = [
        {
            "pid": 1337,
            "process_name": "code.exe",
            "action_type": "CREATE",
            "target_directory": "C:\\Projects\\AI-Breadboard",
            "file_path": "C:\\Projects\\AI-Breadboard\\main.py",
            "bytes_affected": 1024,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "pid": 1337,
            "process_name": "code.exe",
            "action_type": "MODIFY",
            "target_directory": "C:\\Projects\\AI-Breadboard",
            "file_path": "C:\\Projects\\AI-Breadboard\\config.json",
            "bytes_affected": 2048,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "pid": 9999,
            "process_name": "explorer.exe",
            "action_type": "DELETE",
            "target_directory": "C:\\Downloads",
            "file_path": "C:\\Downloads\\temp.zip",
            "bytes_affected": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]

    writer.insert_process_file_events(events)

    # Фильтрация по PID
    pid_events = reader.get_process_file_events(pid=1337)
    assert len(pid_events) == 2
    assert all(e["pid"] == 1337 for e in pid_events)

    # Фильтрация по директории
    dir_events = reader.get_process_file_events(directory="Downloads")
    assert len(dir_events) == 1
    assert dir_events[0]["process_name"] == "explorer.exe"


# =============================================================================
# 2. Тесты REST API эндпоинтов (FastAPI)
# =============================================================================

def test_get_process_telemetry_from_db_endpoint(api_client: TestClient, temp_db_path: Path) -> None:
    """Проверяет эндпоинт GET /api/v1/telemetry/processes/{pid} при наличии данных в БД."""
    storage = TelemetryStorage.get_instance()
    storage.insert_process_pid_snapshots([{
        "pid": 4242,
        "process_name": "ffmpeg.exe",
        "executable_path": "C:\\Tools\\ffmpeg.exe",
        "cpu_percent": 85.0,
        "user_time_ms": 30000,
        "kernel_time_ms": 5000,
        "thread_count": 16,
        "working_set_bytes": 512 * 1024 * 1024,
        "private_bytes": 480 * 1024 * 1024,
        "page_faults_count": 12000,
        "gpu_vram_bytes": 256 * 1024 * 1024,
        "gpu_utilization": 70.5,
        "read_bytes_total": 10485760,
        "write_bytes_total": 5242880,
        "read_ops_total": 1200,
        "write_ops_total": 600,
        "net_bytes_sent_total": 0,
        "net_bytes_recv_total": 0,
        "handle_count": 150,
        "gdi_objects": 0,
        "user_objects": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }])

    start_t = time.perf_counter()
    response = api_client.get("/api/v1/telemetry/processes/4242")
    latency_ms = (time.perf_counter() - start_t) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["pid"] == 4242
    assert data["process_name"] == "ffmpeg.exe"
    assert data["cpu"]["percent"] == 85.0
    assert data["cpu"]["user_time_ms"] == 30000
    assert data["memory"]["working_set_mb"] == 512.0
    assert data["gpu"]["vram_dedicated_mb"] == 256.0
    assert data["gpu"]["utilization_percent"] == 70.5
    assert data["io"]["read_bytes_sec"] == 10485760
    assert data["io"]["handles_count"] == 150


def test_get_current_process_telemetry_live_fallback(api_client: TestClient) -> None:
    """Проверяет live fallback для текущего запущенного процесса (os.getpid())."""
    current_pid = os.getpid()
    response = api_client.get(f"/api/v1/telemetry/processes/{current_pid}")
    assert response.status_code == 200
    data = response.json()
    assert data["pid"] == current_pid
    assert "cpu" in data
    assert "memory" in data
    assert data["memory"]["working_set_mb"] > 0


def test_get_nonexistent_process_telemetry_404(api_client: TestClient) -> None:
    """Проверяет возврат 404 для несуществующего PID."""
    response = api_client.get("/api/v1/telemetry/processes/99999999")
    assert response.status_code == 404


def test_get_process_file_activity_endpoint(api_client: TestClient) -> None:
    """Проверяет эндпоинт GET /api/v1/telemetry/processes/{pid}/file-activity."""
    storage = TelemetryStorage.get_instance()
    storage.insert_process_file_events([
        {
            "pid": 5555,
            "process_name": "builder.exe",
            "action_type": "CREATE",
            "target_directory": "C:\\Build",
            "file_path": "C:\\Build\\out.bin",
            "bytes_affected": 4096,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ])

    response = api_client.get("/api/v1/telemetry/processes/5555/file-activity")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["pid"] == 5555
    assert events[0]["action_type"] == "CREATE"
    assert events[0]["target_directory"] == "C:\\Build"


def test_manage_tracked_directories_endpoint(api_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет добавление и удаление отслеживаемых директорий через REST API."""
    cfg_file = tmp_path / "test_config.json"
    cfg_file.write_text('{"watch_directories": []}', encoding="utf-8")
    engine = DirectoryWatchEngine(config_path=cfg_file)
    monkeypatch.setattr(DirectoryWatchEngine, "get_instance", lambda *args, **kwargs: engine)

    # 1. Добавление
    add_req = {"action": "add", "directory_path": str(tmp_path / "WatchFolder")}
    resp_add = api_client.post("/api/v1/telemetry/tracked-directories", json=add_req)
    assert resp_add.status_code == 200
    data_add = resp_add.json()
    assert data_add["status"] == "ok"
    assert str(tmp_path / "WatchFolder") in data_add["tracked_directories"]

    # 2. Получение списка
    resp_list = api_client.get("/api/v1/telemetry/tracked-directories")
    assert resp_list.status_code == 200
    assert len(resp_list.json()["tracked_directories"]) == 1

    # 3. Удаление
    remove_req = {"action": "remove", "directory_path": str(tmp_path / "WatchFolder")}
    resp_rem = api_client.post("/api/v1/telemetry/tracked-directories", json=remove_req)
    assert resp_rem.status_code == 200
    data_rem = resp_rem.json()
    assert len(data_rem["tracked_directories"]) == 0


# =============================================================================
# 3. Тесты обслуживания и очистки устаревших записей (Retention)
# =============================================================================

def test_maintenance_cleans_per_pid_records(connection_manager: TelemetryConnectionManager) -> None:
    """Проверяет удаление посекундных записей process_pid_snapshots старше retention периода."""
    writer = TelemetryWriter(connection_manager)
    reader = TelemetryReader(connection_manager)
    maint = TelemetryMaintenance(connection_manager)

    old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    fresh_ts = datetime.now(timezone.utc).isoformat()

    writer.insert_process_pid_snapshots([
        {"pid": 101, "process_name": "old.exe", "cpu_percent": 1.0, "timestamp": old_ts},
        {"pid": 102, "process_name": "fresh.exe", "cpu_percent": 2.0, "timestamp": fresh_ts},
    ])

    # Запуск очистки с retention 1 день
    maint.cleanup_old_records(retention_days=1)

    assert reader.get_process_pid_snapshot(pid=101) is None
    assert reader.get_process_pid_snapshot(pid=102) is not None
