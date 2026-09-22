# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Provider
# =============================================================================
# Description:
#   Аппаратный провайдер LibreHardwareMonitor. Поддерживает сбор сенсоров через
#   локальный Web JSON API (http://localhost:8085/data.json) и WMI.
#
# File: lhm_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции с LibreHardwareMonitor (Web JSON API / WMI)."""

from __future__ import annotations

import os
import urllib.request
import json
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
    StorageInventory,
    SystemHardwareInventory,
)

DEFAULT_LHM_ENDPOINT = "http://localhost:8085/data.json"


class LhmProvider(BaseHardwareProvider):
    """Провайдер LibreHardwareMonitor через Web JSON API и WMI."""

    def __init__(self, binary_path: Optional[str] = None, endpoint_url: str = DEFAULT_LHM_ENDPOINT) -> None:
        """Инициализация провайдера LHM."""
        super().__init__(name="LibreHardwareMonitor", tier=ProviderTier.TIER_2_PRIMARY, binary_path=binary_path)
        self.endpoint_url = endpoint_url

    def is_available(self) -> bool:
        """Проверить доступность Web API или наличие бинарника."""
        # 1. Проверяем доступность REST JSON эндпоинта
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    self._status = ProviderStatus.RUNNING
                    return True
        except Exception:
            pass

        # 2. Проверяем наличие исполняемого файла
        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True

        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Возможности LibreHardwareMonitor."""
        return [
            ProviderCapability.CPU_INVENTORY,
            ProviderCapability.GPU_INVENTORY,
            ProviderCapability.RAM_INVENTORY,
            ProviderCapability.STORAGE_INVENTORY,
            ProviderCapability.LIVE_SENSORS,
        ]

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать дерево датчиков через Web JSON API."""
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            snapshot = SensorSnapshot(source_provider=self.name)
            self._flatten_lhm_tree(data, snapshot)
            return snapshot
        except Exception as e:
            logger.debug(f"LibreHardwareMonitor Web API недоступен: {e}")
            return None

    def _flatten_lhm_tree(self, node: Dict[str, Any], snapshot: SensorSnapshot, current_hw: str = "System", hw_type: str = "System") -> None:
        """Рекурсивный обход иерархического JSON-дерева LibreHardwareMonitor."""
        text = node.get("Text", "")
        # Если узел содержит значение сенсора (например, '45.0 °C' или '1200 RPM')
        value_str = node.get("Value", "")
        if value_str:
            unit = ""
            val = 0.0
            parts = value_str.split(" ")
            try:
                val = float(parts[0].replace(",", "."))
                unit = parts[1] if len(parts) > 1 else ""
            except Exception:
                pass

            sensor_type = "Temperature" if "°c" in unit.lower() else "Fan" if "rpm" in unit.lower() else "General"
            snapshot.sensors.append(
                SensorReading(
                    name=text,
                    sensor_type=sensor_type,
                    value=val,
                    unit=unit,
                    hardware_name=current_hw,
                    hardware_type=hw_type,
                )
            )

        children = node.get("Children", [])
        for child in children:
            sub_hw = current_hw
            sub_type = hw_type
            child_text = child.get("Text", "")
            if "CPU" in child_text:
                sub_hw = child_text
                sub_type = "CPU"
            elif "GPU" in child_text or "NVIDIA" in child_text or "AMD" in child_text:
                sub_hw = child_text
                sub_type = "GPU"
            self._flatten_lhm_tree(child, snapshot, sub_hw, sub_type)

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Сформировать инвентарь оборудования на основе данных LHM."""
        sensors = self.probe_sensors()
        if not sensors:
            return None

        inv = SystemHardwareInventory(sources_used=[self.name])
        hw_names = set(s.hardware_name for s in sensors.sensors)
        for name in hw_names:
            if "CPU" in name:
                inv.cpu = CpuInventory(model_name=name, source_provider=self.name)
            elif "GPU" in name or "NVIDIA" in name or "Radeon" in name:
                inv.gpus.append(GpuInventory(index=len(inv.gpus), name=name, vendor="GPU Vendor", driver_version="N/A", vram_total_mb=0, source_provider=self.name))

        return inv
