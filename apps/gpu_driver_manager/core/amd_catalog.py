# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AMD GPU Driver Catalog Manager
# =============================================================================
# Description:
#   Каталог версий драйверов AMD Software: Adrenalin Edition и PRO Edition,
#   получение официальных релизов Radeon, прямых ссылок на загрузку и Release Notes.
#
# File: amd_catalog.py
# Project: ai-breadboard
# Package: apps.gpu_driver_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер каталога драйверов AMD Radeon."""

from __future__ import annotations

import re
from typing import List, Optional

from src.logger import logger
from apps.gpu_driver_manager.core.models import DriverBranch, DriverRelease, VendorType


class AmdCatalogManager:
    """Управление каталогом версий драйверов AMD."""

    # Встроенный проверенный каталог актуальных и стабильных релизов AMD Software: Adrenalin Edition
    DEFAULT_RELEASES = [
        {
            "version": "24.12.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-12-10",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.12.1-win10-win11-dec10-rdna.exe",
            "file_size_mb": 684.2,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-12-1.html",
            "highlights": ["Indiana Jones and the Great Circle", "Marvel Rivals support", "HYPR-RX improvements", "Vulkan ray tracing speedup"],
        },
        {
            "version": "24.10.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-10-18",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.10.1-win10-win11-oct18-rdna.exe",
            "file_size_mb": 678.5,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-10-1.html",
            "highlights": ["Call of Duty: Black Ops 6", "Unknown 9: Awakening", "AFMF 2 (Fluid Motion Frames 2) updates"],
        },
        {
            "version": "24.9.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-09-24",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.9.1-win10-win11-sep24-rdna.exe",
            "file_size_mb": 671.0,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-9-1.html",
            "highlights": ["Frostpunk 2", "God of War Ragnarök", "Simultaneous AFMF 2 & Radeon Anti-Lag 2 support"],
        },
        {
            "version": "24.8.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-08-29",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.8.1-win10-win11-aug29-rdna.exe",
            "file_size_mb": 665.4,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-8-1.html",
            "highlights": ["Black Myth: Wukong", "Star Wars Outlaws", "Concord", "FSR 3.1 support in Adrenalin"],
        },
        {
            "version": "24.7.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-07-19",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.7.1-win10-win11-jul19-rdna.exe",
            "file_size_mb": 659.1,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-7-1.html",
            "highlights": ["Zenless Zone Zero", "The First Descendant", "DOTA 2 Anti-Lag 2 Technical Preview"],
        },
        {
            "version": "24.Q4",
            "branch": DriverBranch.PRO_ENTERPRISE,
            "release_date": "2024-11-05",
            "download_url": "https://drivers.amd.com/drivers/pro/amd-software-pro-edition-24.q4-win10-win11-rdna.exe",
            "file_size_mb": 690.3,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-PRO-WIN-24-Q4.html",
            "highlights": ["Профессиональная ветка PRO Enterprise для САПР и 3D", "Сертификация Autodesk, SolidWorks, Siemens"],
        },
        {
            "version": "24.3.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2024-03-20",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-24.3.1-win10-win11-mar20-rdna.exe",
            "file_size_mb": 648.7,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-24-3-1.html",
            "highlights": ["Dragon's Dogma 2", "Horizon Forbidden West Complete Edition", "Высокостабильный релиз Q1 2024"],
        },
        {
            "version": "23.12.1",
            "branch": DriverBranch.ADRENALIN,
            "release_date": "2023-12-05",
            "download_url": "https://drivers.amd.com/drivers/amd-software-adrenalin-edition-23.12.1-win10-win11-dec05-rdna.exe",
            "file_size_mb": 630.0,
            "is_whql": True,
            "release_notes_url": "https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-23-12-1.html",
            "highlights": ["Avatar: Frontiers of Pandora", "Обновленный интерфейс вкладки Home", "Стабильный долгосрочный релиз 2023 года"],
        },
    ]

    def __init__(self) -> None:
        """Инициализация каталога AMD."""
        self._releases: List[DriverRelease] = self._load_default_releases()

    def _load_default_releases(self) -> List[DriverRelease]:
        """Загрузить релизы AMD по умолчанию."""
        res: List[DriverRelease] = []
        for item in self.DEFAULT_RELEASES:
            filename = item["download_url"].split("/")[-1]
            release = DriverRelease(
                version=item["version"],
                vendor=VendorType.AMD,
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
        """Получить список доступных версий AMD с фильтрацией.

        Args:
            branch: Фильтр по ветке (Adrenalin, PRO Edition и др.).
            search_query: Поисковый запрос (по номеру версии или особенностям).

        Returns:
            Отсортированный по дате и номеру версии список релизов.
        """
        results = list(self._releases)

        if branch:
            results = [r for r in results if r.branch == branch]

        if search_query:
            q = search_query.strip().lower()
            results = [
                r for r in results
                if q in r.version.lower() or any(q in h.lower() for h in r.highlights) or q in r.branch.value.lower()
            ]

        # Сортировка по дате релиза и номеру версии
        results.sort(key=lambda r: (r.release_date, self.parse_version_tuple(r.version)), reverse=True)
        return results

    def get_latest_release(self, branch: Optional[DriverBranch] = None) -> Optional[DriverRelease]:
        """Получить самый свежий релиз AMD."""
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
        """Разобрать строку версии на числовые компоненты для сравнения."""
        nums = re.findall(r"\d+", version_str)
        return tuple(int(n) for n in nums) if nums else (0,)

    def compare_versions(self, current_version: str, target_version: str) -> int:
        """Сравнить две версии драйверов AMD.

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
