# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router Agents
# =============================================================================
# Description:
#   Testing CRUD and helper endpoints /api/agents.
#
# Usage Examples:
#   Python API:
#     from tests.test_router_agents import TestAgentsRouter
#
#     service = TestAgentsRouter()
#
# File: test_router_agents.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Testing CRUD and helper endpoints /api/agents."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from src.api.routers.core.router_agents import _get_agents_list, _save_agents_list
client = TestClient(app)

class TestAgentsRouter:
    """Testing CRUD and helper endpoints /api/agents."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Save and restore state of agents list."""
        self.original_agents = _get_agents_list()
        yield
        _save_agents_list(self.original_agents)

    def test_list_agents(self):
        """Check retrieval of all agents list."""
        response = client.get('/api/agents')
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0
        ids = [a.get('id') for a in agents]
        assert 'travel_agent' in ids
        assert 'web_search_gemini' in ids
        assert 'web_search_gemini_cli' in ids

    def test_list_tools(self):
        """Check retrieval of tools catalog."""
        response = client.get('/api/agents/tools')
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        tool_ids = [t.get('id') for t in tools]
        assert 'flight_search' in tool_ids
        assert 'flight_price_calculator' in tool_ids
        assert 'web_search' in tool_ids
        assert 'rag_search' in tool_ids
        assert 'python_eval' in tool_ids

    def test_list_providers(self):
        """Check list of providers and models from pool."""
        response = client.get('/api/agents/providers')
        assert response.status_code == 200
        providers = response.json()
        assert 'gemini' in providers
        assert 'agy' in providers
        assert 'foundry' in providers
        assert 'ollama' in providers
        assert len(providers['gemini']['models']) > 0

    def test_create_and_delete_custom_agent(self):
        """Test creating and subsequent deletion of custom agent."""
        new_agent = {'id': 'test_research_agent', 'name': 'Research Assistant', 'description': 'Test agent for information search', 'is_system': False, 'enabled': True, 'provider': 'gemini', 'model': 'gemini-3.5-flash-lite', 'temperature': 0.2, 'max_steps': 10, 'timeout_seconds': 45, 'tools': ['web_search', 'rag_search'], 'system_prompt': 'You are a test research agent.'}
        create_res = client.post('/api/agents', json=new_agent)
        assert create_res.status_code == 200
        data = create_res.json()
        assert data.get('status') == 'ok'
        assert data.get('agent', {}).get('id') == 'test_research_agent'
        assert data.get('agent', {}).get('is_system') is False
        list_res = client.get('/api/agents')
        agent_ids = [a.get('id') for a in list_res.json()]
        assert 'test_research_agent' in agent_ids
        updated_agent = dict(new_agent)
        updated_agent['name'] = 'Updated Research Assistant'
        updated_agent['enabled'] = False
        update_res = client.put('/api/agents/test_research_agent', json=updated_agent)
        assert update_res.status_code == 200
        assert update_res.json().get('agent', {}).get('name') == 'Updated Research Assistant'
        assert update_res.json().get('agent', {}).get('enabled') is False
        del_res = client.delete('/api/agents/test_research_agent')
        assert del_res.status_code == 200
        assert del_res.json().get('deleted_id') == 'test_research_agent'
        list_after = client.get('/api/agents')
        agent_ids_after = [a.get('id') for a in list_after.json()]
        assert 'test_research_agent' not in agent_ids_after

    def test_prevent_delete_system_agent(self):
        """Check prevention of system agents deletion."""
        del_res = client.delete('/api/agents/web_search_gemini')
        assert del_res.status_code == 403
        assert 'cannot be deleted' in del_res.json().get('detail', '').lower()

    def test_prevent_duplicate_agent_id(self):
        """Check error on duplicate agent ID creation."""
        dup_agent = {'id': 'web_search_gemini', 'name': 'Duplicate Agent', 'description': '...', 'enabled': True, 'provider': 'gemini', 'model': 'gemini-3.5-flash-lite', 'temperature': 0.2, 'max_steps': 10, 'timeout_seconds': 30, 'tools': [], 'system_prompt': ''}
        res = client.post('/api/agents', json=dup_agent)
        assert res.status_code == 400
        assert 'already exists' in res.json().get('detail', '').lower()

    @patch('src.api.routers.core.router_agents.get_chat_model')
    def test_generate_prompt_ai(self, mock_get_chat_model):
        """Test system prompt generation via AI model."""
        mock_llm = MagicMock()
        mock_llm.ask = AsyncMock(return_value=json.dumps({'name': 'Data Analyst', 'description': 'Analyzes data and performs calculations', 'system_prompt': 'You are a data analyst.', 'recommended_tools': ['python_eval', 'web_search'], 'temperature': 0.4, 'max_steps': 12}))
        mock_get_chat_model.return_value = mock_llm
        req_payload = {'task_description': 'Create an analytics agent for calculations', 'provider': 'gemini', 'model': 'gemini-3.5-flash-lite'}
        response = client.post('/api/agents/generate-prompt', json=req_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        spec = data.get('data', {})
        assert spec.get('name') == 'Data Analyst'
        assert 'python_eval' in spec.get('recommended_tools', [])

    @patch('src.api.routers.core.router_agents.get_chat_model')
    def test_sandbox_execution(self, mock_get_chat_model):
        """Test sandbox execution of test request."""
        mock_llm = MagicMock()
        mock_llm.ask = AsyncMock(return_value='Test agent response in sandbox.')
        mock_get_chat_model.return_value = mock_llm
        test_payload = {'agent_id': 'web_search_gemini', 'test_message': 'What is the weather today?'}
        response = client.post('/api/agents/test', json=test_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        assert 'test' in data.get('response', '').lower()
        assert len(data.get('steps', [])) > 0
        assert data.get('duration_ms') >= 0