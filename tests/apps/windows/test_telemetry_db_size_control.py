# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Db Size Control
# =============================================================================
# Description:
#   Модульные тесты для системы контроля и ограничения размера базы данных telemetry.db.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_db_size_control import test_storage
#
#     res = test_storage()
#
# File: test_telemetry_db_size_control.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Модульные тесты для системы контроля и ограничения размера базы данных telemetry.db."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import pytest

from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskIoMetrics,
    GpuMetrics,
    MemoryMetrics,
    ProcessMetrics,
    SystemSnapshot,
)
from apps.windows.telemetry.service import TelemetryLoggerService
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager


@pytest.fixture
def test_storage(tmp_path: Path) -> TelemetryStorage:
    """Создает изолированный экземпляр базы данных SQLite для тестирования."""
    db_file = tmp_path / "test_telemetry.db"
    return TelemetryStorage(
        db_path=db_file,
        max_db_size_mb=10.0,
        retention_days=3,
        auto_vacuum=True,
    )


def _create_sample_snapshot(created_at_offset_sec: float = 0.0) -> SystemSnapshot:
    """Вспомогательная функция для создания тестового снимка системы."""
    t_epoch = time.time() - created_at_offset_sec
    t_iso = datetime.fromtimestamp(t_epoch, timezone.utc).isoformat()
    return SystemSnapshot(
        timestamp=t_iso,
        hostname="TEST-PC",
        uptime_seconds=3600.0,
        cpu=CpuMetrics(total_percent=25.5, frequency_mhz=3800.0, per_core_percent=[20.0, 30.0]),
        memory=MemoryMetrics(total_gb=16.0, used_gb=8.0, percent=50.0, swap_percent=10.0),
        gpus=[GpuMetrics(name="NVIDIA RTX", load_percent=45.0, temperature_celsius=62.0)],
        disk_io=DiskIoMetrics(read_bytes_per_sec=1024 * 1024, write_bytes_per_sec=2 * 1024 * 1024),
        top_processes=[
            ProcessMetrics(pid=1001, name="chrome.exe", status="running", cpu_percent=12.5, memory_mb=450.0),
            ProcessMetrics(pid=1002, name="code.exe", status="running", cpu_percent=8.0, memory_mb=300.0),
        ],
    )


def test_config_manager_db_size_options(tmp_path: Path) -> None:
    """Проверка считывания и сохранения параметров размера БД в TelemetryConfigManager."""
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        '{"max_db_size_mb": 25.5, "retention_days": 10, "db_cleanup_interval_seconds": 120.0, "auto_vacuum_enabled": false}',
        encoding="utf-8",
    )
    cfg_mgr = TelemetryConfigManager(config_path=str(cfg_file))
    assert cfg_mgr.get_max_db_size_mb() == 25.5
    assert cfg_mgr.get_retention_days() == 10
    assert cfg_mgr.get_db_cleanup_interval_seconds() == 120.0
    assert cfg_mgr.is_auto_vacuum_enabled() is False

    # Проверка сохранения
    cfg_mgr.save_config({"max_db_size_mb": 40.0, "retention_days": 14})
    assert cfg_mgr.get_max_db_size_mb() == 40.0
    assert cfg_mgr.get_retention_days() == 14


def test_storage_file_sizes_and_wal_checkpoint(test_storage: TelemetryStorage) -> None:
    """Проверка вычисления размеров файлов и работы WAL checkpoint."""
    sizes = test_storage.get_db_file_sizes()
    assert "db_bytes" in sizes
    assert "wal_bytes" in sizes
    assert "shm_bytes" in sizes
    assert "total_bytes" in sizes
    assert sizes["db_bytes"] > 0
    assert sizes["total_bytes"] >= sizes["db_bytes"]

    total_mb = test_storage.get_total_db_size_mb()
    assert total_mb >= 0.0

    # Проверка вызова checkpoint_wal
    assert test_storage.checkpoint_wal() is True


