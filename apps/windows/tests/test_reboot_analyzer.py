# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Reboot Analyzer
# =============================================================================
# Description:
#   Тесты для модуля анализа и корреляции причин перезагрузок Windows (Reboot Analyzer).
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_reboot_analyzer import temp_storage
#
#     res = temp_storage()
#
# File: test_reboot_analyzer.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 00:45:00
# =============================================================================

"""Тесты для модуля анализа и корреляции причин перезагрузок Windows (Reboot Analyzer)."""

import os
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from apps.windows.telemetry.models import (
    RebootAnalysisReport,
    RebootCorrelatedEvent,
    RebootSession,
    ShutdownType,
)
from apps.windows.telemetry_research.reboot_analyzer import WindowsRebootAnalyzer
from apps.windows.telemetry.sqlite import TelemetryStorage


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
        import shutil
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass



def test_reboot_models():
    """Тестирование инициализации моделей данных перезагрузки."""
    event = RebootCorrelatedEvent(
        event_id=1074,
        provider='User32',
        timestamp='2026-10-01 01:42:18',
        level='Information',
        description='Плановый перезапуск',
        details={'param1': 'svchost.exe'},
    )
    assert event.event_id == 1074
    assert event.provider == 'User32'

    session = RebootSession(
        boot_id='reboot-20261001-014218',
        boot_time='2026-10-01 01:42:18',
        shutdown_type=ShutdownType.UPDATE_RESTART,
        likely_class='update_related_restart',
        conclusion='Перезапуск после обновления Windows',
        initiating_process='svchost.exe',
        initiating_user='NT AUTHORITY\\SYSTEM',
        windows_update_kb='KB5034441',
        evidence=['Event 1074', 'Event 19'],
    )
    assert session.shutdown_type == ShutdownType.UPDATE_RESTART
    assert session.initiating_process == 'svchost.exe'

    report = RebootAnalysisReport(
        hostname='TEST-PC',
        current_boot_time='2026-10-01 01:42:18',
        total_reboots_analyzed=1,
        planned_count=1,
        stability_score=100.0,
        sessions=[session],
    )
    assert report.total_reboots_analyzed == 1
    assert len(report.sessions) == 1


def test_correlate_planned_update_1074(temp_storage):
    """Тестирование корреляции планового рестарта после обновления Windows Update."""
    analyzer = WindowsRebootAnalyzer(storage=temp_storage)

    mock_events = [
        {
            'event_id': 12,
            'provider': 'Microsoft-Windows-Kernel-General',
            'timestamp': '2026-10-01 02:00:00',
            'level': 'Information',
            'message': 'Запуск ядра ОС',
            'event_data': {},
        },
        {
            'event_id': 1074,
            'provider': 'User32',
            'timestamp': '2026-10-01 01:58:30',
            'level': 'Information',
            'message': 'The process C:\\Windows\\System32\\svchost.exe has initiated the restart of computer PC on behalf of user NT AUTHORITY\\SYSTEM for the following reason: Operating System: Security Update Reason Code: 0x80020010 Shutdown Type: restart',
            'event_data': {
                'param1': 'C:\\Windows\\System32\\svchost.exe',
                'param2': 'NT AUTHORITY\\SYSTEM',
                'param3': 'Operating System: Security Update',
                'param4': '0x80020010',
                'param5': 'restart',
            },
        },
        {
            'event_id': 19,
            'provider': 'Microsoft-Windows-WindowsUpdateClient',
            'timestamp': '2026-10-01 01:57:00',
            'level': 'Information',
            'message': 'Успешно установлено обновление KB5034441',
            'event_data': {},
        },
    ]

    sessions = analyzer._correlate_events_into_sessions(mock_events, limit=5)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.shutdown_type == ShutdownType.UPDATE_RESTART
    assert s.likely_class == 'update_related_restart'
    assert 'svchost.exe' in s.initiating_process
    assert 'KB5034441' in (s.windows_update_kb or '')
    assert 'SYSTEM' in (s.initiating_user or '')
    assert '0x80020010' in (s.reason_code or '')


def test_correlate_unexpected_dirty_power_loss(temp_storage):
    """Тестирование корреляции внезапного отключения питания (Event 41 + 6008 без 1074)."""
    analyzer = WindowsRebootAnalyzer(storage=temp_storage)

    mock_events = [
        {
            'event_id': 41,
            'provider': 'Microsoft-Windows-Kernel-Power',
            'timestamp': '2026-10-01 03:15:00',
            'level': 'Critical',
            'message': 'Система перезагрузилась без чистого выключения',
            'event_data': {
                'BugcheckCode': '0',
                'PowerButtonTimestamp': '0',
            },
        },
        {
            'event_id': 6008,
            'provider': 'EventLog',
            'timestamp': '2026-10-01 03:15:02',
            'level': 'Error',
            'message': 'Предыдущее завершение работы было неожиданным',
            'event_data': {},
        },
    ]

    sessions = analyzer._correlate_events_into_sessions(mock_events, limit=5)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.shutdown_type == ShutdownType.DIRTY_POWER_LOSS
    assert s.likely_class == 'dirty_power_loss'
    assert 'потеря электропитания' in s.conclusion.lower()


