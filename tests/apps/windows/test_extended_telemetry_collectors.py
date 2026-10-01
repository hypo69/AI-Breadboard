# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Extended Telemetry Collectors
# =============================================================================
# Description:
#   Тесты расширенных коллекторов телеметрии (Defender, Startup, VSS, Users).
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_extended_telemetry_collectors import test_defender_telemetry_collector
#
#     res = test_defender_telemetry_collector()
#
# File: test_extended_telemetry_collectors.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты расширенных коллекторов телеметрии (Defender, Startup, VSS, Users)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from apps.windows.telemetry.models import (
    DefenderTelemetrySummary,
    ExtendedSystemAuditReport,
    StartupTelemetrySummary,
    UserAccountsTelemetrySummary,
    VssTelemetrySummary,
)
from apps.windows.telemetry.deep_diagnostics import DeepDiagnosticsEngine
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.sqlite import TelemetryStorage


def test_defender_telemetry_collector() -> None:
    """Тестирование сборщика телеметрии Windows Defender."""
    engine = DeepDiagnosticsEngine()
    summary = engine.collect_defender_telemetry()
    assert isinstance(summary, DefenderTelemetrySummary)
    assert isinstance(summary.cfa_enabled, bool)
    assert isinstance(summary.path_exclusions, list)
    assert isinstance(summary.active_threats_count, int)


def test_startup_telemetry_collector() -> None:
    """Тестирование сборщика телеметрии точек автозапуска."""
    engine = DeepDiagnosticsEngine()
    summary = engine.collect_startup_telemetry()
    assert isinstance(summary, StartupTelemetrySummary)
    assert isinstance(summary.total_entries, int)
    assert isinstance(summary.entries, list)


def test_vss_telemetry_collector() -> None:
    """Тестирование сборщика состояния теневых копий VSS."""
    engine = DeepDiagnosticsEngine()
    summary = engine.collect_vss_telemetry()
    assert isinstance(summary, VssTelemetrySummary)
    assert isinstance(summary.total_snapshots_count, int)
    assert isinstance(summary.snapshots, list)


def test_users_telemetry_collector() -> None:
    """Тестирование сборщика локальных пользователей."""
    engine = DeepDiagnosticsEngine()
    summary = engine.collect_users_telemetry()
    assert isinstance(summary, UserAccountsTelemetrySummary)
    assert isinstance(summary.total_users_count, int)
    assert isinstance(summary.users, list)
    assert isinstance(summary.admin_usernames, list)


def test_extended_system_audit_report() -> None:
    """Тестирование формирования комплексного расширенного аудита."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_extended_system_audit()
    assert isinstance(report, ExtendedSystemAuditReport)
    assert report.hostname != ""
    assert isinstance(report.defender, DefenderTelemetrySummary)
    assert isinstance(report.startup, StartupTelemetrySummary)
    assert isinstance(report.vss, VssTelemetrySummary)
    assert isinstance(report.users, UserAccountsTelemetrySummary)


def test_storage_extended_audits(tmp_path: Path) -> None:
    """Тестирование сохранения и извлечения расширенных аудитов в TelemetryStorage."""
    db_file = tmp_path / "extended_audit_test.db"
    storage = TelemetryStorage(db_path=db_file)

    report = ExtendedSystemAuditReport(
        hostname="TEST-NODE",
        defender=DefenderTelemetrySummary(cfa_enabled=True, exclusions_count=2, active_threats_count=0),
        startup=StartupTelemetrySummary(total_entries=5, registry_run_count=3),
        vss=VssTelemetrySummary(total_snapshots_count=1, protected_volumes=["C:"]),
        users=UserAccountsTelemetrySummary(total_users_count=3, admin_users_count=1, admin_usernames=["Admin"]),
    )

    row_id = storage.save_extended_audit(report)
    assert row_id > 0

    latest = storage.get_latest_extended_audit()
    assert latest is not None
    assert latest["hostname"] == "TEST-NODE"
    assert latest["defender_cfa_enabled"] == 1
    assert latest["startup_entries_count"] == 5
    assert latest["vss_snapshots_count"] == 1
    assert latest["users_total_count"] == 3
    assert latest["users_admin_count"] == 1
    assert "data" in latest
    assert latest["data"]["defender"]["cfa_enabled"] is True

    history = storage.get_extended_audits(limit=10)
    assert len(history) == 1


def test_collector_extended_audit_integration(tmp_path: Path) -> None:
    """Тестирование вызова расширенного аудита через SystemCollector."""
    db_file = tmp_path / "collector_audit_test.db"
    storage = TelemetryStorage(db_path=db_file)
    collector = SystemCollector(storage=storage)

    report = collector.get_extended_system_audit()
    assert isinstance(report, ExtendedSystemAuditReport)

    latest = collector.get_latest_extended_audit()
    assert latest is not None
    assert "data" in latest
