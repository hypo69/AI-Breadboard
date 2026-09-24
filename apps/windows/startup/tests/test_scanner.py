# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Windows Startup Scanner
# =============================================================================
# Description:
#   Модульные тесты для сканера точек автозагрузки Windows.
#
# Examples:
#   $ pytest apps/windows_startup_auditor/tests/test_scanner.py -v
#
# File: test_scanner.py
# Project: ai-breadboard
# Package: apps.windows.startup.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты сканера автозапуска StartupScanner."""

from apps.windows.startup.core.models import StartupLocationType
from apps.windows.startup.core.scanner import StartupScanner


def test_monitored_locations_list() -> None:
    """Проверка возврата списка контролируемых точек автозапуска."""
    scanner = StartupScanner()
    locations = scanner.get_monitored_locations()
    assert len(locations) >= 8
    location_types = [loc.location_type for loc in locations]
    assert StartupLocationType.REGISTRY_RUN in location_types
    assert StartupLocationType.STARTUP_FOLDER_USER in location_types
    assert StartupLocationType.IFEO in location_types
    assert StartupLocationType.WINLOGON in location_types


def test_parse_command_line() -> None:
    """Проверка парсинга исполняемого пути и аргументов из командной строки."""
    scanner = StartupScanner()

    # С кавычками
    exe, args = scanner._parse_command_line(r'"C:\Program Files\App\app.exe" /minimized --autostart')
    assert exe == r"C:\Program Files\App\app.exe"
    assert args == "/minimized --autostart"

    # Без кавычек
    exe2, args2 = scanner._parse_command_line(r"C:\Windows\notepad.exe C:\test.txt")
    assert exe2 == r"C:\Windows\notepad.exe"
    assert args2 == r"C:\test.txt"

    # Пустая строка
    exe3, args3 = scanner._parse_command_line("")
    assert exe3 == ""
    assert args3 == ""


def test_scan_all_returns_entries() -> None:
    """Проверка выполнения полного сканирования на текущей хост-системе."""
    scanner = StartupScanner()
    entries = scanner.scan_all()
    assert isinstance(entries, list)
    # На реальной Windows системе всегда есть хотя бы Winlogon или базовые службы
    for e in entries:
        assert e.id
        assert e.name
        assert e.location_type
