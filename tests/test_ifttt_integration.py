# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Ifttt Integration
# =============================================================================
# Description:
#   Fixture providing a mocked aiohttp.ClientSession with successful response.
#
# Usage Examples:
#   Python API:
#     from tests.test_ifttt_integration import TestIFTTTClient
#
#     service = TestIFTTTClient()
#
# File: test_ifttt_integration.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Fixture providing a mocked aiohttp.ClientSession with successful response."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from plugins.ifttt import IFTTTClient, send_ifttt_event
from src.ai.agents.tools import ifttt_trigger_event
from src.api.routers.core.router_ifttt import init_router

@pytest.fixture
def mock_aiohttp_session():
    """Fixture providing a mocked aiohttp.ClientSession with successful response."""
    with patch('aiohttp.ClientSession') as mock_session_cls:
        mock_session = MagicMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "Congratulations! You've fired the living_room_lights_on event"
        mock_post_cm = MagicMock()
        mock_post_cm.__aenter__.return_value = mock_response
        mock_post_cm.__aexit__.return_value = None
        mock_session.post.return_value = mock_post_cm
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session_cls.return_value.__aexit__.return_value = None
        yield (mock_session, mock_response)

class TestIFTTTClient:
    """Test suite for IFTTTClient class."""

    @pytest.mark.asyncio
    async def test_trigger_event_happy_path(self, mock_aiohttp_session):
        """Test standard successful event trigger with values (Happy Path).

        Verify: Valid event with value1/value2 sends POST and returns success.
        """
        mock_session, _ = mock_aiohttp_session
        client: IFTTTClient = IFTTTClient(webhook_key='test_secret_key_12345')
        event_name: str = 'living_room_lights_on'
        val1: str = 'warm_white'
        val2: str = '80%'
        result: dict = await client.trigger_event(event_name=event_name, value1=val1, value2=val2)
        assert result['status'] == 'success', f"Expected 'success', got {result.get('status')}"
        assert result['event'] == event_name, f"Expected event '{event_name}', got {result.get('event')}"
        assert result['http_code'] == 200, f"Expected HTTP 200, got {result.get('http_code')}"

    @pytest.mark.asyncio
    async def test_trigger_event_json_payload(self, mock_aiohttp_session):
        """Test triggering event with structured JSON payload (Type Variants).

        Verify: Providing json_payload routes to /json endpoint and dispatches payload.
        """
        mock_session, _ = mock_aiohttp_session
        client: IFTTTClient = IFTTTClient(webhook_key='test_key')
        custom_payload: dict = {'temperature': 22.5, 'mode': 'eco', 'room': 'office'}
        result: dict = await client.trigger_event(event_name='set_climate', json_payload=custom_payload)
        assert result['status'] == 'success', 'Failed to dispatch JSON payload'
        call_args = mock_session.post.call_args
        assert '/json/with/key/' in call_args[0][0], 'Endpoint should contain /json/with/key/'

    @pytest.mark.asyncio
    async def test_trigger_event_empty_name_edge_case(self):
        """Test triggering with empty event name (Edge Cases).

        Verify: Returns error status early without making network calls.
        """
        client: IFTTTClient = IFTTTClient(webhook_key='test_key')
        result: dict = await client.trigger_event(event_name='')
        assert result['status'] == 'error', 'Expected error status for empty event_name'
        assert 'event_name cannot be empty' in result['error'], 'Missing appropriate error message'

    @pytest.mark.asyncio
    async def test_trigger_event_missing_key_edge_case(self):
        """Test triggering when no API key is configured (Edge Cases).

        Verify: Returns error indicating missing IFTTT_WEBHOOK_KEY.
        """
        with patch.dict('os.environ', {}, clear=True):
            client: IFTTTClient = IFTTTClient(webhook_key='')
            client.webhook_key = ''
            result: dict = await client.trigger_event(event_name='test_event')
            assert result['status'] == 'error', 'Expected error when key is absent'
            assert 'IFTTT_WEBHOOK_KEY is not set' in result['error'], 'Expected missing key error text'

    @pytest.mark.asyncio
    async def test_trigger_event_http_error(self, mock_aiohttp_session):
        """Test handling of HTTP failure responses from IFTTT (Error Scenarios).

        Verify: Returns status='error' with error details when status is 401 Unauthorized.
        """
        mock_session, mock_response = mock_aiohttp_session
        mock_response.status = 401
        mock_response.text.return_value = 'Invalid key'
        client: IFTTTClient = IFTTTClient(webhook_key='invalid_key')
        result: dict = await client.trigger_event(event_name='test_event')
        assert result['status'] == 'error', 'Expected error status on HTTP 401'
        assert result['http_code'] == 401, 'Expected HTTP code 401 in result'
        assert result['error'] == 'Invalid key', 'Expected error text matching body'

    @pytest.mark.asyncio
    async def test_trigger_event_network_exception(self):
        """Test client robustness against network exceptions (Error Scenarios).

        Verify: Catches exceptions and returns error dict instead of crashing.
        """
        client: IFTTTClient = IFTTTClient(webhook_key='test_key')
        with patch('aiohttp.ClientSession.post', side_effect=Exception('Connection timed out')):
            result: dict = await client.trigger_event(event_name='test_event')
            assert result['status'] == 'error', 'Expected error status on exception'
            assert 'Connection timed out' in result['error'], 'Expected timeout error message'

    def test_client_status(self):
        """Test get_status method of IFTTTClient."""
        client_configured: IFTTTClient = IFTTTClient(webhook_key='abcdef123456')
        client_unconfigured: IFTTTClient = IFTTTClient(webhook_key='')
        client_unconfigured.webhook_key = ''
        status_cfg = client_configured.get_status()
        assert status_cfg['configured'] is True, 'Expected configured=True'
        assert '...' in status_cfg['masked_key'], 'Expected masked key'
        status_uncfg = client_unconfigured.get_status()
        assert status_uncfg['configured'] is False, 'Expected configured=False'

