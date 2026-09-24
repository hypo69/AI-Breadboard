# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 Hardware Provider
# =============================================================================
# Description:
#   Аппаратный провайдер AIDA64. Поддерживает чтение оперативной телеметрии
#   через Windows Shared Memory ('AIDA64_SensorValues'), реестр, WMI и
#   формирование полного аппаратного инвентаря через CLI (/R /XML /SILENT).
#
# File: aida64_provider.py
# Project: ai-breadboard
# Package: apps.windows.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Провайдер интеграции с AIDA64 (Shared Memory, WMI, CLI)."""

from __future__ import annotations

import ctypes
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
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

# WinAPI константы для Shared Memory
FILE_MAP_READ = 0x0004
SHM_AIDA64_NAME = "AIDA64_SensorValues"


class Aida64Provider(BaseHardwareProvider):
    """Провайдер AIDA64: чтение Shared Memory и генерация отчетов."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера AIDA64."""
        super().__init__(name="AIDA64", tier=ProviderTier.TIER_2_PRIMARY, binary_path=binary_path)

    def is_available(self) -> bool:
        """Проверить доступность: запущен ли Shared Memory или есть ли бинарник."""
        # 1. Проверяем наличие активной Shared Memory
        shm_data = self._read_shared_memory()
        if shm_data:
            self._status = ProviderStatus.RUNNING
            return True

        # 2. Проверяем наличие бинарного файла
        if self.binary_path and os.path.isfile(self.binary_path):
            self._status = ProviderStatus.AVAILABLE
            return True

        self._status = ProviderStatus.NOT_FOUND
        return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Список поддерживаемых возможностей AIDA64."""
        return [
            ProviderCapability.CPU_INVENTORY,
            ProviderCapability.MOTHERBOARD_INVENTORY,
            ProviderCapability.RAM_INVENTORY,
            ProviderCapability.GPU_INVENTORY,
            ProviderCapability.STORAGE_INVENTORY,
            ProviderCapability.LIVE_SENSORS,
            ProviderCapability.SHARED_MEMORY,
            ProviderCapability.OFFLINE_REPORT,
        ]

    def _read_shared_memory(self) -> Optional[str]:
        """Прочитать XML-строку сенсоров из Shared Memory 'AIDA64_SensorValues'."""
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.OpenFileMappingW.restype = wintypes.HANDLE
            kernel32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]

            kernel32.MapViewOfFile.restype = wintypes.LPVOID
            kernel32.MapViewOfFile.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.c_size_t,
            ]

            kernel32.UnmapViewOfFile.restype = wintypes.BOOL
            kernel32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]

            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

            h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHM_AIDA64_NAME)
            if not h_map:
                return None

            p_buf = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, 0)
            if not p_buf:
                kernel32.CloseHandle(h_map)
                return None

            try:
                # Читаем строку из памяти в формате ANSI/UTF-8
                raw_bytes = ctypes.string_at(p_buf)
                # AIDA64 отдает XML-подобную структуру: <root><temp>...</temp></root>
                text = raw_bytes.decode("utf-8", errors="ignore")
                return text
            finally:
                kernel32.UnmapViewOfFile(p_buf)
                kernel32.CloseHandle(h_map)

        except Exception as e:
            logger.debug(f"AIDA64 Shared Memory не доступна: {e}")
            return None

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать данные сенсоров из Shared Memory."""
        xml_text = self._read_shared_memory()
        if not xml_text:
            return None

        snapshot = SensorSnapshot(source_provider=self.name)
        try:
            # Оборачиваем во фрагмент root, если AIDA64 отдает без корня
            if not xml_text.strip().startswith("<root>"):
                xml_text = f"<root>{xml_text}</root>"

            root = ET.fromstring(xml_text)
            for elem in root:
                tag = elem.tag.lower()  # temp, fan, volt, pwr, duty
                sensor_id = elem.findtext("id") or elem.attrib.get("id", "")
                label = elem.findtext("label") or elem.attrib.get("label", sensor_id)
                val_str = elem.findtext("value") or elem.attrib.get("value", "")

                try:
                    val = float(val_str)
                except ValueError:
                    continue

                sensor_type = "Generic"
                unit = ""
                if tag == "temp":
                    sensor_type = "Temperature"
                    unit = "°C"
                elif tag == "fan":
                    sensor_type = "Fan"
                    unit = "RPM"
                elif tag == "volt":
                    sensor_type = "Voltage"
                    unit = "V"
                elif tag == "pwr":
                    sensor_type = "Power"
                    unit = "W"

                hw_type = "CPU" if "cpu" in label.lower() else "GPU" if "gpu" in label.lower() else "System"

                snapshot.sensors.append(
                    SensorReading(
                        name=label,
                        sensor_type=sensor_type,
                        value=val,
                        unit=unit,
                        hardware_name=hw_type,
                        hardware_type=hw_type,
                    )
                )
            return snapshot
        except Exception as e:
            logger.error(f"Ошибка парсинга XML сенсоров AIDA64: {e}")
            return None

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать инвентарь оборудования через silent отчет CLI."""
        if not self.binary_path or not os.path.isfile(self.binary_path):
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_file = os.path.join(tmpdir, "aida_report.xml")
                cmd = [
                    self.binary_path,
                    "/R",
                    report_file,
                    "/XML",
                    "/HW",
                    "/SILENT",
                ]
                logger.debug(f"Запуск AIDA64 CLI: {' '.join(cmd)}")
                res = subprocess.run(cmd, capture_output=True, timeout=30)
                if os.path.exists(report_file):
                    return self._parse_xml_report(report_file)
        except Exception as e:
            logger.error(f"Ошибка вызова AIDA64 CLI: {e}")

        return None

    def _parse_xml_report(self, report_path: str) -> SystemHardwareInventory:
        """Парсинг официального XML отчета AIDA64."""
        inv = SystemHardwareInventory(sources_used=[self.name])
        try:
            tree = ET.parse(report_path)
            root = tree.getroot()

            # Извлечение данных CPU и Материнской платы
            cpu_name = root.findtext(".//CPU/Name") or "AIDA64 Detected CPU"
            inv.cpu = CpuInventory(
                model_name=cpu_name,
                source_provider=self.name,
            )

            mb_name = root.findtext(".//Motherboard/Name") or "AIDA64 Detected Motherboard"
            inv.motherboard = MotherboardInventory(
                product_name=mb_name,
                source_provider=self.name,
            )
        except Exception as e:
            logger.error(f"Ошибка разбора отчета AIDA64: {e}")

        return inv
