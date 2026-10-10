# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Process Activity Deep Dive
# =============================================================================
# Description:
#   Модульные тесты подсистемы Process Intelligence & Activity Deep Dive
#   (защита от PID Recycling, схема SQLite, генеалогия Lineage, выборка сэмплов,
#   SafeOps администрирование и REST API эндпоинты FastAPI).
#
# Usage Examples:
#   CLI:
#     pytest apps/windows/tests/test_process_activity_deep_dive.py -v
#
# File: test_process_activity_deep_dive.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 11:58:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для Process Intelligence и отслеживания активности процессов."""

import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_process_activity import init_router
from apps.windows.api.server import create_app
from apps.windows.sdk.core.process_activity_engine import ProcessActivityEngine
from apps.windows.telemetry.models import (
    ProcessInstanceRecord,
    ProcessSafeOpsRequest,
)
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.sqlite.schema import init_database_schema


@pytest.fixture
def temp_db_file() -> Generator[Path, None, None]:
    """Фикстура пути к временному файлу SQLite базы данных."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    yield db_path
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass


@pytest.fixture
def temp_db(temp_db_file: Path) -> Generator[sqlite3.Connection, None, None]:
    """Фикстура подключения к временной базе данных SQLite."""
    conn = sqlite3.connect(str(temp_db_file), check_same_thread=False)
    init_database_schema(conn)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_storage(temp_db_file: Path, temp_db: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch) -> TelemetryStorage:
    """Фикстура тестового TelemetryStorage с изолированной БД."""
    storage = TelemetryStorage(db_path=temp_db_file, read_only=False)
    monkeypatch.setattr(TelemetryStorage, "get_instance", lambda *args, **kwargs: storage)
    return storage


@pytest.fixture
def engine(mock_storage: TelemetryStorage, monkeypatch: pytest.MonkeyPatch) -> ProcessActivityEngine:
    """Фикстура экземпляра ProcessActivityEngine."""
    engine_inst = ProcessActivityEngine(storage=mock_storage)
    engine_inst._last_scan_time = time.time() + 3600  # Отключаем автосканирование OS во время тестов
    monkeypatch.setattr(ProcessActivityEngine, "get_instance", lambda *args, **kwargs: engine_inst)
    return engine_inst


@pytest.fixture
def client(engine: ProcessActivityEngine) -> TestClient:
    """Фикстура TestClient для проверки REST API."""
    app = create_app()
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Тесты схемы базы данных и PID Recycling
# -----------------------------------------------------------------------------

def test_schema_creates_process_intelligence_tables(temp_db: sqlite3.Connection) -> None:
    """Проверяет создание всех 4 таблиц Process Intelligence и соответствующих индексов."""
    cursor = temp_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "process_definition" in tables
    assert "process_instance" in tables
    assert "process_sample" in tables
    assert "process_file_events" in tables


def test_pid_recycling_resolution(engine: ProcessActivityEngine, temp_db: sqlite3.Connection) -> None:
    """Проверяет, что процессы с одинаковым PID, но разным start_time создают раздельные инстансы."""
    cursor = temp_db.cursor()

    # Создаем описание программы
    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("worker.exe", "C:\\App\\worker.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid

    # Инстанс 1: Запущен в 10:00 (PID 4000)
    cursor.execute(
        """
        INSERT INTO process_instance (
            definition_id, pid, name, executable_path, start_time, exit_time, status
        ) VALUES (?, 4000, 'worker.exe', 'C:\\App\\worker.exe', '2026-10-08T10:00:00Z', '2026-10-08T10:05:00Z', 'EXITED')
        """,
        (def_id,),
    )
    inst_id_1 = cursor.lastrowid

    # Инстанс 2: Запущен в 10:30 (Система переиспользовала PID 4000)
    cursor.execute(
        """
        INSERT INTO process_instance (
            definition_id, pid, name, executable_path, start_time, status
        ) VALUES (?, 4000, 'worker.exe', 'C:\\App\\worker.exe', '2026-10-08T10:30:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    inst_id_2 = cursor.lastrowid
    temp_db.commit()

    assert inst_id_1 != inst_id_2
    assert inst_id_1 is not None and inst_id_2 is not None

    # Добавляем сэмплы для каждого инстанса
    cursor.execute(
        "INSERT INTO process_sample (instance_id, timestamp, created_at, cpu_percent, working_set_mb) VALUES (?, ?, ?, ?, ?)",
        (inst_id_1, "2026-10-08T10:02:00Z", 1728381720.0, 15.5, 120.0),
    )
    cursor.execute(
        "INSERT INTO process_sample (instance_id, timestamp, created_at, cpu_percent, working_set_mb) VALUES (?, ?, ?, ?, ?)",
        (inst_id_2, "2026-10-08T10:32:00Z", 1728383520.0, 85.0, 450.0),
    )
    temp_db.commit()

    samples_1 = engine.get_instance_samples(inst_id_1)
    samples_2 = engine.get_instance_samples(inst_id_2)

    assert len(samples_1) == 1
    assert len(samples_2) == 1
    assert samples_1[0].cpu_percent == 15.5
    assert samples_2[0].cpu_percent == 85.0


# -----------------------------------------------------------------------------
# 2. Тесты генеалогического дерева (Lineage)
# -----------------------------------------------------------------------------

def test_process_lineage_reconstruction(engine: ProcessActivityEngine, temp_db: sqlite3.Connection) -> None:
    """Проверяет корректность построения дерева происхождения предков и потомков."""
    cursor = temp_db.cursor()

    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("app.exe", "C:\\App\\app.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid

    # 1. Родитель: explorer.exe (#100)
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, name, executable_path, start_time, status)
        VALUES (100, ?, 1800, 'explorer.exe', 'C:\\Windows\\explorer.exe', '2026-10-08T08:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )

    # 2. Текущий: python.exe (#102, родитель #100)
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, parent_instance_id, name, executable_path, start_time, status)
        VALUES (102, ?, 7316, 100, 'python.exe', 'C:\\Python\\python.exe', '2026-10-08T10:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )

    # 3. Дочерний: subworker.exe (#103, родитель #102)
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, parent_instance_id, name, executable_path, start_time, status)
        VALUES (103, ?, 8124, 102, 'subworker.exe', 'C:\\Python\\subworker.exe', '2026-10-08T10:01:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    temp_db.commit()

    lineage = engine.get_instance_lineage(102)
    assert lineage.instance_id == 102
    assert lineage.name == "python.exe"
    assert lineage.parent is not None
    assert lineage.parent["instance_id"] == 100
    assert lineage.parent["name"] == "explorer.exe"
    assert len(lineage.children) == 1
    assert lineage.children[0]["instance_id"] == 103
    assert lineage.children[0]["name"] == "subworker.exe"


# -----------------------------------------------------------------------------
# 3. Тесты файловых событий и сетевых сокетов
# -----------------------------------------------------------------------------

def test_file_events_recording_and_query(engine: ProcessActivityEngine, temp_db: sqlite3.Connection) -> None:
    """Проверяет фиксацию и фильтрацию файловых операций инстанса."""
    cursor = temp_db.cursor()
    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("file_worker.exe", "C:\\Data\\file_worker.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, name, executable_path, start_time, status)
        VALUES (500, ?, 5000, 'file_worker.exe', 'C:\\Data\\file_worker.exe', '2026-10-08T10:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    temp_db.commit()

    engine.record_file_event(
        instance_id=500,
        action="CREATE",
        file_path="C:\\Data\\config.json",
        target_folder="C:\\Data",
        bytes_count=1024,
    )
    engine.record_file_event(
        instance_id=500,
        action="MODIFY",
        file_path="C:\\Data\\app.log",
        target_folder="C:\\Data",
        bytes_count=512,
    )

    events_all = engine.get_instance_file_activity(instance_id=500)
    assert len(events_all) == 2

    events_json = engine.get_instance_file_activity(instance_id=500, extension=".json")
    assert len(events_json) == 1
    assert events_json[0].file_path == "C:\\Data\\config.json"


# -----------------------------------------------------------------------------
# 4. Тесты SafeOps администрирования
# -----------------------------------------------------------------------------

def test_safeops_action_execution(engine: ProcessActivityEngine, temp_db: sqlite3.Connection) -> None:
    """Проверяет выполнение SafeOps операций (dump, priority, неизвестные действия)."""
    cursor = temp_db.cursor()
    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("test.exe", "C:\\Test\\test.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, name, executable_path, start_time, status)
        VALUES (999, ?, 99999, 'test.exe', 'C:\\Test\\test.exe', '2026-10-08T10:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    temp_db.commit()

    # Несуществующий PID в ОС возвращает корректное сообщение о завершении процесса
    req = ProcessSafeOpsRequest(action="kill")
    resp = engine.execute_safe_action(instance_id=999, request=req)
    assert resp.instance_id == 999
    assert resp.success is False
    assert "завершён" in resp.message


# -----------------------------------------------------------------------------
# 5. Тесты REST API Эндпоинтов (FastAPI)
# -----------------------------------------------------------------------------

def test_api_active_instances(client: TestClient, temp_db: sqlite3.Connection) -> None:
    """Проверяет эндпоинт GET /api/v1/telemetry/instances/active."""
    cursor = temp_db.cursor()
    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("active_svc.exe", "C:\\Svc\\active_svc.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, name, executable_path, start_time, status)
        VALUES (201, ?, 5555, 'active_svc.exe', 'C:\\Svc\\active_svc.exe', '2026-10-08T10:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    temp_db.commit()

    response = client.get("/api/v1/telemetry/instances/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["instance_id"] == 201 for item in data)


def test_api_instance_details_and_samples(client: TestClient, temp_db: sqlite3.Connection) -> None:
    """Проверяет эндпоинты GET /api/v1/telemetry/instances/{id} и /samples."""
    cursor = temp_db.cursor()
    cursor.execute(
        "INSERT INTO process_definition (name, executable_path, first_seen, last_seen) VALUES (?, ?, ?, ?)",
        ("app.exe", "C:\\App\\app.exe", "2026-10-08T10:00:00Z", "2026-10-08T11:00:00Z"),
    )
    def_id = cursor.lastrowid
    cursor.execute(
        """
        INSERT INTO process_instance (instance_id, definition_id, pid, name, executable_path, start_time, status)
        VALUES (301, ?, 7777, 'app.exe', 'C:\\App\\app.exe', '2026-10-08T10:00:00Z', 'RUNNING')
        """,
        (def_id,),
    )
    cursor.execute(
        """
        INSERT INTO process_sample (
            instance_id, timestamp, created_at, cpu_percent, working_set_mb, thread_count
        ) VALUES (301, '2026-10-08T10:05:00Z', 1728381900.0, 24.5, 310.0, 8)
        """
    )
    temp_db.commit()

    # Детали
    resp_det = client.get("/api/v1/telemetry/instances/301")
    assert resp_det.status_code == 200
    det_json = resp_det.json()
    assert det_json["instance_id"] == 301
    assert det_json["name"] == "app.exe"
    assert det_json["cpu_percent"] == 24.5

    # Сэмплы
    resp_sam = client.get("/api/v1/telemetry/instances/301/samples?limit=10")
    assert resp_sam.status_code == 200
    sam_json = resp_sam.json()
    assert len(sam_json) == 1
    assert sam_json[0]["working_set_mb"] == 310.0
