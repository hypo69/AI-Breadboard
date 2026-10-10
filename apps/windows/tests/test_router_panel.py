# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Router Panel Test
# =============================================================================
# Description:
#   Модульные тесты для универсального роутера GET /api/v1/panel/{panel_id}.
#
# File: test_router_panel.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 09:46:00
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from apps.windows.api.server import create_app


@pytest.fixture
def client() -> TestClient:
    """Создаёт тестовый клиент FastAPI приложения."""
    app = create_app()
    return TestClient(app)


def test_panel_sql_meta(client: TestClient) -> None:
    """Проверяет получение метаданных SQL-запроса для панели."""
    response = client.get("/api/v1/panel/panel-about-platform-os/sql")
    assert response.status_code == 200
    data = response.json()
    assert data["panel_id"] == "panel-about-platform-os"
    assert "SELECT" in data["sql"]
    assert data["table"] == "system_snapshots"


def test_panel_data_query(client: TestClient) -> None:
    """Проверяет выполнение SQL-запроса для панели через GET /api/v1/panel/{panel_id}."""
    response = client.get("/api/v1/panel/panel-cpu-load?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["panel_id"] == "panel-cpu-load"
    assert data["query_type"] == "sql"
    assert "SELECT" in data["sql"]
    assert isinstance(data["data"], list)


def test_panel_generic_query(client: TestClient) -> None:
    """Проверяет выполнение запроса для произвольного идентификатора панели."""
    response = client.get("/api/v1/panel/custom-widget-123?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["panel_id"] == "custom-widget-123"
    assert "SELECT" in data["sql"]
