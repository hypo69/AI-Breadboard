# -*- coding: utf-8 -*-
"""Тесты для скрипта tc.ps1.
Проверяют, что при включённой телеметрии скрипт запускает DirectoryWatcher,
а при отключённой — не запускает.
"""
import os
import subprocess
import sys
import pytest

SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tc.ps1"))

@pytest.mark.skipif(sys.platform != "win32", reason="Тесты требуют Windows PowerShell")
def test_tc_starts_watcher():
    """При обычном запуске (RealtimeTelemetry включён) скрипт выводит сообщение о запуске DirectoryWatcher."""
    result = subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        SCRIPT_PATH
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"Скрипт завершился с ошибкой: {result.stderr}"
    # В выводе должен присутствовать наш маркер
    assert "[⚡] Запуск DirectoryWatcher" in result.stdout

@pytest.mark.skipif(sys.platform != "win32", reason="Тесты требуют Windows PowerShell")
def test_tc_without_watcher():
    """При отключении телеметрии скрипт не должен запускать DirectoryWatcher."""
    result = subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        SCRIPT_PATH,
        "-DisableRealtimeTelemetry"
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"Скрипт завершился с ошибкой: {result.stderr}"
    assert "[⚡] Запуск DirectoryWatcher" not in result.stdout

"""Примечание: скрипт использует Start-Process для фонового запуска Python‑кода.
Тест проверяет только наличие/отсутствие маркера в выводе скрипта.
"""
