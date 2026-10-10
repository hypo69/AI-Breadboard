# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests - TC Launcher Script Tests
# =============================================================================
# Description:
#   Модульные тесты для скриптов запуска внутреннего API Windows (tc.ps1 и tc.py).
#
# File: test_tc_script.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:02:00
# =============================================================================

"""Тесты для скриптов tc.ps1 и tc.py: проверка профиля конфигурации, UI ссылок и параметров."""

import os
import subprocess
import sys
from pathlib import Path
import pytest

SCRIPT_PS1_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tc.ps1"))
SCRIPT_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tc.py"))


@pytest.mark.skipif(sys.platform != "win32", reason="Тесты требуют Windows PowerShell")
def test_tc_ps1_output_config_and_ui():
    """Проверка, что tc.ps1 выводит активный профиль и URL интерфейса TC UI."""
    result = subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"& '{SCRIPT_PS1_PATH}' -HostAddress 127.0.0.1 -Port 8001 | Out-String"
    ], capture_output=True, text=True, timeout=15)

    stdout = result.stdout
    assert "Config Profile" in stdout or "apps\\windows\\config.json" in stdout
    assert "http://127.0.0.1:8001/tc" in stdout


@pytest.mark.skipif(sys.platform != "win32", reason="Тесты требуют Windows PowerShell")
def test_tc_ps1_with_region_parameter():
    """Проверка передачи параметра локализации BCP 47 в tc.ps1."""
    result = subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"& '{SCRIPT_PS1_PATH}' -Region 'ru-ru' | Out-String"
    ], capture_output=True, text=True, timeout=15)

    stdout = result.stdout
    assert "ru-RU" in stdout
    assert "?region=ru-RU" in stdout


def test_tc_py_cli_dry_run():
    """Проверка запуска tc.py в режиме CLI с флагом --dry-run."""
    result = subprocess.run([
        sys.executable,
        SCRIPT_PY_PATH,
        "--dry-run",
        "--region", "ru-ru",
        "--host", "127.0.0.1",
        "--port", "8001"
    ], capture_output=True, text=True, timeout=15, encoding="utf-8")

    assert result.returncode == 0
    stdout = result.stdout
    assert "apps\\windows\\config.json" in stdout or "Config Profile" in stdout
    assert "ru-RU" in stdout
    assert "http://127.0.0.1:8001/tc?region=ru-RU" in stdout


def test_tc_py_bcp47_normalization():
    """Проверка логики нормализации языковых и региональных тегов BCP 47 в tc.py."""
    import tc
    assert tc.normalize_bcp47_tag("ru-ru") == "ru-RU"
    assert tc.normalize_bcp47_tag("en_us") == "en-US"
    assert tc.normalize_bcp47_tag("he") == "he-IL"
    assert tc.normalize_bcp47_tag("de-de") == "de-DE"
    assert tc.normalize_bcp47_tag("fr") == "fr-FR"


def test_tc_py_parse_args():
    """Проверка парсера аргументов командной строки tc.py."""
    import tc
    args = tc.parse_args(["--port", "8005", "--region", "uk-ua", "--dry-run"])
    assert args.port == 8005
    assert args.region == "uk-ua"
    assert args.dry_run is True


def test_tc_py_run_tc_function():
    """Проверка прямого программного вызова функции run_tc."""
    import tc
    code = tc.run_tc(
        host="127.0.0.1",
        port=8001,
        region="he-il",
        dry_run=True
    )
    assert code == 0
