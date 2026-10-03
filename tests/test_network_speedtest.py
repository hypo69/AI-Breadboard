# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Network Speedtest (FAST.com / bufferbloat)
# =============================================================================
# File: test_network_speedtest.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 00:55:00
# =============================================================================

"""Тесты расчёта latency, bufferbloat и оценки качества движка NetworkSpeedTester."""

from apps.windows.modules.network.speedtest import NetworkSpeedTester


def test_latency_stats_empty() -> None:
    """Пустая выборка даёт нулевую статистику."""
    assert NetworkSpeedTester._latency_stats([])['count'] == 0


def test_latency_stats_values() -> None:
    """Медиана, min/max и jitter считаются корректно."""
    stats = NetworkSpeedTester._latency_stats([8.0, 10.0, 9.0])
    assert stats['median_ms'] == 9.0
    assert stats['min_ms'] == 8.0 and stats['max_ms'] == 10.0
    assert stats['jitter_ms'] == 1.5


def test_quality_downgraded_by_bufferbloat() -> None:
    """Высокий bufferbloat снижает оценку даже при отличной скорости."""
    tester = NetworkSpeedTester()
    assert tester._evaluate_quality(900, 100, 7, 5)['rating'] == 'A+'
    assert tester._evaluate_quality(900, 100, 7, 80)['rating'] == 'B'
    assert tester._evaluate_quality(900, 100, 7, 273)['rating'] == 'C'
