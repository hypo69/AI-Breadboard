# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Security ACL Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Security ACL (security_acl.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_security_acl_tools.py -v
#
# File: test_windows_security_acl_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:10:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Security ACL."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_security_acl_audit,
    windows_security_acl_action,
    WINDOWS_SECURITY_ACL_TOOLS,
)
from apps.windows.modules.security_acl.core.models import (
    AclEntry,
    BitLockerVolumeStatus,
    SecurityAclReport,
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
async def test_windows_security_acl_audit_report():
    """Тест получения отчета безопасности ACL и BitLocker."""
    sample_report = SecurityAclReport(
        bitlocker_volumes=[
            BitLockerVolumeStatus(
                drive_letter="C:",
                conversion_status="FullyEncrypted",
                protection_status="ProtectionOn",
                encryption_method="XTS-AES 128",
                lock_status="Unlocked",
            )
        ],
        efs_enabled=True,
        uac_level="AlwaysNotify",
        timestamp="2026-10-08T22:00:00",
    )
    with patch("apps.windows.modules.security_acl.core.manager.SecurityAclManager.generate_report", return_value=sample_report):
        res_str = await call_tool(windows_security_acl_audit, action="report")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "report" in res
        assert res["report"]["efs_enabled"] is True


@pytest.mark.asyncio
async def test_windows_security_acl_action_dry_run():
    """Тест выполнения изменения прав ACL в режиме dry_run."""
    sample_res = {
        "status": "DRY_RUN_SUCCESS",
        "target": "C:\\TestDir",
        "principal": "BUILTIN\\Users",
        "action": "grant",
        "message": "Симуляция изменения ACL выполнена успешно.",
    }
    with patch("apps.windows.modules.security_acl.core.manager.SecurityAclManager.execute_acl_modification", return_value=sample_res):
        res_str = await call_tool(
            windows_security_acl_action,
            target_path="C:\\TestDir",
            principal="BUILTIN\\Users",
            rights="ReadAndExecute",
            action="grant",
            dry_run=True,
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["result"]["status"] == "DRY_RUN_SUCCESS"


def test_windows_controller_agent_has_security_acl_tools():
    """Проверка наличия новых инструментов security_acl в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_security_acl_audit" in tool_names
    assert "windows_security_acl_action" in tool_names
