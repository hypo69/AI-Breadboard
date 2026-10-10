# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router App Logs
# =============================================================================
# Description:
#   Тесты для FastAPI роутера анализа, экспорта и стриминга внутренних логов программы
#   из каталога %APPDATA%\AI-Breadboard\logs.
#
# Usage Examples:
#   Pytest CLI:
#     pytest tests/test_router_app_logs.py -v
#
# File: test_router_app_logs.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:38:00
# =============================================================================

import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_app_logs import init_router, get_logs_dir


@pytest.fixture
def test_logs_dir(tmp_path, monkeypatch):
    """Фикстура изолированной тестовой папки логов."""
    logs_dir = tmp_path / "test_app_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AI_BREADBOARD_LOGS_DIR", str(logs_dir))

    # Создаем тестовые файлы логов
    json_log = logs_dir / "log.json"
    json_entries = [
        {"timestamp": "2026-10-08 10:00:01", "level": "INFO", "levelname": "INFO", "message": "[InternalApp] Сервер запущен на 127.0.0.1:8001", "exc_info": None},
        {"timestamp": "2026-10-08 10:00:05", "level": "DEBUG", "levelname": "DEBUG", "message": "[Router] Зарегистрирован роутер /api/v1/app_logs", "exc_info": None},
        {"timestamp": "2026-10-08 10:01:10", "level": "WARNING", "levelname": "WARNING", "message": "[Config] Не удалось найти опциональный модуль", "exc_info": None},
        {"timestamp": "2026-10-08 10:02:15", "level": "ERROR", "levelname": "ERROR", "message": "[FastAPI] Syntax error parsing json config at line 42", "exc_info": "Traceback (most recent call last):\n  File 'app.py', line 42\nValueError: Extra data"},
        {"timestamp": "2026-10-08 10:02:20", "level": "CRITICAL", "levelname": "CRITICAL", "message": "[System] Access denied accessing protected token", "exc_info": None},
    ]
    with open(json_log, "w", encoding="utf-8") as f:
        for entry in json_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    text_log = logs_dir / "errors.log"
    with open(text_log, "w", encoding="utf-8") as f:
        f.write("2026-10-08 10:02:15 ERROR: [FastAPI] Syntax error parsing json config\n")
        f.write("[3x] 2026-10-08 10:02:20 CRITICAL: [System] Access denied\n")

    info_log = logs_dir / "info.log"
    with open(info_log, "w", encoding="utf-8") as f:
        f.write("2026-10-08 10:00:01 INFO: [InternalApp] Server started\n")

    return logs_dir


@pytest.fixture
def client(test_logs_dir):
    """Тестовый клиент FastAPI для router_app_logs."""
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return TestClient(app)


def test_list_log_files(client, test_logs_dir):
    """Проверка получения списка доступных файлов логов."""
    response = client.get("/api/v1/app_logs/files")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["total_files"] >= 3
    file_names = [f["name"] for f in data["files"]]
    assert "log.json" in file_names
    assert "errors.log" in file_names
    assert "info.log" in file_names


def test_get_logs_overview(client, test_logs_dir):
    """Проверка сводного обзора логов системы."""
    response = client.get("/api/v1/app_logs/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] >= 3
    assert data["total_size_bytes"] > 0
    assert "system_health" in data
    assert isinstance(data["files"], list)


def test_get_log_records_json(client, test_logs_dir):
    """Проверка выборки и парсинга структурированных JSON записей."""
    response = client.get("/api/v1/app_logs/records?file_name=log.json")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 5
    assert len(data["records"]) == 5
    assert data["stats"]["errors_count"] == 2
    assert data["stats"]["warnings_count"] == 1
    assert data["stats"]["levels"]["INFO"] == 1

    # Проверка извлечения компонентов
    comps = [c["name"] for c in data["stats"]["components"]]
    assert "InternalApp" in comps or "Router" in comps or "FastAPI" in comps


def test_get_log_records_filtering(client, test_logs_dir):
    """Проверка фильтрации по уровню и тексту."""
    # Фильтр только ошибок
    res_err = client.get("/api/v1/app_logs/records?file_name=log.json&level=ERRORS")
    assert res_err.status_code == 200
    data_err = res_err.json()
    assert data_err["total_matches"] == 2
    for r in data_err["records"]:
        assert r["level"] in ("ERROR", "CRITICAL")

    # Полнотекстовый поиск
    res_search = client.get("/api/v1/app_logs/records?file_name=log.json&search=Syntax error")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total_matches"] == 1
    assert "Syntax error" in data_search["records"][0]["message"]
    assert data_search["records"][0]["exc_info"] is not None


def test_get_log_records_text(client, test_logs_dir):
    """Проверка парсинга обычного текстового лог-файла."""
    response = client.get("/api/v1/app_logs/records?file_name=errors.log")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 2
    assert data["records"][0]["repeat_count"] == 3 or data["records"][1]["repeat_count"] == 3


def test_export_logs_formats(client, test_logs_dir):
    """Проверка экспорта записей в CSV, JSON и Markdown форматы."""
    # CSV
    res_csv = client.get("/api/v1/app_logs/export?file_name=log.json&export_format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Timestamp,Level,Component" in res_csv.text

    # JSON
    res_json = client.get("/api/v1/app_logs/export?file_name=log.json&export_format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    data = json.loads(res_json.text)
    assert isinstance(data, list)
    assert len(data) == 5

    # Markdown
    res_md = client.get("/api/v1/app_logs/export?file_name=log.json&export_format=markdown")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert "# 📑 Аналитический отчет" in res_md.text


def test_tail_log(client, test_logs_dir):
    """Проверка эндпоинта tail для потокового терминала."""
    response = client.get("/api/v1/app_logs/tail?file_name=log.json&lines=3")
    assert response.status_code == 200
    data = response.json()
    assert data["returned_lines"] == 3
    assert len(data["lines"]) == 3


def test_diagnose_log(client, test_logs_dir):
    """Проверка AI диагностики и кластеризации сбоев."""
    payload = {
        "file_name": "log.json",
        "limit": 50,
        "focus_errors_only": True
    }
    response = client.post("/api/v1/app_logs/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["faults_count"] >= 2
    assert len(data["clusters"]) >= 1
    assert len(data["recommendations"]) >= 1


def test_clear_and_download_log(client, test_logs_dir):
    """Проверка очистки и скачивания лог-файла."""
    # Скачивание
    res_dl = client.get("/api/v1/app_logs/download?file_name=info.log")
    assert res_dl.status_code == 200
    assert b"Server started" in res_dl.content

    # Очистка
    res_clear = client.post("/api/v1/app_logs/clear", json={"file_name": "info.log"})
    assert res_clear.status_code == 200
    assert res_clear.json()["success"] is True

    # Проверка, что файл пуст
    res_records = client.get("/api/v1/app_logs/records?file_name=info.log")
    assert res_records.status_code == 200
    assert res_records.json()["total_matches"] == 0
