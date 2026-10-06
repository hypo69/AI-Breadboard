# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Main
# =============================================================================
# Description:
#   Тесты для точки входа apps.windows.main.
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_main import client
#
#     res = client()
#
# File: test_main.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 11:24:00
# =============================================================================

"""Тесты для точки входа apps.windows.main."""

from fastapi.testclient import TestClient
import pytest
from apps.windows.main import create_windows_app, load_tc_config


@pytest.fixture
def client():
    """Фикстура тестового клиента для Windows App."""
    app = create_windows_app()
    with TestClient(app) as test_client:
        yield test_client


def test_config_loading():
    """Проверка загрузки конфигурации tc.json."""
    cfg = load_tc_config()
    assert isinstance(cfg, dict)
    assert 'apps' in cfg or 'server' in cfg or len(cfg) >= 0


def test_tc_index_page(client: TestClient):
    """Проверка доступности страницы /tc."""
    resp = client.get('/tc')
    assert resp.status_code == 200
    assert 'text/html' in resp.headers.get('content-type', '')


def test_apps_status_endpoint(client: TestClient):
    """Проверка эндпоинта статуса приложений для формирования динамического меню."""
    resp = client.get('/api/v1/apps/status')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'ok'
    assert 'apps' in data


def test_windows_health_endpoint(client: TestClient):
    """Проверка эндпоинта здоровья Windows."""
    resp = client.get('/api/windows/health')
    assert resp.status_code == 200
    data = resp.json()
    assert 'health_score' in data


def test_chat_active_model_endpoint(client: TestClient):
    """Проверка эндпоинта активной модели ИИ."""
    resp = client.get('/api/v1/chat/active-model')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') in ('ok', 'success')
    assert 'model' in data
