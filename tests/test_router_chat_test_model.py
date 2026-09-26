# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test suite for test model verification endpoint
# =============================================================================
# Description:
#   Comprehensive testing of /api/chat/test-model and /api/chat/models endpoints.
#
# File: test_router_chat_test_model.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.router_chat import TestModelRequest, init_router

class TestRouterChatTestModel(unittest.TestCase):
    """Test suite for model verification request endpoint /api/chat/test-model."""

    def setUp(self) -> None:
        """Setup FastAPI test application and client before each test."""
        # Creation of chat and narrator model stubs
        self.mock_chat_model: MagicMock = MagicMock()
        self.mock_chat_model.api_key = "fake_key_123"
        self.mock_narrator_model: MagicMock = MagicMock()
        self.mock_plugins: dict = {}

        # Initialize chat router with dependency injection
        self.router = init_router(
            chat_model=self.mock_chat_model,
            narrator_model=self.mock_narrator_model,
            plugins=self.mock_plugins,
        )

        # Create isolated FastAPI application for testing
        self.app: FastAPI = FastAPI()
        self.app.state.chat_model = self.mock_chat_model
        self.app.include_router(self.router)
        self.client: TestClient = TestClient(self.app)

    # =========================================================================
    # 1. Happy Path Scenarios
    # =========================================================================

    @patch("src.api.router_chat.get_chat_model")
    def test_test_model_gemini_happy_path(self, mock_get_chat_model: MagicMock) -> None:
        """Test successful verification request to Gemini model.

        Check: endpoint returns success status, model response and execution time.
        """
        # --- Setup input data (Arrange) ---
        # Initialize mock AI model with ask method
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Test connection successful. I am Gemini model.")
        mock_get_chat_model.return_value = mock_instance

        # Prepare request payload
        payload: dict[str, str] = {
            "model": "gemini-3.7-flash",
            "provider": "gemini",
            "message": "Hello! Tell me your model name.",
            "system_instruction": "You are a tester."
        }

        # --- Execution (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check results (Assert) ---
        self.assertEqual(response.status_code, 200, "Response code should be 200 OK")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Response status should be success")
        self.assertEqual(data.get("model", ""), "gemini-3.7-flash", "Model name should match request")
        self.assertEqual(data.get("provider", ""), "gemini", "Provider name should match request")

    @patch("src.api.router_chat.get_chat_model")
    def test_test_model_default_fallback_when_empty_model_and_provider(self, mock_get_chat_model: MagicMock) -> None:
        """Test verification request with empty model and provider falling back to default settings."""
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Default model ready.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "",
            "provider": "",
            "message": "Тест настроек по умолчанию.",
        }

        response = self.client.post("/api/chat/test-model", json=payload)
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("model"))
        self.assertTrue(data.get("provider"))

    @patch("src.api.router_chat.get_chat_model")
    def test_test_model_default_fallback_when_only_provider_specified(self, mock_get_chat_model: MagicMock) -> None:
        """Test verification request with provider specified but empty model falling back to provider default."""
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Ollama model ready.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "",
            "provider": "ollama",
            "message": "Тест ollama по умолчанию.",
        }

        response = self.client.post("/api/chat/test-model", json=payload)
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("provider"), "ollama")
        self.assertIn("ollama:", data.get("model", ""))

    def test_get_model_instruction(self) -> None:
        """Test GET /api/chat/model-instruction returns active system instruction."""
        response = self.client.get("/api/chat/model-instruction")
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("instruction", data)
        self.assertIn("system_instruction", data)
        self.assertIn("provider", data)

    def test_set_model_instruction(self) -> None:
        """Test POST /api/chat/model-instruction updates active system instruction."""
        new_instruction = "Вы — тестовый AI-ассистент для юнит-тестов."
        response = self.client.post("/api/chat/model-instruction", json={
            "instruction": new_instruction,
            "save_to_disk": False,
        })
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("instruction"), new_instruction)
        self.mock_chat_model.update_system_instruction.assert_called_with(new_instruction)

    def test_set_model_instruction_empty_error(self) -> None:
        """Test POST /api/chat/model-instruction with empty instruction returns 400."""
        response = self.client.post("/api/chat/model-instruction", json={
            "instruction": "",
        })
        self.assertEqual(response.status_code, 400)

    def test_get_active_model_endpoint(self) -> None:
        """Test GET /api/chat/active-model returns active model info."""
        response = self.client.get("/api/chat/active-model")
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("model"))
        self.assertTrue(data.get("provider"))

    def test_set_active_model_endpoint(self) -> None:
        """Test POST /api/chat/set-active-model updates active model."""
        response = self.client.post("/api/chat/set-active-model", json={
            "model": "llama3.1",
            "provider": "ollama",
        })
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("model"), "ollama:llama3.1")
        self.assertEqual(data.get("provider"), "OLLAMA")

    def test_get_provider_endpoint(self) -> None:
        """Test GET /api/chat/provider returns active provider."""
        response = self.client.get("/api/chat/provider")
        self.assertEqual(response.status_code, 200)
        data: dict = response.json()
        self.assertEqual(data.get("status"), "success")
    def test_get_chat_model_ollama_fallback_simple_namespace(self) -> None:
        """Тестирование функции get_chat_model для Ollama при использовании SimpleNamespace без атрибута ollama_base_url."""
        from types import SimpleNamespace
        from src.api.router_chat import get_chat_model

        fake_ai_cfg = SimpleNamespace()  # без атрибута ollama_base_url
        with patch("src.api.router_chat.ai_cfg", fake_ai_cfg):
            model_inst = get_chat_model("ollama:llama3.1")
            self.assertIsNotNone(model_inst)
            self.assertEqual(getattr(model_inst, "_api_url", None), "http://localhost:11434")




