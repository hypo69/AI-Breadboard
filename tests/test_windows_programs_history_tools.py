# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Programs History Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Programs History Deep Research (programms_history.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_programs_history_tools.py -v
#
# File: test_windows_programs_history_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:07:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Programs History."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_programs_history_report,
    windows_programs_history_audit,
    WINDOWS_PROGRAMS_HISTORY_TOOLS,
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
async def test_windows_programs_history_report_summary():
    """Тест получения сводного отчета по программам и артефактам."""
    sample_report = {
        "generated_at": "2026-10-08T22:00:00Z",
        "installed_programs": [{"name": "7-Zip", "publisher": "Igor Pavlov"}],
        "detected_artifacts": [],
        "mapped_artifacts": [],
        "unknown_artifacts": [],
    }
    with patch("apps.windows.modules.programms_history_deep_researh.report.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_programs_history_report, action="summary", limit=5)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "summary" in res
        assert res["summary"]["total_installed_programs"] == 1


@pytest.mark.asyncio
async def test_windows_programs_history_audit():
    """Тест быстрого аудита программ в реестре."""
    sample_progs = [
        {"displayname": "Google Chrome", "publisher": "Google LLC"},
        {"displayname": "Python 3.12", "publisher": "Python Software Foundation"},
    ]
    with patch("apps.windows.modules.programms_history_deep_researh.registry_extractor.get_installed_programs", return_value=sample_progs):
        res_str = await call_tool(windows_programs_history_audit, query_name="Chrome")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["count"] == 1
        assert res["programs"][0]["displayname"] == "Google Chrome"


def test_windows_controller_agent_has_programs_history_tools():
    """Проверка наличия новых инструментов programms_history в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_programs_history_report" in tool_names
    assert "windows_programs_history_audit" in tool_names
