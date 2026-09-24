# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Storage Sensor Package
# =============================================================================
# Description:
#   Пакет сенсоров дисковой подсистемы Windows. Предоставляет нативные
#   инструменты сбора информации о накопителях, счетчиках надежности и
#   событиях дисковой подсистемы без необходимости установки сторонних утилит.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.storage_sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет нативных сенсоров дисков Windows."""

from apps.windows.storage_sensors.windows_storage_sensor import (
    StorageDiskHealthInfo,
    WindowsStorageSensor,
    collect_storage_snapshot,
    save_snapshot,
)

__all__ = [
    "StorageDiskHealthInfo",
    "WindowsStorageSensor",
    "collect_storage_snapshot",
    "save_snapshot",
]
