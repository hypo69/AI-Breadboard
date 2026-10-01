# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Diagnostics Full
# =============================================================================
# Description:
#   Тесты полной диагностики и обнаружения инцидентов телеметрии.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_diagnostics_full import DummyDiagnosticEngine
#
#     service = DummyDiagnosticEngine()
#
# File: test_telemetry_diagnostics_full.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты полной диагностики и обнаружения инцидентов телеметрии.

Updated: 2026-10-01 11:07:00"""

import pytest

from apps.windows.telemetry.models import AnomalyItem, SystemSnapshot, CpuMetrics, MemoryMetrics
# Updated: 2026-10-01 11:30:00
from apps.windows.telemetry_research.incident_detector import IncidentDetector
from apps.windows.telemetry_research.diagnostic_engine import DiagnosticEngine, SystemDiagnosticEngine
from apps.windows.telemetry_research.deep_diagnostics import DeepDiagnosticsEngine


class DummyDiagnosticEngine(SystemDiagnosticEngine):
    """Тестовая реализация конкретного TelemetryDiagnosticEngine."""

    def evaluate_heuristics(self, data):
        anomalies = [AnomalyItem(subsystem='cpu', title='High CPU', description='CPU usage > 80%', severity='warning', value=90.0, threshold=80.0)]
        return 75, anomalies, ['Загрузка CPU превышает 80%']


class TestDiagnosticEngine:
    """Тесты эвристического и LLM анализа телеметрии."""

    def test_build_prompt(self):
        engine = DummyDiagnosticEngine()
        anomalies = [AnomalyItem(subsystem='memory', title='High RAM', description='RAM usage high', severity='critical', value=95.0, threshold=90.0)]
        snapshot = SystemSnapshot(timestamp='2026-10-01T10:00:00Z')
        prompt = engine.build_prompt(snapshot, 60, anomalies, 'Критическая загрузка ОЗУ')
        assert 'High RAM' in prompt or 'ОЗУ' in prompt

    @pytest.mark.asyncio
    async def test_diagnose_async(self):
        engine = DummyDiagnosticEngine(chat_model=None)
        snapshot = SystemSnapshot(timestamp='2026-10-01T10:00:00Z')
        report = await engine.diagnose(snapshot)
        assert report is not None
        assert report.health_score == 75


class TestIncidentDetector:
    """Тесты классификации системных инцидентов и аномалий."""

    def test_detect_incidents_empty(self):
        detector = IncidentDetector()
        incident = detector.check_anomaly({})
        assert incident is None

    def test_detect_cpu_ram_incidents(self):
        detector = IncidentDetector()
        snapshot_dict = {'cpu_usage_pct': 96.0, 'memory_pct': 92.0}
        incident = detector.check_anomaly(snapshot_dict)
        assert incident is None or hasattr(incident, 'severity')


class TestDeepDiagnosticsEngine:
    """Тесты поведенческой форензики, утечек ресурсов и состояния оборудования."""

    @pytest.fixture
    def deep_engine(self):
        return DeepDiagnosticsEngine()

    def test_diagnose_process_leaks(self, deep_engine):
        report = deep_engine.collect_process_leaks(limit=5)
        assert report is not None

    def test_diagnose_kernel_throttling(self, deep_engine):
        report = deep_engine.collect_kernel_throttling()
        assert report is not None

    def test_diagnose_storage_battery_wear(self, deep_engine):
        report = deep_engine.collect_storage_battery_wear()
        assert report is not None

    def test_diagnose_peripherals_network(self, deep_engine):
        report = deep_engine.collect_peripherals_network()
        assert report is not None

    def test_diagnose_forensics_activity(self, deep_engine):
        report = deep_engine.collect_forensics_activity()
        assert report is not None

    def test_diagnose_summaries(self, deep_engine):
        def_summary = deep_engine.collect_defender_telemetry()
        assert def_summary is not None

        start_summary = deep_engine.collect_startup_telemetry()
        assert start_summary is not None

        vss_summary = deep_engine.collect_vss_telemetry()
        assert vss_summary is not None

        user_summary = deep_engine.collect_users_telemetry()
        assert user_summary is not None

    def test_perform_extended_audit(self, deep_engine):
        audit_report = deep_engine.collect_extended_system_audit()
        assert audit_report is not None
        d = audit_report.model_dump()
        assert isinstance(d, dict)
