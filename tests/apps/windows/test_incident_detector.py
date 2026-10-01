# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Incident Detector
# =============================================================================
# Description:
#   Тесты детекции аномалий и захвата инцидентов.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_incident_detector import test_incident_detector_cpu_spike
#
#     res = test_incident_detector_cpu_spike()
#
# File: test_incident_detector.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты детекции аномалий и захвата инцидентов."""

import time
import pytest
from apps.windows.telemetry.incident_detector import IncidentDetector
from apps.windows.telemetry.ring_buffer import TelemetryRingBuffer


def test_incident_detector_cpu_spike():
    """Проверяет срабатывание триггера CPU spike и связывание кольцевого буфера."""
    rb = TelemetryRingBuffer(capacity=50)
    for i in range(10):
        rb.append({"sample_id": i, "cpu_percent": 10.0}, epoch_timestamp=time.time() - (10 - i))

    detector = IncidentDetector(cpu_threshold=85.0, ring_buffer=rb)

    # Нормальный срез
    inc1 = detector.check_anomaly({"cpu_total_percent": 30.0})
    assert inc1 is None

    # Всплеск нагрузки
    inc2 = detector.check_anomaly(
        {"cpu_total_percent": 96.0, "disk_write_bytes_sec": 0.0},
        processes=[{"name": "heavy.exe", "pid": 777, "cpu_percent": 95.0, "path": "C:\\Program Files\\Heavy\\heavy.exe"}],
    )
    assert inc2 is not None
    assert inc2.trigger_type == "cpu_spike"
    assert inc2.severity == "critical"
    assert len(inc2.suspect_processes) > 0
    assert len(inc2.raw_window) == 10

    # Проверка экспорта в Markdown для AI-диагностики
    md = IncidentDetector.format_incident_markdown_for_llm(inc2)
    assert "ДИАГНОСТИЧЕСКИЙ ИНЦИДЕНТ" in md
    assert "heavy.exe" in md


def test_incident_detector_suspicious_process_location():
    """Проверяет детектирование процессов, запущенных из Temp каталогов."""
    detector = IncidentDetector()
    inc = detector.check_anomaly(
        {"cpu_total_percent": 40.0},
        processes=[
            {
                "name": "updater_svchost.exe",
                "pid": 8812,
                "cpu_percent": 35.0,
                "path": "C:\\Users\\user\\AppData\\Local\\Temp\\updater_svchost.exe",
            }
        ],
    )
    assert inc is not None
    assert inc.trigger_type == "suspicious_process"
    assert "updater_svchost.exe" in inc.title
    assert inc.suspect_processes[0]["pid"] == 8812
