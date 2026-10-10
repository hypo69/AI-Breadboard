# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Watcher Telemetry
# =============================================================================
# Description:
#   Unit-тесты для FileWatcherTelemetryEngine, Multi-DirectoryWatcher и REST API.
#
# Usage Examples:
#   Python API:
#     from tests.test_watcher_telemetry import test_watcher_telemetry_rates_calculation
#
#     res = test_watcher_telemetry_rates_calculation()
#
# File: test_watcher_telemetry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 03:45:00
# =============================================================================

from __future__ import annotations
"""Unit-тесты для FileWatcherTelemetryEngine, Multi-DirectoryWatcher и REST API."""

import csv
import os
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sysadmin.src.watcher_telemetry import FileWatcherTelemetryEngine, WatcherTelemetrySnapshot
from apps.windows.sysadmin.src.directory_watcher import DirectoryWatcher
from apps.windows.sysadmin.router import router as sysadmin_router

def test_watcher_telemetry_rates_calculation() -> None:
    """Проверка расчета скоростей и темпа файловых операций."""
    engine = FileWatcherTelemetryEngine(window_seconds=2.0)
    engine.record_event('Created', watch_dir='C:\\test1')
    engine.record_event('Created', watch_dir='C:\\test2')
    engine.record_event('Modified', watch_dir='C:\\test1')
    engine.record_event('Deleted', watch_dir='D:\\test3')
    rates = engine.compute_rates()
    assert rates['window_events_count'] == 4
    assert rates['created_rate'] == 2.0 / 2.0
    assert rates['modified_rate'] == 1.0 / 2.0
    assert rates['deleted_rate'] == 1.0 / 2.0
    assert rates['total_rate'] == 4.0 / 2.0

def test_watcher_telemetry_burst_detection() -> None:
    """Проверка детекции аномального всплеска массового удаления файлов."""
    engine = FileWatcherTelemetryEngine(window_seconds=1.0)
    for _ in range(25):
        engine.record_event('Deleted')
    snap = engine.get_telemetry_snapshot(watch_dirs=['C:\\test1', 'D:\\test2'], total_history_events=25)
    assert snap.burst_deletions_alert is True
    assert 'всплеск удалений' in snap.status_label.lower()
    assert len(snap.watch_dirs) == 2

def test_watcher_telemetry_drive_metrics() -> None:
    """Проверка определения дисков, чтения счетчиков и привязки температуры накопителей."""
    from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import StorageDiskHealthInfo
    engine = FileWatcherTelemetryEngine(window_seconds=5.0)
    mock_disk = StorageDiskHealthInfo(
        device_id='\\\\.\\PhysicalDrive0',
        friendly_name='CT1000MX500SSD1',
        model='Crucial CT1000MX500SSD1',
        serial_number='12345678',
        bus_type='SATA',
        media_type='SSD',
        size_gb=1000.0,
        health_status='Healthy',
        operational_status='OK',
        temperature_c=34.0,
    )
    with patch('apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor.WindowsStorageSensor.get_physical_disks', return_value=[mock_disk]):
        hw = engine.get_drive_hardware_metrics(watch_dirs=['C:\\Projects\\AI-Breadboard', 'D:\\Data'])
        assert 'C:' in hw['drive_letters']
        assert 'D:' in hw['drive_letters']
        assert hw['drive_model'] == 'CT1000MX500SSD1'
        assert hw['temperature_c'] == 34.0

def test_watcher_telemetry_csv_logging(tmp_path: Path) -> None:
    """Проверка записи снапшотов телеметрии в CSV-файл."""
    engine = FileWatcherTelemetryEngine(window_seconds=5.0)
    with patch('apps.windows.sysadmin.src.watcher_telemetry.write_csv_row') as mock_write_csv:
        snap = engine.get_telemetry_snapshot(watch_dirs=['C:\\Projects', 'D:\\Logs'], total_history_events=10)
        assert len(snap.watch_dirs) == 2
        mock_write_csv.assert_called()

def test_directory_watcher_multi_dir_management(tmp_path: Path) -> None:
    """Проверка управления несколькими директориями в DirectoryWatcher."""
    dir1 = tmp_path / 'dir1'
    dir2 = tmp_path / 'dir2'
    dir3 = tmp_path / 'dir3'
    dir1.mkdir()
    dir2.mkdir()
    dir3.mkdir()
    watcher = DirectoryWatcher(watch_dirs=[str(dir1), str(dir2)], max_history=50)
    assert len(watcher.get_watch_dirs()) == 2
    assert str(dir1.resolve()) in watcher.get_watch_dirs()
    assert str(dir2.resolve()) in watcher.get_watch_dirs()
    added = watcher.add_watch_dir(str(dir3))
    assert added is True
    assert len(watcher.get_watch_dirs()) == 3
    removed = watcher.remove_watch_dir(str(dir2))
    assert removed is True
    assert len(watcher.get_watch_dirs()) == 2
    assert str(dir2.resolve()) not in watcher.get_watch_dirs()
    set_res = watcher.set_watch_dirs([str(dir1)])
    assert set_res is True
    assert len(watcher.get_watch_dirs()) == 1

