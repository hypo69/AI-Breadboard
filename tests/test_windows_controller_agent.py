# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Controller Agent
# =============================================================================
# Description:
#   Тестовый набор для проверки инструментов Windows, агента WindowsControllerAgent
#   и навыка windows-system-controller.
#
# Usage Examples:
#   CLI:
#     pytest tests/test_windows_controller_agent.py -v
#
# File: test_windows_controller_agent.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 20:20:00
# =============================================================================

"""Тестовый набор для проверки инструментов Windows, агента и навыка."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from langchain_core.messages import AIMessage

from src.ai.agents.loader import load_agent_from_manifest
from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_collector_audit,
    windows_execute_atomic_op,
    windows_manage_service,
    windows_manage_process,
    windows_manage_restore_point,
    windows_manage_sys_param,
    windows_safe_probe,
    windows_manage_optional_feature,
    WINDOWS_NATIVE_TOOLS,
)
from src.skills.registry import SkillRegistry



async def call_tool(tool, **kwargs):
    """Вспомогательная функция для вызова инструмента (LangChain StructuredTool или функции)."""
    if hasattr(tool, 'ainvoke'):
        return await tool.ainvoke(kwargs)
    elif hasattr(tool, 'invoke'):
        return tool.invoke(kwargs)
    elif hasattr(tool, 'func') and tool.func:
        func = tool.func
        return await func(**kwargs) if asyncio.iscoroutinefunction(func) else func(**kwargs)
    else:
        return await tool(**kwargs)


class TestWindowsTools:
    """Тестирование набора нативных инструментов Windows."""

    @pytest.mark.asyncio
    async def test_windows_collector_audit_tool(self):
        """Проверка запуска коллектора аудита."""
        raw_res = await call_tool(windows_collector_audit, collector_name='process')
        data = json.loads(raw_res)
        assert 'status' in data
        assert data['collector'] == 'process'

    @pytest.mark.asyncio
    async def test_windows_execute_atomic_op_dry_run(self):
        """Проверка выполнения атомарной операции в режиме dry-run."""
        raw_res = await call_tool(windows_execute_atomic_op, operation_id='diskpart.disk.list', dry_run=True)
        data = json.loads(raw_res)
        assert data['status'] in ('DRY_RUN', 'DRY_RUN_SIMULATED')
        assert data['operation_id'] == 'diskpart.disk.list'
        assert data['is_dry_run'] is True
        assert 'command_executed' in data

    @pytest.mark.asyncio
    async def test_windows_manage_service_status(self):
        """Проверка запроса статуса службы."""
        raw_res = await call_tool(windows_manage_service, service_name='wuauserv', action='status')
        data = json.loads(raw_res)
        assert data['status'] in ('ok', 'not_found')
        if data['status'] == 'ok':
            assert 'service' in data
            assert 'name' in data['service']

    @pytest.mark.asyncio
    async def test_windows_manage_process_list(self):
        """Проверка получения списка процессов."""
        raw_res = await call_tool(windows_manage_process, action='list')
        data = json.loads(raw_res)
        assert data['status'] == 'ok'
        assert 'processes' in data
        assert isinstance(data['processes'], list)

    @pytest.mark.asyncio
    async def test_windows_manage_restore_point_status(self):
        """Проверка запроса статуса защиты системы."""
        raw_res = await call_tool(windows_manage_restore_point, action='status')
        data = json.loads(raw_res)
        assert 'system_protection_enabled' in data

    @pytest.mark.asyncio
    async def test_windows_manage_sys_param_list(self):
        """Проверка каталога параметров SafeOps."""
        raw_res = await call_tool(windows_manage_sys_param, action='list')
        data = json.loads(raw_res)
        assert data['status'] == 'ok'
        assert 'parameters' in data

    @pytest.mark.asyncio
    async def test_windows_safe_probe_security_filter(self):
        """Проверка блокировки деструктивных команд в safe probe."""
        raw_res = await call_tool(windows_safe_probe, script='Remove-Item -Recurse C:\\Windows\\System32')
        data = json.loads(raw_res)
        assert data['status'] == 'error'
        assert 'SafeOps' in data['message'] or 'отклонена' in data['message']

    @pytest.mark.asyncio
    async def test_windows_execute_powershell_basic(self):
        """Проверка выполнения базовой команды PowerShell."""
        from src.ai.agents.windows_tools import windows_execute_powershell
        raw_res = await call_tool(windows_execute_powershell, script='Write-Output "PowerShell_OK"')
        data = json.loads(raw_res)
        assert data['status'] == 'ok'
        assert 'PowerShell_OK' in data.get('stdout', '')

    @pytest.mark.asyncio
    async def test_windows_execute_powershell_dry_run(self):
        """Проверка симуляции команды PowerShell."""
        from src.ai.agents.windows_tools import windows_execute_powershell
        raw_res = await call_tool(windows_execute_powershell, script='Restart-Computer', dry_run=True)
        data = json.loads(raw_res)
        assert data['status'] == 'DRY_RUN_SIMULATED'
        assert data['is_dry_run'] is True

    @pytest.mark.asyncio
    async def test_windows_execute_powershell_json_parsing(self):
        """Проверка выполнения команды с парсингом JSON."""
        from src.ai.agents.windows_tools import windows_execute_powershell
        raw_res = await call_tool(windows_execute_powershell, script='[PSCustomObject]@{Name="Test"; Status="Active"} | ConvertTo-Json', as_json=True)
        data = json.loads(raw_res)
        assert data['status'] == 'ok'
        assert isinstance(data.get('data'), dict)
        assert data['data'].get('Name') == 'Test'

    @pytest.mark.asyncio
    async def test_windows_manage_optional_feature_mock(self):
        """Проверка работы инструмента управления optional features с моком manager."""
        with patch('apps.windows.features.manager.get_windows_features', return_value=[{'FeatureName': 'TelnetClient', 'State': 'Disabled'}]):
            raw_res = await call_tool(windows_manage_optional_feature, action='list')
            data = json.loads(raw_res)
            assert data['status'] == 'ok'
            assert data['action'] == 'list'
            assert isinstance(data['features'], list)
            assert data['features'][0]['FeatureName'] == 'TelnetClient'


class TestWindowsControllerAgent:
    """Тестирование класса агента и манифеста."""

    def test_load_agent_from_manifest(self):
        """Проверка загрузки агента из .agents/windows_controller_agent.json."""
        agent = load_agent_from_manifest('windows_controller_agent')
        assert isinstance(agent, WindowsControllerAgent)
        assert len(agent.native_tools) >= 8

    def test_agent_native_tools_registered(self):
        """Проверка состава инструментов агента."""
        agent = WindowsControllerAgent()
        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.native_tools]
        assert 'windows_collector_audit' in tool_names
        assert 'windows_execute_atomic_op' in tool_names
        assert 'windows_manage_service' in tool_names
        assert 'windows_manage_process' in tool_names
        assert 'windows_manage_restore_point' in tool_names
        assert 'windows_manage_sys_param' in tool_names
        assert 'windows_safe_probe' in tool_names
        assert 'windows_execute_powershell' in tool_names
        assert 'windows_manage_optional_feature' in tool_names


    @pytest.mark.asyncio
    async def test_agent_search_mock(self):
        """Проверка выполнения ReAct цикла с мок-моделью."""
        agent = WindowsControllerAgent()
        mock_llm = MagicMock()
        agent._llm = mock_llm
        with patch('langgraph.prebuilt.create_react_agent') as mock_create_agent:
            mock_executor = MagicMock()
            mock_executor.ainvoke = AsyncMock(return_value={'messages': [AIMessage(content='{"action": "windows_control_report", "summary": "Аудит завершен успешно"}')]})
            mock_create_agent.return_value = mock_executor

            res = await agent.search("Проведи диагностику дисков и сети")
            assert res.get('action') == 'windows_control_report'
            assert 'summary' in res or 'text' in res

    @pytest.mark.asyncio
    async def test_agent_search_stream(self):
        """Проверка потоковой генерации статусов."""
        agent = WindowsControllerAgent()
        with patch.object(agent, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {'action': 'windows_control_report', 'summary': 'ОК'}
            statuses = []
            async for chunk in agent.search_stream("Проверь систему"):
                statuses.append(chunk)

            assert len(statuses) >= 2
            assert any('status' in s for s in statuses)
            assert any('result' in s for s in statuses)


class TestWindowsSkill:
    """Тестирование регистрации навыка Windows."""

    def test_skill_discovery(self):
        """Проверка нахождения навыка windows-system-controller в SkillRegistry."""
        registry = SkillRegistry()
        skill = registry.get('windows-system-controller')
        assert skill is not None
        assert skill.name == 'windows-system-controller'
        assert 'Windows' in skill.description
        prompt = skill.prompt()
        assert 'SafeOps' in prompt
        assert 'windows_collector_audit' in prompt
