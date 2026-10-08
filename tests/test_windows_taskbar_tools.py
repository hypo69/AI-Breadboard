# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Taskbar Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов панели задач Windows
#   (windows_taskbar_audit, windows_taskbar_action).
#
# Usage Examples:
#   pytest tests/test_windows_taskbar_tools.py -v
#
# File: test_windows_taskbar_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:38:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.taskbar import (
    windows_taskbar_audit,
    windows_taskbar_action,
)
from apps.windows.modules.taskbar.core.models import TaskbarSummaryReport, TaskbarSettings, WindowItem


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
def mock_summary():
    """Фикстура сводного отчета панели задач."""
    win = WindowItem(hwnd=1001, title="AI Breadboard", process_name="python.exe", is_visible=True)
    return TaskbarSummaryReport(
        os_version="Windows 11 Pro",
        is_win11=True,
        taskbar_rect={"left": 0, "top": 1000, "right": 1920, "bottom": 1080},
        settings=TaskbarSettings(auto_hide=False, align_center=True),
        windows_count=5,
        visible_windows_count=3,
        foreground_window=win,
        pinned_apps_count=4,
    )


@pytest.mark.asyncio
async def test_windows_taskbar_audit_summary(mock_summary):
    """Тестирование получения сводки панели задач."""
    with patch("apps.windows.modules.taskbar.core.manager.TaskbarController.get_summary", return_value=mock_summary):
        res_raw = await call_tool(windows_taskbar_audit, action="summary")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "summary"
        assert res["summary"]["is_win11"] is True
        assert res["summary"]["visible_windows_count"] == 3


@pytest.mark.asyncio
async def test_windows_taskbar_action_dry_run():
    """Тестирование выполнения действия над панелью задач в режиме dry_run."""
    res_raw = await call_tool(windows_taskbar_action, action="pin_app", target="Notepad", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "Notepad" in res.get("message", "")


def test_windows_controller_agent_has_taskbar_tools():
    """Проверка присутствия инструментов taskbar в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_taskbar_audit" in tool_names
    assert "windows_taskbar_action" in tool_names
