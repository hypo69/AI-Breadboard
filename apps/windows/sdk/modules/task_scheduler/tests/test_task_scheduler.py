# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler Tests - Test Task Scheduler
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.task_scheduler.tests.test_task_scheduler import manager
#
#     res = manager()
#
# File: test_task_scheduler.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.task_scheduler.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sdk.modules.task_scheduler.core.manager import TaskSchedulerManager
from apps.windows.sdk.modules.task_scheduler.core.models import TaskActionRequest
from apps.windows.sdk.modules.task_scheduler.router import init_router


@pytest.fixture
def manager() -> TaskSchedulerManager:
    return TaskSchedulerManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_task_scheduler_report(manager: TaskSchedulerManager):
    """Проверка генерации отчета о заданиях."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_tasks >= 0


@pytest.mark.asyncio
async def test_task_action_simulation(manager: TaskSchedulerManager):
    """Проверка симуляции действия с заданием."""
    req = TaskActionRequest(
        task_path='\\Microsoft\\Windows\\Defrag\\ScheduledDefrag',
        action='run',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_task_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_task_scheduler_endpoints(client: TestClient):
    """Проверка REST эндпоинтов task_scheduler."""
    resp = client.get('/api/task-scheduler/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'tasks' in data

    resp_tasks = client.get('/api/task-scheduler/tasks')
    assert resp_tasks.status_code == 200
