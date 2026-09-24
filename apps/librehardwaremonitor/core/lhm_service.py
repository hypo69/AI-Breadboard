# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Standalone Service (Alias / Re-export)
# =============================================================================
# Description:
#   Реэкспорт сервиса взаимодействия с LibreHardwareMonitor из стека
#   apps.windows.hardware.lhm_service для обратной совместимости.
#
# File: lhm_service.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Реэкспорт сервиса LibreHardwareMonitor из apps.windows.hardware."""

from __future__ import annotations

from apps.windows.hardware.lhm_service import (
    DEFAULT_ENDPOINT,
    LhmService,
    parse_sensor_value,
)

__all__ = [
    "DEFAULT_ENDPOINT",
    "LhmService",
    "parse_sensor_value",
]
