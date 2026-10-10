# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Services Manager Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Services Manager (services_manager.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_services_tools.py -v
#
# File: test_windows_services_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:13:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Services Manager."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_services_list,
    windows_services_action,
    WINDOWS_SERVICES_MANAGER_TOOLS,
)
from apps.windows.sdk.modules.services_manager.core.models import (
    ServiceItem,
    ServicesReport,
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
async def test_windows_services_list_summary():
    """Тест получения сводной информации о службах."""
    sample_report = ServicesReport(
        total_services=150,
        running_services=80,
        stopped_services=70,
        auto_start_services=60,
        orphaned_services_count=0,
        services=[
            ServiceItem(name="wuauserv", display_name="Windows Update", status="RUNNING")
        ],
        timestamp="2026-10-08T22:00:00",
    )
    with patch("apps.windows.sdk.modules.services_manager.core.manager.ServicesManager.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_services_list, action="summary")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "summary" in res
        assert res["summary"]["total_services"] == 150
        assert res["summary"]["running_services"] == 80


@pytest.mark.asyncio
async def test_windows_services_action_dry_run():
    """Тест симуляции управления состоянием службы."""
    sample_res = {
        "status": "DRY_RUN_SUCCESS",
        "name": "wuauserv",
        "action": "restart",
        "message": "Симуляция restart для службы wuauserv выполнена успешно.",
    }
    with patch("apps.windows.sdk.modules.services_manager.core.manager.ServicesManager.execute_service_action", return_value=sample_res):
        res_str = await call_tool(
            windows_services_action,
            name="wuauserv",
            action="restart",
            dry_run=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["name"] == "wuauserv"
        assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_services_tools():
    """Проверка наличия новых инструментов services_manager в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_services_list" in tool_names
    assert "windows_services_action" in tool_names
