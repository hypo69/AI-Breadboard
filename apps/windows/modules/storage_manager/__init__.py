# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager - Init
# =============================================================================
# Description:
#   Менеджер накопителей Windows (Storage Manager) и бенчмарк DiskSpd.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager import StorageBenchmarkService, StorageManager
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 08:16:00
# =============================================================================

"""Менеджер накопителей Windows (Storage Manager) и бенчмарк DiskSpd."""

from apps.windows.modules.storage_manager.core.benchmark import (
    DEFAULT_CDM_PROFILES,
    StorageBenchmarkService,
)
from apps.windows.modules.storage_manager.core.benchmark_sensor import (
    StorageBenchmarkSensor,
    get_storage_benchmark_sensor,
    run_quick_storage_benchmark,
)
from apps.windows.modules.storage_manager.core.manager import StorageManager
from apps.windows.modules.storage_manager.core.models import (
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
from apps.windows.modules.storage_manager.core.windows_storage_sensor import (
    StorageDiskHealthInfo,
    WindowsStorageSensor,
    collect_storage_snapshot,
    save_snapshot,
)
from apps.windows.modules.storage_manager.router import init_router
from apps.windows.modules.storage_manager.tui import StorageManagerTUI

__all__ = [
    'StorageManager',
    'StorageBenchmarkService',
    'DEFAULT_CDM_PROFILES',
    'StorageManagerTUI',
    'init_router',
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
