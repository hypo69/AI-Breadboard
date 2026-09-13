# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for core/fastapi module
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
        from src.api.router_auth import TokenData, create_jwt_token
        
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
        from src.api.router_auth import TokenData, create_jwt_token, verify_jwt_token
        
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
        from src.api.router_auth import verify_jwt_token
        
        result = verify_jwt_token("invalid_token")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_settings_search_engine(self):
        """Тест получения настроек пользователя с актуальным search_engine."""
        from src.api.router_auth import get_settings, TokenData, create_jwt_token
        from fastapi import Request

        token_data = TokenData(email="test@example.com", name="Test User", id=1)
        token = create_jwt_token(token_data)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {"auth_token": token}

        with patch("src.user_manager.user_manager.get_user_by_email", return_value={"id": 1, "email": "test@example.com"}):
            with patch("src.user_manager.user_manager.get_user_settings", return_value={"user_id": 1, "theme": "dark", "model": "gemini-2.5-flash"}):
                res = await get_settings(mock_request)
                assert "search_engine" in res
                assert res["search_engine"] in ["gemini_cli", "gemini", "agy", "langchain", "playwright"]

class TestRouterChat:
    """Тесты router_chat.py."""

    def test_init_router(self, app_client):
        """Тест инициализации чат-роутера."""
        from src.api.router_chat import init_router
        
        mock_model = Mock()
        mock_model.chat = AsyncMock()
        mock_model.chat_stream = AsyncMock()
        
        plugins = {}
        
        router = init_router(mock_model, mock_model, plugins)
        
        assert router is not None

    @pytest.mark.asyncio
    async def test_get_models_logging(self):
        """Тест получения списка моделей."""
        from src.api.router_chat import init_router
        
        mock_model = Mock()
        router = init_router(mock_model, mock_model, {})
        
        get_models_func = None
        for route in router.routes:
            if route.path in ('/models', '/api/chat/models'):
                get_models_func = route.endpoint
                break
        
        assert get_models_func is not None
        res = await get_models_func(fastapi_req=None)
        assert 'models' in res
        assert 'gemini' in res['models']
        assert 'agy' in res['models']

    @pytest.mark.asyncio
    async def test_chat_stream_excludes_search_engine_for_model(self):
        """Тест checks, что search_engine из generation_config не попадает в chat_stream модели."""
        from src.api.router_chat import init_router, ChatRequest
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

        with patch('src.api.router_chat._extract_user_auth', return_value=("user1", "", "gemini-2.5-flash", {})), \
             patch('src.api.router_chat.get_chat_model', return_value=mock_model):
            resp = await chat_endpoint(chat_req=req, request=mock_fastapi_req)
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
        from src.api.router_tts import init_router
        
        router = init_router(prefix='/api/tts')
        
        assert router is not None
        assert router.prefix == '/api/tts'

class TestRouterControl:
    """Тесты router_control.py."""

    def test_connection_manager(self):
        """Тест ConnectionManager."""
        from src.api.router_control import ControlConnectionManager
        
        # Экземпляр менеджера подключений
        manager = ControlConnectionManager()
        
        # Проверка создания экземпляра и начального состояния комнат
        assert manager is not None
        assert len(manager.rooms) == 0

    def test_remote_mic_interface_rendering(self):
        """Happy path: рендеринг страницы голосового пульта /mic."""
        from src.app import create_app, register_pages
        from fastapi.testclient import TestClient
        
        app = create_app()
        register_pages(app)
        client = TestClient(app)
        resp = client.get('/mic')
        
        # Проверка статус-кода ответа
        assert resp.status_code == 200
        # Проверка наличия ключевых элементов интерфейса в ответе
        decoded_body = resp.text
        assert "Голосовой Пульт" in decoded_body
        assert "btn-mic-giant" in decoded_body
        assert "btn-upload-audio" in decoded_body
        assert "btn-upload-media" in decoded_body
        assert "audio-file-input" in decoded_body
        assert "media-file-input" in decoded_body

    def test_root_page_serves_html(self):
        """Happy path: корневой маршрут / отдает HTML страницу."""
        from src.app import create_app, register_pages
        from fastapi.testclient import TestClient

        app = create_app()
        register_pages(app)
        client = TestClient(app)
        resp = client.get('/')
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_remote_mic_static_success(self):
        """Happy path: отдача статического файла голосового пульта."""
        from src.app import create_app, register_pages
        from fastapi.testclient import TestClient

        app = create_app()
        register_pages(app)
        client = TestClient(app)
        static_resp = client.get('/remote_mic/index.html')
        
        # Проверка корректности возвращенного контента
        assert static_resp.status_code == 200
        assert len(static_resp.text) > 0

    def test_remote_mic_static_not_found_raises_http_404(self):
        """Error scenario: вызов HTTPException(404) при запросе несуществующего статического ресурса."""
        from src.app import create_app, register_pages
        from fastapi.testclient import TestClient

        app = create_app()
        register_pages(app)
        client = TestClient(app)
        resp = client.get('/remote_mic/non_existent_file.xyz')
        assert resp.status_code == 404


class TestCorsConfig:
    """Tests for CORS configuration loading from config.json."""

    def test_build_cors_config(self):
        """Test building CORS configuration from server config."""
        from src.app.cors import build_cors_config
        from types import SimpleNamespace
        
        server_cfg = SimpleNamespace(
            cors=SimpleNamespace(
                allow_origins=[],
                allow_origin_regex=None,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            ),
            client_url="",
            user_domain="",
            cors_origins=[]
        )
        
        cors_config = build_cors_config(server_cfg)
        assert "allow_origins" in cors_config
        assert "allow_origin_regex" in cors_config
        assert "allow_credentials" in cors_config
        assert "allow_methods" in cors_config
        assert "allow_headers" in cors_config
        assert "http://localhost" in cors_config["allow_origins"]
        assert cors_config["allow_credentials"] is True



