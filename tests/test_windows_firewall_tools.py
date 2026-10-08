# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Firewall Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Firewall Manager (firewall.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_firewall_tools.py -v
#
# File: test_windows_firewall_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:36:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Firewall Manager."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_firewall_audit,
    windows_firewall_rule_action,
    WINDOWS_FIREWALL_TOOLS,
)


from apps.windows.modules.firewall_manager.core.models import FirewallProfile, FirewallRule


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
async def test_windows_firewall_audit_profiles():
    """Тест аудита профилей брандмауэра."""
    with patch("apps.windows.modules.firewall_manager.core.manager.FirewallManager.get_profiles") as mock_func:
        mock_func.return_value = [
            FirewallProfile(profile_type="Domain", enabled=True, default_inbound_action="Block", default_outbound_action="Allow"),
            FirewallProfile(profile_type="Private", enabled=True, default_inbound_action="Block", default_outbound_action="Allow"),
            FirewallProfile(profile_type="Public", enabled=True, default_inbound_action="Block", default_outbound_action="Allow"),
        ]
        res_str = await call_tool(windows_firewall_audit, action="profiles")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "profiles" in res
        assert len(res["profiles"]) == 3


@pytest.mark.asyncio
async def test_windows_firewall_audit_rules():
    """Тест списка правил сетевого экрана."""
    with patch("apps.windows.modules.firewall_manager.core.manager.FirewallManager.list_rules") as mock_func:
        mock_func.return_value = [
            FirewallRule(name="AI-Breadboard FastApi Server", direction="In", action="Allow", enabled=True, protocol="TCP", local_port="8000")
        ]
        res_str = await call_tool(windows_firewall_audit, action="rules", direction="in")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "rules" in res
        assert len(res["rules"]) == 1


@pytest.mark.asyncio
async def test_windows_firewall_rule_action_dry_run():
    """Тест выполнения операции над правилом в режиме dry_run."""
    res_str = await call_tool(
        windows_firewall_rule_action,
        action="enable",
        rule_name="AI-Breadboard FastApi Server",
        dry_run=True,
    )
    res = json.loads(res_str)
    assert res["status"] == "ok"
    assert res["result"]["status"] == "DRY_RUN_SUCCESS"


@pytest.mark.asyncio
async def test_windows_firewall_rule_action_confirmed():
    """Тест изменения правила брандмауэра с пользовательским подтверждением."""
    with patch("apps.windows.telemetry.sqlite.TelemetryStorage.update_firewall_rule_state"):
        res_str = await call_tool(
            windows_firewall_rule_action,
            action="enable",
            rule_name="AI-Breadboard FastApi Server",
            dry_run=False,
            confirmed_by_user=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["result"]["status"] == "SUCCESS"


def test_windows_controller_agent_has_firewall_tools():
    """Проверка наличия новых инструментов брандмауэра в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_firewall_audit" in tool_names
    assert "windows_firewall_rule_action" in tool_names
