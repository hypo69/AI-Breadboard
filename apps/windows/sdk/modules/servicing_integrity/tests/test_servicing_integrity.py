# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Servicing_Integrity Tests - Test Servicing Integrity
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.servicing_integrity.tests.test_servicing_integrity import manager
#
#     res = manager()
#
# File: test_servicing_integrity.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.servicing_integrity.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sdk.modules.servicing_integrity.core.manager import ServicingIntegrityManager
from apps.windows.sdk.modules.servicing_integrity.core.models import ServicingActionRequest
from apps.windows.sdk.modules.servicing_integrity.router import init_router


@pytest.fixture
def manager() -> ServicingIntegrityManager:
    return ServicingIntegrityManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_integrity_report(manager: ServicingIntegrityManager):
    """Проверка генерации отчета целостности SFC/DISM."""
    report = manager.generate_report()
    assert report is not None
    assert 'Clean' in report.sfc_status
    assert report.dism_component_store_status == 'Healthy'
    assert len(report.features) > 0


@pytest.mark.asyncio
async def test_servicing_action_simulation(manager: ServicingIntegrityManager):
    """Проверка симуляции безопасного действия SFC/DISM."""
    req = ServicingActionRequest(
        tool='sfc',
        action='scannow',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_servicing_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_servicing_endpoints(client: TestClient):
    """Проверка REST эндпоинтов servicing_integrity."""
    resp = client.get('/api/servicing-integrity/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'sfc_status' in data
    assert 'features' in data

    resp_feat = client.get('/api/servicing-integrity/features')
    assert resp_feat.status_code == 200
    assert len(resp_feat.json()) > 0
