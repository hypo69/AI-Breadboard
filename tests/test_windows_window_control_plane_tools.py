# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Window Control Plane Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов подсистемы управления окнами Windows
#   (windows_control_plane_audit, windows_control_plane_action).
#
# Usage Examples:
#   pytest tests/test_windows_window_control_plane_tools.py -v
#
# File: test_windows_window_control_plane_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:43:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.window_control_plane import (
    windows_control_plane_audit,
    windows_control_plane_action,
)
from apps.windows.sdk.modules.window_control_plane.models import ControlPlaneSummaryResponse


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
    """Фикстура сводной информации Window Control Plane."""
    return ControlPlaneSummaryResponse(
        total_settings=295,
        categories_count=15,
        by_category={"focus_activation": 20},
        by_support_status={"safe": 200},
        by_doc_status={"documented_api": 295},
        by_risk={"low": 200, "medium": 85, "high": 10},
        by_backend={"registry": 295},
        system_platform="Windows 11",
    )


@pytest.mark.asyncio
async def test_windows_control_plane_audit_summary(mock_summary):
    """Тестирование получения сводной аналитики Window Control Plane."""
    with patch("apps.windows.sdk.modules.window_control_plane.manager.WindowManagementControlPlane.get_summary", return_value=mock_summary):
        res_raw = await call_tool(windows_control_plane_audit, action="summary")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "summary"
        assert res["summary"]["total_settings"] == 295


@pytest.mark.asyncio
async def test_windows_control_plane_action_dry_run():
    """Тестирование выполнения настройки в режиме dry_run."""
    res_raw = await call_tool(windows_control_plane_action, setting_id="snap_assist_001", value=True, dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "snap_assist_001" in res.get("message", "")


def test_windows_controller_agent_has_window_control_plane_tools():
    """Проверка присутствия инструментов window_control_plane в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_control_plane_audit" in tool_names
    assert "windows_control_plane_action" in tool_names