def test_correlate_bsod_crash(temp_storage):
    """Тестирование корреляции синего экрана (BSOD / BugCheck)."""
    analyzer = WindowsRebootAnalyzer(storage=temp_storage)

    mock_events = [
        {
            'event_id': 12,
            'provider': 'Microsoft-Windows-Kernel-General',
            'timestamp': '2026-10-01 04:00:00',
            'level': 'Information',
            'message': 'Запуск ОС',
            'event_data': {},
        },
        {
            'event_id': 41,
            'provider': 'Microsoft-Windows-Kernel-Power',
            'timestamp': '2026-10-01 04:00:01',
            'level': 'Critical',
            'message': 'Аварийное выключение ядра',
            'event_data': {
                'BugcheckCode': '209',  # 0x000000D1
                'BugcheckParameter1': '0x0000000000000000',
                'BugcheckParameter2': '0x0000000000000002',
                'BugcheckParameter3': '0x0000000000000000',
                'BugcheckParameter4': '0xFFFFF80000000000',
            },
        },
        {
            'event_id': 1001,
            'provider': 'WER-SystemErrorReporting',
            'timestamp': '2026-10-01 04:00:05',
            'level': 'Information',
            'message': 'Компьютер был перезагружен после ошибки. Код ошибки: 0x000000d1',
            'event_data': {},
        },
    ]

    sessions = analyzer._correlate_events_into_sessions(mock_events, limit=5)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.shutdown_type == ShutdownType.CRASH_BSOD
    assert s.likely_class == 'bsod_crash'
    assert s.bugcheck_code is not None
    assert 'BSOD' in s.conclusion


def test_correlate_hardware_power_button(temp_storage):
    """Тестирование корреляции принудительного выключения кнопкой питания."""
    analyzer = WindowsRebootAnalyzer(storage=temp_storage)

    mock_events = [
        {
            'event_id': 41,
            'provider': 'Microsoft-Windows-Kernel-Power',
            'timestamp': '2026-10-01 05:00:00',
            'level': 'Critical',
            'message': 'Выключение',
            'event_data': {
                'BugcheckCode': '0',
                'PowerButtonTimestamp': '133400000000000000',
            },
        },
    ]

    sessions = analyzer._correlate_events_into_sessions(mock_events, limit=5)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.shutdown_type == ShutdownType.HARDWARE_POWER_BUTTON
    assert s.likely_class == 'hardware_power_button'
    assert 'кнопки питания' in s.conclusion


def test_correlate_user_initiated_explorer(temp_storage):
    """Тестирование корреляции штатного перезапуска пользователем через explorer.exe."""
    analyzer = WindowsRebootAnalyzer(storage=temp_storage)

    mock_events = [
        {
            'event_id': 6005,
            'provider': 'EventLog',
            'timestamp': '2026-10-01 06:00:00',
            'level': 'Information',
            'message': 'Служба журнала запущена',
            'event_data': {},
        },
        {
            'event_id': 1074,
            'provider': 'User32',
            'timestamp': '2026-10-01 05:59:00',
            'level': 'Information',
            'message': 'The process C:\\Windows\\explorer.exe has initiated the restart of computer on behalf of user ADMIN',
            'event_data': {
                'param1': 'C:\\Windows\\explorer.exe',
                'param2': 'DOMAIN\\AdminUser',
                'param5': 'restart',
            },
        },
    ]

    sessions = analyzer._correlate_events_into_sessions(mock_events, limit=5)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.shutdown_type == ShutdownType.USER_INITIATED
    assert 'explorer.exe' in (s.initiating_process or '')


def test_storage_save_and_retrieve_history(temp_storage):
    """Тестирование персистентного сохранения и извлечения сессий перезагрузки в SQLite."""
    session = RebootSession(
        boot_id='reboot-test-101',
        boot_time='2026-10-01 10:00:00',
        previous_boot_time='2026-10-01 02:00:00',
        uptime_seconds=28800.0,
        uptime_human='8ч 0м',
        shutdown_type=ShutdownType.PLANNED,
        likely_class='planned_clean_reboot',
        conclusion='Штатная плановая перезагрузка',
        initiating_process='explorer.exe',
        initiating_user='TestUser',
        evidence=['Event 1074 User32'],
    )

    row_id = temp_storage.save_reboot_session(session)
    assert row_id > 0

    history = temp_storage.get_reboot_history(limit=10)
    assert len(history) >= 1
    latest = history[0]
    assert latest['boot_id'] == 'reboot-test-101'
    assert latest['shutdown_type'] == 'PLANNED'
    assert latest['initiating_process'] == 'explorer.exe'
    assert 'Event 1074' in str(latest.get('evidence', ''))

    single = temp_storage.get_latest_reboot_session()
    assert single is not None
    assert single['boot_id'] == 'reboot-test-101'


def test_fastapi_router_reboots():
    """Тестирование эндпоинтов /api/windows/reboots в FastAPI роутере."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from apps.windows.router import init_router

    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    resp = client.get('/api/windows/reboots')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_reboots_analyzed' in data
    assert 'stability_score' in data
    assert 'sessions' in data

    resp_latest = client.get('/api/windows/reboots/latest')
    assert resp_latest.status_code == 200

    resp_hist = client.get('/api/windows/reboots/history')
    assert resp_hist.status_code == 200
    assert isinstance(resp_hist.json(), list)