def test_sysadmin_telemetry_and_filesystem_endpoints(tmp_path: Path) -> None:
    """Проверка REST API эндпоинтов телеметрии, обзора дисков и структуры каталогов."""
    app = FastAPI()
    app.include_router(sysadmin_router)
    client = TestClient(app)
    with patch('apps.windows.sysadmin.router._save_configured_watch_dirs'):
        res_telem = client.get('/api/v1/system/file-audit/telemetry')
        assert res_telem.status_code == 200
        data_telem = res_telem.json()
        assert 'events_rate_per_sec' in data_telem
        assert 'drive_letters' in data_telem
        res_drives = client.get('/api/sysadmin/filesystem/drives')
        assert res_drives.status_code == 200
        drives_data = res_drives.json()
        assert 'drives' in drives_data
        assert len(drives_data['drives']) > 0
        test_sub = tmp_path / 'subfolder1'
        test_sub.mkdir()
        res_browse = client.get(f'/api/sysadmin/filesystem/browse?path={tmp_path}')
        assert res_browse.status_code == 200
        browse_data = res_browse.json()
        assert 'directories' in browse_data
        assert any((d['name'] == 'subfolder1' for d in browse_data['directories']))
        res_get_dirs = client.get('/api/v1/system/file-audit/watch-dirs')
        assert res_get_dirs.status_code == 200
        assert 'watch_dirs' in res_get_dirs.json()
        res_set_dirs = client.post('/api/v1/system/file-audit/watch-dirs', json={'paths': [str(test_sub)]})
        assert res_set_dirs.status_code == 200
        assert str(test_sub.resolve()) in res_set_dirs.json()['watch_dirs']

def test_watcher_exclusions_logic() -> None:
    """Проверка логики правил исключений (WatcherExclusions)."""
    from apps.windows.sysadmin.src.directory_watcher import WatcherExclusions
    ex = WatcherExclusions(enabled=True, paths=['AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs', 'AppData\\Local\\Temp', 'node_modules'], extensions=['.tmp', '.log', '.csv', '.db-wal'], patterns=['*system_inspector_polls.csv*', '*Windows.db*', '~$*'], processes=['SearchIndexer.exe'])
    assert ex.is_excluded('C:\\Users\\User\\AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs\\data.csv') is True
    assert ex.is_excluded('C:\\Users\\User\\AppData\\Local\\Temp\\random.txt') is True
    assert ex.is_excluded('C:\\Projects\\my_code.py') is False
    temp_watch = 'C:\\Users\\User\\AppData\\Local\\Temp\\pytest-189\\test\\subfolder1'
    assert ex.is_excluded('C:\\Users\\User\\AppData\\Local\\Temp\\pytest-189\\test\\subfolder1\\file.txt', watch_dir=temp_watch) is False
    assert ex.is_excluded('C:\\Users\\User\\AppData\\Local\\Temp\\pytest-189\\test\\subfolder1\\node_modules\\package.json', watch_dir=temp_watch) is True
    user_watch = 'C:\\Users\\User'
    assert ex.is_excluded('C:\\Users\\User\\AppData\\Local\\Temp\\random.txt', watch_dir=user_watch) is True
    assert ex.is_excluded('C:\\Users\\User\\Documents\\notes.txt', watch_dir=user_watch) is False
    assert ex.is_excluded('C:\\Projects\\test.tmp') is True
    assert ex.is_excluded('C:\\Projects\\app.log') is True
    assert ex.is_excluded('C:\\Projects\\records.csv') is True
    assert ex.is_excluded('C:\\Projects\\app.py') is False
    assert ex.is_excluded('C:\\ProgramData\\Microsoft\\Search\\Data\\Windows.db-wal') is True
    assert ex.is_excluded('C:\\Docs\\~$MyDoc.docx') is True
    assert ex.is_excluded('C:\\ProgramData\\something.txt', proc_name='SearchIndexer.exe') is True
    assert ex.is_excluded('C:\\ProgramData\\something.txt', proc_name='searchindexer.exe') is True
    assert ex.is_excluded('C:\\Projects\\main.py', proc_name='python.exe') is False
    ex.enabled = False
    assert ex.is_excluded('C:\\Projects\\test.tmp') is False
    assert ex.is_excluded('C:\\ProgramData\\something.txt', proc_name='SearchIndexer.exe') is False

def test_sysadmin_exclusions_api_endpoints() -> None:
    """Проверка REST API эндпоинтов управления исключениями."""
    app = FastAPI()
    app.include_router(sysadmin_router)
    client = TestClient(app)
    with patch('apps.windows.sysadmin.router._save_configured_exclusions'):
        res_get = client.get('/api/v1/system/file-audit/exclusions')
        assert res_get.status_code == 200
        ex_data = res_get.json()
        assert 'enabled' in ex_data
        assert 'paths' in ex_data
        assert 'extensions' in ex_data
        assert 'patterns' in ex_data
        assert 'processes' in ex_data
        assert 'filtered_count' in ex_data
        res_add = client.post('/api/v1/system/file-audit/exclusions/add', json={'category': 'extensions', 'value': '.pytest_temp'})
        assert res_add.status_code == 200
        assert res_add.json()['success'] is True
        assert '.pytest_temp' in res_add.json()['exclusions']['extensions']
        res_del = client.post('/api/v1/system/file-audit/exclusions/remove', json={'category': 'extensions', 'value': '.pytest_temp'})
        assert res_del.status_code == 200
        assert res_del.json()['success'] is True
        assert '.pytest_temp' not in res_del.json()['exclusions']['extensions']
        res_toggle = client.post('/api/v1/system/file-audit/exclusions/toggle', json={'enabled': False})
        assert res_toggle.status_code == 200
        assert res_toggle.json()['enabled'] is False
        res_toggle_on = client.post('/api/v1/system/file-audit/exclusions/toggle', json={'enabled': True})
        assert res_toggle_on.status_code == 200
        assert res_toggle_on.json()['enabled'] is True
        res_events = client.get('/api/v1/system/file-audit/live-events')
        assert res_events.status_code == 200
        ev_data = res_events.json()
        assert 'filtered_count' in ev_data
        assert 'exclusions_enabled' in ev_data