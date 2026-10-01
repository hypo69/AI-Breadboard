# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Network Usage
# =============================================================================
# Description:
#   Тесты для модуля многоуровневой сетевой телеметрии и использования сети.
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_network_usage import test_iphelper_adapter_statistics
#
#     res = test_iphelper_adapter_statistics()
#
# File: test_network_usage.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для модуля многоуровневой сетевой телеметрии и использования сети."""

import pytest
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.network.network_usage import WindowsNetworkUsageCollector
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.models import (
    AppNetworkUsageItem,
    NetworkAdapterStatistics,
    NetworkPerformanceCounter,
    NetworkUsagePeriodReport,
)

def test_iphelper_adapter_statistics():
    """Тест получения нативной статистики сетевых адаптеров через IPHelperAPI."""
    api = IPHelperAPI()
    stats = api.get_adapter_statistics()
    assert isinstance(stats, list)
    if stats:
        first = stats[0]
        assert 'name' in first
        assert 'received_bytes' in first
        assert 'sent_bytes' in first

def test_network_usage_collector_adapters():
    """Тест работы коллектора статистики адаптеров."""
    collector = WindowsNetworkUsageCollector()
    stats = collector.get_adapter_statistics()
    assert isinstance(stats, list)
    for item in stats:
        assert isinstance(item, NetworkAdapterStatistics)
        assert item.name is not None
        assert item.received_bytes >= 0
        assert item.sent_bytes >= 0

def test_network_usage_collector_performance_counters():
    """Тест получения Performance Counters по интерфейсам."""
    collector = WindowsNetworkUsageCollector()
    counters = collector.get_performance_counters()
    assert isinstance(counters, list)
    for c in counters:
        assert isinstance(c, NetworkPerformanceCounter)
        assert c.interface_name is not None

def test_network_usage_collector_app_usage():
    """Тест атрибуции сетевого трафика по приложениям и процессам."""
    collector = WindowsNetworkUsageCollector()
    apps = collector.get_app_network_usage(top_limit=5)
    assert isinstance(apps, list)
    for app in apps:
        assert isinstance(app, AppNetworkUsageItem)
        assert app.process_name is not None
        assert app.total_bytes >= 0

def test_network_usage_period_summary():
    """Тест формирования итогового сводного отчета потребления сети за период."""
    collector = WindowsNetworkUsageCollector()
    report = collector.get_traffic_period_summary(period_minutes=1440)
    assert isinstance(report, NetworkUsagePeriodReport)
    assert report.period_minutes == 1440
    assert report.total_rx_bytes >= 0
    assert report.total_tx_bytes >= 0
    assert isinstance(report.summary_text, str)
    assert 'За период' in report.summary_text

def test_system_collector_network_integration():
    """Тест интеграции новой сетевой телеметрии в SystemCollector."""
    collector = SystemCollector()
    metrics = collector.get_network_metrics()
    assert isinstance(metrics, list)
    if metrics:
        first = metrics[0]
        assert first.name is not None

    report = collector.get_network_usage_report(period_minutes=60)
    assert isinstance(report, NetworkUsagePeriodReport)
    assert report.period_minutes == 60

