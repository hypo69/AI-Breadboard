# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Service And Main
# =============================================================================
# Description:
#   Тесты для фонового сервиса TelemetryLoggerService и командного интерфейса main.py на реальных вызовах.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_service_and_main import TestTelemetryLoggerService
#
#     service = TestTelemetryLoggerService()
#
# File: test_telemetry_service_and_main.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты для фонового сервиса TelemetryLoggerService и командного интерфейса main.py на реальных вызовах.

Updated: 2026-10-01 11:07:00"""

import sys
import time
import pytest

from apps.windows.telemetry.service import TelemetryLoggerService
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.main import parse_arguments, signal_handler, _stop_event


@pytest.fixture
def real_telemetry_service(tmp_path):
    """Фикстура создаёт фоновый сервис с реальным сборщиком и реальной SQLite БД."""
    db_path = str(tmp_path / "test_service_telemetry.db")
    storage = TelemetryStorage(db_path=db_path)
    collector = SystemCollector()
    service = TelemetryLoggerService(
        interval_sec=0.2,
        top_processes=5,
        collector=collector,
        storage=storage,
        enable_w64=False
    )
    return service


class TestTelemetryLoggerService:
    """Тесты фонового сервиса сбора системных метрик без моков."""

    def test_service_initialization(self, real_telemetry_service):
        assert real_telemetry_service.interval_sec == 0.2
        assert real_telemetry_service.top_processes == 5
        assert real_telemetry_service.collector is not None
        assert real_telemetry_service.storage is not None

    def test_service_start_and_stop(self, real_telemetry_service):
        real_telemetry_service.start()
        time.sleep(0.3)
        real_telemetry_service.stop()
        assert real_telemetry_service.is_running is False


class TestTelemetryMainCLI:
    """Тесты аргументов командной строки и сигналов управления без моков."""

    def test_parse_arguments_default(self):
        old_argv = list(sys.argv)
        try:
            sys.argv = ['main.py']
            args = parse_arguments()
            assert args.mode is None
            assert args.minimal is False
        finally:
            sys.argv = old_argv

    def test_parse_arguments_custom(self):
        old_argv = list(sys.argv)
        try:
            sys.argv = ['main.py', '--mode', 'hybrid', '--interval', '10.0', '--top-processes', '15']
            args = parse_arguments()
            assert args.mode == 'hybrid'
            assert args.interval == 10.0
            assert args.top_processes == 15
        finally:
            sys.argv = old_argv

    def test_signal_handler(self):
        _stop_event.clear()
        signal_handler(2, None)
        assert _stop_event.is_set()
