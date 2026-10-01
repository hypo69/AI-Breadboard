# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Software_Manager Tests - Test Software Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.software_manager.tests.test_software_manager import manager
#
#     res = manager()
#
# File: test_software_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.software_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.software_manager.core.manager import SoftwarePackagesManager
from apps.windows.modules.software_manager.core.models import PackageActionRequest
from apps.windows.modules.software_manager.router import init_router


@pytest.fixture
def manager() -> SoftwarePackagesManager:
    return SoftwarePackagesManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_software_report(manager: SoftwarePackagesManager):
    """Проверка генерации отчета об установленном ПО."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_packages > 0
    assert len(report.packages) > 0


@pytest.mark.asyncio
async def test_package_action_simulation(manager: SoftwarePackagesManager):
    """Проверка симуляции безопасного действия с пакетом."""
    req = PackageActionRequest(
        package_id='Git.Git',
        action='upgrade',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_package_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_software_endpoints(client: TestClient):
    """Проверка REST эндпоинтов software_manager."""
    resp = client.get('/api/software-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'packages' in data

    resp_pkgs = client.get('/api/software-manager/packages')
    assert resp_pkgs.status_code == 200

    resp_search = client.get('/api/software-manager/search?q=python')
    assert resp_search.status_code == 200
    assert len(resp_search.json()) > 0
