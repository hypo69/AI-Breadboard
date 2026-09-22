# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: smartmontools Standalone Service
# =============================================================================
# Description:
#   Ядро интеграции со smartmontools: выполнение smartctl.exe --json,
#   сканирование дисков, детальный анализ SMART и NVMe здоровья накопителей.
#
# File: smartctl_service.py
# Project: ai-breadboard
# Package: apps.smartmontools.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис интеграции со smartmontools (smartctl)."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from logger import logger
from apps.common.discovery import UtilityDiscovery


class SmartctlService:
    """Сервис для выполнения smartctl команд и парсинга SMART данных."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация сервиса smartmontools."""
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility("smartmontools") or discovery.find_utility("smartctl")

    def is_available(self) -> bool:
        """Проверить наличие исполняемого файла smartctl.exe."""
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def scan_devices(self) -> List[Dict[str, Any]]:
        """Сканирование доступных физических накопителей."""
        if not self.is_available() or not self.binary_path:
            return []

        try:
            cmd = [self.binary_path, "--scan", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.stdout.strip():
                data = json.loads(res.stdout)
                return data.get("devices", [])
        except Exception as e:
            logger.error(f"Ошибка сканирования smartctl: {e}")
        return []

    def get_device_health(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Получить полные диагностические данные по конкретному диску."""
        if not self.is_available() or not self.binary_path:
            return None

        try:
            cmd = [self.binary_path, "-x", device_name, "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.stdout.strip():
                return json.loads(res.stdout)
        except Exception as e:
            logger.error(f"Ошибка получения SMART данных диска {device_name}: {e}")
        return None
