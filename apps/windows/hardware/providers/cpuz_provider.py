# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CPU-Z Hardware Provider
# =============================================================================
# Description:
#   Аппаратный провайдер CPU-Z. Формирует детальный отчет по архитектуре CPU,
#   топологии ядер, кэшу L1/L2/L3, ревизиям материнской платы и SPD таймингам RAM.
#
# File: cpuz_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции с CPU-Z (CLI ghost mode, TXT/HTML отчеты)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import List, Optional

from logger import logger
from apps.windows.hardware.base import (
    BaseHardwareProvider,
    ProviderCapability,
    ProviderStatus,
    ProviderTier,
)
from apps.windows.hardware.models import (
    CpuInventory,
    MemoryInventory,
    MotherboardInventory,
    SensorSnapshot,
    SystemHardwareInventory,
)


class CpuzProvider(BaseHardwareProvider):
    """Провайдер CPU-Z для глубокой идентификации CPU и памяти."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера CPU-Z."""
        super().__init__(name="CPU-Z", tier=ProviderTier.TIER_3_SPECIALIZED, binary_path=binary_path)

    def is_available(self) -> bool:
        """Проверить доступность исполняемого файла cpuz.exe."""
        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True
        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Возможности CPU-Z."""
        return [
            ProviderCapability.CPU_INVENTORY,
            ProviderCapability.MOTHERBOARD_INVENTORY,
            ProviderCapability.RAM_INVENTORY,
            ProviderCapability.OFFLINE_REPORT,
        ]

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """CPU-Z ориентирован на статический инвентарь и не предоставляет живые сенсоры."""
        return None

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать инвентарь оборудования через ghost mode (-txt=...)."""
        if not self.is_available() or not self.binary_path:
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_prefix = os.path.join(tmpdir, "cpuz_report")
                cmd = [self.binary_path, f"-txt={report_prefix}"]
                logger.info(f"Запуск CPU-Z CLI: {' '.join(cmd)}")
                subprocess.run(cmd, capture_output=True, timeout=15)

                txt_path = f"{report_prefix}.txt"
                if os.path.exists(txt_path):
                    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                        return self._parse_cpuz_txt(f.read())
        except Exception as e:
            logger.error(f"Ошибка вызова CPU-Z CLI: {e}")

        return None

    def _parse_cpuz_txt(self, content: str) -> SystemHardwareInventory:
        """Парсинг текстового отчета CPU-Z."""
        inv = SystemHardwareInventory(sources_used=[self.name])
        cpu_name = "Unknown CPU"
        socket = None
        cores = 0
        threads = 0
        mb_model = "Unknown Motherboard"
        mb_vendor = "Unknown"

        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("Name") and "Specification" not in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    cpu_name = parts[-1].strip()
            elif "Package (platform ID)" in line_str or "Package" in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    socket = parts[-1].strip()
            elif line_str.startswith("Number of cores"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    try:
                        cores = int(parts[-1].strip())
                    except ValueError:
                        pass
            elif line_str.startswith("Number of threads"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    try:
                        threads = int(parts[-1].strip())
                    except ValueError:
                        pass
            elif line_str.startswith("Mainboard Model"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    mb_model = parts[-1].strip()
            elif line_str.startswith("Mainboard Vendor"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    mb_vendor = parts[-1].strip()

        inv.cpu = CpuInventory(
            model_name=cpu_name,
            socket=socket,
            physical_cores=cores,
            logical_cores=threads,
            source_provider=self.name,
        )
        inv.motherboard = MotherboardInventory(
            product_name=mb_model,
            manufacturer=mb_vendor,
            source_provider=self.name,
        )
        return inv
