# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тесты модуля core/fastapi
# =============================================================================
# Description:
#   Module содержит тесты для модуля FastAPI API сервера. Checks создание
#
# File: test_fastapi.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Тесты модуля core/fastapi
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

@pytest.fixture
def app_client():
    """Создание FastAPI тестового клиента."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    
    return app

class TestRouterAuth:
    """Тесты router_auth.py."""

    def test_create_jwt_token(self):
        """Тест создания JWT токена."""
        from core.fastapi.router_auth import TokenData, create_jwt_token
        
        token_data = TokenData(
            email="test@example.com",
            name="Test User",
            id=1
        )
        
        token = create_jwt_token(token_data)
        
        assert token is not None
        assert len(token) > 0

    def test_verify_jwt_token(self):
        """Тест верификации JWT токена."""
        from core.fastapi.router_auth import TokenData, create_jwt_token, verify_jwt_token
        
        token_data = TokenData(
            email="test@example.com",
            name="Test User",
            id=1
        )
        
        token = create_jwt_token(token_data)
        verified = verify_jwt_token(token)
        
        assert verified is not None
        assert verified.email == "test@example.com"

    def test_verify_jwt_token_invalid(self):
        """Тест верификации невалидного токена."""
        from core.fastapi.router_auth import verify_jwt_token
        
        result = verify_jwt_token("invalid_token")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_settings_search_engine(self):
        """Тест получения настроек пользователя с актуальным search_engine."""
        from core.fastapi.router_auth import get_settings, TokenData, create_jwt_token
        from fastapi import Request

        token_data = TokenData(email="test@example.com", name="Test User", id=1)
        token = create_jwt_token(token_data)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {"auth_token": token}

        with patch("core.user_manager.user_manager.get_user_by_email", return_value={"id": 1, "email": "test@example.com"}):
            with patch("core.user_manager.user_manager.get_user_settings", return_value={"user_id": 1, "theme": "dark", "model": "gemini-2.5-flash"}):
                res = await get_settings(mock_request)
                assert "search_engine" in res
                assert res["search_engine"] in ["gemini_cli", "gemini", "agy", "langchain", "playwright"]

class TestRouterChat:
    """Тесты router_chat.py."""

    def test_init_router(self, app_client):
        """Тест инициализации чат-роутера."""
        from core.fastapi.router_chat import init_router
        
        mock_model = Mock()
        mock_model.chat = AsyncMock()
        mock_model.chat_stream = AsyncMock()
        
        plugins = {}
        
        router = init_router(mock_model, mock_model, plugins)
        
        assert router is not None

    @pytest.mark.asyncio
    async def test_get_models_logging(self):
        """Тест получения списка моделей."""
        from core.fastapi.router_chat import init_router
        
        mock_model = Mock()
        router = init_router(mock_model, mock_model, {})
        
        get_models_func = None
        for route in router.routes:
            if route.path in ('/models', '/api/chat/models'):
                get_models_func = route.endpoint
                break
        
        assert get_models_func is not None
        res = await get_models_func()
        assert 'models' in res
        assert 'gemini' in res['models']
        assert 'agy' in res['models']

    @pytest.mark.asyncio
    async def test_chat_stream_excludes_search_engine_for_model(self):
        """Тест checks, что search_engine из generation_config не попадает в chat_stream модели."""
        from core.fastapi.router_chat import init_router, ChatRequest
        from fastapi import Request

        called_kwargs = {}

        async def mock_stream(q, **kwargs):
            called_kwargs.update(kwargs)
            yield "Ответ"

        mock_model = Mock()
        mock_model.chat_stream = mock_stream

        router = init_router(mock_model, mock_model, {})
        chat_endpoint = next(r.endpoint for r in router.routes if r.path in ('', '/', '/api/chat'))

        req = ChatRequest(
            message="привет",
            history=[],
            generation_config={"search_engine": "gemini_cli", "model": "gemini-2.5-flash"}
        )

        mock_fastapi_req = Mock(spec=Request)
        mock_fastapi_req.cookies = {}
        mock_fastapi_req.client = Mock(host="127.0.0.1")

        with patch('core.fastapi.router_chat._extract_user_auth', return_value=("user1", "", "gemini-2.5-flash", {})), \
             patch('core.fastapi.router_chat.get_chat_model', return_value=mock_model):
            resp = await chat_endpoint(request=req, fastapi_req=mock_fastapi_req)
            # Читаем стриминг-генератор
            chunks = []
            async for chunk in resp.body_iterator:
                chunks.append(chunk)

        assert "search_engine" not in called_kwargs, "Параметр search_engine не должен передаваться в chat_stream модели"
        assert len(chunks) > 0

class TestRouterTTS:
    """Тесты router_tts.py."""

    def test_init_router(self):
        """Тест инициализации tts-роутера."""
        from core.fastapi.router_tts import init_router
        
        router = init_router(prefix='/api/tts')
        
        assert router is not None
        assert router.prefix == '/api/tts'

class TestRouterControl:
    """Тесты router_control.py."""

    def test_connection_manager(self):
        """Тест ConnectionManager."""
        from core.fastapi.router_control import ControlConnectionManager
        
        manager = ControlConnectionManager()
        
        assert manager is not None
        assert len(manager.rooms) == 0
