# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: smartmontools Hardware Provider
# =============================================================================
# Description:
#   Аппаратный провайдер smartmontools (smartctl.exe). Обеспечивает глубокую
#   диагностику NVMe, SSD, HDD накопителей, чтение SMART атрибутов, расчет
#   процента износа и здоровья дисков через прямой вызов CLI --json.
#
# File: smartmontools_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции со smartmontools (smartctl --json)."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.windows.hardware.base import (
    BaseHardwareProvider,
    ProviderCapability,
    ProviderStatus,
    ProviderTier,
)
from apps.windows.hardware.models import (
    SensorReading,
    SensorSnapshot,
    StorageDeviceInventory,
    StorageInventory,
    SystemHardwareInventory,
)


class SmartmontoolsProvider(BaseHardwareProvider):
    """Провайдер smartmontools (smartctl) для детальной диагностики накопителей."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера smartmontools."""
        super().__init__(name="smartmontools", tier=ProviderTier.TIER_3_SPECIALIZED, binary_path=binary_path)

    def is_available(self) -> bool:
        """Проверить доступность исполняемого файла smartctl.exe."""
        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True
        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Возможности smartmontools."""
        return [
            ProviderCapability.STORAGE_INVENTORY,
            ProviderCapability.SMART_DIAGNOSTICS,
            ProviderCapability.LIVE_SENSORS,
        ]

    def _run_smartctl_json(self, args: List[str]) -> Optional[Dict[str, Any]]:
        """Выполнить smartctl с параметром --json и вернуть распарсенный результат."""
        if not self.is_available() or not self.binary_path:
            return None
        cmd = [self.binary_path, "--json"] + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            # smartctl возвращает битовую маску в exit code (0, 1, 2, ...), поэтому проверяем наличие stdout
            if res.stdout.strip():
                return json.loads(res.stdout)
        except Exception as e:
            logger.error(f"Ошибка вызова smartctl: {e}")
        return None

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать инвентарь всех накопителей через smartctl --scan."""
        scan_data = self._run_smartctl_json(["--scan"])
        if not scan_data:
            return None

        inv = SystemHardwareInventory(sources_used=[self.name])
        storage_inv = StorageInventory(source_provider=self.name)

        devices = scan_data.get("devices", [])
        for dev in devices:
            dev_name = dev.get("name", "")
            dev_type = dev.get("type", "")
            if not dev_name:
                continue

            info = self._run_smartctl_json(["-x", dev_name])
            if not info:
                continue

            model = info.get("model_name", info.get("device", {}).get("name", "Unknown Drive"))
            serial = info.get("serial_number")
            firmware = info.get("firmware_version")
            size_bytes = info.get("user_capacity", {}).get("bytes", 0)
            size_gb = round(size_bytes / (1024**3), 2)

            # Оценка SMART статуса
            smart_status = info.get("smart_status", {})
            passed = smart_status.get("passed", True)
            health_str = "OK" if passed else "Critical"

            temp_c = None
            temp_obj = info.get("temperature", {})
            if "current" in temp_obj:
                temp_c = float(temp_obj["current"])

            # NVMe атрибуты здоровья
            nvme_smart = info.get("nvme_smart_health_information_log", {})
            wear_pct = nvme_smart.get("percentage_used")
            health_pct = max(0.0, 100.0 - float(wear_pct)) if wear_pct is not None else None
            poh = nvme_smart.get("power_on_hours")

            storage_inv.devices.append(
                StorageDeviceInventory(
                    device_id=dev_name,
                    model=model,
                    vendor=info.get("vendor", "Unknown"),
                    interface_type=dev_type.upper(),
                    media_type="SSD" if info.get("rotation_rate") == 0 else "HDD",
                    size_gb=size_gb,
                    serial_number=serial,
                    firmware_revision=firmware,
                    health_status=health_str,
                    health_pct=health_pct,
                    temperature_c=temp_c,
                    power_on_hours=poh,
                    smart_attributes=info.get("ata_smart_attributes", {}),
                    source_provider=self.name,
                )
            )

        inv.storage = storage_inv
        return inv

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать температурные сенсоры накопителей."""
        inv = self.probe_inventory()
        if not inv or not inv.storage:
            return None

        snapshot = SensorSnapshot(source_provider=self.name)
        for dev in inv.storage.devices:
            if dev.temperature_c is not None:
                snapshot.sensors.append(
                    SensorReading(
                        name=f"{dev.model} Temperature",
                        sensor_type="Temperature",
                        value=dev.temperature_c,
                        unit="°C",
                        hardware_name=dev.model,
                        hardware_type="Storage",
                    )
                )
        return snapshot
