# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Boot & Recovery Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Boot & Recovery (boot.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_boot_tools.py -v
#
# File: test_windows_boot_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:12:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Boot & Recovery."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_boot_recovery_audit,
    windows_boot_recovery_action,
    WINDOWS_BOOT_TOOLS,
)


async def call_tool(tool_obj, **kwargs):
    """Вспомогательный вызов инструмента LangChain или базовой функции."""
    if hasattr(tool_obj, "ainvoke"):
        return await tool_obj.ainvoke(kwargs)
    elif hasattr(tool_obj, "invoke"):
        return tool_obj.invoke(kwargs)
    elif hasattr(tool_obj, "func") and tool_obj.func:
        func = tool_obj.func
        return await func(**kwargs) if asyncio.iscoroutinefunction(func) else func(**kwargs)
    else:
        return await tool_obj(**kwargs)


@pytest.mark.asyncio
async def test_windows_boot_recovery_audit():
    """Тест выполнения аудита BCD и WinRE."""
    with patch("apps.windows.sdk.modules.boot_recovery.core.manager.BootRecoveryManager.generate_report") as mock_func:
        mock_func.return_value = {"timeout_seconds": 30, "default_os": "Windows 11", "secure_boot_enabled": True}
        res_str = await call_tool(windows_boot_recovery_audit)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "boot_report" in res
        assert res["boot_report"]["timeout_seconds"] == 30


@pytest.mark.asyncio
async def test_windows_boot_recovery_action_dry_run():
    """Тест симуляции действия SafeOps над BCD."""
    res_str = await call_tool(windows_boot_recovery_action, action="set_timeout", value=10, dry_run=True)
    res = json.loads(res_str)
    assert res["status"] == "ok"
    assert res["action_result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_boot_tools():
    """Проверка наличия новых инструментов Boot & Recovery в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_boot_recovery_audit" in tool_names
    assert "windows_boot_recovery_action" in tool_names
