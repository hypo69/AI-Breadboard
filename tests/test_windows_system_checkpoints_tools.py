# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows System Checkpoints Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов контрольных точек восстановления Windows
#   (windows_checkpoints_audit, windows_checkpoints_action).
#
# Usage Examples:
#   pytest tests/test_windows_system_checkpoints_tools.py -v
#
# File: test_windows_system_checkpoints_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:31:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.system_checkpoints import (
    windows_checkpoints_audit,
    windows_checkpoints_action,
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


@pytest.fixture
def mock_health():
    """Фикстура готовности контрольных точек."""
    return {
        "health_score": 85,
        "winre": {"enabled": True},
        "system_restore": {"protection_enabled": True, "restore_points_count": 2},
        "system_images": {"total_images_found": 1},
        "freshness": {"can_restore_safely": True},
        "timestamp": "2026-10-08T22:31:00",
    }


@pytest.mark.asyncio
async def test_windows_checkpoints_audit_health(mock_health):
    """Тестирование сводной оценки готовности контрольных точек."""
    with patch("apps.windows.sdk.modules.system_checkpoints.core.checkpoint_coordinator.CheckpointCoordinator.get_comprehensive_health", return_value=mock_health):
        res_raw = await call_tool(windows_checkpoints_audit, action="health")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "health"
        assert res["health"]["health_score"] == 85


@pytest.mark.asyncio
async def test_windows_checkpoints_action_dry_run():
    """Тестирование режима dry_run для создания контрольной точки."""
    res_raw = await call_tool(windows_checkpoints_action, action="create", title="Test Point", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "Test Point" in res.get("message", "")


def test_windows_controller_agent_has_checkpoint_tools():
    """Проверка присутствия инструментов system_checkpoints в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_checkpoints_audit" in tool_names
    assert "windows_checkpoints_action" in tool_names
