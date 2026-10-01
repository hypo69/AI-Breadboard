# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager Tests - Test Services Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.services_manager.tests.test_services_manager import manager
#
#     res = manager()
#
# File: test_services_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.services_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.services_manager.core.manager import ServicesManager
from apps.windows.modules.services_manager.core.models import ServiceActionRequest
from apps.windows.modules.services_manager.router import init_router


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
