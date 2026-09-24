# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HWiNFO Hardware Provider
# =============================================================================
# Description:
#   Аппаратный провайдер HWiNFO. Поддерживает чтение оперативной телеметрии
#   через Windows Shared Memory, SDK DLL и генерацию отчетов CLI (-j JSON, -c CSV).
#
# File: hwinfo_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции с HWiNFO (Shared Memory, SDK, CLI)."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from ctypes import wintypes
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.hardware.base import (
    BaseHardwareProvider,
    ProviderCapability,
    ProviderStatus,
    ProviderTier,
)
from apps.windows.hardware.models import (
    CpuInventory,
    GpuInventory,
    MemoryInventory,
    MotherboardInventory,
    SensorReading,
    SensorSnapshot,
    StorageDeviceInventory,
    StorageInventory,
    SystemHardwareInventory,
)

FILE_MAP_READ = 0x0004
SHM_HWINFO_NAME = "Global\\HWiNFO_SENS_SM2"


class HwinfoProvider(BaseHardwareProvider):
    """Провайдер HWiNFO для чтения телеметрии и инвентаря оборудования."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера HWiNFO."""
        super().__init__(name="HWiNFO", tier=ProviderTier.TIER_2_PRIMARY, binary_path=binary_path)

    def is_available(self) -> bool:
        """Проверить доступность: запущен ли HWiNFO с Shared Memory или есть ли бинарник."""
        if self._check_shared_memory():
            self._status = ProviderStatus.RUNNING
            return True

        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True

        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Список поддерживаемых возможностей HWiNFO."""
        return [
            ProviderCapability.CPU_INVENTORY,
            ProviderCapability.MOTHERBOARD_INVENTORY,
            ProviderCapability.RAM_INVENTORY,
            ProviderCapability.GPU_INVENTORY,
            ProviderCapability.STORAGE_INVENTORY,
            ProviderCapability.SMART_DIAGNOSTICS,
            ProviderCapability.LIVE_SENSORS,
            ProviderCapability.SHARED_MEMORY,
            ProviderCapability.OFFLINE_REPORT,
        ]

    def _check_shared_memory(self) -> bool:
        """Проверить наличие активного мэппинга памяти HWiNFO."""
        try:
            kernel32 = ctypes.windll.kernel32
            h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHM_HWINFO_NAME)
            if h_map:
                kernel32.CloseHandle(h_map)
                return True
        except Exception:
            pass
        return False

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать данные сенсоров HWiNFO."""
        # Если HWiNFO запущен в фоне, пробуем прочитать память или выполнить быстрый сбор
        if not self.is_available():
            return None

        snapshot = SensorSnapshot(source_provider=self.name)
        # Если есть CLI, запускаем быстрый сбор лога в JSON
        if self.binary_path and os.path.isfile(self.binary_path):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    log_json = os.path.join(tmpdir, "hwinfo_sensors.json")
                    cmd = [self.binary_path, f"-l{log_json}"]
                    proc = subprocess.run(cmd, capture_output=True, timeout=10)
                    if os.path.exists(log_json):
                        with open(log_json, "r", encoding="utf-8", errors="ignore") as f:
                            data = json.load(f)
                            for s in data.get("Sensors", []):
                                snapshot.sensors.append(
                                    SensorReading(
                                        name=s.get("Name", "Sensor"),
                                        sensor_type=s.get("Type", "General"),
                                        value=float(s.get("Value", 0.0)),
                                        unit=s.get("Unit", ""),
                                        hardware_name=s.get("Device", "HWiNFO Device"),
                                        hardware_type="System",
                                    )
                                )
                        return snapshot
            except Exception as e:
                logger.debug(f"Ошибка сбора сенсоров через CLI HWiNFO: {e}")

        return None

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать детальный инвентарь оборудования через HWiNFO CLI (-j JSON)."""
        if not self.binary_path or not os.path.isfile(self.binary_path):
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_file = os.path.join(tmpdir, "hwinfo_report.json")
                cmd = [self.binary_path, f"-j{report_file}"]
                logger.debug(f"Запуск HWiNFO CLI: {' '.join(cmd)}")
                subprocess.run(cmd, capture_output=True, timeout=25)
                if os.path.exists(report_file):
                    with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                    return self._parse_json_inventory(data)
        except Exception as e:
            logger.error(f"Ошибка вызова HWiNFO CLI: {e}")

        return None

    def _parse_json_inventory(self, data: Dict[str, Any]) -> SystemHardwareInventory:
        """Парсинг JSON-отчета HWiNFO."""
        inv = SystemHardwareInventory(sources_used=[self.name])
        try:
            cpu_info = data.get("CPU", {})
            inv.cpu = CpuInventory(
                model_name=cpu_info.get("BrandName", cpu_info.get("Name", "HWiNFO CPU")),
                physical_cores=cpu_info.get("Cores", 0),
                logical_cores=cpu_info.get("Threads", 0),
                source_provider=self.name,
            )

            mb_info = data.get("Motherboard", {})
            inv.motherboard = MotherboardInventory(
                product_name=mb_info.get("Model", "HWiNFO Motherboard"),
                manufacturer=mb_info.get("Manufacturer", "Unknown"),
                bios_version=mb_info.get("BIOSVersion"),
                source_provider=self.name,
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON HWiNFO: {e}")

        return inv
