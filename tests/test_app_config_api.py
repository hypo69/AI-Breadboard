# -*- coding: utf-8 -*-
# ==========================================================================
# Process Name: Application Configuration Management API Tests
# ==========================================================================
# Description:
#   Unit tests verifying GET and POST /api/admin/apps/{app_name}/config endpoints,
#   including authentication validation, path resolution, and json persistence.
#
# File: test_app_config_api.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# ==========================================================================

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.router_admin import init_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_get_app_config_unauthorized(client):
    res = client.get('/api/admin/apps/trading_terminal/config', headers={'Host': 'external.example.com'})
    assert res.status_code == 401


def test_get_app_config_success(client):
    client.cookies.set('admin_password_verified', 'true')
    res = client.get('/api/admin/apps/trading_terminal/config')
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'ok'
    assert data['app'] == 'trading_terminal'
    assert 'config' in data
    assert 'server' in data['config']
    assert data['config']['server']['port'] == 8103


def test_get_app_config_not_found(client):
    client.cookies.set('admin_password_verified', 'true')
    res = client.get('/api/admin/apps/non_existent_app_xyz/config')
    assert res.status_code == 404


def test_update_app_config_success(client):
    client.cookies.set('admin_password_verified', 'true')

    res = client.get('/api/admin/apps/trading_terminal/config')
    assert res.status_code == 200
    original_config = res.json()['config']

    try:
        modified_config = json.loads(json.dumps(original_config))
        modified_config['server']['port'] = 8103
        modified_config['server']['mode'] = 'dedicated'

        post_res = client.post(
            '/api/admin/apps/trading_terminal/config',
            json={'config': modified_config},
        )
        assert post_res.status_code == 200
        post_data = post_res.json()
        assert post_data['status'] == 'ok'
        assert post_data['config']['server']['mode'] == 'dedicated'

        verify_res = client.get('/api/admin/apps/trading_terminal/config')
        assert verify_res.status_code == 200
        assert verify_res.json()['config']['server']['mode'] == 'dedicated'
    finally:
        client.post(
            '/api/admin/apps/trading_terminal/config',
            json={'config': original_config},
        )
