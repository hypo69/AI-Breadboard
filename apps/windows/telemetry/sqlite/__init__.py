# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sqlite Package
# =============================================================================
# Description:
#   Пакет персистентного хранения и выборки системной телеметрии в SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite import TelemetryStorage, TelemetryReader
#
#     storage = TelemetryStorage.get_instance(read_only=True)
#     cpu = storage.get_latest_cpu()
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 00:20:00
# =============================================================================

from __future__ import annotations

"""Пакет персистентного хранения, буферизации и выборки системной телеметрии в SQLite."""

from .aggregator import AggregationLevel, TelemetrySqlAggregator, sensors_aggregate
from .buffer import TelemetryBuffer
from .connection import TelemetryConnectionManager
from .maintenance import TelemetryMaintenance
from .reader import TelemetryReader
from .schema import init_database_schema
from .storage import TelemetryStorage
from .writer import TelemetryWriter

SQLiteTelemetryStorage = TelemetryStorage

__all__ = [
    'TelemetryStorage',
    'SQLiteTelemetryStorage',
    'TelemetryReader',
    'TelemetryWriter',
    'TelemetryBuffer',
    'TelemetryMaintenance',
    'TelemetryConnectionManager',
    'TelemetrySqlAggregator',
    'AggregationLevel',
    'sensors_aggregate',
    'init_database_schema',
]

