# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Windows Startup Auditor Analysis
# =============================================================================
# Description:
#   Модульные тесты для правил анализа безопасности, классификации и
#   расчета Health Score аудитора автозапуска.
#
# Examples:
#   $ pytest apps/windows_startup_auditor/tests/test_auditor.py -v
#
# File: test_auditor.py
# Project: ai-breadboard
# Package: apps.windows.startup.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты движка аудита StartupAuditor."""

from apps.windows.startup.core.auditor import StartupAuditor
from apps.windows.startup.core.models import (
    ItemCategory,
    RiskLevel,
    StartupEntry,
    StartupLocationType,
)


def test_audit_ifeo_critical_risk() -> None:
    """Проверка присвоения критического риска для IFEO перехватов."""
    auditor = StartupAuditor()
    entry = StartupEntry(
        id="ifeo_sethc",
        name="IFEO Перехват: sethc.exe",
        location_type=StartupLocationType.IFEO,
        executable_path=r"C:\malware\hack.exe",
        command=r"C:\malware\hack.exe",
    )
    audited = auditor._audit_entry(entry)
    assert audited.risk_level == RiskLevel.CRITICAL
    assert "IFEO Debugger" in audited.risk_reasons[0]


def test_audit_broken_entry_warning() -> None:
    """Проверка обнаружения битой ссылки автозапуска."""
    auditor = StartupAuditor()
    entry = StartupEntry(
        id="reg_broken",
        name="DeletedApp",
        location_type=StartupLocationType.REGISTRY_RUN,
        executable_path=r"C:\NonExistentFolder\ghost.exe",
        file_exists=False,
    )
    audited = auditor._audit_entry(entry)
    assert audited.risk_level == RiskLevel.WARNING
    assert audited.category == ItemCategory.BROKEN_ENTRY


def test_audit_hidden_powershell_critical_risk() -> None:
    """Проверка обнаружения скрытого запуска закодированного скрипта."""
    auditor = StartupAuditor()
    entry = StartupEntry(
        id="reg_ps_hidden",
        name="SuspiciousScript",
        location_type=StartupLocationType.REGISTRY_RUN,
        command="powershell.exe -w hidden -enc JAB4ACAAPQAgACIAYQBkAG0AaQBuACIA",
        executable_path=r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        arguments="-w hidden -enc JAB4ACAAPQAgACIAYQBkAG0AaQBuACIA",
        file_exists=True,
    )
    audited = auditor._audit_entry(entry)
    assert audited.risk_level == RiskLevel.CRITICAL
    assert audited.category == ItemCategory.SUSPICIOUS_SCRIPT


def test_audit_temp_path_suspicious_risk() -> None:
    """Проверка обнаружения запуска из временного каталога."""
    auditor = StartupAuditor()
    entry = StartupEntry(
        id="reg_temp_run",
        name="TempDropper",
        location_type=StartupLocationType.REGISTRY_RUN,
        executable_path=r"C:\Users\John\AppData\Local\Temp\drop.exe",
        command=r"C:\Users\John\AppData\Local\Temp\drop.exe",
        file_exists=True,
    )
    audited = auditor._audit_entry(entry)
    assert audited.risk_level == RiskLevel.SUSPICIOUS


def test_audit_clean_system_component() -> None:
    """Проверка доверенного системного компонента."""
    auditor = StartupAuditor()
    entry = StartupEntry(
        id="reg_ms_sys",
        name="SecurityHealth",
        location_type=StartupLocationType.REGISTRY_RUN,
        executable_path=r"C:\Windows\System32\SecurityHealthSystray.exe",
        publisher="Microsoft Corporation",
        is_signed=True,
        file_exists=True,
    )
    audited = auditor._audit_entry(entry)
    assert audited.risk_level == RiskLevel.CLEAN
    assert audited.category == ItemCategory.SYSTEM_CORE


def test_build_summary_calculation() -> None:
    """Проверка подсчета метрик сводки и индекса чистоты."""
    auditor = StartupAuditor()
    entries = [
        StartupEntry(id="1", name="App1", risk_level=RiskLevel.CLEAN, is_enabled=True),
        StartupEntry(id="2", name="App2", risk_level=RiskLevel.WARNING, is_enabled=True, file_exists=False),
        StartupEntry(id="3", name="App3", risk_level=RiskLevel.CRITICAL, is_enabled=True),
    ]
    summary = auditor._build_summary(entries)
    assert summary.total_entries == 3
    assert summary.active_entries == 3
    assert summary.critical_count == 1
    assert summary.warning_count == 1
    # 100 - 25 (critical) - 5 (warning) = 70
    assert summary.health_score == 70
