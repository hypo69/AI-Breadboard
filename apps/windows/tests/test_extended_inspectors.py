# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Extended Inspectors
# =============================================================================
# Description:
#   Тестирование расширенных инспекторов Windows (SRUM, WSL2, Sandbox).
#
# File: test_extended_inspectors.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:05:00
# =============================================================================

"""Модульные тесты для подсистем SRUM, WSL2 и Windows Sandbox."""

import pytest
from apps.windows.sdk.modules.extended_inspectors import (
    SRUMPowerAnalytics,
    WSL2HyperVInspector,
    WindowsSandboxInspector,
)


def test_srum_power_analytics():
    """Проверяет работу модуля SRUMPowerAnalytics."""
    analytics = SRUMPowerAnalytics()
    summary = analytics.analyze_power_and_resource_usage()
    
    assert hasattr(summary, 'srum_db_found')
    assert hasattr(summary, 'sleep_blockers')
    assert isinstance(summary.power_plan, str)
    assert isinstance(summary.to_dict(), dict)


def test_wsl2_hyperv_inspector(tmp_path):
    """Проверяет работу модуля WSL2HyperVInspector."""
    inspector = WSL2HyperVInspector()
    report = inspector.inspect_vhdx_disks(custom_dirs=[tmp_path])
    
    assert hasattr(report, 'total_disks')
    assert hasattr(report, 'total_size_gb')
    assert isinstance(report.to_dict(), dict)


def test_windows_sandbox_inspector(tmp_path):
    """Проверяет генерацию .wsb конфигураций в WindowsSandboxInspector."""
    inspector = WindowsSandboxInspector()
    dummy_bin = tmp_path / "test_app.exe"
    dummy_bin.write_text("dummy binary content", encoding="utf-8")
    
    wsb_path = inspector.generate_wsb_config(str(dummy_bin))
    assert wsb_path.endswith(".wsb")
    
    res = inspector.launch_in_sandbox(str(dummy_bin))
    assert hasattr(res, 'sandbox_available')
    assert hasattr(res, 'launched')
    assert isinstance(res.to_dict(), dict)
