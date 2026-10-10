# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Sysadmin Tools Tests
# =============================================================================
# Description:
#   Модульные тесты для инструментов системного администрирования Windows
#   (windows_sysadmin_audit, windows_sysadmin_action).
#
# Usage Examples:
#   pytest tests/test_windows_sysadmin_tools.py -v
#
# File: test_windows_sysadmin_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:28:00
# =============================================================================

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools.sysadmin import (
    windows_sysadmin_audit,
    windows_sysadmin_action,
)
from apps.windows.sdk.modules.sysadmin.src.user_collector import WindowsAccountDetails
from apps.windows.sdk.modules.sysadmin.src.file_auditor import AuditPolicyStatus


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
def mock_users():
    """Фикстура списка пользователей."""
    u1 = WindowsAccountDetails(
        name="Administrator",
        sid="S-1-5-21-111-222-333-500",
        enabled=True,
        is_admin=True,
    )
    u2 = WindowsAccountDetails(
        name="TestUser",
        sid="S-1-5-21-111-222-333-1001",
        enabled=True,
        is_admin=False,
    )
    return [u1, u2]


@pytest.mark.asyncio
async def test_windows_sysadmin_audit_users(mock_users):
    """Тестирование аудита списка пользователей."""
    with patch("apps.windows.sdk.modules.sysadmin.src.user_collector.WindowsUserCollector.get_all_users", return_value=mock_users):
        res_raw = await call_tool(windows_sysadmin_audit, action="users")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "users"
        assert res["total_users"] == 2


@pytest.mark.asyncio
async def test_windows_sysadmin_audit_policy():
    """Тестирование проверки политики аудита."""
    mock_policy = AuditPolicyStatus(
        subcategory="File System",
        success_enabled=True,
        failure_enabled=False,
    )
    with patch("apps.windows.sdk.modules.sysadmin.src.file_auditor.WindowsFileAuditor.get_audit_policy_status", return_value=mock_policy):
        res_raw = await call_tool(windows_sysadmin_audit, action="audit_policy")
        res = json.loads(res_raw)
        assert res.get("status") == "ok"
        assert res.get("action") == "audit_policy"
        assert res["policy"]["success_enabled"] is True


@pytest.mark.asyncio
async def test_windows_sysadmin_action_dry_run():
    """Тестирование режима dry_run для sysadmin действий."""
    res_raw = await call_tool(windows_sysadmin_action, action="toggle_user_status", target="TestUser", value="disable", dry_run=True)
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("dry_run") is True
    assert "TestUser" in res.get("message", "")


# Updated: 2026-10-08 22:54:00
# =============================================================================

@pytest.mark.asyncio
async def test_windows_sysadmin_audit_usb_history():
    """Тестирование аудита истории USB устройств."""
    res_raw = await call_tool(windows_sysadmin_audit, action="usb_history")
    res = json.loads(res_raw)
    assert res.get("status") == "ok"
    assert res.get("action") == "usb_history"
    assert "usb_devices" in res


def test_windows_controller_agent_has_sysadmin_tools():
    """Проверка присутствия sysadmin инструментов в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_sysadmin_audit" in tool_names
    assert "windows_sysadmin_action" in tool_names

