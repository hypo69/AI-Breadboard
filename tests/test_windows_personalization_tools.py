# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Personalization Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Personalization (personalization.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_personalization_tools.py -v
#
# File: test_windows_personalization_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:05:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Personalization."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_personalization_overview,
    windows_personalization_theme_action,
    windows_personalization_cursor_wallpaper,
    WINDOWS_PERSONALIZATION_TOOLS,
)
from apps.windows.modules.personalization.models import (
    CursorSettings,
    PersonalizationOverviewResponse,
    WallpaperSettings,
    WindowsSpotlightSettings,
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
async def test_windows_personalization_overview():
    """Тест получения полного обзора персонализации."""
    with patch("apps.windows.modules.personalization.manager.PersonalizationManager.get_overview") as mock_func:
        mock_func.return_value = PersonalizationOverviewResponse(
            current_theme="Windows Dark",
            is_dark_mode=True,
            accent_color_hex="#0078D7",
            cursor=CursorSettings(size=32),
            wallpaper=WallpaperSettings(),
            spotlight=WindowsSpotlightSettings(),
        )
        res_str = await call_tool(windows_personalization_overview, action="overview")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "overview" in res
        assert res["overview"]["current_theme"] == "Windows Dark"


@pytest.mark.asyncio
async def test_windows_personalization_theme_action():
    """Тест применения темы оформления."""
    with patch("apps.windows.modules.personalization.manager.PersonalizationManager.apply_theme") as mock_func:
        mock_func.return_value = {"applied": True, "theme_name": "Windows Dark"}
        res_str = await call_tool(
            windows_personalization_theme_action,
            theme_name_or_path="Windows Dark",
            force_dark_mode=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["theme"] == "Windows Dark"


@pytest.mark.asyncio
async def test_windows_personalization_cursor_wallpaper():
    """Тест получения и обновления настроек указателя мыши."""
    with patch("apps.windows.modules.personalization.manager.PersonalizationManager.get_cursor_settings") as mock_func:
        mock_func.return_value = CursorSettings(size=48, shadow=True)
        res_str = await call_tool(windows_personalization_cursor_wallpaper, action="cursor")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["cursor"]["size"] == 48


def test_windows_controller_agent_has_personalization_tools():
    """Проверка наличия новых инструментов персонализации в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_personalization_overview" in tool_names
    assert "windows_personalization_theme_action" in tool_names
    assert "windows_personalization_cursor_wallpaper" in tool_names
