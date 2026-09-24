# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Deep System Diagnostics Unit Tests
# =============================================================================
# Description:
#   Тесты для модулей глубокой диагностики: утечки дескрипторов и GDI,
#   поведенческая форензика, троттлинг ядра, износ накопителей/батареи, периферия.
#
# File: test_deep_diagnostics.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты глубокой системной диагностики."""

from __future__ import annotations

import pytest

from apps.windows.telemetry import (
    DeepDiagnosticsEngine,
    ForensicsActivityReport,
    KernelThrottlingReport,
    PeripheralsNetworkReport,
    ProcessLeakDiagnosticsReport,
    StorageBatteryWearReport,
)


def test_deep_diagnostics_engine_init():
    """Тест инициализации движка глубокой диагностики."""
    engine = DeepDiagnosticsEngine()
    assert engine is not None


def test_collect_process_leaks():
    """Тест сбора утечек дескрипторов и ресурсов процессов."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_process_leaks(limit=20)
    assert isinstance(report, ProcessLeakDiagnosticsReport)
    assert report.total_processes >= 0
    assert isinstance(report.top_handle_hogs, list)
    assert isinstance(report.top_gdi_hogs, list)
    assert isinstance(report.top_page_fault_hogs, list)


def test_collect_forensics_activity():
    """Тест сбора поведенческой форензики и активного окна."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_forensics_activity()
    assert isinstance(report, ForensicsActivityReport)
    assert isinstance(report.foreground_window, dict)
    assert "title" in report.foreground_window
    assert report.user_idle_seconds >= 0.0
    assert isinstance(report.camera_active_apps, list)
    assert isinstance(report.microphone_active_apps, list)


def test_collect_kernel_throttling():
    """Тест сбора латентности DPC/ISR и троттлинга ядра."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_kernel_throttling()
    assert isinstance(report, KernelThrottlingReport)
    assert report.dpc_latency_pct >= 0.0
    assert report.interrupt_latency_pct >= 0.0
    assert report.dpc_status in ("optimal", "elevated", "severe")
    assert report.system_uptime_seconds >= 0.0


def test_collect_storage_battery_wear():
    """Тест сбора износа SSD и батареи."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_storage_battery_wear()
    assert isinstance(report, StorageBatteryWearReport)
    assert isinstance(report.disks_wear, list)
    assert isinstance(report.battery_wear, dict)
    assert "has_battery" in report.battery_wear


def test_collect_peripherals_network():
    """Тест сбора USB периферии и Wi-Fi."""
    engine = DeepDiagnosticsEngine()
    report = engine.collect_peripherals_network()
    assert isinstance(report, PeripheralsNetworkReport)
    assert isinstance(report.usb_devices, list)
    assert isinstance(report.wifi_telemetry, dict)
    assert isinstance(report.audio_endpoints, list)
