# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Audits - Performance Collector
# =============================================================================
# Description:
#   Коллектор аудита производительности и автозагрузки Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.audits.performance_collector import PerformanceCollector
#
#     service = PerformanceCollector()
#
# File: performance_collector.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core.audits
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:20:00
# =============================================================================

from __future__ import annotations
"""Коллектор аудита производительности и автозагрузки Windows."""

import time
import winreg
from typing import Any, Dict, List
import psutil
from logger import logger
from apps.windows.sdk.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel
from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider

class PerformanceCollector(TelemetryProvider):
    """Коллектор фактов производительности и точек автозагрузки."""

    def __init__(self) -> None:
        self._last_result: Optional[DomainAuditResult] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели производительности как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            metrics = self._last_result.metrics
            sensors.append(HardwareSensor(sensor_id='perf_cpu_percent', name='Загрузка CPU (%)', category='performance', value=float(metrics.get('cpu_percent', 0.0)), unit='%'))
            sensors.append(HardwareSensor(sensor_id='perf_memory_percent', name='Загрузка RAM (%)', category='performance', value=float(metrics.get('memory_percent', 0.0)), unit='%'))
            sensors.append(HardwareSensor(sensor_id='perf_uptime_hours', name='Время работы системы (ч)', category='performance', value=float(metrics.get('uptime_hours', 0.0)), unit='hours'))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор данных о производительности и автозапуске."""
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        try:
            cpu_pct = float(psutil.cpu_percent(interval=0.1))
        except Exception:
            cpu_pct = 0.0
        try:
            mem = psutil.virtual_memory()
            mem_pct = float(mem.percent)
            mem_used = round(mem.used / 1024 ** 3, 2)
            mem_total = round(mem.total / 1024 ** 3, 2)
        except Exception:
            mem_pct, mem_used, mem_total = (0.0, 0.0, 0.0)
        try:
            swap = psutil.swap_memory()
            swap_pct = float(swap.percent)
        except Exception:
            swap_pct = 0.0
        try:
            boot_time = psutil.boot_time()
            uptime_hours = round((time.time() - boot_time) / 3600.0, 2)
        except Exception:
            uptime_hours = 0.0
        startup_items = self._get_registry_startup()
        if cpu_pct >= 90.0:
            action = RemediationAction(action_id='perf_cpu_high', action_type=ActionType.KILL_PROCESS, title='Завершение ресурсоемких процессов', description='Завершите процессы, утилизирующие большую часть ресурсов процессора.', target='CPU', risk=RiskLevel.CAUTION)
            findings.append(AuditFinding(domain='performance', category='cpu', title=f'Критическая загрузка процессора: {cpu_pct:.1f}%', description='Процессор загружен более чем на 90%, возможны зависания и задержки отклика.', severity=RiskLevel.CRITICAL, actions=[action]))
        elif cpu_pct >= 75.0:
            findings.append(AuditFinding(domain='performance', category='cpu', title=f'Повышенная нагрузка CPU: {cpu_pct:.1f}%', description='Процессор загружен выше нормального рабочего диапазона.', severity=RiskLevel.CAUTION))
        if mem_pct >= 90.0:
            findings.append(AuditFinding(domain='performance', category='memory', title=f'Критическое заполнение оперативной памяти: {mem_pct:.1f}% ({mem_used} GB / {mem_total} GB)', description='Оперативная память почти исчерпана, система может активно использовать файл подкачки.', severity=RiskLevel.CRITICAL))
        if len(startup_items) > 15:
            findings.append(AuditFinding(domain='performance', category='startup', title=f'Большое количество программ в автозагрузке ({len(startup_items)})', description='Множество программ в реестре автозапуска замедляют старт Windows.', severity=RiskLevel.CAUTION))
        metrics: Dict[str, Any] = {'cpu_percent': cpu_pct, 'memory_percent': mem_pct, 'memory_used_gb': mem_used, 'memory_total_gb': mem_total, 'swap_percent': swap_pct, 'uptime_hours': uptime_hours, 'startup_items_count': len(startup_items)}
        duration_ms = (time.perf_counter() - start_t) * 1000
        status = 'ok'
        if any((f.severity == RiskLevel.CRITICAL for f in findings)):
            status = 'critical'
        elif any((f.severity == RiskLevel.CAUTION for f in findings)):
            status = 'warning'
        result = DomainAuditResult(domain_name='performance', title_ru='Производительность и автозагрузка', status=status, findings=findings, metrics=metrics, scan_duration_ms=round(duration_ms, 2))
        self._last_result = result
        return result

    def _get_registry_startup(self) -> List[Dict[str, str]]:
        """Извлечение записей из веток Run (HKCU и HKLM)."""
        items: List[Dict[str, str]] = []
        paths = [(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run'), (winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run')]
        for hive, subkey in paths:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(key, i)
                            hive_name = 'HKCU' if hive == winreg.HKEY_CURRENT_USER else 'HKLM'
                            items.append({'name': name, 'command': str(val), 'location': f'{hive_name}\\{subkey}'})
                            i += 1
                        except OSError:
                            break
            except (OSError, PermissionError):
                pass
        return items