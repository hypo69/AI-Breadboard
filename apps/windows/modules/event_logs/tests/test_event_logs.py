# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs Tests - Test Event Logs
# =============================================================================
# Description:
#   Тестирование модуля управления журналами событий Windows и Log Intelligence API.
#
# Usage Examples:
#   Python API:
#     pytest apps/windows/modules/event_logs/tests/test_event_logs.py
#
# File: test_event_logs.py
# Project: ai-breadboard
# Package: apps.windows.modules.event_logs.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations
"""Тестирование модуля управления журналами событий Windows и Log Intelligence API."""

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

    resp_events = client.get('/api/event-logs/events?channel=System&limit=10')
    assert resp_events.status_code == 200
    assert isinstance(resp_events.json(), list)


def test_event_logs_intelligence_pipeline(client: TestClient, manager: EventLogsManager):
    """Проверка интеграции Log Intelligence через API event_logs."""
    # 1. Profile / Process
    resp = client.get('/api/event-logs/intelligence/profile?channel=System&hours=24&limit=20')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channel' in data
    assert 'profile' in data
    assert 'decision' in data
    assert 'health_score' in data['profile']
    assert 'strategy' in data['decision']

    # 2. Audit
    resp_audit = client.get('/api/event-logs/intelligence/audit?channel=System&hours=24&limit=20')
    assert resp_audit.status_code == 200
    audit_data = resp_audit.json()
    assert 'health_score' in audit_data
    assert 'redundancy_pct' in audit_data
    assert 'strategy' in audit_data

    # 3. RAG Search
    resp_search = client.get('/api/event-logs/intelligence/search?query=system&top_k=3')
    assert resp_search.status_code == 200
    assert isinstance(resp_search.json(), list)
