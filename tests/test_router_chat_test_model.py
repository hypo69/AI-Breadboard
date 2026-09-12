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

from src.fastapi.router_chat import TestModelRequest, init_router

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
        self.app.include_router(self.router)
        self.client: TestClient = TestClient(self.app)

    # =========================================================================
    # 1. Happy Path Scenarios
    # =========================================================================

    @patch("src.fastapi.router_chat.get_chat_model")
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
