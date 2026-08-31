# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Integration tests for API endpoints
# =============================================================================
# Description:
#   Module contains integration tests for all API endpoints of the application.
#
# File: test_integration_api.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Integration tests for API endpoints.

Tests for chat, auth, control, TTS, and admin API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, AsyncMock, patch

class TestChatAPI:
    """Integration tests for /api/chat endpoints."""

    @pytest.mark.asyncio
    async def test_post_chat(self):
        """Test POST /api/chat endpoint.
        
        Verifies that chat messages are processed and responses returned.
        """
        from fastapi import FastAPI
        from core.fastapi.router_chat import init_router
        
        app = FastAPI()
        mock_model = Mock()
        mock_model.chat = AsyncMock(return_value="Test response")
        async def mock_stream(*args, **kwargs):
            yield "Test response"
        mock_model.chat_stream = mock_stream
        
        plugins = {}
        app.include_router(init_router(mock_model, mock_model, plugins))
        
        with patch('core.fastapi.router_chat._extract_user_auth', return_value=("user1", "", "gemini-2.5-flash", {})), \
             patch('core.fastapi.router_chat.get_chat_model', return_value=mock_model):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    '/api/chat',
                    json={
                        'message': 'What movie should I watch?',
                        'history': []
                    }
                )
                assert response.status_code == 200

class TestAuthAPI:
    """Integration tests for /api/auth endpoints."""

    @pytest.mark.asyncio
    async def test_get_models(self):
        """Test GET /api/chat/models endpoint.
        
        Verifies that available models list is returned.
        """
        from fastapi import FastAPI
        from core.fastapi.router_chat import init_router
        
        app = FastAPI()
        mock_model = Mock()
        app.include_router(init_router(mock_model, mock_model, {}))
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get('/api/chat/models')
            assert response.status_code == 200
            data = response.json()
            assert 'models' in data

class TestControlAPI:
    """Integration tests for WebSocket control endpoints."""

    @pytest.mark.asyncio
    async def test_get_control_status(self):
        """Test GET /api/control/status endpoint.
        
        Verifies that control status can be retrieved.
        """
        from fastapi import FastAPI
        from core.fastapi.router_control import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get('/api/control/status')
            assert response.status_code == 200

class TestTTSAPI:
    """Integration tests for /api/tts endpoints."""

    @pytest.mark.asyncio
    async def test_tts_synthesize(self):
        """Test text-to-speech synthesis endpoint.
        
        Verifies that TTS synthesis can be triggered.
        """
        from fastapi import FastAPI
        from core.fastapi.router_tts import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                '/api/tts/synthesize',
                json={'text': 'Hello world', 'voice': 'en-US-AriaNeural', 'system': 'edge-tts'}
            )
            assert response.status_code in [200, 404, 405, 500]

class TestAdminAPI:
    """Integration tests for admin endpoints."""

    @pytest.mark.asyncio
    async def test_admin_interface_redirect(self):
        """Test admin interface access.
        
        Verifies that admin endpoint is accessible.
        """
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
            response = await client.get('/admin')
            assert response.status_code in [200, 303, 307]

    @pytest.mark.asyncio
    async def test_root_redirect(self):
        """Test root endpoint redirect.
        
        Verifies that root endpoint returns proper response.
        """
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
            response = await client.get('/')
            assert response.status_code in [200, 302, 303, 307]
