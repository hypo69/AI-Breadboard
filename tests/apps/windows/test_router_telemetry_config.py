# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router Telemetry Config
# =============================================================================
# Description:
#   Модульные тесты для API роутера управления конфигурацией телеметрии
#   /api/windows/telemetry/config.
#
# Usage Examples:
#   CLI:
#     pytest tests/apps/windows/test_router_telemetry_config.py
#
# File: test_router_telemetry_config.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 03:20:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/windows/telemetry/config."""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_telemetry_config import init_router


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Фикстура тестового клиента с изолированным файлом конфигурации."""
    test_cfg = tmp_path / "test_telemetry_cfg.json"
    initial_data = {
        "mode": "hybrid",
        "interval_seconds": 4.0,
        "heavy_interval_seconds": 45.0,
        "top_processes": 12,
        "max_db_size_mb": 40.0,
        "sensors": {
            "cpu": {"enabled": True, "interval_seconds": 4.0},
            "gpu": {"enabled": False, "interval_seconds": 20.0}
        }
    }
    test_cfg.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    # Перенаправляем путь по умолчанию на тестовый файл
    monkeypatch.setattr(
        "apps.windows.telemetry.telemetry_config.get_default_telemetry_config_path",
        lambda: test_cfg
    )
    monkeypatch.setattr(
        "apps.windows.api.routers.router_telemetry_config.get_default_telemetry_config_path",
        lambda: test_cfg
    )

    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_get_telemetry_config(client):
    """Тест получения текущей конфигурации телеметрии."""
    res = client.get("/api/windows/telemetry/config")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "config" in data
    assert data["config"]["mode"] == "hybrid"
    assert data["config"]["interval_seconds"] == 4.0
    assert "intervals" in data


def test_get_raw_telemetry_config(client):
    """Тест получения сырого JSON текста конфигурации."""
    res = client.get("/api/windows/telemetry/config/raw")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "raw_json" in data
    parsed = json.loads(data["raw_json"])
    assert parsed["top_processes"] == 12


def test_save_structured_telemetry_config(client):
    """Тест сохранения структурированной конфигурации."""
    payload = {
        "config": {
            "mode": "minimal",
            "interval_seconds": 2.5,
            "heavy_interval_seconds": 90.0,
            "top_processes": 8,
            "sensors": {
                "cpu": {"enabled": True, "interval_seconds": 2.5}
            }
        }
    }
    res = client.post("/api/windows/telemetry/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["config"]["mode"] == "minimal"
    assert data["config"]["interval_seconds"] == 2.5

    # Проверяем последующий GET
    check_res = client.get("/api/windows/telemetry/config")
    assert check_res.json()["config"]["mode"] == "minimal"


def test_save_raw_telemetry_config_valid(client):
    """Тест сохранения валидного сырого текста JSON."""
    raw_text = json.dumps({
        "mode": "full",
        "interval_seconds": 1.0,
        "top_processes": 25
    }, indent=2)

    res = client.post("/api/windows/telemetry/config/raw", json={"raw_json": raw_text})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["config"]["mode"] == "full"


def test_save_raw_telemetry_config_invalid_syntax(client):
    """Тест валидации некорректного синтаксиса JSON."""
    broken_json = "{ mode: 'hybrid', unclosed: "
    res = client.post("/api/windows/telemetry/config/raw", json={"raw_json": broken_json})
    assert res.status_code == 400
    assert "Ошибка синтаксиса JSON" in res.json()["detail"]


def test_reset_telemetry_config(client):
    """Тест сброса конфигурации к шаблону по умолчанию."""
    res = client.post("/api/windows/telemetry/config/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "config" in data
