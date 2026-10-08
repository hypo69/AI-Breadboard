# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Router Log Settings
# =============================================================================
# Description:
#   Тестирование REST роутера настройки и параметров журналов событий Windows
#   (/api/v1/log-settings/*), аудита создания процессов и управления закладками.
#
# Usage Examples:
#   Python API:
#     pytest apps/windows/tests/test_router_log_settings.py -v
#
# File: test_router_log_settings.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:30:00
# =============================================================================

from __future__ import annotations
"""Тестирование REST роутера настройки и параметров журналов событий Windows."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_log_settings import init_router


@pytest.fixture
def client() -> TestClient:
    """Фикстура тестового клиента FastAPI."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_get_channels_list(client: TestClient):
    """Проверка получения списка каналов и их параметров."""
    resp = client.get('/api/v1/log-settings/channels')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channels' in data
    assert 'total' in data
    assert len(data['channels']) > 0

    first = data['channels'][0]
    assert 'channel_name' in first
    assert 'max_size_mb' in first
    assert 'file_size_mb' in first
    assert 'usage_pct' in first
    assert 'record_count' in first
    assert 'is_enabled' in first


def test_get_channel_detail(client: TestClient):
    """Проверка получения детальных параметров конкретного канала."""
    resp = client.get('/api/v1/log-settings/channel/System')
    assert resp.status_code == 200
    data = resp.json()
    assert data['channel_name'] == 'System'
    assert 'max_size_mb' in data
    assert 'record_count' in data
    assert 'is_accessible' in data


def test_set_channel_config_success(client: TestClient):
    """Проверка применения параметров конфигурации канала."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "name: System\nenabled: true\nmaxSize: 104857600\n"

    with patch('subprocess.run', return_value=mock_run):
        payload = {
            'channel_name': 'System',
            'max_size_mb': 100,
            'is_enabled': True,
            'auto_backup': False,
            'retention': False,
        }
        resp = client.post('/api/v1/log-settings/channel/config', json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['channel_name'] == 'System'
        assert data['applied']['max_size_mb'] == 100


def test_clear_channel_log_success(client: TestClient):
    """Проверка очистки журнала с опцией бэкапа."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ""

    with patch('subprocess.run', return_value=mock_run):
        payload = {
            'channel_name': 'Application',
            'backup_path': r'C:\Windows\Temp\test_backup.evtx',
        }
        resp = client.post('/api/v1/log-settings/channel/clear', json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['backup_saved'] is True


def test_get_audit_status(client: TestClient):
    """Проверка получения статуса аудита и закладки."""
    resp = client.get('/api/v1/log-settings/audit-status')
    assert resp.status_code == 200
    data = resp.json()
    assert 'cmdline_audit_enabled' in data
    assert 'security_channel_accessible' in data
    assert 'db_security_events_count' in data


def test_set_cmdline_audit_mock(client: TestClient):
    """Проверка переключения аудита командной строки в реестре."""
    with patch('winreg.CreateKeyEx', return_value=MagicMock()):
        with patch('winreg.SetValueEx', return_value=None):
            resp = client.post('/api/v1/log-settings/audit-status/cmdline', json={'enabled': True})
            assert resp.status_code == 200
            data = resp.json()
            assert data['success'] is True
            assert data['cmdline_audit_enabled'] is True


def test_reset_collector_bookmark(client: TestClient):
    """Проверка сброса закладки сборщика телеметрии."""
    payload = {'channel': 'Security', 'record_id': 2812345}
    resp = client.post('/api/v1/log-settings/collector/reset-bookmark', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data['success'] is True
    assert data['reset_record_id'] == 2812345


def test_run_collector_collection(client: TestClient):
    """Проверка ручного запуска инкрементального сбора телеметрии."""
    resp = client.post('/api/v1/log-settings/collector/collect?limit=50')
    assert resp.status_code == 200
    data = resp.json()
    assert data['success'] is True
    assert 'total_events_ingested' in data
    assert 'last_record_id' in data


def test_get_channel_events(client: TestClient):
    """Проверка чтения событий через роутер с фильтрами."""
    resp = client.get('/api/v1/log-settings/events?channel=System&limit=10')
    assert resp.status_code == 200
    data = resp.json()
    assert 'channel' in data
    assert 'events' in data
    assert 'total' in data

    # Проверка чтения из telemetry_db
    resp_db = client.get('/api/v1/log-settings/events?channel=telemetry_db&limit=5')
    assert resp_db.status_code == 200
    data_db = resp_db.json()
    assert data_db['source'] == 'telemetry.db'
    assert 'events' in data_db
