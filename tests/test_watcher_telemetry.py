# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Real-Time File Watcher Telemetry Engine
# =============================================================================
# Description:
#   Тесты для модуля FileWatcherTelemetryEngine и Multi-Directory Watcher:
#   - Расчет темпа файловых операций (events/sec, created/sec, deleted/sec)
#   - Детекция аномалий всплесков удалений
#   - Сбор аппаратных сенсоров нескольких дисков и LHM
#   - CSV-логгирование телеметрии
#   - Управление списком отслеживаемых папок (add, remove, set)
#   - REST API эндпоинты телеметрии, проводника файловой системы и управления вотчером
#
# File: test_watcher_telemetry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit-тесты для FileWatcherTelemetryEngine, Multi-DirectoryWatcher и REST API."""

from __future__ import annotations

import csv
import os
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sysadmin.src.watcher_telemetry import (
    FileWatcherTelemetryEngine,
    WatcherTelemetrySnapshot,
)
from apps.windows.sysadmin.src.directory_watcher import DirectoryWatcher
from apps.windows.sysadmin.router import router as sysadmin_router


def test_watcher_telemetry_rates_calculation() -> None:
    """Проверка расчета скоростей и темпа файловых операций."""
    engine = FileWatcherTelemetryEngine(window_seconds=2.0)

    # Записываем серии событий
    engine.record_event("Created", watch_dir="C:\\test1")
    engine.record_event("Created", watch_dir="C:\\test2")
    engine.record_event("Modified", watch_dir="C:\\test1")
    engine.record_event("Deleted", watch_dir="D:\\test3")

    rates = engine.compute_rates()
    assert rates["window_events_count"] == 4
    assert rates["created_rate"] == 2.0 / 2.0
    assert rates["modified_rate"] == 1.0 / 2.0
    assert rates["deleted_rate"] == 1.0 / 2.0
    assert rates["total_rate"] == 4.0 / 2.0


def test_watcher_telemetry_burst_detection() -> None:
    """Проверка детекции аномального всплеска массового удаления файлов."""
    engine = FileWatcherTelemetryEngine(window_seconds=1.0)

    # Имитируем всплеск 25 удалений в секунду
    for _ in range(25):
        engine.record_event("Deleted")

    snap = engine.get_telemetry_snapshot(watch_dirs=["C:\\test1", "D:\\test2"], total_history_events=25)
    assert snap.burst_deletions_alert is True
    assert "всплеск удалений" in snap.status_label.lower()
    assert len(snap.watch_dirs) == 2


def test_watcher_telemetry_drive_metrics() -> None:
    """Проверка определения дисков, чтения счетчиков и привязки температуры LHM."""
    engine = FileWatcherTelemetryEngine(window_seconds=5.0)

    mock_sensors = [
        {
            "hardware_name": "CT1000MX500SSD1",
            "hardware_type": "storage",
            "sensor_category": "Temperatures",
            "sensor_name": "Temperature",
            "value_numeric": 34.0,
        }
    ]

    with patch.object(engine._lhm_service, "get_flattened_sensors", return_value=mock_sensors):
        hw = engine.get_drive_hardware_metrics(watch_dirs=["C:\\Projects\\AI-Breadboard", "D:\\Data"])
        assert "C:" in hw["drive_letters"]
        assert "D:" in hw["drive_letters"]
        assert hw["drive_model"] == "CT1000MX500SSD1"
        assert hw["temperature_c"] == 34.0


def test_watcher_telemetry_csv_logging(tmp_path: Path) -> None:
    """Проверка записи снапшотов телеметрии в CSV-файл."""
    engine = FileWatcherTelemetryEngine(window_seconds=5.0)

    with patch("apps.windows.sysadmin.src.watcher_telemetry.write_csv_row") as mock_write_csv:
        snap = engine.get_telemetry_snapshot(watch_dirs=["C:\\Projects", "D:\\Logs"], total_history_events=10)
        assert len(snap.watch_dirs) == 2
        mock_write_csv.assert_called()


def test_directory_watcher_multi_dir_management(tmp_path: Path) -> None:
    """Проверка управления несколькими директориями в DirectoryWatcher."""
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir3 = tmp_path / "dir3"
    dir1.mkdir()
    dir2.mkdir()
    dir3.mkdir()

    watcher = DirectoryWatcher(watch_dirs=[str(dir1), str(dir2)], max_history=50)
    assert len(watcher.get_watch_dirs()) == 2
    assert str(dir1.resolve()) in watcher.get_watch_dirs()
    assert str(dir2.resolve()) in watcher.get_watch_dirs()

    # Добавление новой папки
    added = watcher.add_watch_dir(str(dir3))
    assert added is True
    assert len(watcher.get_watch_dirs()) == 3

    # Удаление папки
    removed = watcher.remove_watch_dir(str(dir2))
    assert removed is True
    assert len(watcher.get_watch_dirs()) == 2
    assert str(dir2.resolve()) not in watcher.get_watch_dirs()

    # Установка нового набора папок
    set_res = watcher.set_watch_dirs([str(dir1)])
    assert set_res is True
    assert len(watcher.get_watch_dirs()) == 1


def test_sysadmin_telemetry_and_filesystem_endpoints(tmp_path: Path) -> None:
    """Проверка REST API эндпоинтов телеметрии, обзора дисков и структуры каталогов."""
    app = FastAPI()
    app.include_router(sysadmin_router)
    client = TestClient(app)

    # 1. Telemetry
    res_telem = client.get("/api/sysadmin/file-audit/telemetry")
    assert res_telem.status_code == 200
    data_telem = res_telem.json()
    assert "events_rate_per_sec" in data_telem
    assert "drive_letters" in data_telem

    # 2. System Drives
    res_drives = client.get("/api/sysadmin/filesystem/drives")
    assert res_drives.status_code == 200
    drives_data = res_drives.json()
    assert "drives" in drives_data
    assert len(drives_data["drives"]) > 0

    # 3. Browse Directory
    test_sub = tmp_path / "subfolder1"
    test_sub.mkdir()
    res_browse = client.get(f"/api/sysadmin/filesystem/browse?path={tmp_path}")
    assert res_browse.status_code == 200
    browse_data = res_browse.json()
    assert "directories" in browse_data
    assert any(d["name"] == "subfolder1" for d in browse_data["directories"])

    # 4. Watch Dirs API
    res_get_dirs = client.get("/api/sysadmin/file-audit/watch-dirs")
    assert res_get_dirs.status_code == 200
    assert "watch_dirs" in res_get_dirs.json()

    # 5. Set Watch Dirs POST
    res_set_dirs = client.post("/api/sysadmin/file-audit/watch-dirs", json={"paths": [str(test_sub)]})
    assert res_set_dirs.status_code == 200
    assert str(test_sub.resolve()) in res_set_dirs.json()["watch_dirs"]
