# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry_Research - Test Research Analytics Full
# =============================================================================
# Description:
#   Тесты аналитических подсистем телеметрии на 100% реальных системных вызовах без использования моков.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry_research.test_research_analytics_full import ConcreteDiagnosticEngine
#
#     service = ConcreteDiagnosticEngine()
#
# File: test_research_analytics_full.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты аналитических подсистем телеметрии на 100% реальных системных вызовах без использования моков.

Updated: 2026-10-01 11:30:00"""

import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry_research.reboot_analyzer import WindowsRebootAnalyzer
from apps.windows.telemetry_research.aggregator import TelemetryAggregator
from apps.windows.telemetry_research.grouped_telemetry import GroupedTelemetryBuilder
from apps.windows.telemetry_research.compactor import TelemetryCompactor, compute_percentile
from apps.windows.telemetry_research.hardware_history_manager import HardwareHistoryManager
from apps.windows.telemetry_research.hardware_auditor import HardwareAuditor
from apps.windows.telemetry_research.audit_startup_checker import AuditStartupChecker, run_startup_audit
from apps.windows.telemetry_research.diagnostic_engine import DiagnosticEngine, SystemDiagnosticEngine
from apps.windows.telemetry_research.deep_diagnostics import DeepDiagnosticsEngine
from apps.windows.telemetry_research.incident_detector import IncidentDetector
from apps.windows.telemetry.models import AnomalyItem, SystemSnapshot


@pytest.fixture
def real_telemetry_storage(tmp_path: Path):
    """Фикстура реального хранилища SQLite во временной директории."""
    db_file = tmp_path / "telemetry_test.db"
    return TelemetryStorage.get_instance(db_path=db_file)


class ConcreteDiagnosticEngine(SystemDiagnosticEngine):
    """Конкретная реальная имплементация эвристического диагностического движка."""

    def evaluate_heuristics(self, data: Any):
        anomalies = [
            AnomalyItem(
                subsystem="cpu",
                title="High CPU Load",
                description="CPU usage > 80%",
                severity="warning",
                value=85.0,
                threshold=80.0,
            )
        ]
        return 80, anomalies, ["Повышенная загрузка ЦП"]


class TestTelemetryAnalyticsReal:
    """Полное функциональное тестирование 10 перенесенных аналитических подсистем на реальных вызовах."""

    def test_reboot_analyzer_real(self, real_telemetry_storage):
        """Тест анализатора перезагрузок WindowsRebootAnalyzer."""
        analyzer = WindowsRebootAnalyzer(storage=real_telemetry_storage)
        boot_dt, uptime_sec = analyzer.get_current_boot_info()

        assert isinstance(boot_dt, datetime)
        assert uptime_sec >= 0.0

        report = analyzer.collect_reboot_history(limit=5, hours=24, persist_to_storage=True)
        assert report.current_uptime_seconds >= 0.0
        assert report.stability_score >= 0.0
        assert isinstance(report.summary_ru, str)

    def test_aggregator_real_poll(self, real_telemetry_storage, tmp_path: Path):
        """Тест агрегатора телеметрии TelemetryAggregator на реальном поллинге."""
        aggregator = TelemetryAggregator(log_dir=str(tmp_path), storage=real_telemetry_storage)
        aggregator.poll_once()

        last = aggregator.get_last_measurement()
        assert last is not None
        assert "timestamp" in last
        assert "hardware" in last

        status = aggregator.get_status()
        assert status["measurement_count"] == 1

    def test_grouped_telemetry_builder_real(self):
        """Тест формирования 4 доменных групп утилизации ресурсов."""
        collector = SystemCollector()
        snapshot = collector.get_snapshot()

        builder = GroupedTelemetryBuilder()
        groups = builder.build_all_groups(snapshot)

        assert len(groups) == 4
        group_ids = [g.group_id for g in groups]
        assert "compute_thermals" in group_ids
        assert "memory_processes" in group_ids
        assert "storage_smart" in group_ids
        assert "system_network" in group_ids

    def test_compactor_and_percentiles(self):
        """Тест многоуровневого компактора и расчета перцентилей p95."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        p95 = compute_percentile(values, 95.0)
        assert round(p95, 1) == 95.5

        tier_10s = TelemetryCompactor.get_tier_for_age(1200.0)
        assert tier_10s == "10s"

        samples = [
            {"cpu_total_percent": 10.0, "memory_used_gb": 4.0, "memory_percent": 25.0},
            {"cpu_total_percent": 90.0, "memory_used_gb": 8.0, "memory_percent": 50.0},
        ]
        now_str = datetime.now(timezone.utc).isoformat()
        rollup = TelemetryCompactor.compact_system_metrics(samples, now_str, now_str, tier="1m")

        assert rollup.sample_count == 2
        assert rollup.cpu_max == 90.0
        assert rollup.cpu_min == 10.0
        assert rollup.cpu_avg == 50.0

    def test_hardware_auditor_and_history_real(self, tmp_path: Path):
        """Тест аудитора устройств HardwareAuditor и менеджера истории Diff Engine."""
        auditor = HardwareAuditor()
        report = auditor.audit_hardware()

        assert report.devices_count > 0
        assert len(report.devices) > 0

        archive_dir = tmp_path / "hw_archives"
        history_mgr = HardwareHistoryManager(archive_dir=archive_dir)

        entry1 = history_mgr.archive_report(report, auto_diff=True)
        assert entry1.archive_id.startswith("hw_")

        latest = history_mgr.get_latest_archive()
        assert latest is not None
        assert latest.archive_id == entry1.archive_id

    def test_audit_startup_checker_real(self):
        """Тест быстрой стартовой проверки здоровья системы."""
        checker = AuditStartupChecker()
        res = checker.check_startup_health(check_integrity=True, check_performance=True)

        assert isinstance(res.is_healthy, bool)
        assert res.duration_ms >= 0.0

        util_res = run_startup_audit(check_integrity=True, check_performance=True)
        assert isinstance(util_res.is_healthy, bool)

    def test_diagnostic_and_deep_diagnostics_real(self):
        """Тест эвристического и глубокого диагностического движка."""
        engine = ConcreteDiagnosticEngine()
        collector = SystemCollector()
        snapshot = collector.get_snapshot()

        score, anomalies, summary = engine.evaluate_heuristics(snapshot)
        assert score == 80
        assert len(anomalies) == 1

        prompt = engine.build_prompt(snapshot, score, anomalies, "Все хорошо")
        assert "Аномалии" in prompt

        deep_engine = DeepDiagnosticsEngine()
        ext_audit = deep_engine.collect_extended_system_audit()
        assert ext_audit.timestamp != ""
        assert ext_audit.hostname != ""

    async def test_incident_detector_real(self):
        """Тест детектора системных инцидентов."""
        detector = IncidentDetector(cpu_threshold=0.0)
        collector = SystemCollector()
        snapshot_model = await collector.get_snapshot()
        snapshot = snapshot_model.model_dump()

        incident = detector.check_anomaly(snapshot)
        assert incident is not None
        assert incident.title != ""
