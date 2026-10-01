# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Storage Incidents
# =============================================================================
# Description:
#   Тесты персистентного хранения инцидентов и rollups в SQLite.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_storage_incidents import test_storage_incidents_and_rollups_lifecycle
#
#     res = test_storage_incidents_and_rollups_lifecycle()
#
# File: test_telemetry_storage_incidents.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты персистентного хранения инцидентов и rollups в SQLite."""

from pathlib import Path
import pytest
from apps.windows.telemetry.models import SystemMetricRollup, TelemetryIncident
from apps.windows.telemetry.sqlite import TelemetryStorage


def test_storage_incidents_and_rollups_lifecycle(tmp_path: Path):
    """Проверяет сохранение, извлечение и статистику инцидентов и rollups."""
    db_path = tmp_path / "test_telemetry.db"
    storage = TelemetryStorage(db_path=db_path, buffer_mode="direct", auto_flush=False)

    # 1. Сохранение инцидента
    incident = TelemetryIncident(
        incident_id="INC-20261001-TEST",
        trigger_type="cpu_spike",
        severity="critical",
        title="Тестовый всплеск CPU",
        description="Нагрузка 99%",
        trigger_metrics={"cpu_percent": 99.0},
        suspect_processes=[{"name": "miner.exe", "pid": 1234, "cpu_percent": 95.0}],
        raw_window=[{"ts": 1000.0, "cpu": 99.0}],
    )
    saved = storage.save_incident(incident)
    assert saved is True

    # Извлечение инцидента
    incidents = storage.get_incidents(limit=10)
    assert len(incidents) == 1
    assert incidents[0]["incident_id"] == "INC-20261001-TEST"
    assert incidents[0]["suspect_processes"][0]["name"] == "miner.exe"

    # 2. Сохранение rollup
    rollup = SystemMetricRollup(
        period_start="2026-10-01T10:00:00+00:00",
        period_end="2026-10-01T10:01:00+00:00",
        duration_seconds=60.0,
        sample_count=60,
        tier="1m",
        cpu_avg=25.0,
        cpu_max=99.0,
        cpu_p95=80.0,
        disk_write_total_mb=120.0,
    )
    saved_rollup = storage.save_system_rollup(rollup)
    assert saved_rollup is True

    # Извлечение rollups
    rollups = storage.get_system_rollups(tier="1m")
    assert len(rollups) == 1
    assert rollups[0]["cpu_max"] == 99.0
    assert rollups[0]["cpu_p95"] == 80.0

    # 3. Проверка статистики
    stats = storage.get_storage_stats()
    assert stats["incidents_count"] == 1
    assert stats["telemetry_rollups_count"] == 1
