# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Apps Research Statistic
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_apps_research_statistic`).
#
# Usage Examples:
#   Python API:
#     from tests.test_apps_research_statistic import client
#
#     res = client()
#
# File: test_apps_research_statistic.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_apps_research_statistic`)."""

import pytest
import os
import pandas as pd
from fastapi.testclient import TestClient
from src.app import create_app, AppState, register_routers

@pytest.fixture
def client():
    app = create_app()
    state = AppState()
    register_routers(app, state)
    return TestClient(app)

@pytest.fixture
def dummy_csv(tmp_path):
    d = tmp_path / 'data'
    d.mkdir()
    p = d / 'test.csv'
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df.to_csv(p, index=False)
    return str(p)

def test_research_statistic_health(client):
    response = client.get('/apps/research-statistic/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}

def test_run_research(client, dummy_csv):
    response = client.post('/apps/research-statistic/run-research', json={'file_path': dummy_csv})
    assert response.status_code == 200
    data = response.json()
    if 'error' in data:
        assert data['error'] == 'Dependencies not installed'
    else:
        assert 'statistics' in data
        assert 'ai_report' in data
        assert 'visualizations' in data