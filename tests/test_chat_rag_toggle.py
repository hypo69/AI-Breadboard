# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test suite for Chat RAG toggle and user configuration persistence
# =============================================================================
# Description:
#   Validates user settings storage for rag_enabled, /auth/settings endpoints,
#   and conditional execution of RAG in /api/chat.
#
# File: test_chat_rag_toggle.py
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

from src.user_manager import user_manager
from src.fastapi.router_auth import init_router as init_auth_router
from src.fastapi.router_chat import init_router as init_chat_router
from src.rag.models import RAGRouteDecision, RAGDecisionType

class TestChatRagToggle(unittest.TestCase):
    """Test suite for RAG toggle persistence and chat integration."""

    def setUp(self) -> None:
        """Set up test clients and routers."""
        self.mock_chat_model = MagicMock()
        self.mock_chat_model.api_key = "fake_key_123"
        
        async def dummy_chat_stream(prompt, **kwargs):
            yield "Test response from AI."

        self.mock_chat_model.chat_stream = dummy_chat_stream

        self.mock_narrator_model = MagicMock()
        self.mock_narrator_model.chat_stream = dummy_chat_stream

        self.app = FastAPI()
        self.app.include_router(init_auth_router())
        self.app.include_router(init_chat_router(
            chat_model=self.mock_chat_model,
            narrator_model=self.mock_narrator_model,
            plugins={}
        ))
        self.client = TestClient(self.app)

    def test_user_manager_rag_setting_persistence(self) -> None:
        """Test that user_manager updates and retrieves rag_enabled properly."""
        # 1. Update rag_enabled to 0
        success = user_manager.update_user_settings(1, rag_enabled=0)
        self.assertTrue(success, "Updating rag_enabled to 0 should succeed")

        settings = user_manager.get_user_settings(1)
        self.assertEqual(settings.get("rag_enabled"), 0, "rag_enabled should be 0")

        # 2. Update rag_enabled to 1
        success = user_manager.update_user_settings(1, rag_enabled=1)
        self.assertTrue(success, "Updating rag_enabled to 1 should succeed")

        settings = user_manager.get_user_settings(1)
        self.assertEqual(settings.get("rag_enabled"), 1, "rag_enabled should be 1")

    @patch("src.rag.get_rag_engine")
    def test_chat_with_rag_disabled(self, mock_get_rag_engine: MagicMock) -> None:
        """Test that /api/chat skips RAG evaluation when rag_enabled is False in generation_config."""
        mock_engine = MagicMock()
        mock_get_rag_engine.return_value = mock_engine

        payload = {
            "message": "Привет! Какая погода?",
            "history": [],
            "generation_config": {
                "rag_enabled": False
            }
        }

        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)

        # RAG engine evaluate should NOT have been called
        mock_engine.evaluate.assert_not_called()

    @patch("src.rag.get_rag_engine")
    def test_chat_with_rag_enabled(self, mock_get_rag_engine: MagicMock) -> None:
        """Test that /api/chat executes RAG evaluation when rag_enabled is True in generation_config."""
        mock_engine = MagicMock()
        mock_engine.evaluate = AsyncMock(return_value=RAGRouteDecision(
            decision_type=RAGDecisionType.LLM_FALLBACK,
            is_direct=False,
            context_text="[Контекст из базы знаний]: тестовый контекст",
            confidence_score=0.5
        ))
        mock_get_rag_engine.return_value = mock_engine

        payload = {
            "message": "Привет! Какая погода?",
            "history": [],
            "generation_config": {
                "rag_enabled": True
            }
        }

        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)

        # RAG engine evaluate should have been called
        mock_engine.evaluate.assert_called_once()
