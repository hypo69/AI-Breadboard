# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Diagnostics Checks
# =============================================================================
# Description:
#   Тестирование всех 40+ диагностических проверок DiagnosticsEngine.
#
# File: test_diagnostics_checks.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 04:58:00
# =============================================================================

"""Тестирование функциональных проверок движка диагностики Windows."""

import pytest
from apps.windows.sdk.core.data_model import (
    SystemState, ProcessInfo, ModuleInfo, ServiceInfo, DriverInfo, ServiceState, MemoryInfo
)
from apps.windows.sdk.core.diagnostics import DiagnosticsEngine, Severity


@pytest.fixture
def mock_system_state() -> SystemState:
    """Создает тестовое состояние системы с процессами, службами и модулями."""
    proc1 = ProcessInfo(
        pid=100, ppid=4, name='svchost.exe', executable='C:\\Windows\\System32\\svchost.exe',
        is_signed=True, elevation='Full',
        modules=[
            ModuleInfo(name='ws2_32.dll', path='C:\\Windows\\System32\\ws2_32.dll', is_signed=True),
            ModuleInfo(name='custom.dll', path='C:\\Users\\User\\AppData\\Local\\Temp\\custom.dll', is_signed=False)
        ]
    )
    proc2 = ProcessInfo(
        pid=200, ppid=100, name='unsigned_app.exe', executable='C:\\Users\\User\\Downloads\\app.exe',
        is_signed=False, elevation='Full'
    )
    svc1 = ServiceInfo(
        name='UnquotedSvc', display_name='Unquoted Service', current_state=ServiceState.RUNNING,
        executable='C:\\Program Files\\My App\\service.exe', is_signed=False
    )
    drv1 = DriverInfo(
        name='my_driver.sys', display_name='My Driver', service_name='UnquotedSvc',
        path='C:\\Windows\\System32\\drivers\\my_driver.sys', is_signed=True
    )
    
    return SystemState(
        hostname='TEST-PC',
        processes=[proc1, proc2],
        services=[svc1],
        drivers=[drv1],
        system_memory=MemoryInfo(working_set=1024*1024*1024, paged_pool=50*1024*1024, nonpaged_pool=30*1024*1024)
    )


def test_diagnostics_engine_run_all_checks(mock_system_state: SystemState):
    """Проверяет выполнение всех зарегистрированных диагностических проверок без заглушек Not yet implemented."""
    engine = DiagnosticsEngine()
    results = engine.run_all_checks(mock_system_state)
    
    assert len(results) >= 40, f"Ожидалось не менее 40 проверок, получено: {len(results)}"
    
    for r in results:
        assert "Not yet implemented" not in r.message, f"Обнаружена заглушка в проверке {r.check_id}: {r.message}"
    
    summary = engine.get_summary(results)
    assert summary['total_checks'] == len(results)
    assert 'success_rate' in summary


def test_diagnostics_category_checks(mock_system_state: SystemState):
    """Проверяет запуск фильтрованных категорий диагностики (proc, mem, svc, drv, sec)."""
    engine = DiagnosticsEngine()
    proc_results = engine.run_category_checks(mock_system_state, 'proc')
    assert len(proc_results) > 0
    assert all(r.check_id.startswith('proc_') for r in proc_results)
