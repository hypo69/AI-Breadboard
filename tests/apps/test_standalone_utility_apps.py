# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Standalone Utility Apps Unit Tests
# =============================================================================
# Description:
#   Модульные тесты для автономных приложений утилит в /apps (AIDA64, HWiNFO,
#   smartmontools, CPU-Z, GPU-Z, LibreHardwareMonitor).
#
# File: test_standalone_utility_apps.py
# Project: ai-breadboard
# Package: tests.apps
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для автономных приложений в apps/."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.aida64.router import init_router as init_aida64_router
from apps.hwinfo.router import init_router as init_hwinfo_router
from apps.smartmontools.router import init_router as init_smartmontools_router
from apps.cpuz.router import init_router as init_cpuz_router
from apps.gpuz.router import init_router as init_gpuz_router
from apps.librehardwaremonitor.router import init_router as init_lhm_router
from fastapi import FastAPI


def test_aida64_standalone_app():
    """Тестирование эндпоинтов приложения AIDA64."""
    app = FastAPI()
    app.include_router(init_aida64_router())
    client = TestClient(app)

    res = client.get("/api/v1/aida64/status")
    assert res.status_code == 200
    assert "is_running" in res.json()

    res_sens = client.get("/api/v1/aida64/sensors")
    assert res_sens.status_code == 200
    assert "sensors" in res_sens.json()


def test_hwinfo_standalone_app():
    """Тестирование эндпоинтов приложения HWiNFO."""
    app = FastAPI()
    app.include_router(init_hwinfo_router())
    client = TestClient(app)

    res = client.get("/api/v1/hwinfo/status")
    assert res.status_code == 200
    assert "is_running" in res.json()


def test_smartmontools_standalone_app():
    """Тестирование эндпоинтов приложения smartmontools."""
    app = FastAPI()
    app.include_router(init_smartmontools_router())
    client = TestClient(app)

    res = client.get("/api/v1/smartmontools/status")
    assert res.status_code == 200
    assert "is_available" in res.json()


def test_cpuz_standalone_app():
    """Тестирование эндпоинтов приложения CPU-Z."""
    app = FastAPI()
    app.include_router(init_cpuz_router())
    client = TestClient(app)

    res = client.get("/api/v1/cpuz/status")
    assert res.status_code == 200
    assert "is_available" in res.json()


def test_gpuz_standalone_app():
    """Тестирование эндпоинтов приложения GPU-Z."""
    app = FastAPI()
    app.include_router(init_gpuz_router())
    client = TestClient(app)

    res = client.get("/api/v1/gpuz/status")
    assert res.status_code == 200
    assert "is_available" in res.json()


def test_lhm_standalone_app():
    """Тестирование эндпоинтов приложения LibreHardwareMonitor."""
    app = FastAPI()
    app.include_router(init_lhm_router())
    client = TestClient(app)

    res = client.get("/api/v1/lhm/status")
    assert res.status_code == 200
    assert "is_running" in res.json()
