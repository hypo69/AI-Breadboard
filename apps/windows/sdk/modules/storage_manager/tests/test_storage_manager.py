# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Tests - Test Storage Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.tests.test_storage_manager import storage_manager
#
#     res = storage_manager()
#
# File: test_storage_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sdk.modules.storage_manager.core.manager import StorageManager
from apps.windows.sdk.modules.storage_manager.core.models import DiskOperationRequest
from apps.windows.sdk.modules.storage_manager.router import init_router


@pytest.fixture
def storage_manager() -> StorageManager:
    return StorageManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_storage_manager_report_generation(storage_manager: StorageManager):
    """Проверка генерации сводного отчета дисков и томов."""
    report = storage_manager.generate_report()
    assert report is not None
    assert len(report.volumes) >= 0
    assert report.fs_features is not None
    assert report.fs_features.trim_enabled is True


@pytest.mark.asyncio
async def test_storage_operation_simulation(storage_manager: StorageManager):
    """Проверка симуляции безопасной операции (Dry-Run)."""
    req = DiskOperationRequest(
        disk_id=0,
        action='clean',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await storage_manager.execute_disk_operation(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_storage_manager_endpoints(client: TestClient):
    """Проверка REST эндпоинтов модуля Storage Manager."""
    resp = client.get('/api/storage-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'volumes' in data
    assert 'disks' in data

    resp_disks = client.get('/api/storage-manager/disks')
    assert resp_disks.status_code == 200

    resp_vols = client.get('/api/storage-manager/volumes')
    assert resp_vols.status_code == 200
