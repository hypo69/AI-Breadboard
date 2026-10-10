# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Registry Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Registry (registry.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_registry_tools.py -v
#
# File: test_windows_registry_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:08:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Registry."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_registry_read,
    windows_registry_search,
    windows_registry_action,
    WINDOWS_REGISTRY_TOOLS,
)
from apps.windows.registry.models import BookmarkItem, RegistryKeyDetailsDTO


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
async def test_windows_registry_read_bookmarks():
    """Тест получения доступных закладок реестра."""
    sample_bookmarks = [
        BookmarkItem(
            id="startup_run",
            title="Run",
            hive="HKEY_CURRENT_USER",
            path="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            description="Auto run",
            icon="🚀",
        )
    ]
    with patch("apps.windows.sdk.modules.registry.viewer.RegistryViewer.get_bookmarks", return_value=sample_bookmarks):
        res_str = await call_tool(windows_registry_read, action="bookmarks")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "bookmarks" in res
        assert len(res["bookmarks"]) == 1


@pytest.mark.asyncio
async def test_windows_registry_action_dry_run():
    """Тест выполнения изменения реестра в режиме dry_run."""
    res_str = await call_tool(
        windows_registry_action,
        action="set_value",
        hive="HKEY_CURRENT_USER",
        path="Software\\TestKey",
        value_name="TestVal",
        value_data="123",
        dry_run=True,
    )
    res = json.loads(res_str)
    assert res["status"] == "ok"
    assert res["dry_run"] is True


def test_windows_controller_agent_has_registry_tools():
    """Проверка наличия новых инструментов registry в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_registry_read" in tool_names
    assert "windows_registry_search" in tool_names
    assert "windows_registry_action" in tool_names
