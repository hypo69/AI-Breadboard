# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows System Control Center Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов единого центра управления Windows
#   (windows_system_control_audit, windows_system_control_action).
#
# Usage Examples:
#   pytest tests/test_windows_system_control_center_tools.py -v
#
# File: test_windows_system_control_center_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:33:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.system_control_center import (
    windows_system_control_audit,
    windows_system_control_action,
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


@pytest.fixture
def mock_status_data():
    """Фикстура данных статуса центра управления."""
    return {
        "is_elevated": True,
        "system": {"hostname": "TEST-PC", "ram_percent": 42.0},
        "security": {"defender_enabled": True, "overall_status": "SECURE"},
        "disk": {"cleanup_estimate": {"total_cleanable_mb": 250}},
        "restore": {"restore_points_count": 3},
        "timestamp": "2026-10-08T22:33:00",
    }


@pytest.mark.asyncio
async def test_windows_system_control_audit_status(mock_status_data):
    """Тестирование получения сводного статуса центра управления."""
    with patch("apps.windows.sdk.modules.system_control_center.router._collect_status_sync", return_value=mock_status_data):
        res_raw = await call_tool(windows_system_control_audit, action="status")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "status"
        assert res["system_control"]["is_elevated"] is True


@pytest.mark.asyncio
async def test_windows_system_control_action_dry_run():
    """Тестирование режима dry_run для системного действия."""
    res_raw = await call_tool(windows_system_control_action, action="clean_temp_files", target="temp", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "clean_temp_files" in res.get("message", "")


def test_windows_controller_agent_has_system_control_tools():
    """Проверка присутствия инструментов system_control_center в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_system_control_audit" in tool_names
    assert "windows_system_control_action" in tool_names
