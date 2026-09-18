# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Utility Discovery Engine
# =============================================================================
# Description:
#   Автоматический поиск портативных диагностических утилит в /bin,
#   системных каталогах, Program Files, Portable путях и %PATH%.
#
# File: discovery.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Детектор и сканер местоположения портативных утилит Windows."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import logger


class UtilityDiscovery:
    """Интеллектуальный сканер для поиска исполняемых файлов утилит."""

    _GLOBAL_CACHE: Dict[str, Optional[str]] = {}

    # Карта названий утилит и вероятных имен бинарных файлов
    UTILITY_EXECUTABLES: Dict[str, List[str]] = {
        "aida64": ["aida64.exe", "aida64_cl.exe"],
        "hwinfo": ["HWiNFO64.exe", "HWiNFO32.exe", "HWiNFO.exe"],
        "cpuz": ["cpuz_x64.exe", "cpuz.exe", "cpuz64.exe"],
        "gpuz": ["GPU-Z.exe", "GPUZ.exe"],
        "lhm": ["LibreHardwareMonitor.exe", "LibreHardwareMonitorLib.dll"],
        "librehardwaremonitor": ["LibreHardwareMonitor.exe"],
        "ohm": ["OpenHardwareMonitor.exe"],
        "smartctl": ["smartctl.exe"],
        "smartmontools": ["smartctl.exe"],
        "crystaldiskinfo": ["DiskInfo64.exe", "DiskInfo32.exe", "DiskInfo.exe"],
        "speccy": ["Speccy64.exe", "Speccy.exe"],
        "coretemp": ["Core Temp.exe", "CoreTemp.exe"],
        "afterburner": ["MSIAfterburner.exe", "RTSS.exe"],
    }

    KNOWN_INSTALL_DIRS: Dict[str, List[str]] = {
        "aida64": [
            "FinalWire/AIDA64 Extreme",
            "FinalWire/AIDA64 Engineer",
            "FinalWire/AIDA64 Business",
            "AIDA64 Extreme",
            "AIDA64",
        ],
        "hwinfo": [
            "HWiNFO64",
            "HWiNFO32",
            "HWiNFO",
        ],
        "cpuz": [
            "CPUID/CPU-Z",
            "CPUID/cpu-z",
            "CPU-Z",
            "cpuz",
        ],
        "gpuz": [
            "GPU-Z",
            "TechPowerUp GPU-Z",
            "gpuz",
        ],
        "smartmontools": [
            "smartmontools/bin",
            "smartmontools",
        ],
        "smartctl": [
            "smartmontools/bin",
            "smartmontools",
        ],
        "crystaldiskinfo": [
            "CrystalDiskInfo",
        ],
        "lhm": [
            "LibreHardwareMonitor",
        ],
        "librehardwaremonitor": [
            "LibreHardwareMonitor",
        ],
        "speccy": [
            "Speccy",
            "CCleaner/Speccy",
        ],
        "coretemp": [
            "Core Temp",
        ],
        "afterburner": [
            "MSI Afterburner",
        ],
    }

    @classmethod
    def clear_cache(cls) -> None:
        """Сброс глобального кэша найденных путей к утилитам."""
        cls._GLOBAL_CACHE.clear()

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Инициализация путей поиска."""
        if project_root is None:
            # Путь к корню AI-Breadboard
            self.project_root = Path(__file__).resolve().parent.parent.parent.parent
            self._is_default_root = True
        else:
            self.project_root = project_root
            self._is_default_root = False

        self._search_roots: List[Path] = self._build_search_roots()
        self._cached_paths: Dict[str, Optional[str]] = {}

    def _build_search_roots(self) -> List[Path]:
        """Сформировать список приоритетных каталогов поиска."""
        roots: List[Path] = []

        # 1. Приоритетный каталог /bin проекта
        bin_dir = self.project_root / "bin"
        if bin_dir.exists():
            roots.append(bin_dir)

        # 2. Пользовательские переменные окружения
        env_custom = os.environ.get("PORTABLE_TOOLS_DIR")
        if env_custom and os.path.exists(env_custom):
            roots.append(Path(env_custom))

        # 3. Общие каталоги инструментов на диске
        for drive in ["C:", "D:", "E:"]:
            for folder in ["Tools", "PortableApps", "bin", "Utilities", "Diagnostics"]:
                p = Path(f"{drive}/{folder}")
                if p.exists():
                    roots.append(p)

        return roots

    def find_utility(self, utility_name: str) -> Optional[str]:
        """Найти исполняемый файл для указанной утилиты.

        Args:
            utility_name: Ключ утилиты (напр. 'hwinfo', 'aida64', 'cpuz').

        Returns:
            Абсолютный путь к найденному файлу или None.
        """
        key = utility_name.lower().strip()
        if key in self._cached_paths:
            return self._cached_paths[key]

        if self._is_default_root and key in self._GLOBAL_CACHE:
            return self._GLOBAL_CACHE[key]

        target_bins = self.UTILITY_EXECUTABLES.get(key, [f"{key}.exe"])

        # 1. Поиск в PATH через shutil.which (быстро)
        for bin_name in target_bins:
            found = shutil.which(bin_name)
            if found:
                resolved = str(Path(found).resolve())
                self._cached_paths[key] = resolved
                if self._is_default_root:
                    self._GLOBAL_CACHE[key] = resolved
                return resolved

        # 2. Поиск в /bin проекта и портативных корнях
        for search_root in self._search_roots:
            if not search_root.exists():
                continue
            for bin_name in target_bins:
                direct_path = search_root / bin_name
                if direct_path.is_file():
                    resolved = str(direct_path.resolve())
                    self._cached_paths[key] = resolved
                    if self._is_default_root:
                        self._GLOBAL_CACHE[key] = resolved
                    return resolved

                subfolder_path = search_root / key / bin_name
                if subfolder_path.is_file():
                    resolved = str(subfolder_path.resolve())
                    self._cached_paths[key] = resolved
                    if self._is_default_root:
                        self._GLOBAL_CACHE[key] = resolved
                    return resolved

        # 3. Прямая проверка известных путей установки в Program Files и AppData
        system_roots: List[Path] = []
        for pf_var in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
            val = os.environ.get(pf_var)
            if val and os.path.exists(val):
                system_roots.append(Path(val))

        known_subs = self.KNOWN_INSTALL_DIRS.get(key, [key])
        for s_root in system_roots:
            for sub in known_subs:
                for bin_name in target_bins:
                    target_file = s_root / sub / bin_name
                    if target_file.is_file():
                        resolved = str(target_file.resolve())
                        self._cached_paths[key] = resolved
                        if self._is_default_root:
                            self._GLOBAL_CACHE[key] = resolved
                        return resolved

        self._cached_paths[key] = None
        if self._is_default_root:
            self._GLOBAL_CACHE[key] = None
        return None

    def scan_all_available(self) -> Dict[str, Optional[str]]:
        """Просканировать все зарегистрированные утилиты и вернуть их статус."""
        results: Dict[str, Optional[str]] = {}
        for util_key in self.UTILITY_EXECUTABLES:
            results[util_key] = self.find_utility(util_key)
        return results
