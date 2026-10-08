# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Software Manager Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Software Manager (software_manager.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_software_tools.py -v
#
# File: test_windows_software_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:16:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Software Manager."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_software_list,
    windows_software_action,
    WINDOWS_SOFTWARE_MANAGER_TOOLS,
)
from apps.windows.modules.software_manager.core.models import (
    InstalledPackage,
    SoftwareReport,
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
async def test_windows_software_list_report():
    """Тест получения отчета об установленном ПО."""
    sample_report = SoftwareReport(
        total_packages=5,
        updates_available_count=1,
        winget_available=True,
        packages=[
            InstalledPackage(name="Git", package_id="Git.Git", version="2.47.0")
        ],
        timestamp="2026-10-08T22:00:00",
    )
    with patch("apps.windows.modules.software_manager.core.manager.SoftwarePackagesManager.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_software_list, action="report")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "report" in res
        assert res["report"]["total_packages"] == 5
        assert res["report"]["updates_available_count"] == 1


@pytest.mark.asyncio
async def test_windows_software_action_dry_run():
    """Тест выполнения действия над пакетом ПО в режиме dry_run."""
    sample_res = {
        "status": "DRY_RUN_SUCCESS",
        "package_id": "Git.Git",
        "action": "upgrade",
        "message": "Симуляция upgrade для пакета 'Git.Git' выполнена успешно.",
    }
    with patch("apps.windows.modules.software_manager.core.manager.SoftwarePackagesManager.execute_package_action", return_value=sample_res):
        res_str = await call_tool(
            windows_software_action,
            package_id="Git.Git",
            action="upgrade",
            dry_run=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["package_id"] == "Git.Git"
        assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_software_tools():
    """Проверка наличия новых инструментов software_manager в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_software_list" in tool_names
    assert "windows_software_action" in tool_names
