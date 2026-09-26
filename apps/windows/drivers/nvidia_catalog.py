# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: NVIDIA GPU Driver Catalog Manager
# =============================================================================
# Description:
#   Каталог версий драйверов NVIDIA (Game Ready, Studio Driver, Enterprise WHQL),
#   получение официальных релизов, прямых ссылок на загрузку и Release Notes.
#
# File: nvidia_catalog.py
# Project: ai-breadboard
# Package: apps.windows.drivers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер каталога драйверов NVIDIA."""

from __future__ import annotations

import re
from typing import List, Optional

try:
    from src.logger import logger
except ImportError:
    from logger import logger

from apps.windows.drivers.models import DriverBranch, DriverRelease, VendorType


class NvidiaCatalogManager:
    """Управление каталогом версий драйверов NVIDIA."""

    DEFAULT_RELEASES = [
        {
            "version": "572.70",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2025-02-28",
            "download_url": "https://us.download.nvidia.com/Windows/572.70/572.70-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 718.5,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/572.70/572.70-win11-win10-release-notes.pdf",
            "highlights": ["Оптимизация для новых игр 2025", "DLSS 3.5 улучшения", "Исправления стабильности RTX 40/50"],
        },
        {
            "version": "572.16",
            "branch": DriverBranch.STUDIO,
            "release_date": "2025-02-14",
            "download_url": "https://us.download.nvidia.com/Windows/572.16/572.16-desktop-win10-win11-64bit-international-nsd-dch-whql.exe",
            "file_size_mb": 716.2,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/572.16/572.16-win11-win10-release-notes.pdf",
            "highlights": ["Стабильность в Blender, DaVinci Resolve", "CUDA 12.8 acceleration", "Adobe Premiere Pro optimizations"],
        },
        {
            "version": "566.36",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-12-05",
            "download_url": "https://us.download.nvidia.com/Windows/566.36/566.36-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 709.8,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/566.36/566.36-win11-win10-release-notes.pdf",
            "highlights": ["Indiana Jones and the Great Circle", "Marvel Rivals", "Path Tracing enhancements"],
        },
        {
            "version": "566.14",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-11-12",
            "download_url": "https://us.download.nvidia.com/Windows/566.14/566.14-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 708.4,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/566.14/566.14-win11-win10-release-notes.pdf",
            "highlights": ["S.T.A.L.K.E.R. 2: Heart of Chornobyl", "Flight Simulator 2024", "DLSS 3 Frame Generation"],
        },
        {
            "version": "566.03",
            "branch": DriverBranch.STUDIO,
            "release_date": "2024-10-22",
            "download_url": "https://us.download.nvidia.com/Windows/566.03/566.03-desktop-win10-win11-64bit-international-nsd-dch-whql.exe",
            "file_size_mb": 704.1,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/566.03/566.03-win11-win10-release-notes.pdf",
            "highlights": ["Adobe Creative Cloud 2025 release support", "Stable Diffusion AI WebUI speedup", "Autodesk 3ds Max enhancements"],
        },
        {
            "version": "561.09",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-09-11",
            "download_url": "https://us.download.nvidia.com/Windows/561.09/561.09-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 698.2,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/561.09/561.09-win11-win10-release-notes.pdf",
            "highlights": ["Final Fantasy XVI", "God of War Ragnarök", "EA SPORTS FC 25"],
        },
        {
            "version": "560.94",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-08-20",
            "download_url": "https://us.download.nvidia.com/Windows/560.94/560.94-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 692.1,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/560.94/560.94-win11-win10-release-notes.pdf",
            "highlights": ["Black Myth: Wukong Day 1 Ready", "Star Wars Outlaws", "Full Ray Tracing Support"],
        },
        {
            "version": "560.81",
            "branch": DriverBranch.STUDIO,
            "release_date": "2024-08-06",
            "download_url": "https://us.download.nvidia.com/Windows/560.81/560.81-desktop-win10-win11-64bit-international-nsd-dch-whql.exe",
            "file_size_mb": 691.5,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/560.81/560.81-win11-win10-release-notes.pdf",
            "highlights": ["DaVinci Resolve 19 Studio AI tools", "RTX Video Super Resolution HDR", "PyTorch 2.4 acceleration"],
        },
        {
            "version": "556.12",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-06-27",
            "download_url": "https://us.download.nvidia.com/Windows/556.12/556.12-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 685.0,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/556.12/556.12-win11-win10-release-notes.pdf",
            "highlights": ["The First Descendant", "PAYDAY 3 DLSS 3 update", "Стабильный релиз 556-й ветки"],
        },
        {
            "version": "552.44",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2024-05-09",
            "download_url": "https://us.download.nvidia.com/Windows/552.44/552.44-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 673.4,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/552.44/552.44-win11-win10-release-notes.pdf",
            "highlights": ["Ghost of Tsushima DIRECTOR'S CUT", "Homeworld 3", "Высокая стабильность"],
        },
        {
            "version": "537.58",
            "branch": DriverBranch.GAME_READY,
            "release_date": "2023-10-10",
            "download_url": "https://us.download.nvidia.com/Windows/537.58/537.58-desktop-win10-win11-64bit-international-dch-whql.exe",
            "file_size_mb": 654.8,
            "is_whql": True,
            "release_notes_url": "https://us.download.nvidia.com/Windows/537.58/537.58-win11-win10-release-notes.pdf",
            "highlights": ["Lords of the Fallen", "Легендарный ультра-стабильный legacy-драйвер ветки 537"],
        },
    ]

    def __init__(self) -> None:
        """Инициализация каталога NVIDIA."""
        self._releases: List[DriverRelease] = self._load_default_releases()

    def _load_default_releases(self) -> List[DriverRelease]:
        """Загрузить релизы по умолчанию."""
        res: List[DriverRelease] = []
        for item in self.DEFAULT_RELEASES:
            filename = item["download_url"].split("/")[-1]
            release = DriverRelease(
                version=item["version"],
                vendor=VendorType.NVIDIA,
                branch=item["branch"],
                release_date=item["release_date"],
                os="Windows 10/11 64-bit",
                download_url=item["download_url"],
                file_size_mb=item.get("file_size_mb"),
                is_whql=item.get("is_whql", True),
                release_notes_url=item.get("release_notes_url"),
                highlights=item.get("highlights", []),
                installer_filename=filename,
            )
            res.append(release)
        return res

    def get_releases(
        self,
        branch: Optional[DriverBranch] = None,
        search_query: Optional[str] = None,
    ) -> List[DriverRelease]:
        """Получить список доступных версий NVIDIA с фильтрацией."""
        results = list(self._releases)

        if branch:
            results = [r for r in results if r.branch == branch]

        if search_query:
            q = search_query.strip().lower()
            results = [
                r for r in results
                if q in r.version.lower() or any(q in h.lower() for h in r.highlights) or q in r.branch.value.lower()
            ]

        results.sort(key=lambda r: self.parse_version_tuple(r.version), reverse=True)
        return results

    def get_latest_release(self, branch: Optional[DriverBranch] = None) -> Optional[DriverRelease]:
        """Получить самый свежий релиз NVIDIA."""
        releases = self.get_releases(branch=branch)
        return releases[0] if releases else None

    def find_release_by_version(self, version: str) -> Optional[DriverRelease]:
        """Найти релиз по точному или частичному номеру версии."""
        v_clean = version.strip().lower()
        for r in self._releases:
            if r.version.lower() == v_clean:
                return r
        for r in self._releases:
            if v_clean in r.version.lower():
                return r
        return None

    @staticmethod
    def parse_version_tuple(version_str: str) -> tuple:
        """Разобрать строку версии на числовые компоненты для точного сравнения."""
        nums = re.findall(r"\d+", version_str)
        return tuple(int(n) for n in nums) if nums else (0,)

    def compare_versions(self, current_version: str, target_version: str) -> int:
        """Сравнить две версии драйверов.

        Returns:
            -1 если current_version < target_version,
             0 если равны,
             1 если current_version > target_version.
        """
        c_tup = self.parse_version_tuple(current_version)
        t_tup = self.parse_version_tuple(target_version)
        if c_tup < t_tup:
            return -1
        if c_tup > t_tup:
            return 1
        return 0
