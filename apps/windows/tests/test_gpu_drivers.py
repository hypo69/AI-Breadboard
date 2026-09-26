# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU Drivers Integration Test Suite
# =============================================================================
# Description:
#   Модульные тесты для детектора GPU оборудования, каталогов версий NVIDIA/AMD
#   и менеджера загрузки драйверов.
#
# File: test_gpu_drivers.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для встроенного модуля управления драйверами apps.windows.drivers."""

import pytest
from pathlib import Path
from apps.windows.drivers import (
    GpuHardwareDetector,
    NvidiaCatalogManager,
    AmdCatalogManager,
    DriverDownloader,
    VendorType,
    DriverBranch,
)


def test_hardware_detector_version_formatting():
    """Проверить форматирование сырых версий WMI для NVIDIA и AMD."""
    detector = GpuHardwareDetector()

    # NVIDIA: WMI '32.0.15.6094' -> '560.94'
    nv_ver = detector.format_driver_version("32.0.15.6094", VendorType.NVIDIA)
    assert nv_ver == "560.94"

    # AMD: WMI '31.0.24033.1003' -> '24.3.1'
    amd_ver = detector.format_driver_version("31.0.24033.1003", VendorType.AMD)
    assert amd_ver == "24.3.1"


def test_nvidia_catalog_filtering():
    """Проверить фильтрацию релиза NVIDIA по ветке и поиск по версии."""
    catalog = NvidiaCatalogManager()
    grd_releases = catalog.get_releases(branch=DriverBranch.GAME_READY)
    assert len(grd_releases) > 0
    assert all(r.branch == DriverBranch.GAME_READY for r in grd_releases)

    release = catalog.find_release_by_version("560.94")
    assert release is not None
    assert release.version == "560.94"
    assert release.vendor == VendorType.NVIDIA


def test_amd_catalog_filtering():
    """Проверить получение последних версий и сравнение версий AMD."""
    catalog = AmdCatalogManager()
    latest = catalog.get_latest_release()
    assert latest is not None
    assert latest.vendor == VendorType.AMD

    cmp_res = catalog.compare_versions("24.8.1", "24.12.1")
    assert cmp_res == -1


def test_driver_downloader_initialization(tmp_path: Path):
    """Проверить инициализацию загрузчика и создание каталога загрузки."""
    downloader = DriverDownloader(download_dir=tmp_path)
    assert downloader.get_download_dir() == tmp_path
    assert len(downloader.list_tasks()) == 0
