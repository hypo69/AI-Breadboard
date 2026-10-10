# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Performance_Tracing Tests - Test Performance Tracing
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.performance_tracing.tests.test_performance_tracing import manager
#
#     res = manager()
#
# File: test_performance_tracing.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.performance_tracing.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sdk.modules.performance_tracing.core.manager import PerformanceTracingManager
from apps.windows.sdk.modules.performance_tracing.core.models import CollectorActionRequest
from apps.windows.sdk.modules.performance_tracing.router import init_router


@pytest.fixture
def manager() -> PerformanceTracingManager:
    return PerformanceTracingManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_performance_report(manager: PerformanceTracingManager):
    """Проверка генерации отчета производительности."""
    report = manager.generate_report()
    assert report is not None
    assert report.cpu_usage_percent >= 0.0
    assert len(report.counter_samples) > 0


@pytest.mark.asyncio
async def test_collector_action_simulation(manager: PerformanceTracingManager):
    """Проверка симуляции безопасного действия со сборщиком."""
    req = CollectorActionRequest(
        collector_name='System Diagnostics',
        action='start',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_collector_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_performance_endpoints(client: TestClient):
    """Проверка REST эндпоинтов performance_tracing."""
    resp = client.get('/api/performance-tracing/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'counter_samples' in data
    assert 'collectors' in data

    resp_counters = client.get('/api/performance-tracing/counters')
    assert resp_counters.status_code == 200
    assert len(resp_counters.json()) > 0
