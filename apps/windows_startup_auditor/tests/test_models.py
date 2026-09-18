# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Windows Startup Auditor Models
# =============================================================================
# Description:
#   Модульные тесты для DTO и Pydantic-моделей данных приложения
#   Windows Startup Auditor.
#
# Examples:
#   $ pytest apps/windows_startup_auditor/tests/test_models.py -v
#
# File: test_models.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты моделей данных Startup Auditor."""

from apps.windows_startup_auditor.core.models import (
    AuditReport,
    AuditSummary,
    ItemCategory,
    LocationInfo,
    RiskLevel,
    StartupEntry,
    StartupLocationType,
    ToggleRequest,
    ToggleResponse,
)


def test_startup_entry_defaults() -> None:
    """Проверка значений по умолчанию модели StartupEntry."""
    entry = StartupEntry(
        id="test_entry_1",
        name="TestApp",
        executable_path=r"C:\Program Files\Test\app.exe",
    )
    assert entry.id == "test_entry_1"
    assert entry.name == "TestApp"
    assert entry.location_type == StartupLocationType.OTHER
    assert entry.risk_level == RiskLevel.CLEAN
    assert entry.is_enabled is True
    assert entry.file_exists is True


def test_audit_summary_and_report_serialization() -> None:
    """Проверка сериализации AuditSummary и AuditReport."""
    summary = AuditSummary(
        total_entries=10,
        active_entries=8,
        disabled_entries=2,
        broken_entries=1,
        clean_count=6,
        notice_count=2,
        warning_count=1,
        suspicious_count=1,
        critical_count=0,
        health_score=85,
    )
    assert summary.total_entries == 10
    assert summary.health_score == 85

    report = AuditReport(
        timestamp="2026-09-16T22:00:00",
        hostname="TEST-PC",
        os_name="Windows 11 Pro",
        scan_duration_ms=45.2,
        summary=summary,
        entries=[],
        security_alerts=[],
        broken_items=[],
        recommendations=["Очистить битые записи"],
    )
    data = report.model_dump()
    assert data["hostname"] == "TEST-PC"
    assert data["summary"]["health_score"] == 85
    assert len(data["recommendations"]) == 1


def test_toggle_models() -> None:
    """Проверка моделей запроса и ответа переключения состояния."""
    req = ToggleRequest(entry_id="reg_run_1", enable=False)
    assert req.entry_id == "reg_run_1"
    assert req.enable is False

    res = ToggleResponse(
        success=True,
        entry_id="reg_run_1",
        new_state=False,
        message="Элемент успешно отключен",
    )
    assert res.success is True
    assert res.new_state is False
