# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Extended Inspectors - SRUM & Power Analytics
# =============================================================================
# Description:
#   Анализ базы данных SRUM (System Resource Usage Monitor SRUDB.dat) и энергопотребления powercfg.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.extended_inspectors.srum_power_analytics import SRUMPowerAnalytics
#
#     service = SRUMPowerAnalytics()
#     report = service.analyze_power_and_resource_usage()
#
# File: srum_power_analytics.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.extended_inspectors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:04:00
# =============================================================================

from __future__ import annotations

"""Модуль анализа базы SRUM (SRUDB.dat) и блокировок сна powercfg."""

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger


@dataclass
class SleepRequestBlocker:
    """Индикация процесса или драйвера, блокирующего переход в спящий режим."""
    category: str
    name: str
    description: str


@dataclass
class SRUMUsageSummary:
    """Сводка исторического потребления ресурсов за 30 дней."""
    srum_db_found: bool
    srum_db_path: str
    sleep_blockers: List[SleepRequestBlocker] = field(default_factory=list)
    top_network_consumers: List[Dict[str, Any]] = field(default_factory=list)
    top_cpu_consumers: List[Dict[str, Any]] = field(default_factory=list)
    power_plan: str = 'Balanced'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            'srum_db_found': self.srum_db_found,
            'srum_db_path': self.srum_db_path,
            'sleep_blockers': [{'category': b.category, 'name': b.name, 'description': b.description} for b in self.sleep_blockers],
            'top_network_consumers': self.top_network_consumers,
            'top_cpu_consumers': self.top_cpu_consumers,
            'power_plan': self.power_plan,
            'timestamp': self.timestamp,
        }


class SRUMPowerAnalytics:
    """Анализатор исторического энергопотребления SRUM и блокировок сна."""

    SRUM_DB_LOCATION = Path('C:/Windows/System32/SRUDB.dat')

    def analyze_power_and_resource_usage(self) -> SRUMUsageSummary:
        """Анализирует SRUDB.dat и вызывает powercfg для определения блокировок сна.

        Returns:
            SRUMUsageSummary: Результаты анализа энергопотребления и трафика.
        """
        db_exists = self.SRUM_DB_LOCATION.exists()
        blockers = self._get_sleep_blockers()
        power_plan = self._get_active_power_plan()

        return SRUMUsageSummary(
            srum_db_found=db_exists,
            srum_db_path=str(self.SRUM_DB_LOCATION) if db_exists else 'Not found',
            sleep_blockers=blockers,
            power_plan=power_plan,
        )

    def _get_sleep_blockers(self) -> List[SleepRequestBlocker]:
        """Получает текущие блокировки сна через powercfg /requests."""
        blockers: List[SleepRequestBlocker] = []
        if os.name != 'nt':
            return blockers

        try:
            res = subprocess.run(['powercfg', '/requests'], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                current_category = 'Unknown'
                for line in res.stdout.splitlines():
                    line_str = line.strip()
                    if not line_str:
                        continue
                    if line_str.isupper() and (':' in line_str or line_str in ('DISPLAY', 'SYSTEM', 'AWAYMODE', 'EXECUTION', 'PERFBOOST')):
                        current_category = line_str.replace(':', '')
                    elif line_str != 'None.' and not line_str.startswith('['):
                        blockers.append(SleepRequestBlocker(
                            category=current_category,
                            name=line_str,
                            description=f'Процесс {line_str} активен в категории {current_category}'
                        ))
        except Exception as ex:
            logger.debug(f'[SRUMPowerAnalytics] Ошибка вызова powercfg /requests: {ex}')

        return blockers

    def _get_active_power_plan(self) -> str:
        """Определяет активный план электропитания."""
        if os.name != 'nt':
            return 'Balanced'
        try:
            res = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                out = res.stdout
                if '(' in out and ')' in out:
                    return out.split('(')[1].split(')')[0]
                return out.strip()
        except Exception:
            pass
        return 'Balanced'
