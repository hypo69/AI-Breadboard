# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Focus Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Focus Policy Engine (focus.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_focus_tools.py -v
#
# File: test_windows_focus_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:40:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Focus Policy Engine."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_focus_status_profiles,
    windows_focus_session_action,
    windows_focus_notifications,
    WINDOWS_FOCUS_TOOLS,
)
from apps.windows.modules.focus_policy.models import FocusStatus, FocusProfile, SessionSummary, SuppressedNotification


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
async def test_windows_focus_status_profiles_status():
    """Тест получения текущего статуса фокусировки."""
    with patch("apps.windows.modules.focus_policy.controller.WindowsFocusController.status") as mock_func:
        mock_func.return_value = FocusStatus(is_focus_active=False, listener_access_status="Allowed")
        res_str = await call_tool(windows_focus_status_profiles, action="status")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "focus_status" in res
        assert res["focus_status"]["is_focus_active"] is False


@pytest.mark.asyncio
async def test_windows_focus_status_profiles_save():
    """Тест создания профиля фокусировки."""
    with patch("apps.windows.modules.focus_policy.controller.WindowsFocusController.save_profile") as mock_func:
        mock_func.return_value = FocusProfile(profile_id="prof-test", name="Тест")
        res_str = await call_tool(
            windows_focus_status_profiles,
            action="save_profile",
            profile_id="prof-test",
            name="Тест",
            start_time="10:00",
            end_time="19:00",
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["profile_id"] == "prof-test"
        assert "profile" in res


@pytest.mark.asyncio
async def test_windows_focus_session_action_start_stop():
    """Тест запуска и остановки сессии фокусировки."""
    with patch("apps.windows.modules.focus_policy.controller.WindowsFocusController.start_session") as mock_start:
        mock_start.return_value = "sess-20261008-210000"
        res_str = await call_tool(windows_focus_session_action, action="start", profile_id="prof-test")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["session_id"] == "sess-20261008-210000"

    with patch("apps.windows.modules.focus_policy.controller.WindowsFocusController.stop_session") as mock_stop:
        mock_stop.return_value = SessionSummary(session_id="sess-20261008-210000", profile_id="prof-test", total_suppressed=3)
        res_str = await call_tool(windows_focus_session_action, action="stop")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["summary"]["total_suppressed"] == 3


@pytest.mark.asyncio
async def test_windows_focus_notifications_poll():
    """Тест опроса подавленных уведомлений."""
    with patch("apps.windows.modules.focus_policy.controller.WindowsFocusController.poll_notifications") as mock_func:
        mock_func.return_value = 5
        res_str = await call_tool(windows_focus_notifications, action="poll")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["suppressed_count"] == 5


def test_windows_controller_agent_has_focus_tools():
    """Проверка наличия новых инструментов фокусировки в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_focus_status_profiles" in tool_names
    assert "windows_focus_session_action" in tool_names
    assert "windows_focus_notifications" in tool_names
