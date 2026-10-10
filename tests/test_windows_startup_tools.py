# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Startup Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов аудита и управления автозагрузкой Windows
#   (windows_startup_audit, windows_startup_action).
#
# Usage Examples:
#   pytest tests/test_windows_startup_tools.py -v
#
# File: test_windows_startup_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:26:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.startup import (
    windows_startup_audit,
    windows_startup_action,
)
from apps.windows.sdk.modules.startup.core.models import (
    AuditReport,
    AuditSummary,
    StartupEntry,
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
def mock_audit_report():
    """Фикстура с тестовым отчетом аудита автозагрузки."""
    summary = AuditSummary(
        total_entries=2,
        active_entries=2,
        disabled_entries=0,
        broken_entries=0,
        clean_count=2,
        health_score=100,
    )
    entry1 = StartupEntry(id="reg_test1", name="TestApp1", command="C:\\test1.exe")
    entry2 = StartupEntry(id="reg_test2", name="TestApp2", command="C:\\test2.exe")
    return AuditReport(
        timestamp="2026-10-08T22:26:00",
        hostname="TEST-PC",
        os_name="Windows 11",
        scan_duration_ms=15.5,
        summary=summary,
        entries=[entry1, entry2],
        security_alerts=[],
        broken_items=[],
        recommendations=["Отличная чистота автозапуска"],
    )


@pytest.mark.asyncio
async def test_windows_startup_audit_summary(mock_audit_report):
    """Тестирование получения сводки элементов автозагрузки."""
    with patch("apps.windows.sdk.modules.startup.core.auditor.StartupAuditor.run_audit", return_value=mock_audit_report):
        res_raw = await call_tool(windows_startup_audit, action="summary")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "summary"
        assert res["summary"]["total_entries"] == 2


@pytest.mark.asyncio
async def test_windows_startup_audit_report(mock_audit_report):
    """Тестирование получения полного отчета по автозагрузке."""
    with patch("apps.windows.sdk.modules.startup.core.auditor.StartupAuditor.run_audit", return_value=mock_audit_report):
        res_raw = await call_tool(windows_startup_audit, action="report", limit=10)
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "report"
        assert len(res["entries"]) == 2


@pytest.mark.asyncio
async def test_windows_startup_action_dry_run():
    """Тестирование безопасности вызова управления автозапуском в режиме dry_run."""
    res_raw = await call_tool(windows_startup_action, entry_id_or_name="test_app", enable=False, dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "test_app" in res.get("message", "")


# Updated: 2026-10-08 22:54:00
# =============================================================================

@pytest.mark.asyncio
async def test_windows_startup_audit_wmi_persistence():
    """Тестирование аудита WMI Persistence."""
    res_raw = await call_tool(windows_startup_audit, action="wmi_persistence")
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("action") == "wmi_persistence"
    assert "wmi_event_consumers" in res


def test_windows_controller_agent_has_startup_tools():
    """Проверка присутствия инструментов startup в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_startup_audit" in tool_names
    assert "windows_startup_action" in tool_names

