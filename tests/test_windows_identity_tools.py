# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Identity Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Identity (identity.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_identity_tools.py -v
#
# File: test_windows_identity_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 20:55:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Identity."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_identity_explain,
    windows_identity_explain_pid,
    windows_identity_audit_security,
    windows_identity_manage_account,
    windows_identity_audit_events,
    windows_identity_graph_build,
    WINDOWS_IDENTITY_TOOLS,
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
async def test_windows_identity_explain_current():
    """Тест вызова windows_identity_explain без параметров (текущий контекст)."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.get_current_identity") as mock_func:
        mock_func.return_value = {"username": "test_user", "sid": "S-1-5-21-1234"}
        res_str = await call_tool(windows_identity_explain)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["target"] == "current_identity"
        assert "identity" in res


@pytest.mark.asyncio
async def test_windows_identity_explain_target():
    """Тест вызова windows_identity_explain с указанием пользователя."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.explain") as mock_func:
        mock_func.return_value = {"name": "onela", "sid": "S-1-5-21-5678"}
        res_str = await call_tool(windows_identity_explain, identifier="onela")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["target"] == "onela"
        assert "principal" in res


@pytest.mark.asyncio
async def test_windows_identity_explain_pid():
    """Тест вызова windows_identity_explain_pid."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.explain_pid") as mock_func:
        mock_func.return_value = {"pid": 1234, "process": "python.exe", "elevated": True}
        res_str = await call_tool(windows_identity_explain_pid, pid=1234)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["pid"] == 1234
        assert "pid_analysis" in res


@pytest.mark.asyncio
async def test_windows_identity_audit_security():
    """Тест аудита безопасности через windows_identity_audit_security."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.who_is_admin") as mock_admin, \
         patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.who_can_rdp") as mock_rdp, \
         patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.who_can_logon_as_service") as mock_srv, \
         patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.find_orphaned_sids") as mock_sids, \
         patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.find_orphaned_profiles") as mock_prof:

        mock_admin.return_value = [{"name": "Administrator"}]
        mock_rdp.return_value = ["Administrator", "onela"]
        mock_srv.return_value = ["LOCAL SERVICE"]
        mock_sids.return_value = []
        mock_prof.return_value = []

        res_str = await call_tool(windows_identity_audit_security, mode="all")
        res = json.loads(res_str)

        assert res["status"] == "ok"
        assert "admins" in res
        assert "rdp_users" in res
        assert "service_logon_users" in res
        assert "orphaned_sids" in res


@pytest.mark.asyncio
async def test_windows_identity_manage_account():
    """Тест операций управления учетными записями."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.list_users") as mock_users:
        mock_users.return_value = [{"name": "User1"}, {"name": "User2"}]
        res_str = await call_tool(windows_identity_manage_account, action="list_users")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert len(res["users"]) == 2


@pytest.mark.asyncio
async def test_windows_identity_audit_events():
    """Тест запроса журнала событий безопасности."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.get_audit_events") as mock_events:
        mock_events.return_value = [{"event_id": 4624, "user": "onela"}]
        res_str = await call_tool(windows_identity_audit_events, limit=10)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert len(res["events"]) == 1


@pytest.mark.asyncio
async def test_windows_identity_graph_build():
    """Тест построения Identity Graph."""
    with patch("apps.windows.modules.accounts_identity.service.AccountsIdentityService.get_identity_graph") as mock_graph:
        mock_graph.return_value = {"nodes": [], "edges": []}
        res_str = await call_tool(windows_identity_graph_build)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "graph" in res


def test_windows_controller_agent_has_identity_tools():
    """Проверка, что WindowsControllerAgent содержит новые инструменты."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_identity_explain" in tool_names
    assert "windows_identity_explain_pid" in tool_names
    assert "windows_identity_audit_security" in tool_names
    assert "windows_identity_manage_account" in tool_names
    assert "windows_identity_audit_events" in tool_names
    assert "windows_identity_graph_build" in tool_names
