# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Tests - Test Process Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.process_manager.tests.test_process_manager import manager
#
#     res = manager()
#
# File: test_process_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.process_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.process_manager.core.manager import ProcessManager
from apps.windows.modules.process_manager.core.models import ProcessKillRequest
from apps.windows.modules.process_manager.router import init_router


@pytest.fixture
def manager() -> ProcessManager:
    return ProcessManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_process_manager_report(manager: ProcessManager):
    """Проверка генерации отчета процессов."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_processes > 0
    assert len(report.processes) > 0


@pytest.mark.asyncio
async def test_process_kill_simulation(manager: ProcessManager):
    """Проверка симуляции завершения процесса."""
    req = ProcessKillRequest(
        pid=999999,
        kill_tree=True,
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.kill_process(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_process_manager_endpoints(client: TestClient):
    """Проверка REST эндпоинтов process_manager."""
    resp = client.get('/api/process-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_processes' in data
    assert 'processes' in data

    resp_list = client.get('/api/process-manager/list')
    assert resp_list.status_code == 200
    assert len(resp_list.json()) > 0
