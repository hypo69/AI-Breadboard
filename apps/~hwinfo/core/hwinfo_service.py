# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HWiNFO Standalone Service
# =============================================================================
# Description:
#   Ядро интеграции с HWiNFO: Shared Memory, SDK DLL и CLI (-j JSON, -l).
#
# File: hwinfo_service.py
# Project: ai-breadboard
# Package: apps.hwinfo.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис интеграции с HWiNFO."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from logger import logger
from apps.common.discovery import UtilityDiscovery

FILE_MAP_READ = 0x0004
SHM_HWINFO_NAME = "Global\\HWiNFO_SENS_SM2"


class HwinfoService:
    """Сервис для сбора данных и запуска отчетов HWiNFO."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация сервиса HWiNFO."""
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility("hwinfo")

    def is_running(self) -> bool:
        """Проверить активность Shared Memory HWiNFO."""
        try:
            kernel32 = ctypes.windll.kernel32
            h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHM_HWINFO_NAME)
            if h_map:
                kernel32.CloseHandle(h_map)
                return True
        except Exception:
            pass
        return False

    def is_binary_available(self) -> bool:
        """Проверить наличие исполняемого файла HWiNFO."""
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def generate_json_report(self) -> Optional[Dict[str, Any]]:
        """Сгенерировать подробный JSON-отчет оборудования через HWiNFO CLI (-j)."""
        if not self.is_binary_available() or not self.binary_path:
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_file = os.path.join(tmpdir, "hwinfo_report.json")
                cmd = [self.binary_path, f"-j{report_file}"]
                subprocess.run(cmd, capture_output=True, timeout=25)
                if os.path.exists(report_file):
                    with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
                        return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка вызова HWiNFO CLI: {e}")
        return None

    def get_live_sensors(self) -> List[Dict[str, Any]]:
        """Собрать данные сенсоров HWiNFO."""
        if not self.is_binary_available() or not self.binary_path:
            return []

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                log_json = os.path.join(tmpdir, "hwinfo_sensors.json")
                cmd = [self.binary_path, f"-l{log_json}"]
                subprocess.run(cmd, capture_output=True, timeout=10)
                if os.path.exists(log_json):
                    with open(log_json, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        return data.get("Sensors", [])
        except Exception as e:
            logger.debug(f"Ошибка получения сенсоров HWiNFO: {e}")
        return []
