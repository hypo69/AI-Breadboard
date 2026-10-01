# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs Tests - Test Event Logs
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.event_logs.tests.test_event_logs import manager
#
#     res = manager()
#
# File: test_event_logs.py
# Project: ai-breadboard
# Package: apps.windows.modules.event_logs.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.event_logs.core.manager import EventLogsManager
from apps.windows.modules.event_logs.core.models import EventLogActionRequest
from apps.windows.modules.event_logs.router import init_router


@pytest.fixture
def manager() -> EventLogsManager:
    return EventLogsManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_event_logs_report(manager: EventLogsManager):
    """Проверка генерации отчета журналов событий."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_channels > 0
    assert len(report.channels) > 0


@pytest.mark.asyncio
async def test_event_log_action_simulation(manager: EventLogsManager):
    """Проверка симуляции безопасного действия с журналом."""
    req = EventLogActionRequest(
        channel_name='Application',
        action='clear',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_channel_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_event_logs_endpoints(client: TestClient):
    """Проверка REST эндпоинтов event_logs."""
    resp = client.get('/api/event-logs/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channels' in data
    assert 'recent_errors' in data

    resp_channels = client.get('/api/event-logs/channels')
    assert resp_channels.status_code == 200

    resp_errors = client.get('/api/event-logs/errors')
    assert resp_errors.status_code == 200
