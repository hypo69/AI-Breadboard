# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Apps Telemetry & Logging Module
# =============================================================================
# Description:
#   Набор тестов для модуля apps/common/csv_logger.py: проверка SQLite как
#   Single Source of Truth, работы On-Demand экспорта в CSV, проверки отсутствия
#   дискового оверхеда при enable_csv_mirroring=False, опциональной пакетной
#   буферизации в памяти и обратной совместимости при зеркалировании.
#
# File: test_apps_csv_logger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты модуля телеметрии и логирования приложений с On-Demand CSV."""

import csv
import threading
from pathlib import Path
import pytest

from apps.common.csv_logger import (
    AppCsvLogger,
    export_app_events_to_csv,
    export_app_param_changes_to_csv,
    export_app_polls_to_csv,
    export_to_csv,
    flush_batch_buffer,
    get_apps_log_dir,
    is_csv_mirroring_enabled,
    is_memory_batching_enabled,
    is_mirroring_logs_to_csv_enabled,
    log_custom_csv,
    log_event,
    log_param_change,
    log_poll,
    set_apps_log_dir_override,
    set_csv_mirroring,
    set_memory_batching,
    set_mirroring_logs_to_csv,
    write_csv_row,
)
from apps.windows.telemetry.storage import TelemetryStorage


@pytest.fixture(autouse=True)
def setup_tmp_log_dir(tmp_path: Path):
    """Изолирует каталог логов и БД во временную папку на время каждого теста."""
    temp_logs = tmp_path / "apps_logs"
    set_apps_log_dir_override(temp_logs)
    set_mirroring_logs_to_csv(False)
    set_memory_batching(False)

    # Инициализируем изолированное SQLite хранилище
    db_file = temp_logs / "telemetry.db"
    TelemetryStorage._instance = TelemetryStorage(db_path=db_file)

    yield

    set_apps_log_dir_override(None)
    set_csv_mirroring(False)
    set_memory_batching(False)
    TelemetryStorage._instance = None


def test_get_apps_log_dir():
    """Проверяет получение и автоматическое создание директории логов."""
    log_dir = get_apps_log_dir()
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_sqlite_primary_no_csv_pollution_by_default():
    """Проверяет, что по умолчанию логи пишутся в SQLite и не создают CSV-файлы."""
    assert not is_csv_mirroring_enabled()

    log_poll(
        app="cloudflared_monitor",
        poll_type="ping",
        metric_name="latency",
        value=14.2,
        unit="ms",
        status="OK",
        filename="cloudflared_poll_events.csv",
    )
    log_event(
        app="cloudflared_monitor",
        event_type="service_started",
        status="SUCCESS",
        details="Daemon started",
        filename="cloudflared_events.csv",
    )
    log_param_change(
        app="cloudflared_monitor",
        param_name="tunnel_id",
        old_value="abc",
        new_value="xyz",
        filename="cloudflared_param_changes.csv",
    )

    # Проверяем, что физические CSV файлы НЕ создались (экономия диска)
    log_dir = get_apps_log_dir()
    assert not (log_dir / "cloudflared_poll_events.csv").exists()
    assert not (log_dir / "cloudflared_events.csv").exists()
    assert not (log_dir / "cloudflared_param_changes.csv").exists()

    # Проверяем, что данные гарантированно записаны в SQLite (Single Source of Truth)
    storage = TelemetryStorage.get_instance()
    polls = storage.get_app_polls(app="cloudflared_monitor")
    assert len(polls) == 1
    assert polls[0]["metric_name"] == "latency"
    assert polls[0]["value"] == 14.2

    events = storage.get_app_events(app="cloudflared_monitor")
    assert len(events) == 1
    assert events[0]["event_type"] == "service_started"

    params = storage.get_app_param_changes(app="cloudflared_monitor")
    assert len(params) == 1
    assert params[0]["param_name"] == "tunnel_id"


def test_on_demand_csv_export():
    """Проверяет генерацию CSV-файлов по требованию из SQLite."""
    app_logger = AppCsvLogger("nginx_monitor")

    for i in range(5):
        app_logger.log_poll("status_check", "active_connections", 100 + i, unit="conn")
        app_logger.log_event("request_peak", status="WARNING", details=f"Load peak {i}")

    app_logger.log_param_change("worker_processes", "2", "4", user="admin")

    # Экспорт по требованию
    exported = export_to_csv(app="nginx_monitor", target_type="all")
    assert "polls" in exported
    assert "events" in exported
    assert "params" in exported

    polls_csv = exported["polls"]
    assert polls_csv.exists()
    with open(polls_csv, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 6  # 1 header + 5 rows
        assert reader[0] == ["timestamp", "app", "poll_type", "metric_name", "value", "unit", "status", "details"]
        assert reader[1][1] == "nginx_monitor"

    events_csv = exported["events"]
    assert events_csv.exists()
    with open(events_csv, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 6

    params_csv = exported["params"]
    assert params_csv.exists()
    with open(params_csv, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2


def test_mirroring_logs_to_csv_enabled():
    """Проверяет работу при явно включенном флаге зеркалирования логов в CSV."""
    set_mirroring_logs_to_csv(True)
    assert is_mirroring_logs_to_csv_enabled()
    assert is_csv_mirroring_enabled()  # Проверка алиаса обратной совместимости

    file_path = log_event(
        app="system_control_center",
        event_type="firewall_rule_added",
        status="SUCCESS",
        details="Port 8080 opened",
        filename="system_control_events.csv",
    )
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2
        assert reader[1][1] == "system_control_center"
        assert reader[1][2] == "firewall_rule_added"

    # Проверка выключения через алиас
    set_csv_mirroring(False)
    assert not is_mirroring_logs_to_csv_enabled()


def test_memory_batching():
    """Проверяет опциональный режим пакетной буферизации в памяти."""
    set_memory_batching(True)
    assert is_memory_batching_enabled()

    storage = TelemetryStorage.get_instance()

    # Записываем опрос - он попадает в буфер памяти
    log_poll("batch_app", "test_poll", "temp", 42.0)
    log_event("batch_app", "buffered_event", status="OK")
    log_param_change("batch_app", "mode", "A", "B")

    # Принудительный сброс буфера
    flush_batch_buffer()

    polls = storage.get_app_polls(app="batch_app")
    assert len(polls) == 1
    assert polls[0]["value"] == 42.0

    events = storage.get_app_events(app="batch_app")
    assert len(events) == 1
    assert events[0]["event_type"] == "buffered_event"

    params = storage.get_app_param_changes(app="batch_app")
    assert len(params) == 1


def test_multithreaded_logging():
    """Проверяет потокобезопасность при конкурентной записи."""
    logger = AppCsvLogger("multi_test")

    def worker(worker_id: int):
        for i in range(25):
            logger.log_event("worker_event", status="OK", details=f"Worker {worker_id} iteration {i}")
            logger.log_poll("worker_poll", f"metric_{worker_id}", i * 1.5)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    storage = TelemetryStorage.get_instance()
    events = storage.get_app_events(app="multi_test", limit=500)
    polls = storage.get_app_polls(app="multi_test", limit=500)
    assert len(events) == 100
    assert len(polls) == 100

    # Проверяем экспорт после многопоточной записи
    exported = logger.export_csv(target_type="events")
    assert exported["events"].exists()
    with open(exported["events"], "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 101
