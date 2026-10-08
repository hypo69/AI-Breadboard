# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Performance Tracing Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Performance Tracing (performance_tracing.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_performance_tracing_tools.py -v
#
# File: test_windows_performance_tracing_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:57:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Performance Tracing."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_performance_tracing_audit,
    windows_performance_collector_action,
    WINDOWS_PERFORMANCE_TRACING_TOOLS,
)
from apps.windows.modules.performance_tracing.core.models import (
    PerformanceCounterSample,
    DataCollectorSet,
    PerformanceTracingReport,
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
async def test_windows_performance_tracing_audit_counters():
    """Тест моментальных значений счетчиков производительности."""
    with patch("apps.windows.modules.performance_tracing.core.manager.PerformanceTracingManager.get_counter_samples") as mock_func:
        mock_func.return_value = [
            PerformanceCounterSample(path="\\Processor(_Total)\\% Processor Time", value=15.5, unit="%"),
            PerformanceCounterSample(path="\\Memory\\% Committed Bytes In Use", value=42.0, unit="%"),
        ]
        res_str = await call_tool(windows_performance_tracing_audit, action="counters")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "counters" in res
        assert len(res["counters"]) == 2


@pytest.mark.asyncio
async def test_windows_performance_tracing_audit_collectors():
    """Тест списка сборщиков данных ETW."""
    with patch("apps.windows.modules.performance_tracing.core.manager.PerformanceTracingManager.list_collectors") as mock_func:
        mock_func.return_value = [
            DataCollectorSet(name="System Diagnostics", status="Stopped"),
            DataCollectorSet(name="EventLog-Security", status="Running"),
        ]
        res_str = await call_tool(windows_performance_tracing_audit, action="collectors")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "collectors" in res
        assert len(res["collectors"]) == 2


@pytest.mark.asyncio
async def test_windows_performance_collector_action_dry_run():
    """Тест выполнения симуляции действия со сборщиком ETW."""
    res_str = await call_tool(
        windows_performance_collector_action,
        collector_name="System Diagnostics",
        action="start",
        dry_run=True,
    )
    res = json.loads(res_str)
    assert res["status"] == "ok"
    assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_performance_tracing_tools():
    """Проверка наличия новых инструментов производительности в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_performance_tracing_audit" in tool_names
    assert "windows_performance_collector_action" in tool_names
