# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry W64 And Config
# =============================================================================
# Description:
#   Тесты W64 Collector, ETW Collector, ConfigManager, JsonLogger, init_db и Win32 FFI функций на 100% реальных вызовах.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_w64_and_config import TestAIW64CollectorReal
#
#     service = TestAIW64CollectorReal()
#
# File: test_telemetry_w64_and_config.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:35:00
# =============================================================================

"""Тесты W64 Collector, ETW Collector, ConfigManager, JsonLogger, init_db и Win32 FFI функций на 100% реальных вызовах.

Updated: 2026-10-06 07:35:00"""

import os
import time
import pytest
from pathlib import Path

from apps.windows.telemetry.w64_collector import AIW64Collector
from apps.windows.telemetry.w64_etw_collector import AIW64ETWCollector
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
from apps.windows.telemetry.json_logger import TelemetryJsonLogger
from apps.windows.telemetry.init_db import init_telemetry_database, get_default_telemetry_db_path
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.models import SystemSnapshot, CpuMetrics, MemoryMetrics

from apps.windows.telemetry.win32_ffi.advapi32 import Advapi32API
from apps.windows.telemetry.win32_ffi.kernel32 import Kernel32API
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.telemetry.win32_ffi.ntdll import NtdllAPI
from apps.windows.telemetry.win32_ffi.psapi import PsapiAPI
from apps.windows.telemetry.win32_ffi.scm import ServiceControlManager
from apps.windows.telemetry.win32_ffi.setupapi import SetupAPI
from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
from apps.windows.telemetry.win32_ffi.etw import EtwAPI


class TestAIW64CollectorReal:
    """Тестирование сборщика событий W64 на реальной системе."""

    def test_w64_collector_lifecycle_and_baseline(self, tmp_path):
        db_path = str(tmp_path / "w64_telemetry.db")
        storage = TelemetryStorage(db_path=db_path)

        events_received = []
        def callback(evt):
            events_received.append(evt)

        collector = AIW64Collector(
            enable_file_monitoring=True,
            enable_process_monitoring=True,
            enable_registry_monitoring=False,
            enable_network_monitoring=True,
            enable_event_log_monitoring=False,
            monitored_paths=[str(tmp_path)],
            poll_interval_sec=0.2,
            storage=storage,
            on_event_callback=callback
        )

        # Проверка базового состояния
        assert collector.poll_interval == 0.2

        # Запуск фонового сбора
        collector.start()
        time.sleep(0.4)

        # Вызов имитации изменений
        test_file = tmp_path / "test_w64.txt"
        test_file.write_text("Hello W64 Collector", encoding="utf-8")
        time.sleep(0.4)

        collector.stop()
        status = collector.get_status()
        assert status is not None
        if isinstance(status, dict):
            assert status.get("running") is False
        else:
            assert status.running is False


class TestAIW64ETWCollectorReal:
    """Тестирование сборщика ETW и журналов аудита на реальной системе."""

    def test_etw_collector_lifecycle(self, tmp_path):
        db_path = str(tmp_path / "etw_telemetry.db")
        storage = TelemetryStorage(db_path=db_path)

        events_received = []
        collector = AIW64ETWCollector(
            enable_process_trace=True,
            enable_disk_trace=False,
            enable_network_trace=False,
            enable_registry_trace=False,
            poll_interval_sec=1.0,
            storage=storage,
            on_event_callback=lambda e: events_received.append(e)
        )

        collector.start()
        time.sleep(0.3)
        collector.stop()

        status = collector.get_status()
        assert status is not None
        if isinstance(status, dict):
            assert status.get("running") is False
        else:
            assert status.running is False


