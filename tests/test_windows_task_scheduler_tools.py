# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Task Scheduler Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов управления планировщиком задач Windows
#   (windows_task_scheduler_audit, windows_task_scheduler_action).
#
# Usage Examples:
#   pytest tests/test_windows_task_scheduler_tools.py -v
#
# File: test_windows_task_scheduler_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:36:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.task_scheduler import (
    windows_task_scheduler_audit,
    windows_task_scheduler_action,
)
from apps.windows.sdk.modules.task_scheduler.core.models import ScheduledTaskItem, TaskSchedulerReport


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
def mock_tasks():
    """Фикстура списка тестовых задач."""
    t1 = ScheduledTaskItem(task_path="\\Microsoft\\Windows\\Defrag\\Defrag", task_name="Defrag", state="Ready", enabled=True)
    t2 = ScheduledTaskItem(task_path="\\Microsoft\\Windows\\Maintenance\\Clean", task_name="Clean", state="Disabled", enabled=False)
    return [t1, t2]


@pytest.mark.asyncio
async def test_windows_task_scheduler_audit_list(mock_tasks):
    """Тестирование получения списка задач планировщика."""
    with patch("apps.windows.sdk.modules.task_scheduler.core.manager.TaskSchedulerManager.list_tasks", return_value=mock_tasks):
        res_raw = await call_tool(windows_task_scheduler_audit, action="list")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "list"
        assert res["total_tasks"] == 2


@pytest.mark.asyncio
async def test_windows_task_scheduler_action_dry_run():
    """Тестирование выполнения действия над задачей в режиме dry_run."""
    res_raw = await call_tool(windows_task_scheduler_action, task_path="\\TestTask", action="run", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "\\TestTask" in res.get("message", "")


def test_windows_controller_agent_has_task_scheduler_tools():
    """Проверка присутствия инструментов task_scheduler в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_task_scheduler_audit" in tool_names
    assert "windows_task_scheduler_action" in tool_names
