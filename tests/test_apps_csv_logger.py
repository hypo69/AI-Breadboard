# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Apps CSV Logger Module
# =============================================================================
# Description:
#   Набор тестов для модуля apps/common/csv_logger.py: проверка корректности
#   создания каталогов, генерации CSV-заголовков, многопоточной записи и
#   форматирования событий, параметров и опросов.
#
# File: test_apps_csv_logger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты модуля CSV-логгирования приложений."""

import csv
import threading
from pathlib import Path
import pytest

from apps.common.csv_logger import (
    AppCsvLogger,
    get_apps_log_dir,
    log_custom_csv,
    log_event,
    log_param_change,
    log_poll,
    set_apps_log_dir_override,
    write_csv_row,
)


@pytest.fixture(autouse=True)
def setup_tmp_log_dir(tmp_path: Path):
    """Изолирует каталог логов во временную папку на время теста."""
    set_apps_log_dir_override(tmp_path / "apps_logs")
    yield
    set_apps_log_dir_override(None)


def test_get_apps_log_dir():
    """Проверяет получение и автоматическое создание директории логов."""
    log_dir = get_apps_log_dir()
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_log_event():
    """Проверяет запись события приложения."""
    file_path = log_event(
        app="cloudflared_monitor",
        event_type="start_tunnel",
        status="SUCCESS",
        details="Daemon started successfully with PID 1234",
        filename="cloudflared_service_events.csv",
    )
    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2
        assert reader[0] == ["timestamp", "app", "event_type", "status", "details"]
        assert reader[1][1] == "cloudflared_monitor"
        assert reader[1][2] == "start_tunnel"
        assert reader[1][3] == "SUCCESS"
        assert "1234" in reader[1][4]


def test_log_param_change():
    """Проверяет запись изменения параметра."""
    file_path = log_param_change(
        app="system_control_center",
        param_name="sec.uac_level",
        old_value=1,
        new_value=0,
        status="SUCCESS",
        user="admin",
        details={"restore_point_id": "rp_99"},
        filename="system_control_param_changes.csv",
    )
    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2
        assert reader[0] == ["timestamp", "app", "param_name", "old_value", "new_value", "status", "user", "details"]
        assert reader[1][1] == "system_control_center"
        assert reader[1][2] == "sec.uac_level"
        assert reader[1][3] == "1"
        assert reader[1][4] == "0"
        assert reader[1][5] == "SUCCESS"
        assert reader[1][6] == "admin"
        assert "restore_point_id" in reader[1][7]


def test_log_poll():
    """Проверяет запись опроса метрик/сенсоров."""
    file_path = log_poll(
        app="hwinfo",
        poll_type="sensor_read",
        metric_name="CPU Core Temperature",
        value=54.5,
        unit="°C",
        status="OK",
        details="Tctl sensor",
        filename="hwinfo_sensor_polls.csv",
    )
    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2
        assert reader[0] == ["timestamp", "app", "poll_type", "metric_name", "value", "unit", "status", "details"]
        assert reader[1][1] == "hwinfo"
        assert reader[1][2] == "sensor_read"
        assert reader[1][3] == "CPU Core Temperature"
        assert reader[1][4] == "54.5"
        assert reader[1][5] == "°C"


def test_app_csv_logger_class():
    """Проверяет методы класса AppCsvLogger."""
    app_logger = AppCsvLogger("trading_terminal")
    
    # Poll
    p_file = app_logger.log_poll("ticker", "BTC/USDT", 65000.0, unit="USD", filename="trading_terminal_market_polls.csv")
    assert p_file.exists()
    
    # Event
    e_file = app_logger.log_event("kill_switch", status="EXECUTED", details="Liquidated all open positions", filename="trading_terminal_kill_switch.csv")
    assert e_file.exists()
    
    # Param change
    pc_file = app_logger.log_param_change("symbol", "BTC/USDT", "ETH/USDT", filename="trading_terminal_param_changes.csv")
    assert pc_file.exists()

    # Custom
    c_file = app_logger.log_custom("trading_orders.csv", ["order_id", "side", "qty", "price"], ["ord_1", "BUY", 0.5, 65000.0])
    assert c_file.exists()


def test_multithreaded_csv_logging():
    """Проверяет потокобезопасность одновременной записи."""
    logger = AppCsvLogger("multi_test")
    
    def worker(worker_id: int):
        for i in range(20):
            logger.log_event("worker_event", status="OK", details=f"Worker {worker_id} iteration {i}", filename="concurrent_events.csv")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    file_path = get_apps_log_dir() / "concurrent_events.csv"
    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        # 1 header + 100 rows
        assert len(reader) == 101