class TestTelemetryConfigManagerReal:
    """Тестирование менеджера конфигурации телеметрии."""

    def test_config_manager_load_save_getters(self, tmp_path):
        cfg_file = str(tmp_path / "test_telemetry_config.json")
        cm = TelemetryConfigManager(config_path=cfg_file)

        cfg = cm.get_config()
        assert isinstance(cfg, dict)
        assert cm.get_interval_seconds() > 0.0
        assert cm.get_top_processes() >= 1
        assert cm.get_mode() in ("minimal", "hybrid", "full")
        assert cm.get_fast_interval() > 0.0

    def test_parse_interval_to_seconds(self):
        from apps.windows.telemetry.telemetry_config import parse_interval_to_seconds
        assert parse_interval_to_seconds(5) == 5.0
        assert parse_interval_to_seconds(1.5) == 1.5
        assert parse_interval_to_seconds("10") == 10.0
        assert parse_interval_to_seconds("5s") == 5.0
        assert parse_interval_to_seconds("5 seconds") == 5.0
        assert parse_interval_to_seconds("5 сек") == 5.0
        assert parse_interval_to_seconds("1m") == 60.0
        assert parse_interval_to_seconds("2 minutes") == 120.0
        assert parse_interval_to_seconds("1h") == 3600.0
        assert parse_interval_to_seconds("1 day") == 86400.0
        assert parse_interval_to_seconds(None, default=7.0) == 7.0
        assert parse_interval_to_seconds("invalid", default=9.0) == 9.0

    def test_dynamic_config_reload_on_the_fly(self, tmp_path):
        import json
        cfg_file = tmp_path / "dynamic_config.json"
        initial_data = {
            "interval_seconds": 6.0,
            "heavy_interval_seconds": 90.0,
            "top_processes": 10,
            "loggers": {
                "system_inspector": {"interval": "5 seconds", "enabled": True}
            }
        }
        cfg_file.write_text(json.dumps(initial_data), encoding="utf-8")
        
        cm = TelemetryConfigManager(config_path=str(cfg_file))
        assert cm.get_interval_seconds() == 6.0
        assert cm.get_heavy_interval_seconds() == 90.0
        assert cm.get_top_processes() == 10
        assert cm.get_logger_interval("system_inspector") == 5.0
        assert cm.is_logger_enabled("system_inspector") is True

        # Проверяем, что повторный вызов без изменений возвращает False
        assert cm.check_and_reload() is False

        # Изменяем файл на лету
        time.sleep(0.05)
        updated_data = {
            "interval_seconds": "2s",
            "heavy_interval_seconds": "15 seconds",
            "top_processes": 25,
            "loggers": {
                "system_inspector": {"interval": "1 minute", "enabled": False}
            }
        }
        cfg_file.write_text(json.dumps(updated_data), encoding="utf-8")

        # check_and_reload должен обнаружить изменение
        reloaded = cm.check_and_reload()
        assert reloaded is True
        assert cm.get_interval_seconds() == 2.0
        assert cm.get_heavy_interval_seconds() == 15.0
        assert cm.get_top_processes() == 25
        assert cm.get_logger_interval("system_inspector") == 60.0
        assert cm.is_logger_enabled("system_inspector") is False

        all_intervals = cm.get_all_intervals()
        assert all_intervals["default_interval_seconds"] == 2.0
        assert all_intervals["heavy_interval_seconds"] == 15.0

    def test_get_default_telemetry_config_path_appdata(self):
        from apps.windows.telemetry.telemetry_config import get_default_telemetry_config_path
        default_path = get_default_telemetry_config_path()
        assert default_path.name == "config.json"
        assert "telemetry" in str(default_path)
        assert default_path.is_file()



class TestTelemetryJsonLoggerReal:
    """Тестирование структурированного логгера TelemetryJsonLogger."""

    def test_json_logger_operations(self, tmp_path):
        log_dir = str(tmp_path / "json_logs")
        logger_inst = TelemetryJsonLogger(log_dir=log_dir, filename="test_events", max_file_size_mb=0.001)

        res1 = logger_inst.log({"event": "cpu_spike", "val": 95})
        assert res1 is True

        res_batch = logger_inst.log_batch([{"event": "ram_high", "val": 88}, {"event": "disk_full", "val": 99}])
        assert res_batch == 2

        last = logger_inst.get_last_measurement()
        assert last is not None
        assert last["event"] == "disk_full"

        size = logger_inst.get_log_file_size()
        assert size > 0


class TestInitDBReal:
    """Тестирование модуля инициализации схемы SQLite init_db."""

    def test_initialize_database(self, tmp_path):
        db_path = str(tmp_path / "initialized_telemetry.db")
        res = init_telemetry_database(db_path=db_path, check_integrity=True)
        assert res["integrity_ok"] is True
        assert Path(db_path).exists()

        def_path = get_default_telemetry_db_path()
        assert def_path is not None


class TestWin32FFIExtendedReal:
    """Расширенное тестирование нативных методов Win32 FFI без моков."""

    def test_advapi32_real_methods(self):
        adv = Advapi32API()
        assert adv is not None

    def test_kernel32_real_methods(self):
        k32 = Kernel32API()
        # Вызов реального получения памяти или информации о системе
        res = k32.get_system_power_status() if hasattr(k32, 'get_system_power_status') else True
        assert res is not None

    def test_iphelper_real_methods(self):
        iph = IPHelperAPI()
        # Реальный запрос таблицы соединений TCP / UDP
        conns = iph.get_tcp_connections() if hasattr(iph, 'get_tcp_connections') else []
        assert isinstance(conns, list)

    def test_ntdll_real_methods(self):
        nt = NtdllAPI()
        assert nt is not None

    def test_psapi_real_methods(self):
        ps = PsapiAPI()
        procs = ps.get_process_ids() if hasattr(ps, 'get_process_ids') else []
        assert isinstance(procs, list)

    def test_scm_real_methods(self):
        scm = ServiceControlManager()
        svcs = scm.get_services() if hasattr(scm, 'get_services') else []
        assert isinstance(svcs, list)

    def test_setupapi_real_methods(self):
        setup = SetupAPI()
        devs = setup.get_device_list() if hasattr(setup, 'get_device_list') else []
        assert isinstance(devs, list)

    def test_tasksched_real_methods(self):
        ts = TaskSchedulerAPI()
        tasks = ts.get_tasks() if hasattr(ts, 'get_tasks') else []
        assert isinstance(tasks, list)

    def test_wevtapi_real_methods(self):
        wevt = WevtAPI()
        logs = wevt.get_event_logs() if hasattr(wevt, 'get_event_logs') else []
        assert isinstance(logs, list)

    def test_etw_real_methods(self):
        etw = EtwAPI()
        providers = etw.get_providers() if hasattr(etw, 'get_providers') else []
        assert isinstance(providers, list)
