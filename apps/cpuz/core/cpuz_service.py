# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CPU-Z Standalone Service
# =============================================================================
# Description:
#   Ядро интеграции с CPU-Z: Ghost mode CLI (-txt=...), глубокий аудит CPU,
#   топологии ядер, кэшей, материнской платы и таймингов памяти.
#
# File: cpuz_service.py
# Project: ai-breadboard
# Package: apps.cpuz.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис интеграции с CPU-Z."""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

from src.logger import logger
from apps.common.discovery import UtilityDiscovery


class CpuzService:
    """Сервис для запуска и разбора отчетов CPU-Z."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        """Инициализация сервиса CPU-Z."""
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility("cpuz")

    def is_available(self) -> bool:
        """Проверить наличие исполняемого файла cpuz.exe."""
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def generate_report(self) -> Optional[Dict[str, Any]]:
        """Сгенерировать и распарсить текстовый отчет CPU-Z."""
        if not self.is_available() or not self.binary_path:
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_prefix = os.path.join(tmpdir, "cpuz_out")
                cmd = [self.binary_path, f"-txt={report_prefix}"]
                subprocess.run(cmd, capture_output=True, timeout=15)
                txt_path = f"{report_prefix}.txt"
                if os.path.exists(txt_path):
                    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                        return self._parse_txt(f.read())
        except Exception as e:
            logger.error(f"Ошибка вызова CPU-Z CLI: {e}")
        return None

    def _parse_txt(self, content: str) -> Dict[str, Any]:
        """Разбор текстового отчета CPU-Z."""
        res: Dict[str, Any] = {
            "cpu_name": "Unknown",
            "socket": None,
            "cores": None,
            "threads": None,
            "motherboard_model": None,
            "motherboard_vendor": None,
        }
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("Name") and "Specification" not in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["cpu_name"] = parts[-1].strip()
            elif "Package" in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["socket"] = parts[-1].strip()
            elif line_str.startswith("Number of cores"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["cores"] = parts[-1].strip()
            elif line_str.startswith("Number of threads"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["threads"] = parts[-1].strip()
            elif line_str.startswith("Mainboard Model"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["motherboard_model"] = parts[-1].strip()
            elif line_str.startswith("Mainboard Vendor"):
                parts = line_str.split("\t")
                if len(parts) > 1:
                    res["motherboard_vendor"] = parts[-1].strip()
        return res
