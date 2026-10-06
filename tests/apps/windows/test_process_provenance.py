# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Process Provenance
# =============================================================================
# Description:
#   Комплексные модульные тесты для подсистемы Process Provenance (происхождение,
#   идентичность, токены SID, сессии, цепочки предков и история жизненного цикла).
#
# Usage Examples:
#   pytest tests/apps/windows/test_process_provenance.py
#
# File: test_process_provenance.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 00:49:00
# =============================================================================

from __future__ import annotations
"""Комплексные тесты для подсистемы Process Provenance и происхождения процессов."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.models import (
    ProcessLifecycleEvent,
    ProcessMetrics,
    ProcessProvenanceInfo,
    ProcessProvenanceReport,
    ProcessTokenInfo,
)
from apps.windows.telemetry.process_token_collector import ProcessTokenCollector
from apps.windows.telemetry.sqlite import TelemetryStorage


@pytest.fixture
def test_storage(tmp_path: Path) -> TelemetryStorage:
    """Создает изолированное хранилище SQLite для тестов."""
    db_file = tmp_path / "test_provenance.db"
    return TelemetryStorage(db_path=db_file, buffer_mode="direct")


@pytest.fixture
def test_collector(test_storage: TelemetryStorage) -> SystemCollector:
    """Создает экземпляр SystemCollector с тестовым хранилищем."""
    return SystemCollector(storage=test_storage)


def test_process_provenance_models() -> None:
    """Тестирование инициализации и валидации моделей Process Provenance."""
    now_iso = datetime.now(timezone.utc).isoformat()

    metric = ProcessMetrics(
        pid=1234,
        name="python.exe",
        status="running",
        cpu_percent=5.5,
        memory_mb=150.0,
        memory_percent=1.2,
        num_threads=8,
        username="ONELA\\user",
        integrity_level="Medium",
        elevation=False,
        ppid=4321,
        parent_name="WindowsTerminal.exe",
        executable_path="C:\\Python312\\python.exe",
        sid="S-1-5-21-123456789-1001",
        session_id=1,
        creation_time=now_iso,
        process_guid="proc_1234_1700000000",
        ancestor_chain="explorer.exe → WindowsTerminal.exe → python.exe",
        launch_reason="terminal_cli",
    )
    assert metric.pid == 1234
    assert metric.ppid == 4321
    assert metric.sid == "S-1-5-21-123456789-1001"
    assert metric.session_id == 1
    assert metric.launch_reason == "terminal_cli"

    event = ProcessLifecycleEvent(
        event_type="ProcessCreated",
        process_guid="proc_1234_1700000000",
        pid=1234,
        name="python.exe",
        executable_path="C:\\Python312\\python.exe",
        command_line="python.exe main.py",
        user="ONELA\\user",
        sid="S-1-5-21-123456789-1001",
        integrity_level="Medium",
        elevation=False,
        parent_pid=4321,
        parent_name="WindowsTerminal.exe",
        parent_guid="proc_4321_1699999900",
        created_at=now_iso,
    )
    assert event.event_type == "ProcessCreated"
    assert event.parent_guid == "proc_4321_1699999900"

    report = ProcessProvenanceReport(
        total_processes=1,
        active_provenance=[
            ProcessProvenanceInfo(
                pid=metric.pid,
                ppid=metric.ppid,
                process_guid=metric.process_guid or "proc_1234",
                name=metric.name,
                executable_path=metric.executable_path,
                user=metric.username,
                sid=metric.sid,
                session_id=metric.session_id,
                integrity_level=metric.integrity_level,
                elevation=metric.elevation,
                parent_name=metric.parent_name,
                ancestor_chain=["explorer.exe", "WindowsTerminal.exe", "python.exe"],
                ancestor_chain_str=metric.ancestor_chain or "",
                who_runs_it="ONELA\\user (S-1-5-21, Session 1)",
                who_created_it="WindowsTerminal.exe (PPID: 4321)",
                why_was_it_created=metric.launch_reason or "unknown",
                creation_time=metric.creation_time,
            )
        ],
        timestamp=now_iso,
        summary="Test report summary",
    )
    assert report.total_processes == 1
    assert len(report.active_provenance) == 1
    assert report.active_provenance[0].name == "python.exe"


def test_classify_launch_reason() -> None:
    """Тестирование классификации причин запуска процессов."""
    # Служба
    assert SystemCollector._classify_launch_reason("services.exe", "svchost.exe", session_id=0) == "service"
    assert SystemCollector._classify_launch_reason("svchost.exe", "spoolsv.exe", session_id=0) == "service"

    # Запланированная задача
    assert SystemCollector._classify_launch_reason("taskhostw.exe", "app.exe") == "scheduled_task"
    assert SystemCollector._classify_launch_reason("taskeng.exe", "app.exe") == "scheduled_task"

    # Проводник / Графический запуск
    assert SystemCollector._classify_launch_reason("explorer.exe", "notepad.exe", session_id=1) == "shell_interactive"

    # Терминал / Консоль
    assert SystemCollector._classify_launch_reason("WindowsTerminal.exe", "pwsh.exe") == "terminal_cli"
    assert SystemCollector._classify_launch_reason("cmd.exe", "python.exe") == "terminal_cli"
    assert SystemCollector._classify_launch_reason("pwsh.exe", "git.exe") == "terminal_cli"

    # IDE / Разработка
    assert SystemCollector._classify_launch_reason("code.exe", "node.exe") == "ide_developer"
    assert SystemCollector._classify_launch_reason("devenv.exe", "msbuild.exe") == "ide_developer"

    # Загрузка системы
    assert SystemCollector._classify_launch_reason("winlogon.exe", "userinit.exe") == "system_boot"

    # Прочий родитель
    assert SystemCollector._classify_launch_reason("chrome.exe", "crashpad_handler.exe") == "spawned_by_chrome"
    assert SystemCollector._classify_launch_reason(None, "unknown.exe") == "unknown"


def test_process_token_collector_fallback() -> None:
    """Тестирование сбора токенов процессов и Fallback."""
    collector = ProcessTokenCollector()
    tokens = collector.collect()
    assert isinstance(tokens, list)
    if tokens:
        first = tokens[0]
        assert isinstance(first, ProcessTokenInfo)
        assert first.pid >= 0

    single = collector.get_process_token_info(os.getpid(), "python.exe")
    if single:
        assert single.pid == os.getpid()


def test_telemetry_storage_provenance_crud(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения и извлечения событий жизненного цикла процессов в SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()

    event1 = ProcessLifecycleEvent(
        event_type="ProcessCreated",
        process_guid="proc_100_1700000000",
        pid=100,
        name="explorer.exe",
        executable_path="C:\\Windows\\explorer.exe",
        user="ONELA\\user",
        sid="S-1-5-21-1001",
        integrity_level="Medium",
        parent_pid=50,
        parent_name="userinit.exe",
        parent_guid="proc_50_1699999000",
        created_at=now_iso,
    )

    event2 = ProcessLifecycleEvent(
        event_type="ProcessCreated",
        process_guid="proc_200_1700000100",
        pid=200,
        name="WindowsTerminal.exe",
        executable_path="C:\\Program Files\\WindowsApps\\wt.exe",
        user="ONELA\\user",
        sid="S-1-5-21-1001",
        integrity_level="Medium",
        parent_pid=100,
        parent_name="explorer.exe",
        parent_guid="proc_100_1700000000",
        created_at=now_iso,
    )

    event3 = ProcessLifecycleEvent(
        event_type="ProcessCreated",
        process_guid="proc_300_1700000200",
        pid=300,
        name="python.exe",
        executable_path="C:\\Python312\\python.exe",
        command_line="python -m pytest",
        user="ONELA\\user",
        sid="S-1-5-21-1001",
        integrity_level="High",
        parent_pid=200,
        parent_name="WindowsTerminal.exe",
        parent_guid="proc_200_1700000100",
        created_at=now_iso,
    )

    # Сохранение по одному и пачкой
    assert test_storage.save_process_provenance_event(event1) is True
    assert test_storage.save_process_provenance_batch([event2, event3]) == 2

    # Получение истории
    history = test_storage.get_process_provenance_history()
    assert len(history) == 3

    # Фильтр по имени
    py_history = test_storage.get_process_provenance_history(name="python.exe")
    assert len(py_history) == 1
    assert py_history[0]["pid"] == 300
    assert py_history[0]["parent_name"] == "WindowsTerminal.exe"

    # Фильтр по GUID
    guid_history = test_storage.get_process_provenance_history(guid="proc_200_1700000100")
    assert len(guid_history) == 1
    assert guid_history[0]["name"] == "WindowsTerminal.exe"

    # Фильтр по пользователю
    user_history = test_storage.get_process_provenance_history(user="ONELA\\user")
    assert len(user_history) == 3


def test_telemetry_storage_lineage_resolution(test_storage: TelemetryStorage) -> None:
    """Тестирование построения дерева/цепочки предков процесса (Lineage)."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Дерево: winlogon -> userinit -> explorer -> wt -> python
    events = [
        ProcessLifecycleEvent(
            event_type="ProcessCreated",
            process_guid="proc_10_1000",
            pid=10,
            name="winlogon.exe",
            parent_pid=4,
            parent_name="smss.exe",
            created_at=now_iso,
        ),
        ProcessLifecycleEvent(
            event_type="ProcessCreated",
            process_guid="proc_20_2000",
            pid=20,
            name="userinit.exe",
            parent_pid=10,
            parent_name="winlogon.exe",
            parent_guid="proc_10_1000",
            created_at=now_iso,
        ),
        ProcessLifecycleEvent(
            event_type="ProcessCreated",
            process_guid="proc_30_3000",
            pid=30,
            name="explorer.exe",
            parent_pid=20,
            parent_name="userinit.exe",
            parent_guid="proc_20_2000",
            created_at=now_iso,
        ),
        ProcessLifecycleEvent(
            event_type="ProcessCreated",
            process_guid="proc_40_4000",
            pid=40,
            name="WindowsTerminal.exe",
            parent_pid=30,
            parent_name="explorer.exe",
            parent_guid="proc_30_3000",
            created_at=now_iso,
        ),
        ProcessLifecycleEvent(
            event_type="ProcessCreated",
            process_guid="proc_50_5000",
            pid=50,
            name="python.exe",
            parent_pid=40,
            parent_name="WindowsTerminal.exe",
            parent_guid="proc_40_4000",
            created_at=now_iso,
        ),
    ]
    test_storage.save_process_provenance_batch(events)

    lineage = test_storage.get_process_lineage("proc_50_5000")
    assert len(lineage) == 5
    names = [node["name"] for node in lineage]
    assert names == ["winlogon.exe", "userinit.exe", "explorer.exe", "WindowsTerminal.exe", "python.exe"]

    # Проверка поиска по PID
    lineage_by_pid = test_storage.get_process_lineage("50")
    assert len(lineage_by_pid) == 5
    assert lineage_by_pid[-1]["pid"] == 50


def test_system_collector_provenance_report(test_collector: SystemCollector) -> None:
    """Тестирование формирования сводного отчета происхождения процессов через SystemCollector."""
    report = test_collector.get_process_provenance_report(limit=10)
    assert isinstance(report, ProcessProvenanceReport)
    assert report.total_processes >= len(report.active_provenance)
    assert len(report.active_provenance) <= 10
    if report.active_provenance:
        p = report.active_provenance[0]
        assert p.pid >= 0
        assert p.name is not None
        assert p.process_guid is not None


