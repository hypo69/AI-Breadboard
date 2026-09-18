# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows Diagnostic Center Test Suite
# =============================================================================
# Description:
#   Тесты для проверки всех 15 коллекторов фактов, SafeOps исполнителя,
#   движка расследования первопричин и REST API роутера.
#
# File: test_ai_diagnostic_center.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тестовый набор для AI Windows Diagnostic & Administration Center."""

import pytest
from apps.windows.core.models import ActionType, RemediationAction, RiskLevel
from apps.windows.core.modules import (
    BaselineCollector,
    CleanCollector,
    DriverCollector,
    EventLogCollector,
    IntegrityCollector,
    NetworkCollector,
    PerformanceCollector,
    PostInstallCollector,
    ProcessCollector,
    SecurityCollector,
    ServicesCollector,
    SoftwareCollector,
    StorageCollector,
    TasksCollector,
    UpdateCollector,
)
from apps.windows.core.root_cause_engine import RootCauseEngine
from apps.windows.core.safe_executor import SafeExecutor
from apps.windows.router import init_router


def test_clean_collector():
    """Тест коллектора очистки."""
    collector = CleanCollector()
    res = collector.collect()
    assert res.domain_name == "clean"
    assert "total_cleanable_bytes" in res.metrics


def test_performance_collector():
    """Тест коллектора производительности."""
    collector = PerformanceCollector()
    res = collector.collect()
    assert res.domain_name == "performance"
    assert "cpu_percent" in res.metrics
    assert "memory_percent" in res.metrics


def test_driver_collector():
    """Тест коллектора драйверов."""
    collector = DriverCollector()
    res = collector.collect()
    assert res.domain_name == "drivers"
    assert "problem_devices_count" in res.metrics


def test_software_collector():
    """Тест коллектора программ."""
    collector = SoftwareCollector()
    res = collector.collect()
    assert res.domain_name == "software"
    assert "total_apps_count" in res.metrics


def test_integrity_collector():
    """Тест коллектора целостности."""
    collector = IntegrityCollector()
    res = collector.collect()
    assert res.domain_name == "integrity"
    assert "pending_reboot" in res.metrics


def test_storage_collector():
    """Тест коллектора дисков."""
    collector = StorageCollector()
    res = collector.collect()
    assert res.domain_name == "storage"
    assert "volumes" in res.metrics


def test_security_collector():
    """Тест коллектора безопасности."""
    collector = SecurityCollector()
    res = collector.collect()
    assert res.domain_name == "security"
    assert "uac_enabled" in res.metrics


def test_eventlog_collector():
    """Тест коллектора журналов событий."""
    collector = EventLogCollector()
    res = collector.collect(hours=1)
    assert res.domain_name == "eventlog"
    assert "total_events" in res.metrics


def test_process_collector():
    """Тест коллектора процессов."""
    collector = ProcessCollector()
    res = collector.collect()
    assert res.domain_name == "processes"
    assert "total_processes_count" in res.metrics


def test_services_collector():
    """Тест коллектора служб."""
    collector = ServicesCollector()
    res = collector.collect()
    assert res.domain_name == "services"
    assert "total_services_count" in res.metrics


def test_tasks_collector():
    """Тест коллектора задач планировщика."""
    collector = TasksCollector()
    res = collector.collect()
    assert res.domain_name == "tasks"
    assert "total_tasks_count" in res.metrics


def test_network_collector():
    """Тест коллектора сети."""
    collector = NetworkCollector()
    res = collector.collect()
    assert res.domain_name == "network"
    assert "listening_ports_count" in res.metrics


def test_update_collector():
    """Тест коллектора обновлений."""
    collector = UpdateCollector()
    res = collector.collect()
    assert res.domain_name == "updates"
    assert "installed_kb_count" in res.metrics


def test_baseline_collector():
    """Тест коллектора базовой линии."""
    collector = BaselineCollector()
    res = collector.collect()
    assert res.domain_name == "baseline"


def test_postinstall_collector():
    """Тест коллектора пост-установки."""
    collector = PostInstallCollector()
    res = collector.collect()
    assert res.domain_name == "postinstall"
    assert "checklist" in res.metrics


def test_safe_executor_dry_run():
    """Тест симуляции SafeOps (Dry-Run)."""
    executor = SafeExecutor()
    action = RemediationAction(
        action_id="test_act",
        action_type=ActionType.CLEAN_DIRECTORY,
        title="Тестовая очистка",
        description="Тест",
        target="C:/Windows/Temp",
        risk=RiskLevel.SAFE,
    )
    sim = executor.simulate(action)
    assert sim["simulated"] is True
    assert sim["action_id"] == "test_act"


def test_safe_executor_requires_confirmation():
    """Тест блокировки критического действия без явного подтверждения."""
    executor = SafeExecutor()
    action = RemediationAction(
        action_id="crit_act",
        action_type=ActionType.DISABLE_SERVICE,
        title="Критическое действие",
        description="Тест",
        target="Spooler",
        risk=RiskLevel.CRITICAL,
    )
    result = executor.execute(action, confirmed_by_user=False)
    assert result.executed is False
    assert "требует явного подтверждения" in (result.error_message or "")


def test_root_cause_engine_investigate():
    """Тест движка расследования первопричины по симптому."""
    engine = RootCauseEngine()
    rep = engine.investigate("Компьютер сильно тормозит из-за нагрузки на процессор")
    assert rep.symptom == "Компьютер сильно тормозит из-за нагрузки на процессор"
    assert rep.confidence_score > 0.0
    assert rep.probable_root_cause


def test_router_initialization():
    """Тест инициализации FastAPI роутера."""
    r = init_router()
    routes = [route.path for route in r.routes]
    assert "/api/windows/health" in routes
    assert "/api/windows/audit/full" in routes
    assert "/api/windows/investigate" in routes
    assert "/api/windows/software" in routes
    assert "/api/windows/software/audit" in routes

