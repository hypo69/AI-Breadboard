# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router System Logs Explain
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_router_system_logs_explain`).
#
# Usage Examples:
#   Python API:
#     import tests.test_router_system_logs_explain as test_router_system_logs_explain
#
# File: test_router_system_logs_explain.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_router_system_logs_explain`)."""

import pytest
from unittest.mock import AsyncMock, patch
from src.api.routers.core.router_system_logs import ExplainRequest, explain_event

@pytest.mark.asyncio
async def test_explain_event_heuristic_bits():
    req = ExplainRequest(provider='Microsoft-Windows-Bits-Client', event_id=16393, level='Warning', message='ErrorCode: 2147747072', channel='System')
    result = await explain_event(req)
    assert 'summary' in result
    assert 'root_cause' in result
    assert 'recommendations' in result
    assert 'BITS' in result['summary'] or 'bits' in result['summary'].lower()
    assert '2147747072' in result['root_cause']
    assert any(('Get-BitsTransfer' in r or 'BITS' in r for r in result['recommendations']))

@pytest.mark.asyncio
async def test_explain_event_heuristic_dcom():
    req = ExplainRequest(provider='Microsoft-Windows-DistributedCOM', event_id=10016, level='Warning', message='The application-specific permission settings do not grant Local Activation permission')
    result = await explain_event(req)
    assert 'DCOM' in result['summary']
    assert len(result['recommendations']) > 0

@pytest.mark.asyncio
async def test_explain_event_with_mocked_llm():
    mock_model = AsyncMock()
    mock_model.ask.return_value = '```json\n{"summary": "Фоновая передача BITS временно остановлена.", "root_cause": "Сетевой таймаут при обращении к серверу обновлений Windows.", "recommendations": ["Проверить статус подключения к интернету", "Перезапустить службу BITS: Restart-Service BITS"]}\n```'
    with patch('src.api.routers.core.router_chat.get_chat_model', return_value=mock_model):
        req = ExplainRequest(provider='Microsoft-Windows-Bits-Client', event_id=16393, level='Warning', message='ErrorCode: 2147747072')
        result = await explain_event(req)
        assert result['summary'] == 'Фоновая передача BITS временно остановлена.'
        assert 'Сетевой таймаут' in result['root_cause']
        assert len(result['recommendations']) == 2