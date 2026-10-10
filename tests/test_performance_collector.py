# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Performance Collector
# =============================================================================
# Description:
#   Тест регистрации сенсоров производительности.
#
# Usage Examples:
#   Python API:
#     from tests.test_performance_collector import test_performance_collector_sensors
#
#     res = test_performance_collector_sensors()
#
# File: test_performance_collector.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тест регистрации сенсоров производительности."""

import pytest
from unittest.mock import patch
from apps.windows.sdk.core.models import DomainAuditResult
from apps.windows.sdk.core.audits.performance_collector import PerformanceCollector

def test_performance_collector_sensors():
    """Тест регистрации сенсоров производительности."""
    collector = PerformanceCollector()
    mock_result = DomainAuditResult(domain_name='performance', title_ru='Производительность', status='ok', findings=[], metrics={'cpu_percent': 10.5, 'memory_percent': 20.0, 'uptime_hours': 1.5}, scan_duration_ms=10.0)
    with patch.object(collector, 'collect', side_effect=lambda: setattr(collector, '_last_result', mock_result) or mock_result):
        collector.collect()
        sensors = collector.get_sensors()
        sensor_ids = [s.sensor_id for s in sensors]
        assert 'perf_cpu_percent' in sensor_ids
        assert 'perf_memory_percent' in sensor_ids
        assert 'perf_uptime_hours' in sensor_ids
        for s in sensors:
            if s.sensor_id == 'perf_cpu_percent':
                assert s.value == 10.5