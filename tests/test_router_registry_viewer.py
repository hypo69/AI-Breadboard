# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router Registry Viewer
# =============================================================================
# Description:
#   Тесты для роутера Registry Viewer.
#
# Usage Examples:
#   Python API:
#     from tests.test_router_registry_viewer import client
#
#     res = client()
#
# File: test_router_registry_viewer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:20:00
# =============================================================================

"""Тесты для роутера Registry Viewer."""

import pytest
from fastapi.testclient import TestClient
from src.app import create_app, register_routers, AppState

@pytest.fixture
def client():
    app = create_app()
    state = AppState()
    app.state.app_state = state
    from apps.windows.sdk.modules.registry import init_router as init_reg_router
    from src.api.routers.core.router_admin import init_router as init_admin_router
    app.include_router(init_reg_router())
    app.include_router(init_admin_router())
    return TestClient(app)

def test_registry_bookmarks(client):
    """Проверка получения списка закладок реестра."""
    response = client.get('/api/registry/bookmarks')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'bookmarks' in data
    assert len(data['bookmarks']) > 0
    bookmark_ids = [b['id'] for b in data['bookmarks']]
    assert 'startup_run' in bookmark_ids
    assert 'installed_apps_x64' in bookmark_ids
    assert 'services' in bookmark_ids

def test_registry_key_details_hklm(client):
    """Проверка получения параметров и подразделов ветки HKLM."""
    response = client.get('/api/registry/key?hive=HKEY_LOCAL_MACHINE&path=SOFTWARE')
    assert response.status_code == 200
    data = response.json()
    assert data['hive'] == 'HKEY_LOCAL_MACHINE'
    assert 'subkeys' in data
    assert isinstance(data['subkeys'], list)
    assert 'values' in data
    assert isinstance(data['values'], list)

def test_registry_key_details_hkcu(client):
    """Проверка получения параметров и подразделов ветки HKCU."""
    response = client.get('/api/registry/key?hive=HKEY_CURRENT_USER&path=Software')
    assert response.status_code == 200
    data = response.json()
    assert data['hive'] == 'HKEY_CURRENT_USER'
    assert 'subkeys' in data

def test_registry_search(client):
    """Проверка поиска по реестру."""
    response = client.get('/api/registry/search?hive=HKEY_LOCAL_MACHINE&path=SOFTWARE&query=Windows&max_results=10')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_apps_status_contains_new_apps(client):
    """Проверка наличия software_audit и registry_viewer в реестре приложений."""
    response = client.get('/api/v1/apps/status')
    assert response.status_code == 200
    data = response.json()
    assert 'apps' in data
    apps = data['apps']
    assert 'software_audit' in apps
    assert 'registry_viewer' in apps
    assert apps['software_audit']['tab'] == 'tab-software-audit'
    assert apps['registry_viewer']['tab'] == 'tab-registry-viewer'