# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Backup Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Backup & Recovery (backup.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_backup_tools.py -v
#
# File: test_windows_backup_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:06:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Backup & Recovery."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_backup_health_check,
    windows_backup_file_history,
    windows_backup_vss_snapshots,
    windows_backup_user_folders,
    windows_backup_version_control,
    WINDOWS_BACKUP_TOOLS,
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
async def test_windows_backup_health_check():
    """Тест вызова диагностики здоровья бэкапов."""
    with patch("apps.windows.sdk.modules.backup_manager.core.health_checker.BackupHealthChecker.generate_report") as mock_func:
        mock_func.return_value = {"health_score": 90, "recommendations": ["Всё в порядке"]}
        res_str = await call_tool(windows_backup_health_check)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "health_report" in res
        assert res["health_report"]["health_score"] == 90


@pytest.mark.asyncio
async def test_windows_backup_file_history_status():
    """Тест получения статуса Истории файлов."""
    mock_status = MagicMock()
    mock_status.to_dict.return_value = {"service_status": "Running", "service_start_type": "Automatic"}
    with patch("apps.windows.sdk.modules.backup_manager.core.file_history_manager.FileHistoryManager.get_status") as mock_func:
        mock_func.return_value = mock_status
        res_str = await call_tool(windows_backup_file_history, action="status")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["file_history"]["service_status"] == "Running"


@pytest.mark.asyncio
async def test_windows_backup_file_history_trigger():
    """Тест принудительного запуска архивации."""
    with patch("apps.windows.sdk.modules.backup_manager.core.file_history_manager.FileHistoryManager.trigger_backup_now") as mock_func:
        mock_func.return_value = (True, "Запущено")
        res_str = await call_tool(windows_backup_file_history, action="trigger")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["triggered"] is True


@pytest.mark.asyncio
async def test_windows_backup_vss_snapshots():
    """Тест получения списка снимков VSS."""
    with patch("apps.windows.sdk.modules.backup_manager.core.vss_manager.VssManager.list_snapshots") as mock_func:
        mock_func.return_value = [{"shadow_id": "{1234}", "volume": "C:\\"}]
        res_str = await call_tool(windows_backup_vss_snapshots)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert len(res["vss_snapshots"]) == 1


@pytest.mark.asyncio
async def test_windows_backup_user_folders_overview():
    """Тест получения обзора пользовательских папок."""
    with patch("apps.windows.sdk.modules.backup_manager.core.user_folders_manager.UserFoldersManager.get_overview") as mock_func:
        mock_func.return_value = {"folders": [{"name": "Documents", "size_bytes": 1024}]}
        res_str = await call_tool(windows_backup_user_folders, action="overview")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "user_folders" in res


@pytest.mark.asyncio
async def test_windows_backup_version_control_list():
    """Тест получения истории версий файла."""
    with patch("apps.windows.sdk.modules.backup_manager.core.version_provider.WindowsVersionProvider.list_versions") as mock_func:
        mock_func.return_value = [{"version_id": 1, "timestamp": "2026-10-08 12:00:00"}]
        res_str = await call_tool(windows_backup_version_control, action="list", file_path="C:\\test.txt")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert len(res["versions"]) == 1


def test_windows_controller_agent_has_backup_tools():
    """Проверка наличия новых инструментов бэкапов в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_backup_health_check" in tool_names
    assert "windows_backup_file_history" in tool_names
    assert "windows_backup_vss_snapshots" in tool_names
    assert "windows_backup_user_folders" in tool_names
    assert "windows_backup_version_control" in tool_names
