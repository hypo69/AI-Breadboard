# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Fastapi Router Keys
# =============================================================================
# Description:
#   Тесты для роутера API ключей (src/api/routers/core/router_keys.py).
#
# Usage Examples:
#   Python API:
#     from tests.test_fastapi_router_keys import TestRouterKeysHelpers
#
#     service = TestRouterKeysHelpers()
#
# File: test_fastapi_router_keys.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 11:07:00
# =============================================================================

"""Тесты для роутера API ключей и вспомогательных функций."""

from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from src.api.routers.core.router_keys import (
    KeyCreateRequest,
    KeyEntry,
    KeyUpdateRequest,
    KeyTestPayload,
    _mask_key,
    init_router,
)

class TestRouterKeysHelpers:
    """Тесты для вспомогательных функций router_keys."""

    def test_mask_key_short(self):
        """Тест маскирования короткого ключа."""
        result = _mask_key("short")
        assert result == "*hort"

    def test_mask_key_long(self):
        """Тест маскирования длинного API-ключа."""
        api_key = "AIzaSyDaGmWKaJsXk_hKl_pQrBwV8MiFa"
        result = _mask_key(api_key)
        assert result.endswith("MiFa")
        assert result.startswith("****************************")
        assert len(result) == len(api_key)


class TestRouterKeysEndpoints:
    """Тесты эндпоинтов API."""

    def test_list_keys_empty(self):
        """Тест получения списка ключей когда хранилище пусто."""
        with patch("src.api.routers.core.router_keys._load_keys_from_file", return_value=[]):
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            response = client.get("/api/keys/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_key_create_request_model(self):
        """Тест модели KeyCreateRequest."""
        request = KeyCreateRequest(name="test", role="admin")
        assert request.name == "test"
        assert request.role == "admin"

    def test_key_update_request_model(self):
        """Тест модели KeyUpdateRequest."""
        request = KeyUpdateRequest(role="user")
        assert request.role == "user"
        assert request.name is None

    def test_key_entry_model(self):
        """Тест модели KeyEntry."""
        entry = KeyEntry(id="k1", name="k1", role="admin", masked_key="***1234")
        assert entry.id == "k1"
        assert entry.masked_key == "***1234"
        assert entry.status == "active"
        assert entry.exhausted is False

    def test_key_test_payload_model(self):
        """Тест модели KeyTestPayload."""
        payload = KeyTestPayload()
        assert payload.model == "gemini-3.1-flash-lite"
        assert payload.message == "hello world"


class TestRouterKeysLogic:
    """Тесты бизнес-логики и тестирования ключей."""

    def test_test_key_endpoint_success(self):
        """Тест успешной проверки ключа через эндпоинт POST /api/keys/{name}/test."""
        with patch("src.ai.gemini.gemini_api_key_state._load_keys_file") as mock_load, \
             patch("src.ai.gemini.gemini_api_key_state.update_last_run"), \
             patch("src.ai.gemini.gemini_api_key_state.reset_quota"), \
             patch("google.genai.Client") as mock_genai_cls:
            
            mock_load.return_value = {"GEMINI_API_KEY": {"value": "valid_key_123", "status": "active"}}
            mock_instance = MagicMock()
            mock_resp = MagicMock()
            mock_resp.text = "hello back from gemini"
            mock_instance.models.generate_content.return_value = mock_resp
            mock_genai_cls.return_value = mock_instance

            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post("/api/keys/GEMINI_API_KEY/test", json={"message": "hello", "model": "gemini-3.1-flash-lite"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["valid"] is True
            assert data["response"] == "hello back from gemini"
            assert "duration_ms" in data

    def test_test_key_endpoint_error_handling(self):
        """Тест обработки ошибки проверки ключа."""
        with patch("src.ai.gemini.gemini_api_key_state._load_keys_file") as mock_load, \
             patch("src.ai.gemini.gemini_api_key_state.mark_exhausted") as mock_mark, \
             patch("google.genai.Client") as mock_genai_cls:
            
            mock_load.return_value = {"EXHAUSTED_KEY": {"value": "invalid_key_456", "status": "active"}}
            mock_instance = MagicMock()
            mock_instance.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
            mock_genai_cls.return_value = mock_instance

            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post("/api/keys/EXHAUSTED_KEY/test", json={"message": "hello"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert data["valid"] is False
            assert "RESOURCE_EXHAUSTED" in data["error"]
            mock_mark.assert_called_once_with("EXHAUSTED_KEY")

    def test_test_key_endpoint_not_found(self):
        """Тест запроса проверки для несуществующего ключа."""
        with patch("src.ai.gemini.gemini_api_key_state.load_api_keys", return_value=({}, [])), \
             patch("src.ai.gemini.gemini_api_key_state._load_keys_file", return_value={}):
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post("/api/keys/NON_EXISTENT_KEY/test", json={"message": "hello"})
            assert response.status_code == 404

    def test_activate_key_endpoint(self):
        """Тест эндпоинта назначения ключа активным."""
        with patch("src.ai.gemini.gemini_api_key_state.set_active_key", return_value=True) as mock_set_active:
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post("/api/keys/MY_KEY/activate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["active_key"] == "MY_KEY"
            mock_set_active.assert_called_once_with("MY_KEY")

    def test_toggle_key_status_success(self):
        """Тест переключения статуса ключа (active -> disabled)."""
        fake_keys = {
            "aistros.com@gmail.com": {
                "value": "AIzaSyTest123",
                "status": "active",
                "last_run": "",
                "exhausted_at": ""
            }
        }
        with patch("src.ai.gemini.gemini_api_key_state._load_keys_file", return_value=fake_keys), \
             patch("src.ai.gemini.gemini_api_key_state._save_keys_file", return_value=True) as mock_save, \
             patch("src.ai.gemini.gemini_api_key_state._sync_environment"):
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.patch("/api/keys/aistros.com@gmail.com", json={"status": "disabled"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "disabled" in data["message"]
            assert fake_keys["aistros.com@gmail.com"]["status"] == "disabled"
            mock_save.assert_called_once()

    def test_toggle_key_status_not_found(self):
        """Тест переключения статуса несуществующего ключа."""
        with patch("src.ai.gemini.gemini_api_key_state._load_keys_file", return_value={}):
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.patch("/api/keys/unknown_key@gmail.com", json={"status": "disabled"})
            assert response.status_code == 404
            assert "не найден" in response.json()["detail"]