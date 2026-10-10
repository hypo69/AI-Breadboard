# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager Tests - Test Services Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.services_manager.tests.test_services_manager import manager
#
#     res = manager()
#
# File: test_services_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.services_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Тестирование модуля управления службами Windows на базе SQLite."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sdk.modules.services_manager.core.manager import ServicesManager
from apps.windows.sdk.modules.services_manager.core.models import ServiceActionRequest
from apps.windows.sdk.modules.services_manager.router import init_router


@pytest.fixture
def manager() -> ServicesManager:
    return ServicesManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_services_report(manager: ServicesManager):
    """Проверка генерации отчета о службах."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_services >= 0


@pytest.mark.asyncio
async def test_service_action_simulation(manager: ServicesManager):
    """Проверка симуляции безопасного действия со службой."""
    req = ServiceActionRequest(
        name='wuauserv',
        action='restart',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_service_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_services_endpoints(client: TestClient):
    """Проверка REST эндпоинтов services_manager."""
    resp = client.get('/api/services-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_services' in data
    assert 'services' in data

    resp_list = client.get('/api/services-manager/list')
    assert resp_list.status_code == 200


def test_services_sqlite_data_first_and_scan(client: TestClient):
    """Проверка работы архитектуры Data-First SQLite и эндпоинта /scan."""
    resp_scan = client.post('/api/services-manager/scan')
    assert resp_scan.status_code == 200
    data = resp_scan.json()
    assert data['total_services'] > 0
    assert len(data['services']) > 0

    resp_summary = client.get('/api/services-manager/summary')
    assert resp_summary.status_code == 200
    assert resp_summary.json()['total_services'] == data['total_services']
