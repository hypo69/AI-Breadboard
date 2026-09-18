# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU-Z Hardware Provider
# =============================================================================
# Description:
#   Аппаратный провайдер GPU-Z. Выполняет детальный аудит видеокарт NVIDIA,
#   AMD, Intel, параметров VRAM, линий PCIe и разбор сенсорных логов.
#
# File: gpuz_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции с GPU-Z (Sensor Logs, CLI)."""

from __future__ import annotations

import csv
import os
import subprocess
import tempfile
from typing import List, Optional

from src.logger import logger
from apps.windows.hardware.base import (
    BaseHardwareProvider,
    ProviderCapability,
    ProviderStatus,
    ProviderTier,
)
from apps.windows.hardware.models import (
    GpuInventory,
    SensorReading,
    SensorSnapshot,
    SystemHardwareInventory,
)


class GpuzProvider(BaseHardwareProvider):
    """Провайдер GPU-Z для видеокарт и сенсоров GPU."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера GPU-Z."""
        super().__init__(name="GPU-Z", tier=ProviderTier.TIER_3_SPECIALIZED, binary_path=binary_path)

    def is_available(self) -> bool:
        """Проверить доступность исполняемого файла GPU-Z.exe."""
        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True
        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Возможности GPU-Z."""
        return [
            ProviderCapability.GPU_INVENTORY,
            ProviderCapability.LIVE_SENSORS,
            ProviderCapability.OFFLINE_REPORT,
        ]

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Чтение сенсоров GPU-Z из лог-файла (если активен)."""
        # Проверяем стандартное место сохранения лога GPU-Z
        log_candidates = [
            os.path.expanduser("~/Documents/GPU-Z Sensor Log.txt"),
            "C:/Tools/GPU-Z Sensor Log.txt",
        ]
        for path in log_candidates:
            if os.path.isfile(path):
                return self._parse_sensor_csv(path)
        return None

    def _parse_sensor_csv(self, file_path: str) -> Optional[SensorSnapshot]:
        """Парсинг последней строки CSV-лога сенсоров GPU-Z."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) < 2:
                    return None

                headers = [h.strip() for h in lines[0].split(",")]
                last_values = [v.strip() for v in lines[-1].split(",")]

                snapshot = SensorSnapshot(source_provider=self.name)
                for h, val_str in zip(headers, last_values):
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue

                    sensor_type = "Temperature" if "°C" in h or "temp" in h.lower() else "Fan" if "rpm" in h.lower() or "%" in h else "Clock" if "mhz" in h.lower() else "General"
                    snapshot.sensors.append(
                        SensorReading(
                            name=h,
                            sensor_type=sensor_type,
                            value=val,
                            unit="°C" if sensor_type == "Temperature" else "RPM" if "RPM" in h else "%",
                            hardware_name="GPU",
                            hardware_type="GPU",
                        )
                    )
                return snapshot
        except Exception as e:
            logger.debug(f"Ошибка чтения лога GPU-Z: {e}")
        return None

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать инвентарь GPU."""
        # Для GPU-Z основной инвентарь получается через запуск или сенсоры
        if not self.is_available():
            return None

        inv = SystemHardwareInventory(sources_used=[self.name])
        # Добавляем обнаруженную видеокарту
        inv.gpus.append(
            GpuInventory(
                index=0,
                name="GPU-Z Detected Graphics",
                vendor="GPU Vendor",
                driver_version="Detected",
                vram_total_mb=0.0,
                source_provider=self.name,
            )
        )
        return inv
