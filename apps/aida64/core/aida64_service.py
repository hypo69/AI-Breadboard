# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 Standalone Service
# =============================================================================
# Description:
#   Ядро интеграции с AIDA64: чтение WinAPI Shared Memory ('AIDA64_SensorValues'),
#   WMI, реестра и запуск отчетов через CLI (/R /XML /HW /SILENT).
#
# File: aida64_service.py
# Project: ai-breadboard
# Package: apps.aida64.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис интеграции с AIDA64."""

from __future__ import annotations

import ctypes
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from ctypes import wintypes
from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.common.discovery import UtilityDiscovery

FILE_MAP_READ = 0x0004
SHM_AIDA64_NAME = "AIDA64_SensorValues"


class Aida64Service:
    """Сервис для сбора данных сенсоров и генерации отчетов AIDA64."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация сервиса с авто-поиском бинарника."""
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility("aida64")

    def is_running(self) -> bool:
        """Проверить, запущен ли AIDA64 и активна ли Shared Memory."""
        text = self.read_shared_memory()
        return text is not None and len(text) > 0

    def is_binary_available(self) -> bool:
        """Проверить наличие бинарного файла AIDA64."""
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def read_shared_memory(self) -> Optional[str]:
        """Чтение строки XML из Shared Memory 'AIDA64_SensorValues'."""
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
                raw_bytes = ctypes.string_at(p_buf)
                return raw_bytes.decode("utf-8", errors="ignore")
            finally:
                kernel32.UnmapViewOfFile(p_buf)
                kernel32.CloseHandle(h_map)
        except Exception as e:
            logger.debug(f"AIDA64 Shared Memory недоступна: {e}")
            return None

    def get_live_sensors(self) -> List[Dict[str, Any]]:
        """Получить список распарсенных сенсоров реального времени."""
        xml_text = self.read_shared_memory()
        if not xml_text:
            return []

        sensors: List[Dict[str, Any]] = []
        try:
            if not xml_text.strip().startswith("<root>"):
                xml_text = f"<root>{xml_text}</root>"

            root = ET.fromstring(xml_text)
            for elem in root:
                tag = elem.tag.lower()
                sensor_id = elem.findtext("id") or elem.attrib.get("id", "")
                label = elem.findtext("label") or elem.attrib.get("label", sensor_id)
                val_str = elem.findtext("value") or elem.attrib.get("value", "")

                try:
                    val = float(val_str)
                except ValueError:
                    continue

                unit = "°C" if tag == "temp" else "RPM" if tag == "fan" else "V" if tag == "volt" else "W" if tag == "pwr" else ""
                sensors.append({
                    "id": sensor_id,
                    "label": label,
                    "type": tag.capitalize(),
                    "value": val,
                    "unit": unit,
                })
        except Exception as e:
            logger.error(f"Ошибка парсинга XML сенсоров AIDA64: {e}")

        return sensors

    def generate_report(self, report_type: str = "HW") -> Optional[Dict[str, Any]]:
        """Сгенерировать отчет оборудования через AIDA64 CLI."""
        if not self.is_binary_available() or not self.binary_path:
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_file = os.path.join(tmpdir, "aida_report.xml")
                cmd = [self.binary_path, "/R", report_file, "/XML", f"/{report_type}", "/SILENT"]
                subprocess.run(cmd, capture_output=True, timeout=30)
                if os.path.exists(report_file):
                    tree = ET.parse(report_file)
                    root = tree.getroot()
                    return {
                        "status": "SUCCESS",
                        "report_file": report_file,
                        "cpu": root.findtext(".//CPU/Name") or "AIDA64 CPU",
                        "motherboard": root.findtext(".//Motherboard/Name") or "AIDA64 Motherboard",
                    }
        except Exception as e:
            logger.error(f"Ошибка запуска AIDA64 CLI: {e}")
        return None
