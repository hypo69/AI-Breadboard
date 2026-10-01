# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Boot_Recovery Tests - Test Boot Recovery
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.boot_recovery.tests.test_boot_recovery import manager
#
#     res = manager()
#
# File: test_boot_recovery.py
# Project: ai-breadboard
# Package: apps.windows.modules.boot_recovery.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.boot_recovery.core.manager import BootRecoveryManager
from apps.windows.modules.boot_recovery.core.models import BootActionRequest
from apps.windows.modules.boot_recovery.router import init_router


@pytest.fixture
def manager() -> BootRecoveryManager:
    return BootRecoveryManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_boot_recovery_report(manager: BootRecoveryManager):
    """Проверка генерации отчета загрузчика."""
    report = manager.generate_report()
    assert report is not None
    assert len(report.entries) > 0
    assert report.winre.enabled is True


@pytest.mark.asyncio
async def test_boot_action_simulation(manager: BootRecoveryManager):
    """Проверка симуляции безопасного действия BCD."""
    req = BootActionRequest(
        action='set_timeout',
        value=10,
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_boot_recovery_endpoints(client: TestClient):
    """Проверка REST эндпоинтов boot_recovery."""
    resp = client.get('/api/boot-recovery/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'entries' in data
    assert 'winre' in data

    resp_entries = client.get('/api/boot-recovery/entries')
    assert resp_entries.status_code == 200

    resp_winre = client.get('/api/boot-recovery/winre')
    assert resp_winre.status_code == 200
