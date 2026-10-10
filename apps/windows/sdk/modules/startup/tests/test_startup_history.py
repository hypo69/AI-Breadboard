# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Startup Tests - History Manager
# =============================================================================
# Description:
#   Модульные тесты менеджера дифференциальной истории автозапуска
#   (StartupHistoryManager) и фиксации снимков в телеметрии.
#
# Usage Examples:
#   CLI:
#     pytest apps/windows/modules/startup/tests/test_startup_history.py -v
#
# File: test_startup_history.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.startup.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:05:00
# =============================================================================

"""Модульные тесты менеджера истории и расчета диффов автозапуска."""

import tempfile
import shutil
from pathlib import Path
from apps.windows.sdk.modules.startup.core.models import StartupEntry, AuditReport, AuditSummary
from apps.windows.telemetry_research.startup_history_manager import StartupHistoryManager

def test_startup_history_diff_detection() -> None:
    """Проверка корректного обнаружения добавления, удаления и изменения записей."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        manager = StartupHistoryManager(storage_dir=temp_dir)

        # Снимок 1
        entry1 = StartupEntry(
            id="reg_run_app1",
            name="App1",
            location_type="registry_run",
            location_path=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            command="C:\\App1.exe",
            executable_path="C:\\App1.exe",
            is_enabled=True,
            risk_level="clean",
        )
        entry2 = StartupEntry(
            id="reg_run_app2",
            name="App2",
            location_type="registry_run",
            location_path=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            command="C:\\App2.exe",
            executable_path="C:\\App2.exe",
            is_enabled=True,
            risk_level="clean",
        )

        report1 = AuditReport(
            timestamp="2026-10-06T12:00:00",
            hostname="TEST-PC",
            os_name="Windows 11 Pro",
            scan_duration_ms=12.5,
            entries=[entry1, entry2],
            summary=AuditSummary(total_entries=2, active_entries=2),
        )

        archive1, changes1 = manager.record_snapshot(report1)
        assert archive1.total_entries == 2
        assert len(changes1) == 0  # Первый снимок - базовый

        # Снимок 2: App1 отключен, App2 удален, добавлен App3, App1 изменил путь
        entry1_mod = StartupEntry(
            id="reg_run_app1",
            name="App1",
            location_type="registry_run",
            location_path=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            command="C:\\App1_v2.exe",
            executable_path="C:\\App1_v2.exe",
            is_enabled=False,
            risk_level="warning",
        )
        entry3 = StartupEntry(
            id="reg_run_app3",
            name="App3",
            location_type="registry_run",
            location_path=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            command="C:\\App3.exe",
            executable_path="C:\\App3.exe",
            is_enabled=True,
            risk_level="clean",
        )

        report2 = AuditReport(
            timestamp="2026-10-06T12:05:00",
            hostname="TEST-PC",
            os_name="Windows 11 Pro",
            scan_duration_ms=10.2,
            entries=[entry1_mod, entry3],
            summary=AuditSummary(total_entries=2, active_entries=1),
        )

        archive2, changes2 = manager.record_snapshot(report2)
        assert archive2.total_entries == 2
        assert len(changes2) >= 4  # added App3, removed App2, state_changed App1, path_changed App1, risk_changed App1

        change_types = {c.change_type for c in changes2}
        assert "added" in change_types
        assert "removed" in change_types
        assert "state_changed" in change_types
        assert "path_changed" in change_types

        # Проверка чтения истории и изменений
        history = manager.get_history(limit=5)
        assert len(history) == 2

        all_changes = manager.get_changes(limit=20)
        assert len(all_changes) == len(changes2)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