def test_storage_stats_contains_size_fields(test_storage: TelemetryStorage) -> None:
    """Проверка наличия новых полей контроля размера в get_storage_stats()."""
    stats = test_storage.get_storage_stats()
    assert "max_db_size_mb" in stats
    assert "retention_days" in stats
    assert "wal_size_mb" in stats
    assert "total_size_mb" in stats
    assert "size_limit_exceeded" in stats
    assert stats["max_db_size_mb"] == 10.0
    assert stats["retention_days"] == 3
    assert stats["size_limit_exceeded"] is False


def test_vacuum_execution(test_storage: TelemetryStorage) -> None:
    """Проверка успешного выполнения метода vacuum()."""
    # Добавим несколько записей
    for _ in range(5):
        test_storage.save_snapshot(_create_sample_snapshot())
    test_storage.flush()

    assert test_storage.vacuum() is True
    assert test_storage.db_path.exists()


def test_cleanup_old_records_cascade(test_storage: TelemetryStorage) -> None:
    """Проверка каскадного удаления устаревших записей по сроку хранения."""
    # Сохраняем старые снимки (старше 5 дней при retention=3)
    old_snap = _create_sample_snapshot(created_at_offset_sec=5 * 86400)
    test_storage.save_snapshot(old_snap)

    # Сохраняем свежие снимки
    fresh_snap = _create_sample_snapshot(created_at_offset_sec=0)
    test_storage.save_snapshot(fresh_snap)

    test_storage.flush()
    stats_before = test_storage.get_storage_stats()
    assert stats_before["snapshots_count"] == 2

    deleted_count = test_storage.cleanup_old_records(retention_days=3, vacuum_after=True)
    assert deleted_count == 1

    stats_after = test_storage.get_storage_stats()
    assert stats_after["snapshots_count"] == 1


def test_enforce_size_limit_under_limit(test_storage: TelemetryStorage) -> None:
    """Проверка enforce_size_limit когда база данных не превышает лимит."""
    test_storage.save_snapshot(_create_sample_snapshot())
    test_storage.flush()

    res = test_storage.enforce_size_limit(max_size_mb=100.0)
    assert res["pruned"] is False
    assert res["deleted_snapshots"] == 0


def test_enforce_size_limit_pruning_and_compaction(tmp_path: Path) -> None:
    """Проверка усечения и освобождения места при превышении лимита размера БД."""
    db_file = tmp_path / "prune_test.db"
    storage = TelemetryStorage(db_path=db_file, max_db_size_mb=0.001, retention_days=1, auto_vacuum=True)

    # Заполняем базу множеством записей
    for i in range(40):
        snap = _create_sample_snapshot(created_at_offset_sec=float(40 - i) * 60)
        storage.save_snapshot(snap)
    storage.flush()

    stats_before = storage.get_storage_stats()
    assert stats_before["snapshots_count"] == 40

    # Запускаем ограничение с очень малым порогом (0.001 МБ)
    res = storage.enforce_size_limit(max_size_mb=0.001, target_ratio=0.8)
    assert res["pruned"] is True
    assert res["deleted_snapshots"] > 0

    stats_after = storage.get_storage_stats()
    assert stats_after["snapshots_count"] < stats_before["snapshots_count"]
    assert stats_after["snapshots_count"] >= 1


def test_prune_to_size_wrapper(tmp_path: Path) -> None:
    """Проверка удобной обертки prune_to_size."""
    db_file = tmp_path / "prune_to_size_test.db"
    storage = TelemetryStorage(db_path=db_file, max_db_size_mb=50.0)

    for i in range(15):
        storage.save_snapshot(_create_sample_snapshot())
    storage.flush()

    res = storage.prune_to_size(target_size_mb=0.001)
    assert res["pruned"] is True


def test_service_cleanup_db_call(tmp_path: Path) -> None:
    """Проверка работы метода cleanup_db в TelemetryLoggerService."""
    db_file = tmp_path / "svc_clean_test.db"
    storage = TelemetryStorage(db_path=db_file, max_db_size_mb=10.0)
    service = TelemetryLoggerService(storage=storage, interval_sec=1.0, db_cleanup_interval_sec=30.0)

    res = service.cleanup_db()
    assert isinstance(res, dict)
    assert "pruned" in res
