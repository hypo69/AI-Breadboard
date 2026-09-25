# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Standalone Utility Apps Unit Tests
# =============================================================================
# Description:
#   Модульные тесты для автономных приложений утилит в /apps
#   (LibreHardwareMonitor).
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

from apps.librehardwaremonitor.router import init_router as init_lhm_router
from fastapi import FastAPI


def test_lhm_standalone_app():
    """Тестирование эндпоинтов приложения LibreHardwareMonitor."""
    app = FastAPI()
    app.include_router(init_lhm_router())
    client = TestClient(app)

    res = client.get("/api/v1/lhm/status")
    assert res.status_code == 200
    assert "is_running" in res.json()
