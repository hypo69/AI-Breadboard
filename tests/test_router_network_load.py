# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router Network Load
# =============================================================================
# Description:
#   Тесты роутера сетевой нагрузки и активности процессов
#   (GET /api/v1/panel/network-load и GET /api/v1/system/network-activity).
#
# File: test_router_network_load.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:25:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/network-load и /api/v1/system/network-activity."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_network_load import init_router


@pytest.fixture
def client():
    """Тестовый клиент FastAPI для роутера сетевой нагрузки."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_get_network_load(client: TestClient):
    """Проверка эндпоинта GET /api/v1/panel/network-load."""
    response = client.get("/api/v1/panel/network-load")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "download_bytes_sec" in data
    assert "upload_bytes_sec" in data
    assert "adapters" in data
    assert isinstance(data["adapters"], list)
    assert "wifi" in data
    assert "bluetooth" in data


def test_get_network_activity_system_endpoint(client: TestClient):
    """Проверка эндпоинта GET /api/v1/system/network-activity."""
    response = client.get("/api/v1/system/network-activity?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "pid" in item
        assert "name" in item
        assert "local_address" in item
        assert "remote_address" in item
        assert "protocol" in item
        assert "status" in item


def test_get_network_activity_panel_endpoint(client: TestClient):
    """Проверка эндпоинта GET /api/v1/panel/network-activity."""
    response = client.get("/api/v1/panel/network-activity?limit=10&only_internet=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
