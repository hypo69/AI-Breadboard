# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Extended Inspectors - WSL2 & Hyper-V Inspector
# =============================================================================
# Description:
#   Мониторинг виртуальных дисков .vhdx WSL2 / Hyper-V и их автоматическая оптимизация.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.extended_inspectors.wsl2_hyperv_inspector import WSL2HyperVInspector
#
#     inspector = WSL2HyperVInspector()
#     report = inspector.inspect_vhdx_disks()
#
# File: wsl2_hyperv_inspector.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.extended_inspectors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:04:00
# =============================================================================

from __future__ import annotations

"""Мониторинг разрастания дисков .vhdx WSL2/Hyper-V и сжатия через compact vdisk."""

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger


@dataclass
class VHDXDiskInfo:
    """Информация о виртуальном диске VHDX."""
    path: str
    size_bytes: int
    size_gb: float
    distro_or_vm_name: str
    needs_compact: bool


@dataclass
class WSL2InspectionReport:
    """Отчет инспектора WSL2 и Hyper-V."""
    total_disks: int
    total_size_gb: float
    disks: List[VHDXDiskInfo] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            'total_disks': self.total_disks,
            'total_size_gb': round(self.total_size_gb, 2),
            'disks': [
                {
                    'path': d.path,
                    'size_gb': round(d.size_gb, 2),
                    'distro_name': d.distro_or_vm_name,
                    'needs_compact': d.needs_compact,
                }
                for d in self.disks
            ],
            'timestamp': self.timestamp,
        }


class WSL2HyperVInspector:
    """Инспектор виртуальных дисков WSL2 и Hyper-V."""

    def inspect_vhdx_disks(self, custom_dirs: Optional[List[Path]] = None) -> WSL2InspectionReport:
        """Поиск и анализ файлов .vhdx в пользовательском профиле и виртуальных машинах.

        Args:
            custom_dirs: Опциональный пользовательский список директорий для поиска.

        Returns:
            WSL2InspectionReport: Сводка по дискам .vhdx.
        """
        vhdx_files: List[VHDXDiskInfo] = []
        user_profile = os.environ.get('USERPROFILE', 'C:/Users/Default')
        search_dirs = custom_dirs or [
            Path(user_profile) / '.wsl',
            Path(user_profile) / 'AppData' / 'Local' / 'Packages',
            Path('C:/ProgramData/Microsoft/Windows/Containers'),
        ]

        for base in search_dirs:
            if base.exists():
                try:
                    base_depth = len(base.parts)
                    for root, dirs, files in os.walk(base):
                        cur_depth = len(Path(root).parts) - base_depth
                        if cur_depth > 4:
                            dirs.clear()
                            continue
                        for f in files:
                            if f.lower().endswith('.vhdx'):
                                full_p = Path(root) / f
                                try:
                                    sz = full_p.stat().st_size
                                    sz_gb = sz / (1024 ** 3)
                                    name = full_p.parent.name
                                    vhdx_files.append(VHDXDiskInfo(
                                        path=str(full_p),
                                        size_bytes=sz,
                                        size_gb=sz_gb,
                                        distro_or_vm_name=name,
                                        needs_compact=sz_gb > 10.0,
                                    ))
                                except (OSError, PermissionError):
                                    pass
                except Exception as ex:
                    logger.debug(f'[WSL2Inspector] Ошибка обхода директории {base}: {ex}')

        total_gb = sum(d.size_gb for d in vhdx_files)
        return WSL2InspectionReport(
            total_disks=len(vhdx_files),
            total_size_gb=total_gb,
            disks=vhdx_files,
        )

    def compact_vdisk(self, vhdx_path: str) -> bool:
        """Выполняет сжатие виртуального диска VHDX через diskpart.

        Args:
            vhdx_path: Путь к файлу .vhdx.

        Returns:
            bool: True если сжатие выполнено успешно.
        """
        p = Path(vhdx_path)
        if not p.exists() or os.name != 'nt':
            return False

        script_content = f"select vdisk file=\"{p}\"\nattach vdisk readonly\ncompact vdisk\ndetach vdisk\n"
        script_file = p.parent / f"compact_{p.stem}.txt"
        try:
            script_file.write_text(script_content, encoding='utf-8')
            res = subprocess.run(['diskpart', '/s', str(script_file)], capture_output=True, text=True, timeout=120)
            return res.returncode == 0
        except Exception as ex:
            logger.error(f'[WSL2Inspector] Ошибка вызова diskpart для {vhdx_path}: {ex}')
            return False
        finally:
            if script_file.exists():
                try:
                    script_file.unlink()
                except OSError:
                    pass
