# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage Manager Core - Init
# =============================================================================
# Description:
#   Экспорт базовых компонентов, сенсоров и сервиса бенчмарка модуля storage_manager.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core import StorageBenchmarkService, WindowsStorageSensor
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 08:16:00
# =============================================================================

"""Экспорт базовых компонентов, сенсоров и сервиса бенчмарка модуля storage_manager."""

from .benchmark import DEFAULT_CDM_PROFILES, StorageBenchmarkService
from .benchmark_sensor import (
    StorageBenchmarkSensor,
    get_storage_benchmark_sensor,
    run_quick_storage_benchmark,
)
from .manager import StorageManager
from .models import (
    BenchmarkHistoryItem,
    BenchmarkProfileResult,
    BenchmarkRequest,
    BenchmarkSuiteResult,
    BenchmarkTargetInfo,
    DiskInfo,
    DiskOperationRequest,
    FsFeaturesInfo,
    PartitionInfo,
    StorageReport,
    VolumeInfo,
)
from .windows_storage_sensor import (
    StorageDiskHealthInfo,
    WindowsStorageSensor,
    collect_storage_snapshot,
    save_snapshot,
)

__all__ = [
    'StorageManager',
    'StorageBenchmarkService',
    'StorageBenchmarkSensor',
    'get_storage_benchmark_sensor',
    'run_quick_storage_benchmark',
    'DEFAULT_CDM_PROFILES',
    'DiskInfo',
    'PartitionInfo',
    'VolumeInfo',
    'FsFeaturesInfo',
    'StorageReport',
    'DiskOperationRequest',
    'BenchmarkTargetInfo',
    'BenchmarkRequest',
    'BenchmarkProfileResult',
    'BenchmarkSuiteResult',
    'BenchmarkHistoryItem',
    'StorageDiskHealthInfo',
    'WindowsStorageSensor',
    'collect_storage_snapshot',
    'save_snapshot',
]
