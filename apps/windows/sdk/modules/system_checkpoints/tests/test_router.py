# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Router
# =============================================================================
# Description:
#   Тесты FastAPI REST API для приложения контрольных точек Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.tests.test_router import test_get_health_endpoint
#
#     res = test_get_health_endpoint()
#
# File: test_router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты FastAPI REST API для приложения контрольных точек Windows."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from apps.windows.system_checkpoints.router import router
from apps.windows.system_checkpoints.models import FreshnessLevel, FreshnessReport, WinREStatus


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_health_endpoint():
    """Проверка эндпоинта /api/v1/windows-checkpoints/health."""
    with patch(
        "apps.windows.system_checkpoints.router._coordinator.get_comprehensive_health",
        return_value={"health_score": 90, "winre": {"enabled": True}},
    ):
        res = client.get("/api/v1/windows-checkpoints/health")
        assert res.status_code == 200
        data = res.json()
        assert data["health_score"] == 90
        assert data["winre"]["enabled"] is True


def test_get_freshness_endpoint():
    """Проверка эндпоинта /api/v1/windows-checkpoints/freshness."""
    mock_report = FreshnessReport(
        last_image_name="Recovery_Baseline.wim",
        freshness_level=FreshnessLevel.HIGH,
        freshness_label_ru="Высокая",
    )
    with patch(
        "apps.windows.system_checkpoints.router._coordinator.get_freshness_report",
        return_value=mock_report,
    ):
        res = client.get("/api/v1/windows-checkpoints/freshness")
        assert res.status_code == 200
        data = res.json()
        assert data["freshness_level"] == "HIGH"
        assert data["last_image_name"] == "Recovery_Baseline.wim"


def test_get_catalog_endpoint():
    """Проверка эндпоинта /api/v1/windows-checkpoints/catalog."""
    with patch(
        "apps.windows.system_checkpoints.router._coordinator.load_catalog",
        return_value=[],
    ):
        res = client.get("/api/v1/windows-checkpoints/catalog")
        assert res.status_code == 200
        assert res.json() == []


def test_get_winre_status_endpoint():
    """Проверка эндпоинта /api/v1/windows-checkpoints/winre/status."""
    with patch(
        "apps.windows.system_checkpoints.router._winre_mgr.get_status",
        return_value=WinREStatus(enabled=True, location="Recovery/WindowsRE"),
    ):
        res = client.get("/api/v1/windows-checkpoints/winre/status")
        assert res.status_code == 200
        data = res.json()
        assert data["enabled"] is True
        assert "Recovery/WindowsRE" in data["location"]


def test_get_images_endpoint():
    """Проверка эндпоинта /api/v1/windows-checkpoints/images."""
    with patch(
        "apps.windows.system_checkpoints.router._image_mgr.scan_recovery_images",
        return_value=[],
    ):
        res = client.get("/api/v1/windows-checkpoints/images")
        assert res.status_code == 200
        assert res.json() == []
