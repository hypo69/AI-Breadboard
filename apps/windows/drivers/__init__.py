# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Drivers -   Init  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.drivers.__init__ import VendorType
#
#     service = VendorType()
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.drivers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger


class VendorType(str, Enum):
    """Тип производителя графического ускорителя."""
    NVIDIA = 'NVIDIA'
    AMD = 'AMD'
    INTEL = 'INTEL'
    UNKNOWN = 'UNKNOWN'


class DriverBranch(str, Enum):
    """Ветка драйвера."""
    GAME_READY = 'GAME_READY'
    STUDIO = 'STUDIO'
    PRO = 'PRO'
    STANDARD = 'STANDARD'


@dataclass
class DriverRelease:
    """Информация о релизе драйвера."""
    version: str
    vendor: VendorType
    branch: DriverBranch = DriverBranch.STANDARD
    release_date: str = ''
    download_url: str = ''
    notes: str = ''


class GpuHardwareDetector:
    """Детектор графических адаптеров и форматирования версий WMI."""

    def format_driver_version(self, raw_version: str, vendor: VendorType) -> str:
        """Форматирование версии драйвера из формата WMI в официальный вид.

        Args:
            raw_version: Сырая строка версии из WMI/SetupAPI (например '32.0.15.6094').
            vendor: Производитель GPU.

        Returns:
            Отформатированная строка версии (например '560.94').
        """
        if not raw_version:
            return ''
        parts = raw_version.split('.')
        if vendor == VendorType.NVIDIA:
            # NVIDIA WMI format: X.Y.Z.ABCD -> ABCD formatted as ABC.D or last 5 digits
            if len(parts) >= 4:
                last_two = parts[-2] + parts[-1]
                if len(last_two) >= 5:
                    sub = last_two[-5:]
                    return f"{int(sub[:3])}.{sub[3:]}"
            return raw_version
        elif vendor == VendorType.AMD:
            # AMD WMI format: 31.0.24033.1003 -> 24.3.1
            if len(parts) >= 3 and len(parts[2]) >= 3:
                year = parts[2][:2]
                month = str(int(parts[2][2:4])) if len(parts[2]) >= 4 else '1'
                rev = parts[3][0] if len(parts) >= 4 and parts[3] else '1'
                return f"{year}.{month}.{rev}"
            return raw_version
        return raw_version


class NvidiaCatalogManager:
    """Каталог драйверов NVIDIA."""

    def __init__(self) -> None:
        self._releases: List[DriverRelease] = [
            DriverRelease(
                version='560.94',
                vendor=VendorType.NVIDIA,
                branch=DriverBranch.GAME_READY,
                release_date='2024-08-20',
                download_url='https://us.download.nvidia.com/Windows/560.94/560.94-desktop-win10-win11-64bit-international-dch-whql.exe'
            ),
            DriverRelease(
                version='560.81',
                vendor=VendorType.NVIDIA,
                branch=DriverBranch.GAME_READY,
                release_date='2024-08-06',
            ),
            DriverRelease(
                version='560.70',
                vendor=VendorType.NVIDIA,
                branch=DriverBranch.STUDIO,
                release_date='2024-07-16',
            ),
        ]

    def get_releases(self, branch: Optional[DriverBranch] = None) -> List[DriverRelease]:
        """Получение списка релизов по ветке."""
        if branch is None:
            return list(self._releases)
        return [r for r in self._releases if r.branch == branch]

    def find_release_by_version(self, version: str) -> Optional[DriverRelease]:
        """Поиск релиза по номеру версии."""
        for r in self._releases:
            if r.version == version:
                return r
        return None


class AmdCatalogManager:
    """Каталог драйверов AMD."""

    def __init__(self) -> None:
        self._releases: List[DriverRelease] = [
            DriverRelease(
                version='24.12.1',
                vendor=VendorType.AMD,
                branch=DriverBranch.STANDARD,
                release_date='2024-12-05'
            ),
            DriverRelease(
                version='24.8.1',
                vendor=VendorType.AMD,
                branch=DriverBranch.STANDARD,
                release_date='2024-08-29'
            ),
            DriverRelease(
                version='24.3.1',
                vendor=VendorType.AMD,
                branch=DriverBranch.STANDARD,
                release_date='2024-03-20'
            ),
        ]

    def get_latest_release(self) -> Optional[DriverRelease]:
        """Получение последней доступной версии."""
        return self._releases[0] if self._releases else None

    def compare_versions(self, v1: str, v2: str) -> int:
        """Сравнение версий драйверов (-1 если v1 < v2, 0 если v1 == v2, 1 если v1 > v2)."""
        p1 = [int(x) for x in v1.split('.') if x.isdigit()]
        p2 = [int(x) for x in v2.split('.') if x.isdigit()]
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
        return 0


class DriverDownloader:
    """Менеджер загрузки и отслеживания файлов драйверов."""

    def __init__(self, download_dir: Optional[Path] = None) -> None:
        self._download_dir = download_dir or Path.home() / 'Downloads' / 'Drivers'
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, Any] = {}

    def get_download_dir(self) -> Path:
        """Получение пути к каталогу загрузки."""
        return self._download_dir

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Список текущих задач загрузки."""
        return list(self._tasks.values())


__all__ = [
    'VendorType',
    'DriverBranch',
    'DriverRelease',
    'GpuHardwareDetector',
    'NvidiaCatalogManager',
    'AmdCatalogManager',
    'DriverDownloader',
]
