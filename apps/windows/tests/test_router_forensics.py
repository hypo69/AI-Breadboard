# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Router Forensics
# =============================================================================
# Description:
#   Модульные тесты для роутера поведенческой форензики (router_forensics.py)
#   и интеграции с базой данных telemetry.db (Data-First).
#
# Usage Examples:
#   pytest apps/windows/tests/test_router_forensics.py -v
#
# File: test_router_forensics.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:41:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для роутера форензики на базе SQLite."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.api.routers.router_forensics import init_router
from apps.windows.telemetry.sqlite import TelemetryStorage


@pytest.fixture
def test_client() -> TestClient:
    """Создает тестовый клиент FastAPI с роутером форензики."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_forensics_get_endpoint(test_client: TestClient) -> None:
    """Проверка получения форензик-данных из SQLite с Cold Start."""
    resp = test_client.get("/api/v1/system/diagnostics/forensics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "foreground_window" in data
    assert "user_idle_seconds" in data
    assert "camera_active_apps" in data
    assert "microphone_active_apps" in data
    assert "userassist_top_apps" in data


def test_forensics_refresh_endpoint(test_client: TestClient) -> None:
    """Проверка принудительного обновления форензики по запросу."""
    resp = test_client.post("/api/v1/system/diagnostics/forensics/refresh")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "foreground_window" in data
