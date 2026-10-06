# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Task Scheduler Tests
# =============================================================================
# Description:
#   Модульные тесты для подсистемы Task Scheduler (TaskSchedulerManager, API и роутер).
#
# Usage Examples:
#   pytest apps/windows/tests/test_task_scheduler.py
#
# File: test_task_scheduler.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:35:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для подсистемы Task Scheduler."""

import pytest
from fastapi.testclient import TestClient
from apps.windows.api.internal_app import create_internal_app
from apps.windows.modules.task_scheduler.core.manager import TaskSchedulerManager
from apps.windows.modules.task_scheduler.core.models import (
    ScheduledTaskItem,
    TaskActionRequest,
    TaskSchedulerReport,
)


@pytest.fixture
def manager() -> TaskSchedulerManager:
    """Фикстура экземпляра TaskSchedulerManager."""
    return TaskSchedulerManager()


@pytest.fixture
def client() -> TestClient:
    """Фикстура тестового клиента FastAPI приложения."""
    app = create_internal_app()
    return TestClient(app)


def test_task_scheduler_list_tasks(manager: TaskSchedulerManager) -> None:
    """Проверка сбора задач планировщика."""
    tasks = manager.list_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) > 0

    first_task = tasks[0]
    assert isinstance(first_task, ScheduledTaskItem)
    assert first_task.task_name != ''
    assert first_task.name != ''
    assert first_task.state != ''
    assert first_task.status != ''


def test_task_scheduler_generate_report(manager: TaskSchedulerManager) -> None:
    """Проверка генерации сводного отчета планировщика."""
    report = manager.generate_report()
    assert isinstance(report, TaskSchedulerReport)
    assert report.total_tasks > 0
    assert report.total_tasks == len(report.tasks)
    assert report.ready_tasks >= 0
    assert report.disabled_tasks >= 0
    assert report.timestamp != ''


@pytest.mark.asyncio
async def test_task_scheduler_dry_run_action(manager: TaskSchedulerManager) -> None:
    """Проверка выполнения действия в режиме dry_run."""
    req = TaskActionRequest(
        task_path='\\TestTask',
        action='run',
        dry_run=True,
        confirmed_by_user=True,
    )
    res = await manager.execute_task_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'
    assert res['task_path'] == '\\TestTask'
    assert 'Симуляция' in res['message']


def test_api_task_scheduler_summary(client: TestClient) -> None:
    """Проверка GET эндпоинта /api/task-scheduler/summary."""
    response = client.get('/api/task-scheduler/summary')
    assert response.status_code == 200
    data = response.json()
    assert 'total_tasks' in data
    assert 'ready_tasks' in data
    assert 'tasks' in data
    assert isinstance(data['tasks'], list)
    assert len(data['tasks']) > 0

    task = data['tasks'][0]
    assert 'task_name' in task
    assert 'name' in task
    assert 'state' in task
    assert 'status' in task
    assert 'schedule_type' in task


def test_api_task_scheduler_tasks_filtered(client: TestClient) -> None:
    """Проверка GET эндпоинта /api/task-scheduler/tasks с фильтрацией."""
    response = client.get('/api/task-scheduler/tasks?state=ready')
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    for t in tasks:
        assert 'ready' in t['state'].lower() or 'готов' in t['state'].lower()


def test_api_task_scheduler_action_endpoint(client: TestClient) -> None:
    """Проверка POST эндпоинта /api/task-scheduler/action."""
    payload = {
        'task_path': '\\TestTask',
        'task_name': 'TestTask',
        'action': 'schtasks_run',
        'dry_run': True,
    }
    response = client.post('/api/task-scheduler/action', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'DRY_RUN_SUCCESS'
