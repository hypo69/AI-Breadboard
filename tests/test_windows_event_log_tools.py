# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Event Logs Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Event Log & Log Intelligence (event_logs.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_event_log_tools.py -v
#
# File: test_windows_event_log_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:21:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Event Log."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_event_log_query,
    windows_event_log_intelligence,
    windows_event_log_action,
    WINDOWS_EVENT_LOGS_TOOLS,
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
async def test_windows_event_log_query_recent_errors():
    """Тест получения последних ошибок."""
    with patch("apps.windows.modules.event_logs.core.manager.EventLogsManager.get_recent_errors") as mock_func:
        mock_func.return_value = [{"event_id": 7036, "level": "Error", "message": "Сбой BITS"}]
        res_str = await call_tool(windows_event_log_query, action="recent_errors")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "errors" in res
        assert len(res["errors"]) == 1


@pytest.mark.asyncio
async def test_windows_event_log_intelligence_profile():
    """Тест выполнения профайлинга Log Intelligence."""
    with patch("apps.windows.modules.event_logs.core.manager.EventLogsManager.process_intelligence") as mock_func:
        mock_func.return_value = {"shi": 0.95, "r_dup": 0.1, "channel": "System"}
        res_str = await call_tool(windows_event_log_intelligence, action="profile", channel="System")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "intelligence_profile" in res
        assert res["intelligence_profile"]["shi"] == 0.95


@pytest.mark.asyncio
async def test_windows_event_log_action_dry_run():
    """Тест симуляции очистки канала."""
    res_str = await call_tool(windows_event_log_action, action="clear", channel="System", dry_run=True)
    res = json.loads(res_str)
    assert res["status"] == "ok"
    assert "DRY_RUN" in res["result"]


# Updated: 2026-10-08 22:54:00
# =============================================================================

@pytest.mark.asyncio
async def test_windows_event_log_query_sysmon_and_pending():
    """Тест расширенных запросов sysmon, powershell_scriptblock, wer_bsod и pending_reboots."""
    with patch("apps.windows.modules.event_logs.core.manager.EventLogsManager.get_events") as mock_events:
        mock_events.return_value = []
        res_sysmon = json.loads(await call_tool(windows_event_log_query, action="sysmon"))
        assert res_sysmon["status"] == "ok"
        assert res_sysmon["channel"] == "Microsoft-Windows-Sysmon/Operational"

        res_ps = json.loads(await call_tool(windows_event_log_query, action="powershell_scriptblock"))
        assert res_ps["status"] == "ok"
        assert res_ps["channel"] == "Microsoft-Windows-PowerShell/Operational"

        res_wer = json.loads(await call_tool(windows_event_log_query, action="wer_bsod"))
        assert res_wer["status"] == "ok"
        assert "bsod_events" in res_wer

    res_pending = json.loads(await call_tool(windows_event_log_query, action="pending_reboots"))
    assert res_pending["status"] == "ok"
    assert "pending_reboot_status" in res_pending


def test_windows_controller_agent_has_event_log_tools():
    """Проверка наличия новых инструментов Event Log в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_event_log_query" in tool_names
    assert "windows_event_log_intelligence" in tool_names
    assert "windows_event_log_action" in tool_names

