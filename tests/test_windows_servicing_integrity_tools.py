# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Servicing Integrity Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Servicing Integrity (servicing_integrity.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_servicing_integrity_tools.py -v
#
# File: test_windows_servicing_integrity_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:15:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Servicing Integrity."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_servicing_integrity_audit,
    windows_servicing_integrity_action,
    WINDOWS_SERVICING_INTEGRITY_TOOLS,
)
from apps.windows.modules.servicing_integrity.core.models import (
    IntegrityReport,
    WindowsFeature,
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
async def test_windows_servicing_integrity_audit_report():
    """Тест получения отчета о целостности системных компонентов."""
    sample_report = IntegrityReport(
        sfc_status="Clean (No violations found)",
        sfc_last_scan="2026-10-08 22:00",
        dism_component_store_status="Healthy",
        dism_cleanup_recommended=False,
        corrupted_files_count=0,
        features_count=2,
        features=[
            WindowsFeature(name="Microsoft-Windows-Subsystem-Linux", state="Enabled"),
            WindowsFeature(name="VirtualMachinePlatform", state="Enabled"),
        ],
        timestamp="2026-10-08T22:00:00",
    )
    with patch("apps.windows.modules.servicing_integrity.core.manager.ServicingIntegrityManager.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_servicing_integrity_audit, action="report")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "report" in res
        assert res["report"]["dism_component_store_status"] == "Healthy"


@pytest.mark.asyncio
async def test_windows_servicing_integrity_action_dry_run():
    """Тест выполнения обслуживания в режиме dry_run."""
    sample_res = {
        "status": "DRY_RUN_SUCCESS",
        "tool": "sfc",
        "action": "scannow",
        "message": "Симуляция sfc scannow прошла успешно.",
    }
    with patch("apps.windows.modules.servicing_integrity.core.manager.ServicingIntegrityManager.execute_servicing_action", return_value=sample_res):
        res_str = await call_tool(
            windows_servicing_integrity_action,
            tool_name="sfc",
            action="scannow",
            dry_run=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["tool"] == "sfc"
        assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_servicing_integrity_tools():
    """Проверка наличия новых инструментов servicing_integrity в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_servicing_integrity_audit" in tool_names
    assert "windows_servicing_integrity_action" in tool_names
