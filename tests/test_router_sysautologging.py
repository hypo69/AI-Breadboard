# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test System Auto-Logging REST API Router
# =============================================================================
# Description:
#   Тесты для эндпоинтов src/api/router_sysautologging.py: проверка статуса,
#   чтения и сохранения конфигурации, ручного опроса логгеров,
#   списка файлов, парсинга строк CSV, удаления и скачивания логов.
#
# File: test_router_sysautologging.py
# Project: ai-breadboard
# Package: tests
# Author: Kiro (AI Assistant)
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты FastAPI роутера управления системным автологгированием."""

import csv
import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.common.csv_logger import set_apps_log_dir_override, write_csv_row
from src.api.router_sysautologging import init_router


@pytest.fixture
def test_app(tmp_path: Path):
    """Создает тестовое приложение FastAPI с изолированным роутером."""
    set_apps_log_dir_override(tmp_path / "apps_logs")
    app = FastAPI()
    app.include_router(init_router())
    yield TestClient(app)
    set_apps_log_dir_override(None)


def test_get_sysautolog_status(test_app: TestClient):
    """Проверяет получение текущего статуса автологгирования."""
    response = test_app.get("/sysautologging/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "running" in data
    assert "logs_directory" in data
    assert "registered_pollers" in data
    assert isinstance(data["registered_pollers"], list)


def test_get_sysautolog_config(test_app: TestClient):
    """Проверяет получение текущей конфигурации логгеров."""
    response = test_app.get("/sysautologging/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "enable_autolog" in data
    assert "loggers" in data
    assert "system_inspector" in data["loggers"]
    assert "interval" in data["loggers"]["system_inspector"]


def test_poll_all_and_single_logger(test_app: TestClient):
    """Проверяет эндпоинты ручного опроса всех и конкретного логгера."""
    # Опрос всех логгеров
    resp_all = test_app.post("/sysautologging/poll-all")
    assert resp_all.status_code == 200
    data_all = resp_all.json()
    assert data_all["status"] == "success"
    assert data_all["total_polled"] > 0

    # Опрос конкретного логгера
    resp_single = test_app.post("/sysautologging/poll/system_inspector")
    assert resp_single.status_code == 200
    data_single = resp_single.json()
    assert data_single["status"] == "success"
    assert data_single["app_name"] == "system_inspector"


def test_list_read_delete_csv_files(test_app: TestClient, tmp_path: Path):
    """Проверяет операции с файлами логов: список, чтение, удаление и скачивание."""
    # 1. Записываем тестовый CSV
    headers = ["timestamp", "metric", "val"]
    write_csv_row("test_metric_polls.csv", headers, ["2026-09-19T12:00:00Z", "cpu", "25.4"])
    write_csv_row("test_metric_polls.csv", headers, ["2026-09-19T12:05:00Z", "ram", "70.1"])

    # 2. Список файлов
    resp_files = test_app.get("/sysautologging/files")
    assert resp_files.status_code == 200
    files_data = resp_files.json()
    assert files_data["status"] == "success"
    assert files_data["total_files"] >= 1
    found = next((f for f in files_data["files"] if f["filename"] == "test_metric_polls.csv"), None)
    assert found is not None
    assert found["row_count"] == 2

    # 3. Чтение содержимого файла
    resp_read = test_app.get("/sysautologging/file/test_metric_polls.csv")
    assert resp_read.status_code == 200
    read_data = resp_read.json()
    assert read_data["status"] == "success"
    assert read_data["headers"] == headers
    assert len(read_data["rows"]) == 2
    assert read_data["total_rows"] == 2

    # 4. Скачивание файла
    resp_down = test_app.get("/sysautologging/download/test_metric_polls.csv")
    assert resp_down.status_code == 200
    assert "25.4" in resp_down.text

    # 5. Удаление файла
    resp_del = test_app.get("/sysautologging/file/test_metric_polls.csv")
    assert resp_del.status_code == 200
    del_res = test_app.delete("/sysautologging/file/test_metric_polls.csv")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Проверяем, что файл удален
    resp_after = test_app.get("/sysautologging/file/test_metric_polls.csv")
    assert resp_after.status_code == 404


@pytest.mark.asyncio
async def test_start_and_stop_sysautolog(test_app: TestClient):
    """Проверяет эндпоинты старта и остановки движка."""
    resp_stop = test_app.post("/sysautologging/stop")
    assert resp_stop.status_code == 200
    assert resp_stop.json()["is_running"] is False

    resp_start = test_app.post("/sysautologging/start")
    assert resp_start.status_code == 200

    # Очищаем состояние
    resp_cleanup = test_app.post("/sysautologging/stop")
    assert resp_cleanup.status_code == 200
