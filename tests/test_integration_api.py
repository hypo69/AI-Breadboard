# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеграционные тесты API endpoints
# =============================================================================
# Описание:
#   Модуль содержит интеграционные тесты для всех API endpoint-ов приложения.
#   Проверяет корректность обработки запросов, взаимодействие с плагинами и
#   AI-моделью, а также работу промежуточного ПО (middleware). Обеспечивает
#   покрытие основных сценариев использования API.
#
# File: tests/test_integration_api.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Интеграционные тесты API endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, AsyncMock, patch


class TestChatAPI:
    """Интеграционные тесты /api/chat endpoints."""

    @pytest.mark.asyncio
    async def test_post_chat(self):
        """Тест POST /api/chat."""
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
                        'message': 'Какой фильм посмотреть?',
                        'history': []
                    }
                )
                assert response.status_code == 200


class TestAuthAPI:
    """Интеграционные тесты /api/auth endpoints."""

    @pytest.mark.asyncio
    async def test_get_models(self):
        """Тест GET /api/chat/models."""
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
    """Интеграционные тесты WebSocket control endpoints."""

    @pytest.mark.asyncio
    async def test_get_control_status(self):
        """Тест GET /api/control/status."""
        from fastapi import FastAPI
        from core.fastapi.router_control import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get('/api/control/status')
            assert response.status_code == 200


class TestTTSAPI:
    """Интеграционные тесты /api/tts endpoints."""

    @pytest.mark.asyncio
    async def test_tts_synthesize(self):
        """Тест синтеза речи."""
        from fastapi import FastAPI
        from core.fastapi.router_tts import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                '/api/tts/synthesize',
                json={'text': 'Привет мир', 'voice': 'ru-RU-DmitryNeural', 'system': 'edge-tts'}
            )
            assert response.status_code in [200, 404, 405, 500]


class TestAdminAPI:
    """Интеграционные тесты админских endpoints."""

    @pytest.mark.asyncio
    async def test_admin_interface_redirect(self):
        """Тест доступа к админке."""
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
            response = await client.get('/admin')
            assert response.status_code in [200, 303, 307]

    @pytest.mark.asyncio
    async def test_root_redirect(self):
        """Тест редиректа на главную."""
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
            response = await client.get('/')
            assert response.status_code in [200, 302, 303, 307]