class TestLangChainTool:
    """Test suite for ifttt_trigger_event LangChain tool."""

    @pytest.mark.asyncio
    async def test_tool_invocation_happy_path(self, mock_aiohttp_session):
        """Test invoking ifttt_trigger_event tool from agent context (Happy Path).

        Verify: Tool returns a JSON string containing the success payload.
        """
        with patch.dict('os.environ', {'IFTTT_WEBHOOK_KEY': 'valid_env_key'}):
            tool_output_str: str = await ifttt_trigger_event.invoke({'event_name': 'turn_on_ac', 'value1': '21C', 'value2': 'high'})
            tool_output: dict = json.loads(tool_output_str)
            assert tool_output.get('status') == 'success', 'Tool invocation should succeed'
            assert tool_output.get('event') == 'turn_on_ac', 'Event name mismatch'

    @pytest.mark.asyncio
    async def test_tool_invocation_with_json_data(self, mock_aiohttp_session):
        """Test invoking ifttt_trigger_event tool with json_data string (Type Variants).

        Verify: Parses json_data and sends structured payload.
        """
        with patch.dict('os.environ', {'IFTTT_WEBHOOK_KEY': 'valid_env_key'}):
            json_str: str = json.dumps({'scene': 'reading', 'brightness': 60})
            tool_output_str: str = await ifttt_trigger_event.invoke({'event_name': 'set_lighting_scene', 'json_data': json_str})
            tool_output: dict = json.loads(tool_output_str)
            assert tool_output.get('status') == 'success', 'Tool invocation should succeed with json_data'

class TestFastAPIRouter:
    """Test suite for FastAPI IFTTT router endpoints."""

    @pytest.fixture
    def test_app(self):
        """Fixture creating a test FastAPI app with mounted IFTTT router."""
        app = FastAPI()
        app.include_router(init_router())
        return app

    def test_router_status_endpoint(self, test_app):
        """Test GET /api/ifttt/status endpoint."""
        client = TestClient(test_app)
        response = client.get('/api/ifttt/status')
        assert response.status_code == 200, 'Status endpoint should return 200'
        data = response.json()
        assert 'configured' in data, "Response should include 'configured' field"

    def test_router_trigger_endpoint_happy_path(self, test_app, mock_aiohttp_session):
        """Test POST /api/ifttt/trigger/{event_name} (Happy Path)."""
        client = TestClient(test_app)
        with patch.dict('os.environ', {'IFTTT_WEBHOOK_KEY': 'test_key'}):
            response = client.post('/api/ifttt/trigger/robot_vacuum_start', json={'value1': 'living_room', 'value2': 'spot_clean'})
            assert response.status_code == 200, f'Trigger failed with: {response.text}'
            data = response.json()
            assert data['status'] == 'success', 'Expected status success'

    def test_router_inbound_webhook_endpoint(self, test_app):
        """Test POST /api/ifttt/webhook/{event_name} inbound webhook."""
        client = TestClient(test_app)
        response = client.post('/api/ifttt/webhook/motion_front_door', json={'sensor_id': 'door_1', 'battery': '95%'})
        assert response.status_code == 200, 'Inbound webhook should return 200'
        data = response.json()
        assert data['status'] == 'received', "Expected status 'received'"
        assert data['event'] == 'motion_front_door', "Expected event 'motion_front_door'"