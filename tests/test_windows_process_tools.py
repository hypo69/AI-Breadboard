# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Process Manager Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Process Manager (process_manager.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_process_tools.py -v
#
# File: test_windows_process_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:06:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Process Manager."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_process_list,
    windows_process_action,
    WINDOWS_PROCESS_TOOLS,
)
from apps.windows.sdk.modules.process_manager.core.models import (
    CategorizedProcessReport,
    ProcessItem,
    ProcessReport,
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
async def test_windows_process_list_summary():
    """Тест получения сводного отчета о процессах."""
    sample_report = ProcessReport(
        total_processes=100,
        total_threads=1200,
        total_memory_used_mb=4096.0,
        apps_count=10,
        background_count=50,
        windows_count=40,
        top_cpu_processes=[
            ProcessItem(pid=1234, name="python.exe", cpu_percent=25.5, memory_mb=150.0)
        ],
        top_memory_processes=[
            ProcessItem(pid=1234, name="python.exe", cpu_percent=25.5, memory_mb=150.0)
        ],
    )
    with patch("apps.windows.sdk.modules.process_manager.core.manager.ProcessManager.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_process_list, action="summary", limit=5)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "summary" in res
        assert res["summary"]["total_processes"] == 100
        assert len(res["summary"]["top_cpu_processes"]) == 1


@pytest.mark.asyncio
async def test_windows_process_action_dry_run():
    """Тест выполнения действия завершения процесса в режиме dry_run."""
    sample_res = {
        "status": "DRY_RUN_SUCCESS",
        "pid": 1234,
        "kill_tree": False,
        "message": "Симуляция завершения процесса PID=1234 выполнена успешно."
    }
    with patch("apps.windows.sdk.modules.process_manager.core.manager.ProcessManager.kill_process", return_value=sample_res):
        res_str = await call_tool(windows_process_action, pid=1234, dry_run=True)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["pid"] == 1234
        assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_process_tools():
    """Проверка наличия новых инструментов process_manager в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_process_list" in tool_names
    assert "windows_process_action" in tool_names
