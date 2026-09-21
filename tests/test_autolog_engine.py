# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Applications Auto-Logging Engine
# =============================================================================
# Description:
#   Тесты для модуля apps/common/autolog_engine.py: валидация парсинга интервалов,
#   чтения конфигурации logging из config_tc.json / config.json, жизненного цикла
#   AutoLogEngine (start/stop/status) и выполнения опросов с генерацией CSV-логов.
#
# File: test_autolog_engine.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты движка автологгирования приложений."""

import asyncio
import json
from pathlib import Path
import pytest

from apps.common.autolog_engine import (
    AutoLogEngine,
    load_autolog_config,
    parse_interval_seconds,
)
from apps.common.csv_logger import set_apps_log_dir_override


@pytest.fixture(autouse=True)
def setup_tmp_log_dir(tmp_path: Path):
    """Изолирует каталог логов во временную папку."""
    set_apps_log_dir_override(tmp_path / "autolog_csvs")
    yield
    set_apps_log_dir_override(None)


def test_parse_interval_seconds_various_formats():
    """Проверяет парсер строковых представлений интервалов времени."""
    # Секунды
    assert parse_interval_seconds("5 seconds") == 5.0
    assert parse_interval_seconds("5s") == 5.0
    assert parse_interval_seconds("10 sec") == 10.0
    assert parse_interval_seconds("1 second") == 1.0
    assert parse_interval_seconds("10.5 secs") == 10.5

    # Минуты
    assert parse_interval_seconds("1 minute") == 60.0
    assert parse_interval_seconds("5 minutes") == 300.0
    assert parse_interval_seconds("5m") == 300.0
    assert parse_interval_seconds("0.5 min") == 30.0

    # Часы
    assert parse_interval_seconds("1 hour") == 3600.0
    assert parse_interval_seconds("6 hours") == 21600.0
    assert parse_interval_seconds("24h") == 86400.0
    assert parse_interval_seconds("2 hrs") == 7200.0

    # Дни
    assert parse_interval_seconds("1 day") == 86400.0
    assert parse_interval_seconds("7 days") == 604800.0
    assert parse_interval_seconds("2d") == 172800.0

    # Миллисекунды
    assert parse_interval_seconds("500 ms") == 0.5
    assert parse_interval_seconds("1000 milliseconds") == 1.0

    # Числа
    assert parse_interval_seconds(15) == 15.0
    assert parse_interval_seconds(2.5) == 2.5

    # Фоллбэки
    assert parse_interval_seconds(None, default=42.0) == 42.0
    assert parse_interval_seconds("", default=60.0) == 60.0
    assert parse_interval_seconds("invalid_interval", default=120.0) == 120.0


def test_load_autolog_config(tmp_path: Path):
    """Проверяет корректность загрузки параметров autolog из JSON."""
    cfg_file = tmp_path / "custom_config.json"
    cfg_data = {
        "logging": {
            "enable_autolog": True,
            "default_interval": "5 minutes",
            "loggers": {
                "hwinfo": {"interval": "10 seconds", "enabled": True},
                "cpuz": {"interval": "1 hour", "enabled": False},
            },
        }
    }
    cfg_file.write_text(json.dumps(cfg_data, ensure_ascii=False), encoding="utf-8")

    loaded = load_autolog_config(cfg_file)
    assert loaded["enable_autolog"] is True
    assert loaded["default_interval"] == "5 minutes"
    assert loaded["loggers"]["hwinfo"]["interval"] == "10 seconds"
    assert loaded["loggers"]["cpuz"]["enabled"] is False


def test_autolog_engine_status_and_poll_all():
    """Проверяет сбор диагностического статуса и разовый опрос логгеров."""
    engine = AutoLogEngine()
    status = engine.get_status()

    assert "running" in status
    assert "registered_pollers" in status
    assert "system_inspector" in status["registered_pollers"]
    assert "librehardwaremonitor" in status["registered_pollers"]
    assert "smartmontools" in status["registered_pollers"]

    # Разовый опрос
    results = engine.poll_all_once()
    assert isinstance(results, dict)
    assert "system_inspector" in results
    assert results["system_inspector"] is True

    # Проверка вызова конкретного логгера
    ok = engine.poll_logger("hardware_monitor")
    assert ok is True


@pytest.mark.asyncio
async def test_autolog_engine_lifecycle(tmp_path: Path):
    """Проверяет старт и остановку фонового движка автологгирования."""
    cfg_file = tmp_path / "test_cfg.json"
    cfg_data = {
        "logging": {
            "enable_autolog": True,
            "default_interval": "1 second",
            "loggers": {
                "system_inspector": {"interval": "0.2 seconds", "enabled": True},
                "hardware_monitor": {"interval": "0.2 seconds", "enabled": True},
            },
        }
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    engine = AutoLogEngine()
    custom_called = 0

    def mock_custom_poller():
        nonlocal custom_called
        custom_called += 1

    engine.register_poller("mock_custom_poller", mock_custom_poller)

    started = await engine.start(config_path=cfg_file)
    assert started is True
    assert engine.is_running() is True

    # Даем поработать фоновым задачам
    await asyncio.sleep(0.5)

    await engine.stop()
    assert engine.is_running() is False


@pytest.mark.asyncio
async def test_autolog_engine_disabled(tmp_path: Path):
    """Проверяет поведение при enable_autolog: false."""
    cfg_file = tmp_path / "disabled_cfg.json"
    cfg_data = {
        "logging": {
            "enable_autolog": False,
        }
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    engine = AutoLogEngine()
    started = await engine.start(config_path=cfg_file)
    assert started is False
    assert engine.is_running() is False


def test_parse_interval_russian_units():
    """Проверяет распознавание русских единиц измерения интервала."""
    assert parse_interval_seconds("5 секунд") == 5.0
    assert parse_interval_seconds("10 сек") == 10.0
    assert parse_interval_seconds("1 секунда") == 1.0
    assert parse_interval_seconds("5 минут") == 300.0
    assert parse_interval_seconds("1 минута") == 60.0
    assert parse_interval_seconds("2 часа") == 7200.0
    assert parse_interval_seconds("1 день") == 86400.0
    assert parse_interval_seconds("3 дня") == 259200.0
    assert parse_interval_seconds("500 мс") == 0.5


def test_autolog_csv_writing(tmp_path: Path):
    """Проверяет фактическую запись CSV-логов при выполнении опросов."""
    engine = AutoLogEngine()

    # Опрашиваем несколько встроенных логгеров
    engine.poll_logger("system_inspector")
    engine.poll_logger("website_monitor")
    engine.poll_logger("windows_sysadmin")

    log_dir = tmp_path / "autolog_csvs"
    assert log_dir.exists()

    sys_csv = log_dir / "system_inspector_polls.csv"
    assert sys_csv.exists()
    content = sys_csv.read_text(encoding="utf-8-sig")
    assert "cpu_usage_pct" in content
    assert "memory_usage_pct" in content

    web_csv = log_dir / "website_monitor_poll_events.csv"
    assert web_csv.exists()
    web_content = web_csv.read_text(encoding="utf-8-sig")
    assert "website_monitor" in web_content
    assert "monitor_heartbeat" in web_content
