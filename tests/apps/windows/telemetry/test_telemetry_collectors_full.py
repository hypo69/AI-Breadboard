# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Collectors Full
# =============================================================================
# Description:
#   Тесты полного функционального покрытия для SystemCollector, RebootAnalyzer и AuditStartupChecker на реальных системных вызовах.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_collectors_full import TestSystemCollectorFullReal
#
#     service = TestSystemCollectorFullReal()
#
# File: test_telemetry_collectors_full.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты полного функционального покрытия для SystemCollector, RebootAnalyzer и AuditStartupChecker на реальных системных вызовах.

Updated: 2026-10-01 11:05:00"""

import asyncio
import os
import pytest

# Updated: 2026-10-01 11:30:00
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry_research.reboot_analyzer import WindowsRebootAnalyzer
from apps.windows.telemetry_research.audit_startup_checker import AuditStartupChecker, StartupAuditResult
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry_research.hardware_auditor import HardwareAuditor
from apps.windows.telemetry_research.hardware_history_manager import HardwareHistoryManager


@pytest.fixture
def real_storage(tmp_path):
    """Фикстура реального хранилища TelemetryStorage на основе файла SQLite во временной директории."""
    db_file = tmp_path / "real_telemetry_collectors.db"
    storage = TelemetryStorage(
        db_path=db_file,
        buffer_mode='direct',
        auto_flush=False,
        max_db_size_mb=50.0,
        retention_days=7
    )
    yield storage
    storage.close()


@pytest.fixture
def system_collector(real_storage):
    """Фикстура реального экземпляра SystemCollector с настоящими подсистемами."""
    auditor = HardwareAuditor()
    history_mgr = HardwareHistoryManager()
    collector = SystemCollector(
        auditor=auditor,
        history_manager=history_mgr,
        storage=real_storage
    )
    return collector


class TestSystemCollectorFullReal:
    """Тестирование всех методов SystemCollector на реальной системе без использования моков."""

    def test_get_system_identity_caching_and_locales(self, system_collector):
        """Проверка получения реального идентификатора системы, имени пользователя и локали."""
        id1 = system_collector.get_system_identity()
        assert isinstance(id1, dict)
        assert 'hostname' in id1 or 'user' in id1
        # Повторный вызов отдает кэшированное значение
        id2 = system_collector.get_system_identity()
        assert id1 == id2

    @pytest.mark.asyncio
    async def test_get_cpu_metrics(self, system_collector):
        """Реальный сбор показателей процессора."""
        cpu = await system_collector.get_cpu_metrics()
        assert cpu is not None
        assert cpu.total_percent >= 0.0

    def test_get_memory_and_gpu_metrics(self, system_collector):
        """Реальный сбор показателей ОЗУ и графических адаптеров."""
        mem = system_collector.get_memory_metrics()
        assert mem is not None
        assert mem.total_gb > 0.0

        gpus = system_collector.get_gpu_metrics()
        assert isinstance(gpus, list)

    def test_get_disk_and_network_metrics(self, system_collector):
        """Реальный сбор показателей логических дисков и сетевых карт."""
        partitions, io_metrics = system_collector.get_disk_metrics()
        assert isinstance(partitions, list)

        net_metrics = system_collector.get_network_metrics()
        assert isinstance(net_metrics, list)

        net_report = system_collector.get_network_usage_report(period_minutes=60)
        assert net_report is not None

        disk_report = system_collector.get_disk_usage_report(period_minutes=60, force_refresh_smart=False)
        assert disk_report is not None

    def test_get_top_processes_and_listening_ports(self, system_collector):
        """Реальное получение списка активных процессов и открытых сокетов."""
        procs = system_collector.get_top_processes(limit=5, sort_by='cpu')
        assert isinstance(procs, list)

        ports = system_collector.get_listening_ports(limit=5)
        assert isinstance(ports, list)

    def test_get_process_network_activity(self, system_collector):
        """Реальный мониторинг сетевой активности процессов."""
        activity = system_collector.get_process_network_activity(limit=10, only_internet=False)
        assert isinstance(activity, list)

    def test_traffic_classification(self, system_collector):
        """Классификация типа сетевого трафика."""
        service_type, sent_desc, recv_desc = SystemCollector._classify_traffic('chrome.exe', 443, 'TCP', 'ESTABLISHED', True)
        assert service_type is not None
        assert 'HTTPS' in service_type

    def test_get_health_alerts_and_monitors(self, system_collector):
        """Сбор сведений об алертах здоровья и физических мониторах."""
        alerts = system_collector.get_health_alerts()
        assert alerts is not None

        monitors = system_collector.get_monitors()
        assert isinstance(monitors, list)

    def test_get_updates_and_software_info(self, system_collector):
        """Получение данных из реестра и служб Windows об обновлениях и ПО."""
        updates = system_collector.get_updates_info()
        assert updates is not None

        office = system_collector.get_ms_office_info()
        assert office is not None

        onedrive = system_collector.get_onedrive_info()
        assert onedrive is not None

    @pytest.mark.asyncio
    async def test_get_core_metrics_and_quick_hardware(self, system_collector):
        """Сбор реального снимка ядра и экспресс-сведений об оборудовании."""
        core = await system_collector.get_core_metrics()
        assert core is not None

        quick_hw = await system_collector.get_hardware_quick()
        assert quick_hw is not None

        snapshot = await system_collector.get_snapshot(process_limit=5)
        assert snapshot is not None

    def test_hardware_audit_and_history(self, system_collector):
        """Настоящий аудит оборудования и получение дерева устройств."""
        sensors = system_collector.get_hardware_sensors()
        assert isinstance(sensors, list)

        tree = system_collector.get_hardware_tree(force=True)
        assert isinstance(tree, list)

        audit = system_collector.get_hardware_audit()
        assert audit is not None

        arch = system_collector.archive_hardware_state(auto_diff=True)
        assert arch is not None

        hist = system_collector.get_hardware_history(limit=5)
        assert isinstance(hist, list)

        changes = system_collector.get_hardware_changes(limit=5)
        assert isinstance(changes, list)

    def test_db_snapshot_operations(self, system_collector, real_storage):
        """Сохранение и выгрузка реальных снимков в физический файл SQLite."""
        snap_id = system_collector.save_snapshot_to_db(top_n=5)
        assert snap_id > 0

        snaps = system_collector.get_snapshots(limit=5)
        assert len(snaps) >= 1

        history = system_collector.get_process_history(limit=5)
        assert isinstance(history, list)

    def test_reboot_and_extended_audit_methods(self, system_collector):
        """Реальный запрос отчета о перезагрузках и расширенного аудита."""
        report = system_collector.get_reboot_report(limit=5, hours=24)
        assert report is not None


class TestWindowsRebootAnalyzerReal:
    """Тестирование реального анализатора перезагрузок и системных логов Windows Event Log."""

    def test_get_current_boot_info(self, real_storage):
        """Определение реального времени запуска ОС и текущего аптайма."""
        analyzer = WindowsRebootAnalyzer(storage=real_storage)
        boot_time, uptime = analyzer.get_current_boot_info()
        assert boot_time is not None
        assert uptime >= 0.0

    def test_analyze_reboots(self, real_storage):
        """Реальное чтение журналов выключения и перезагрузок Windows."""
        analyzer = WindowsRebootAnalyzer(storage=real_storage)
        report = analyzer.collect_reboot_history(limit=5, hours=24)
        assert report is not None


class TestAuditStartupCheckerReal:
    """Тестирование реального проверщика аудитов при запуске."""

    def test_startup_audit_result_to_dict(self):
        """Проверка структуры результатов стартовой проверки."""
        res = StartupAuditResult(
            is_healthy=True,
            critical_count=0,
            warning_count=1,
            findings=[{'type': 'test'}],
            checks_passed=['check1'],
            duration_ms=12.5
        )
        d = res.to_dict()
        assert d['is_healthy'] is True

    def test_audit_startup_checker_run(self):
        """Реальный запуск быстрой проверки состояния целостности и системных аудитов."""
        checker = AuditStartupChecker()
        result = checker.check_startup_health()
        assert isinstance(result, StartupAuditResult)
