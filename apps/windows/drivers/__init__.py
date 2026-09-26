# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU Driver Manager Module
# =============================================================================
# Description:
#   Пакет управления графическими адаптерами, каталогами версий NVIDIA и AMD,
#   проверкой обновлений драйверов и фоновой загрузкой пакетов установки.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.drivers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет управления видеодрайверами GPU для Windows."""

from apps.windows.drivers.models import (
    DriverBranch,
    DriverRelease,
    DownloadProgress,
    GpuDevice,
    GpuUpdateCheck,
    TaskStatus,
    VendorType,
)
from apps.windows.drivers.hardware_detector import GpuHardwareDetector
from apps.windows.drivers.nvidia_catalog import NvidiaCatalogManager
from apps.windows.drivers.amd_catalog import AmdCatalogManager
from apps.windows.drivers.driver_downloader import DriverDownloader

__all__ = [
    "DriverBranch",
    "DriverRelease",
    "DownloadProgress",
    "GpuDevice",
    "GpuUpdateCheck",
    "TaskStatus",
    "VendorType",
    "GpuHardwareDetector",
    "NvidiaCatalogManager",
    "AmdCatalogManager",
    "DriverDownloader",
]
