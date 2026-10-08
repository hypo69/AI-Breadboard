# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Storage Manager Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов инспекции и управления дисковым хранилищем
#   (windows_storage_audit, windows_storage_action).
#
# Usage Examples:
#   pytest tests/test_windows_storage_manager_tools.py -v
#
# File: test_windows_storage_manager_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:27:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.storage_manager import (
    windows_storage_audit,
    windows_storage_action,
)
from apps.windows.modules.storage_manager.core.models import (
    DiskInfo,
    StorageReport,
    VolumeInfo,
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
def mock_storage_report():
    """Фикстура с тестовым отчетом по хранилищу."""
    vol = VolumeInfo(
        volume_id="C:",
        drive_letter="C:",
        mount_point="C:\\",
        filesystem="NTFS",
        total_gb=500.0,
        free_gb=250.0,
    )
    disk = DiskInfo(
        disk_id=0,
        name="NVMe SSD 500GB",
        bus_type="NVMe",
        media_type="SSD",
        size_gb=500.0,
    )
    return StorageReport(
        timestamp="2026-10-08T22:27:00",
        volumes=[vol],
        disks=[disk],
    )


@pytest.mark.asyncio
async def test_windows_storage_audit_summary(mock_storage_report):
    """Тест сводной статистики дискового хранилища."""
    with patch("apps.windows.modules.storage_manager.core.manager.StorageManager.generate_report", return_value=mock_storage_report):
        res_raw = await call_tool(windows_storage_audit, action="summary")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "summary"
        assert res["total_disks"] == 1


@pytest.mark.asyncio
async def test_windows_storage_audit_volumes(mock_storage_report):
    """Тест инспекции логических томов."""
    with patch("apps.windows.modules.storage_manager.core.manager.StorageManager.get_volumes", return_value=mock_storage_report.volumes):
        res_raw = await call_tool(windows_storage_audit, action="volumes")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "volumes"
        assert len(res["volumes"]) == 1


@pytest.mark.asyncio
async def test_windows_storage_action_dry_run():
    """Тест выполнения действия над хранилищем в режиме dry_run."""
    res_raw = await call_tool(windows_storage_action, action="check_filesystem", target="C:", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "C:" in res.get("message", "")


def test_windows_controller_agent_has_storage_tools():
    """Проверка присутствия инструментов storage_manager в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_storage_audit" in tool_names
    assert "windows_storage_action" in tool_names
