# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Winre Manager
# =============================================================================
# Description:
#   Тесты менеджера среды восстановления Windows RE (WinRE / reagentc).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.tests.test_winre_manager import test_parse_reagentc_info_english
#
#     res = test_parse_reagentc_info_english()
#
# File: test_winre_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты менеджера среды восстановления Windows RE (WinRE / reagentc)."""

from unittest.mock import MagicMock, patch
from apps.windows.system_checkpoints.core.winre_manager import WinREManager
from apps.windows.system_checkpoints.models import WinREStatus


EN_SAMPLE_OUTPUT = """
Windows Recovery Environment (Windows RE) and system reset configuration
Information:

    Windows RE status:         Enabled
    Windows RE location:       \\\\?\\GLOBALROOT\\device\\harddisk0\\partition4\\Recovery\\WindowsRE
    Boot Configuration Data (BCD) identifier: 12345678-abcd-1234-abcd-123456789abc
    Custom image location:     
    Custom image index:        0
    Recovery image location:   
    Recovery image index:      0
    Is staged:                 1

REAGENTC.EXE: Operation Successful.
"""

RU_SAMPLE_OUTPUT = """
Сведения о среде восстановления Windows (Windows RE) и сбросе системы:

    Состояние Windows RE:            Включено
    Расположение Windows RE:         \\\\?\\GLOBALROOT\\device\\harddisk0\\partition4\\Recovery\\WindowsRE
    Идентификатор данных конфигурации загрузки (BCD): {12345678-abcd-1234-abcd-123456789abc}
    Расположение пользовательского образа: C:\\Recovery\\Custom
    Подготовлено:                    Да

REAGENTC.EXE: Операция выполнена успешно.
"""

DISABLED_OUTPUT = """
Windows RE status:         Disabled
Windows RE location:       
Boot Configuration Data (BCD) identifier: 00000000-0000-0000-0000-000000000000
"""


def test_parse_reagentc_info_english():
    """Проверка парсинга англоязычного вывода reagentc /info."""
    status = WinREManager.parse_reagentc_info(EN_SAMPLE_OUTPUT)
    assert status.enabled is True
    assert "harddisk0" in status.location
    assert "12345678-abcd" in status.bcd_id
    assert status.is_staged is True
    assert status.error is None


def test_parse_reagentc_info_russian():
    """Проверка парсинга русскоязычного вывода reagentc /info."""
    status = WinREManager.parse_reagentc_info(RU_SAMPLE_OUTPUT)
    assert status.enabled is True
    assert "harddisk0" in status.location
    assert "12345678-abcd" in status.bcd_id
    assert status.custom_image_location == "C:\\Recovery\\Custom"
    assert status.is_staged is True


def test_parse_reagentc_disabled():
    """Проверка парсинга отключенной среды WinRE."""
    status = WinREManager.parse_reagentc_info(DISABLED_OUTPUT)
    assert status.enabled is False


@patch("subprocess.run")
def test_winre_actions_mock(mock_run):
    """Проверка выполнения команд enable, disable, set_reimage."""
    mgr = WinREManager()

    # Test enable
    mock_run.return_value = MagicMock(returncode=0, stdout="REAGENTC.EXE: Operation Successful.", stderr="")
    res_en = mgr.enable()
    assert res_en["success"] is True

    # Test disable
    mock_run.return_value = MagicMock(returncode=0, stdout="Disabled.", stderr="")
    res_dis = mgr.disable()
    assert res_dis["success"] is True

    # Test set_reimage_path
    mock_run.return_value = MagicMock(returncode=0, stdout="Success.", stderr="")
    res_path = mgr.set_reimage_path("C:\\Recovery\\Custom")
    assert res_path["success"] is True
    assert res_path["path"] == "C:\\Recovery\\Custom"
