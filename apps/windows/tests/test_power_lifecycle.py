# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Power Lifecycle
# =============================================================================
# Description:
#   Комплексный набор модульных тестов для подсистемы анализа жизненного цикла
#   питания Windows, разбора событий 1074/41/6008/12/13/1001, реконструкции
#   сессий питания (Power Sessions) и сохранения в базу данных telemetry.db.
#
# Usage Examples:
#   CLI:
#     pytest apps/windows/tests/test_power_lifecycle.py -v
#
# File: test_power_lifecycle.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:51:00
# =============================================================================

import os
import shutil
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from apps.windows.telemetry.models import (
    PowerEventRecord,
    PowerSessionRecord,
    PowerLifecycleSummary,
)
from apps.windows.telemetry.power_lifecycle import (
    PowerLifecycleEngine,
    format_uptime_human,
)
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.api.routers.router_power_lifecycle import init_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def temp_storage():
    """Фикстура изолированного хранилища SQLite во временном каталоге."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / 'test_telemetry.db'
    storage = TelemetryStorage(db_path=db_path, buffer_mode='direct', auto_flush=False)
    try:
        yield storage
    finally:
        storage.close()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_uptime_formatting():
    """Проверка форматирования аптайма в человекочитаемый вид."""
    assert format_uptime_human(45) == '45с'
    assert format_uptime_human(125) == '2м 5с'
    assert format_uptime_human(3665) == '1ч 1м 5с'
    assert format_uptime_human(90061) == '1д 1ч 1м 1с'
    assert format_uptime_human(52531) == '14ч 35м 31с'


def test_power_models():
    """Проверка валидации и сериализации Pydantic-моделей жизненного цикла питания."""
    ev = PowerEventRecord(
        event_id=1074,
        provider='User32',
        timestamp='2026-10-07 23:48:02',
        event_type='shutdown_planned',
        shutdown_type='Restart',
        user='DOMAIN\\David',
        process='shutdown.exe',
        reason='Operating System: Service pack (Planned)',
        reason_code='0x80020010',
        comment='Регламентное обновление',
    )
    assert ev.event_id == 1074
    assert ev.user == 'DOMAIN\\David'
    assert ev.reason_code == '0x80020010'

    session = PowerSessionRecord(
        session_id='PS-184',
        boot_time='2026-10-07 09:12:31',
        boot_timestamp=1791364351.0,
        shutdown_time='2026-10-07 23:48:02',
        shutdown_timestamp=1791416882.0,
        uptime_seconds=52531.0,
        uptime_human='14ч 35м 31с',
        shutdown_type='Restart',
        initiator='DOMAIN\\David',
        process='shutdown.exe',
        reason='Operating System: Service pack (Planned)',
        reason_code='0x80020010',
        clean_shutdown=True,
        unexpected_shutdown=False,
    )
    assert session.session_id == 'PS-184'
    assert session.clean_shutdown is True
    assert session.uptime_human == '14ч 35м 31с'


def test_parse_event_1074_user32():
    """Проверка корректного разбора события 1074 (процесс, пользователь, причина, код, цепочка)."""
    engine = PowerLifecycleEngine()

    raw_event = {
        'event_id': 1074,
        'provider': 'User32',
        'message': 'The process C:\\Windows\\System32\\shutdown.exe has initiated the restart of computer PC on behalf of user DOMAIN\\User for the following reason: Operating System: Service pack (Planned) Reason Code: 0x80020010 Shutdown Type: restart Comment: Test reboot',
        'event_data': {
            'param1': 'C:\\Windows\\System32\\shutdown.exe',
            'param2': 'PC',
            'param3': 'Operating System: Service pack (Planned)',
            'param4': '0x80020010',
            'param5': 'restart',
            'param6': 'Test reboot',
            'param7': 'DOMAIN\\User',
        },
    }

    parsed = engine.parse_event_1074(raw_event)
    assert parsed['process'] == 'C:\\Windows\\System32\\shutdown.exe'
    assert parsed['shutdown_type'] == 'Restart'
    assert parsed['reason_code'] == '0x80020010'
    assert parsed['user'] == 'DOMAIN\\User'
    assert parsed['domain'] == 'DOMAIN'
    assert parsed['user_name'] == 'User'
    assert len(parsed['initiator_chain']) > 0


def test_parse_event_1074_wmi_correlation():
    """Проверка распознавания цепочки WMI при вызове wmiprvse.exe."""
    engine = PowerLifecycleEngine()

    raw_event = {
        'event_id': 1074,
        'provider': 'User32',
        'message': 'The process C:\\Windows\\System32\\Wbem\\wmiprvse.exe has initiated the shutdown of computer SERVER on behalf of user NT AUTHORITY\\SYSTEM for the following reason: Other (Unplanned) Reason Code: 0x0 Shutdown Type: power off Comment:',
        'event_data': {
            'param1': 'C:\\Windows\\System32\\Wbem\\wmiprvse.exe',
            'param2': 'SERVER',
            'param3': 'Other (Unplanned)',
            'param4': '0x0',
            'param5': 'power off',
            'param6': '',
            'param7': 'NT AUTHORITY\\SYSTEM',
        },
    }

    parsed = engine.parse_event_1074(raw_event)
    assert parsed['shutdown_type'] == 'PowerOff'
    assert any('WMI' in step for step in parsed['initiator_chain'])


def test_session_reconstruction():
    """Проверка реконструкции сессий питания: Boot -> Normal -> Crash/Unexpected."""
    engine = PowerLifecycleEngine()

    mock_events = [
        # Сессия 1: Штатная
        {
            'event_id': 12,
            'provider': 'Microsoft-Windows-Kernel-General',
            'timestamp': '2026-10-06 08:00:00',
            'created_at': 1791273600.0,
            'event_type': 'boot',
            'reason': 'Запуск ОС',
        },
        {
            'event_id': 1074,
            'provider': 'User32',
            'timestamp': '2026-10-06 20:00:00',
            'created_at': 1791316800.0,
            'event_type': 'shutdown_planned',
            'shutdown_type': 'Shutdown',
            'user': 'DOMAIN\\Admin',
            'process': 'explorer.exe',
            'reason': 'Выключение пользователем',
            'reason_code': '0x80000000',
        },
        {
            'event_id': 6006,
            'provider': 'EventLog',
            'timestamp': '2026-10-06 20:00:05',
            'created_at': 1791316805.0,
            'event_type': 'shutdown_clean',
            'shutdown_type': 'Shutdown',
        },
        # Сессия 2: Внезапная (Power Loss / 41)
        {
            'event_id': 12,
            'provider': 'Microsoft-Windows-Kernel-General',
            'timestamp': '2026-10-07 09:00:00',
            'created_at': 1791363600.0,
            'event_type': 'boot',
            'reason': 'Запуск ОС',
        },
        {
            'event_id': 41,
            'provider': 'Microsoft-Windows-Kernel-Power',
            'timestamp': '2026-10-07 14:30:00',
            'created_at': 1791383400.0,
            'event_type': 'shutdown_unexpected',
            'unexpected': True,
            'shutdown_type': 'Unexpected',
            'reason': 'Внезапное выключение питания',
        },
        # Сессия 3: Активная
        {
            'event_id': 12,
            'provider': 'Microsoft-Windows-Kernel-General',
            'timestamp': '2026-10-07 14:35:00',
            'created_at': 1791383700.0,
            'event_type': 'boot',
            'reason': 'Запуск ОС после сбоя',
        },
    ]

    sessions = engine.reconstruct_power_sessions(mock_events)
    assert len(sessions) == 3

    # Сессия 3 (самая свежая) - Active
    active_sess = sessions[0]
    assert active_sess.shutdown_type == 'Active'
    assert active_sess.boot_time == '2026-10-07 14:35:00'

    # Сессия 2 - Unexpected
    unexp_sess = sessions[1]
    assert unexp_sess.unexpected_shutdown is True
    assert unexp_sess.shutdown_type == 'Unexpected'
    assert unexp_sess.shutdown_event_id == 41

    # Сессия 1 - Clean Shutdown
    clean_sess = sessions[2]
    assert clean_sess.clean_shutdown is True
    assert clean_sess.shutdown_type == 'Shutdown'
    assert clean_sess.initiator == 'DOMAIN\\Admin'
    assert clean_sess.process == 'explorer.exe'


def test_storage_power_crud(temp_storage):
    """Проверка записи и чтения power_events и power_sessions в SQLite."""
    mock_events = [
        PowerEventRecord(
            event_id=1074,
            provider='User32',
            timestamp='2026-10-07 23:48:02',
            event_type='shutdown_planned',
            shutdown_type='Restart',
            user='David',
            process='shutdown.exe',
            reason='Planned restart',
            reason_code='0x80020010',
        ),
        PowerEventRecord(
            event_id=41,
            provider='Microsoft-Windows-Kernel-Power',
            timestamp='2026-10-08 00:02:14',
            event_type='shutdown_unexpected',
            unexpected=True,
            reason='Power loss',
        ),
    ]

    mock_sessions = [
        PowerSessionRecord(
            session_id='PS-184',
            boot_time='2026-10-07 09:12:31',
            shutdown_time='2026-10-07 23:48:02',
            uptime_seconds=52531.0,
            uptime_human='14ч 35м 31с',
            shutdown_type='Restart',
            initiator='David',
            process='shutdown.exe',
            reason='Planned restart',
            reason_code='0x80020010',
            clean_shutdown=True,
            unexpected_shutdown=False,
        ),
        PowerSessionRecord(
            session_id='PS-185',
            boot_time='2026-10-08 00:02:14',
            uptime_seconds=3600.0,
            uptime_human='1ч 0м 0с',
            shutdown_type='Unexpected',
            clean_shutdown=False,
            unexpected_shutdown=True,
            reason='Power loss / Kernel-Power 41',
        ),
    ]

    saved_ev = temp_storage.save_power_events(mock_events)
    assert saved_ev == 2

    saved_sess = temp_storage.save_power_sessions(mock_sessions)
    assert saved_sess == 2

    # Выборка сессий
    db_sessions = temp_storage.get_power_sessions(limit=10)
    assert len(db_sessions) == 2

    # Фильтр по неожиданным
    unexp = temp_storage.get_power_sessions(unexpected_only=True)
    assert len(unexp) == 1
    assert unexp[0]['session_id'] == 'PS-185'

    # Выборка событий
    db_events = temp_storage.get_power_events(limit=10)
    assert len(db_events) == 2

    # Сводка
    summary = temp_storage.get_power_summary()
    assert summary['total_sessions_count'] == 2
    assert summary['clean_shutdowns_count'] == 1
    assert summary['unexpected_shutdowns_count'] == 1


def test_fastapi_power_router(temp_storage, monkeypatch):
    """Проверка работы REST эндпоинтов router_power_lifecycle."""
    # Подменяем дефолтное хранилище на временное
    monkeypatch.setattr('apps.windows.telemetry.power_lifecycle.TelemetryStorage.get_instance', lambda *a, **kw: temp_storage)

    app = FastAPI()
    router = init_router()
    app.include_router(router)
    client = TestClient(app)

    # Проверка /summary
    res_sum = client.get('/api/v1/power/summary')
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    assert 'total_sessions_count' in data_sum

    # Проверка /sessions
    res_sess = client.get('/api/v1/power/sessions')
    assert res_sess.status_code == 200
    assert isinstance(res_sess.json(), list)

    # Проверка /events
    res_ev = client.get('/api/v1/power/events')
    assert res_ev.status_code == 200
    assert isinstance(res_ev.json(), list)
