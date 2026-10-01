# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Audit Startup Checker
# =============================================================================
# Description:
#   Проверка критических аудитов при запуске приложения.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.audit_startup_checker import StartupAuditResult
#
#     service = StartupAuditResult()
#
# File: audit_startup_checker.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Проверка критических аудитов при запуске приложения."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class StartupAuditResult:
    """Результат проверки аудитов при запуске."""
    is_healthy: bool
    critical_count: int = 0
    warning_count: int = 0
    findings: List[Dict[str, Any]] = field(default_factory=list)
    checks_passed: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_healthy': self.is_healthy,
            'critical_count': self.critical_count,
            'warning_count': self.warning_count,
            'findings': self.findings,
            'checks_passed': self.checks_passed,
            'duration_ms': self.duration_ms
        }


class AuditStartupChecker:
    """Проверяет критические состояния системы при запуске."""
    
    def __init__(self) -> None:
        """Инициализирует чекер с ленивой загрузкой коллекторов."""
        self._integrity_collector = None
        self._performance_collector = None
        self._driver_collector = None
        self._eventlog_collector = None
    
    def _get_integrity_collector(self):
        """Ленивая загрузка IntegrityCollector."""
        if self._integrity_collector is None:
            from apps.windows.core.audits.integrity_collector import IntegrityCollector
            self._integrity_collector = IntegrityCollector()
        return self._integrity_collector
    
    def _get_performance_collector(self):
        """Ленивая загрузка PerformanceCollector."""
        if self._performance_collector is None:
            from apps.windows.core.audits.performance_collector import PerformanceCollector
            self._performance_collector = PerformanceCollector()
        return self._performance_collector
    
    def _get_driver_collector(self):
        """Ленивая загрузка DriverCollector."""
        if self._driver_collector is None:
            from apps.windows.core.audits.driver_collector import DriverCollector
            self._driver_collector = DriverCollector()
        return self._driver_collector
    
    def _get_eventlog_collector(self):
        """Ленивая загрузка EventLogCollector."""
        if self._eventlog_collector is None:
            from apps.windows.core.audits.eventlog_collector import EventLogCollector
            self._eventlog_collector = EventLogCollector()
        return self._eventlog_collector
    
    def check_startup_health(
        self,
        check_integrity: bool = True,
        check_performance: bool = True,
        check_drivers: bool = False,
        check_eventlog: bool = False,
        eventlog_hours: int = 1
    ) -> StartupAuditResult:
        """Выполняет быструю проверку критических состояний при запуске.
        
        Args:
            check_integrity: Проверять pending reboot и целостность системы.
            check_performance: Проверять критическую загрузку CPU/RAM.
            check_drivers: Проверять проблемные драйверы (медленнее).
            check_eventlog: Проверять критические события в логах (медленнее).
            eventlog_hours: Сколько часов логов анализировать.
            
        Returns:
            StartupAuditResult с результатами проверки.
        """
        start_t = time.perf_counter()
        result = StartupAuditResult(is_healthy=True)
        
        # 1. Проверка целостности (pending reboot) - быстро
        if check_integrity:
            try:
                integrity = self._get_integrity_collector().collect()
                pending_reboot = integrity.metrics.get('pending_reboot', False)
                
                if pending_reboot:
                    result.findings.append({
                        'domain': 'integrity',
                        'severity': 'warning',
                        'title': 'Требуется перезагрузка системы',
                        'description': 'Обнаружены отложенные операции, требующие перезагрузки'
                    })
                    result.warning_count += 1
                else:
                    result.checks_passed.append('integrity: no pending reboot')
                    
            except Exception as e:
                logger.warning(f'Ошибка при проверке целостности: {e}')
                result.checks_passed.append('integrity: check skipped')
        
        # 2. Проверка производительности - быстро
        if check_performance:
            try:
                perf = self._get_performance_collector().collect()
                cpu_pct = perf.metrics.get('cpu_percent', 0.0)
                mem_pct = perf.metrics.get('memory_percent', 0.0)
                
                if cpu_pct >= 90.0:
                    result.findings.append({
                        'domain': 'performance',
                        'severity': 'critical',
                        'title': f'Критическая загрузка CPU: {cpu_pct:.1f}%',
                        'description': 'Процессор загружен более 90% при запуске'
                    })
                    result.critical_count += 1
                    result.is_healthy = False
                elif cpu_pct >= 75.0:
                    result.findings.append({
                        'domain': 'performance',
                        'severity': 'warning',
                        'title': f'Повышенная загрузка CPU: {cpu_pct:.1f}%',
                        'description': 'Процессор загружен более 75% при запуске'
                    })
                    result.warning_count += 1
                else:
                    result.checks_passed.append(f'performance: CPU {cpu_pct:.1f}%')
                
                if mem_pct >= 90.0:
                    result.findings.append({
                        'domain': 'performance',
                        'severity': 'critical',
                        'title': f'Критическая загрузка RAM: {mem_pct:.1f}%',
                        'description': 'Оперативная память заполнена более 90% при запуске'
                    })
                    result.critical_count += 1
                    result.is_healthy = False
                elif mem_pct >= 80.0:
                    result.findings.append({
                        'domain': 'performance',
                        'severity': 'warning',
                        'title': f'Высокая загрузка RAM: {mem_pct:.1f}%',
                        'description': 'Оперативная память заполнена более 80%'
                    })
                    result.warning_count += 1
                else:
                    result.checks_passed.append(f'performance: RAM {mem_pct:.1f}%')
                    
            except Exception as e:
                logger.warning(f'Ошибка при проверке производительности: {e}')
                result.checks_passed.append('performance: check skipped')
        
        # 3. Проверка драйверов - опционально, медленнее
        if check_drivers:
            try:
                drivers = self._get_driver_collector().collect()
                problem_count = sum(
                    1 for f in drivers.findings 
                    if f.severity.value in ('critical', 'caution')
                )
                
                if problem_count > 0:
                    result.findings.append({
                        'domain': 'drivers',
                        'severity': 'warning',
                        'title': f'Обнаружено проблем с драйверами: {problem_count}',
                        'description': 'Проверьте раздел драйверов для деталей'
                    })
                    result.warning_count += 1
                else:
                    result.checks_passed.append('drivers: no problems')
                    
            except Exception as e:
                logger.warning(f'Ошибка при проверке драйверов: {e}')
                result.checks_passed.append('drivers: check skipped')
        
        # 4. Проверка критических событий в логах - опционально, медленнее
        if check_eventlog:
            try:
                events = self._get_eventlog_collector().collect(hours=eventlog_hours)
                critical_events = [
                    f for f in events.findings 
                    if f.severity.value == 'critical'
                ]
                
                if critical_events:
                    result.findings.append({
                        'domain': 'eventlog',
                        'severity': 'warning',
                        'title': f'Критические события в логах: {len(critical_events)}',
                        'description': 'Обнаружены критические события за последние часы'
                    })
                    result.warning_count += 1
                else:
                    result.checks_passed.append('eventlog: no critical events')
                    
            except Exception as e:
                logger.warning(f'Ошибка при проверке логов: {e}')
                result.checks_passed.append('eventlog: check skipped')
        
        result.duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        
        # Логируем результат
        if result.critical_count > 0:
            logger.error(
                f'Startup audit: CRITICAL issues found: {result.critical_count}, '
                f'warnings: {result.warning_count}'
            )
        elif result.warning_count > 0:
            logger.warning(
                f'Startup audit: warnings found: {result.warning_count}, '
                f'checks passed: {len(result.checks_passed)}'
            )
        else:
            logger.info(
                f'Startup audit: all checks passed ({result.duration_ms}ms)'
            )
        
        return result
    
    def check_pending_reboot_only(self) -> bool:
        """Быстрая проверка только pending reboot.
        
        Returns:
            True если требуется перезагрузка, False иначе.
        """
        try:
            integrity = self._get_integrity_collector().collect()
            return integrity.metrics.get('pending_reboot', False)
        except Exception as e:
            logger.warning(f'Ошибка при проверке pending reboot: {e}')
            return False


def run_startup_audit(
    check_integrity: bool = True,
    check_performance: bool = True,
    check_drivers: bool = False,
    check_eventlog: bool = False
) -> StartupAuditResult:
    """Утилитарная функция для запуска проверки из точки входа.
    
    Args:
        check_integrity: Проверять pending reboot.
        check_performance: Проверять CPU/RAM.
        check_drivers: Проверять драйверы.
        check_eventlog: Проверять логи событий.
        
    Returns:
        StartupAuditResult с результатами.
    """
    checker = AuditStartupChecker()
    return checker.check_startup_health(
        check_integrity=check_integrity,
        check_performance=check_performance,
        check_drivers=check_drivers,
        check_eventlog=check_eventlog
    )
