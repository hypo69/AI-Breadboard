# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Router System Logs
# =============================================================================
# Description:
#   Тестирование REST роутера системных журналов (/api/v1/system_logs) и Log Intelligence.
#
# Usage Examples:
#   Python API:
#     pytest apps/windows/tests/test_router_system_logs.py
#
# File: test_router_system_logs.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations
"""Тестирование REST роутера системных журналов (/api/v1/system_logs) и Log Intelligence."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_system_logs import init_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_system_logs_scan(client: TestClient):
    """Проверка сканирования источников логов в системе."""
    resp = client.get('/api/v1/system_logs/scan')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channels' in data
    assert 'total_sources' in data
    assert len(data['channels']) > 0


def test_system_logs_events(client: TestClient):
    """Проверка получения списка событий."""
    resp = client.get('/api/v1/system_logs/events?channel=System&limit=10')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channel' in data
    assert 'entries' in data
    assert len(data['entries']) > 0
    first = data['entries'][0]
    assert 'timestamp' in first
    assert 'level' in first
    assert 'message' in first


def test_system_logs_incidents(client: TestClient):
    """Проверка анализа инцидентов."""
    resp = client.get('/api/v1/system_logs/incidents?window_seconds=25.0')
    assert resp.status_code == 200
    data = resp.json()
    assert 'incidents' in data


def test_system_logs_timeline(client: TestClient):
    """Проверка временной шкалы событий."""
    resp = client.get('/api/v1/system_logs/timeline')
    assert resp.status_code == 200
    data = resp.json()
    assert 'histogram' in data


def test_system_logs_audit_eda(client: TestClient):
    """Проверка EDA аудита от Log Intelligence (Data Researcher)."""
    resp = client.get('/api/v1/system_logs/audit?channel=System&limit=30')
    assert resp.status_code == 200
    data = resp.json()
    assert 'health_score' in data
    assert 'redundancy_pct' in data
    assert 'strategy' in data
    assert 'top_clusters' in data


def test_system_logs_rag_build_and_query(client: TestClient):
    """Проверка сборки чанков и поиска в Adaptive Log RAG."""
    # 1. Build
    resp_build = client.post('/api/v1/system_logs/rag/build?channel=System&limit=25')
    assert resp_build.status_code == 200
    build_data = resp_build.json()
    assert 'decision' in build_data
    assert 'profile' in build_data

    # 2. Query
    resp_query = client.post('/api/v1/system_logs/rag/query', json={'query': 'сеть network', 'top_k': 3})
    assert resp_query.status_code == 200
    query_data = resp_query.json()
    assert 'results' in query_data


def test_system_logs_explain(client: TestClient):
    """Проверка объяснения события (RCA)."""
    payload = {
        'provider': 'Microsoft-Windows-Bits-Client',
        'event_id': 16393,
        'level': 'Warning',
        'message': 'ErrorCode: 2147747072',
        'channel': 'System',
    }
    resp = client.post('/api/v1/system_logs/explain', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'summary' in data
    assert 'root_cause' in data
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0
