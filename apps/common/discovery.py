# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Apps Common Binary Discovery & Portable Guide Registry
# =============================================================================
# Description:
#   Универсальный сканер для поиска исполняемых файлов внешних утилит в /bin,
#   %PATH%, %ProgramFiles% и генератор бейджей со ссылками/инструкциями для
#   загрузки portable версий.
#
# File: discovery.py
# Project: ai-breadboard
# Package: apps.common
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль обнаружения бинарных файлов и справочник по загрузке portable-версий."""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger


@dataclass
class PortableAppGuide:
    """Справочная информация и инструкция по установке portable-версии утилиты."""
    key: str
    name: str
    official_url: str
    download_url: str
    target_bin_path: str
    badge_label: str
    badge_status: str  # "FOUND", "MISSING_PORTABLE"
    badge_color: str   # "green", "red", "yellow"
    instruction_ru: str

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return asdict(self)


class UtilityDiscovery:
    """Интеллектуальный сканер для поиска исполняемых файлов утилит в /bin и системе."""

    _GLOBAL_CACHE: Dict[str, Optional[str]] = {}

    UTILITY_EXECUTABLES: Dict[str, List[str]] = {
        "aida64": ["aida64.exe", "aida64_cl.exe"],
        "hwinfo": ["HWiNFO64.exe", "HWiNFO32.exe", "HWiNFO.exe"],
        "cpuz": ["cpuz_x64.exe", "cpuz.exe", "cpuz64.exe"],
        "gpuz": ["GPU-Z.exe", "GPUZ.exe"],
        "smartmontools": ["smartctl.exe"],
        "smartctl": ["smartctl.exe"],
        "crystaldiskinfo": ["DiskInfo64.exe", "DiskInfo32.exe", "DiskInfo.exe"],
        "lhm": ["LibreHardwareMonitor.exe", "LibreHardwareMonitorLib.dll"],
        "librehardwaremonitor": ["LibreHardwareMonitor.exe"],
        "speccy": ["Speccy64.exe", "Speccy.exe"],
        "coretemp": ["Core Temp.exe", "CoreTemp.exe"],
        "afterburner": ["MSIAfterburner.exe", "RTSS.exe"],
        "nvcleanstall": ["NVCleanstall.exe", "NVCleanerInstall.exe", "NVCleanstall_x64.exe"],
        "ddu": ["Display Driver Uninstaller.exe", "DisplayDriverUninstaller.exe", "DDU.exe"],
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
        "nvcleanstall": [
            "NVCleanstall",
        ],
        "ddu": [
            "Display Driver Uninstaller",
            "DDU",
        ],
    }

    PORTABLE_GUIDES: Dict[str, Dict[str, str]] = {
        "aida64": {
            "name": "AIDA64 Extreme / Engineer",
            "official_url": "https://www.aida64.com/downloads",
            "download_url": "https://www.aida64.com/downloads/latesta64xe",
            "target_bin_path": "bin/aida64/aida64.exe",
            "instruction_ru": "1. Скачайте ZIP-пакет (Portable) AIDA64.\n2. Распакуйте содержимое архива в папку 'bin/aida64/' в корне проекта AI-Breadboard.\n3. Убедитесь, что файл 'bin/aida64/aida64.exe' существует.\n4. Для чтения датчиков на лету включите в настройках AIDA64 опцию: File -> Preferences -> Hardware Monitoring -> External Applications -> Enable shared memory.",
        },
        "hwinfo": {
            "name": "HWiNFO64 Portable",
            "official_url": "https://www.hwinfo.com/download/",
            "download_url": "https://www.hwinfo.com/files/hwi_portable.zip",
            "target_bin_path": "bin/hwinfo/HWiNFO64.exe",
            "instruction_ru": "1. Перейдите на официальный сайт и скачайте 'HWiNFO Portable (ZIP)'.\n2. Распакуйте архив в папку 'bin/hwinfo/'.\n3. Запустите HWiNFO64.exe один раз и включите опцию 'Shared Memory Support' в настройках (Settings).",
        },
        "smartmontools": {
            "name": "smartmontools (smartctl)",
            "official_url": "https://www.smartmontools.org/",
            "download_url": "https://sourceforge.net/projects/smartmontools/files/smartmontools/",
            "target_bin_path": "bin/smartmontools/smartctl.exe",
            "instruction_ru": "1. Скачайте Windows-дистрибутив smartmontools (ZIP или portable installer).\n2. Скопируйте 'smartctl.exe' в папку 'bin/smartmontools/' или 'bin/'.",
        },
        "cpuz": {
            "name": "CPU-Z (CPUID)",
            "official_url": "https://www.cpuid.com/softwares/cpu-z.htm",
            "download_url": "https://www.cpuid.com/downloads/cpu-z/cpu-z_custom-en.zip",
            "target_bin_path": "bin/cpuz/cpuz.exe",
            "instruction_ru": "1. Скачайте 'ZIP • English' (Portable) с официального сайта CPUID.\n2. Распакуйте файл 'cpuz_x64.exe' (или 'cpuz.exe') в папку 'bin/cpuz/'.",
        },
        "gpuz": {
            "name": "TechPowerUp GPU-Z",
            "official_url": "https://www.techpowerup.com/gpuz/",
            "download_url": "https://www.techpowerup.com/download/techpowerup-gpu-z/",
            "target_bin_path": "bin/gpuz/GPU-Z.exe",
            "instruction_ru": "1. Скачайте исполняемый файл GPU-Z.\n2. Поместите 'GPU-Z.exe' в папку 'bin/gpuz/' (утилита изначально является портативной).",
        },
        "nvcleanstall": {
            "name": "TechPowerUp NVCleanstall",
            "official_url": "https://www.techpowerup.com/download/techpowerup-nvcleanstall/",
            "download_url": "https://www.techpowerup.com/download/techpowerup-nvcleanstall/",
            "target_bin_path": "bin/nvcleanstall/NVCleanstall.exe",
            "instruction_ru": "1. Скачайте портативную утилиту NVCleanstall.\n2. Поместите исполняемый файл 'NVCleanstall.exe' в папку 'bin/nvcleanstall/'.",
        },
        "ddu": {
            "name": "Display Driver Uninstaller (DDU)",
            "official_url": "https://www.wagnardsoft.com/display-driver-uninstaller-ddu-",
            "download_url": "https://www.wagnardsoft.com/display-driver-uninstaller-ddu-",
            "target_bin_path": "bin/ddu/Display Driver Uninstaller.exe",
            "instruction_ru": "1. Скачайте архив Display Driver Uninstaller (DDU) с официального сайта Wagnardsoft.\n2. Распакуйте утилиту в папку 'bin/ddu/'.",
        },
        "crystaldiskinfo": {
            "name": "CrystalDiskInfo Portable",
            "official_url": "https://crystalmark.info/en/software/crystaldiskinfo/",
            "download_url": "https://crystalmark.info/en/download/",
            "target_bin_path": "bin/crystaldiskinfo/DiskInfo64.exe",
            "instruction_ru": "1. Скачайте 'ZIP (Portable)' версию CrystalDiskInfo.\n2. Распакуйте архив в папку 'bin/crystaldiskinfo/'.",
        },
        "librehardwaremonitor": {
            "name": "LibreHardwareMonitor",
            "official_url": "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor",
            "download_url": "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest",
            "target_bin_path": "bin/lhm/LibreHardwareMonitor.exe",
            "instruction_ru": "1. Скачайте последний релизный ZIP-архив с GitHub.\n2. Распакуйте его в папку 'bin/lhm/' или 'bin/librehardwaremonitor/'.\n3. В настройках LHM включите встроенный веб-сервер (Options -> Remote Web Server -> Run).",
        },
    }

    @classmethod
    def clear_cache(cls) -> None:
        """Сброс глобального кэша найденных путей к утилитам."""
        cls._GLOBAL_CACHE.clear()

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Инициализация путей поиска."""
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
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

        # 2. Пользовательская переменная PORTABLE_TOOLS_DIR
        env_custom = os.environ.get("PORTABLE_TOOLS_DIR")
        if env_custom and os.path.exists(env_custom):
            roots.append(Path(env_custom))

        # 3. Общие папки на локальных дисках
        for drive in ["C:", "D:", "E:"]:
            for folder in ["Tools", "PortableApps", "bin", "Utilities", "Diagnostics"]:
                p = Path(f"{drive}/{folder}")
                if p.exists():
                    roots.append(p)

        return roots

    def find_utility(self, utility_name: str) -> Optional[str]:
        """Найти исполняемый файл утилиты по имени."""
        key = utility_name.lower().strip()
        if key in self._cached_paths:
            return self._cached_paths[key]

        if self._is_default_root and key in self._GLOBAL_CACHE:
            return self._GLOBAL_CACHE[key]

        target_bins = self.UTILITY_EXECUTABLES.get(key, [f"{key}.exe"])

        # 1. Поиск в системном PATH (быстро)
        for bin_name in target_bins:
            found = shutil.which(bin_name)
            if found:
                resolved = str(Path(found).resolve())
                self._cached_paths[key] = resolved
                if self._is_default_root:
                    self._GLOBAL_CACHE[key] = resolved
                return resolved

        # 2. Поиск в /bin и портативных каталогах поиска
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

        # 3. Прямая проверка известных путей в Program Files и AppData (без glob сканирования всего диска)
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

    def get_portable_guide(self, utility_name: str) -> PortableAppGuide:
        """Получить бейдж и руководство по установке portable-версии.

        Args:
            utility_name: Имя утилиты.

        Returns:
            Объект PortableAppGuide со статусом, ссылками и инструкцией на русском языке.
        """
        key = utility_name.lower().strip()
        if key == "lhm":
            key = "librehardwaremonitor"
        if key == "smartctl":
            key = "smartmontools"

        found_path = self.find_utility(key)
        guide_info = self.PORTABLE_GUIDES.get(
            key,
            {
                "name": utility_name.upper(),
                "official_url": "https://google.com/search?q=" + utility_name,
                "download_url": "https://google.com/search?q=" + utility_name + "+portable+zip",
                "target_bin_path": f"bin/{key}/{key}.exe",
                "instruction_ru": f"Поместите портативную версию '{key}.exe' в каталог 'bin/{key}/'.",
            },
        )

        if found_path:
            badge_label = "Portable Ready"
            badge_status = "FOUND"
            badge_color = "green"
        else:
            badge_label = "Portable Missing"
            badge_status = "MISSING_PORTABLE"
            badge_color = "red"

        return PortableAppGuide(
            key=key,
            name=guide_info["name"],
            official_url=guide_info["official_url"],
            download_url=guide_info["download_url"],
            target_bin_path=guide_info["target_bin_path"],
            badge_label=badge_label,
            badge_status=badge_status,
            badge_color=badge_color,
            instruction_ru=guide_info["instruction_ru"],
        )
