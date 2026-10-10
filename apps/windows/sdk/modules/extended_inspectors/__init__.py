# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Extended Inspectors Init
# =============================================================================
# Description:
#   Инициализация пакета расширенных инспекторов Windows (SRUM, WSL2/Hyper-V, Sandbox).
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.extended_inspectors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:04:00
# =============================================================================

from __future__ import annotations

"""Пакет расширенных аналитических инспекторов Windows."""

from .srum_power_analytics import SRUMPowerAnalytics, SRUMUsageSummary
from .wsl2_hyperv_inspector import WSL2HyperVInspector, WSL2InspectionReport
from .windows_sandbox_inspector import WindowsSandboxInspector, SandboxLaunchResult

__all__ = [
    'SRUMPowerAnalytics',
    'SRUMUsageSummary',
    'WSL2HyperVInspector',
    'WSL2InspectionReport',
    'WindowsSandboxInspector',
    'SandboxLaunchResult',
]
