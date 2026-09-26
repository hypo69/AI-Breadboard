# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Набор тестов для эндпоинтов сохранения RAG и ролевой маршрутизации
# =============================================================================
# Description:
#   Тестирует работу эндпоинтов /api/chat/save-for-rag-indexing,
#   /api/chat/save-rag-instant и ролевой маршрутизации целевых RAG баз данных.
#
# File: test_router_chat_save_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.router_chat import init_router as init_chat_router


class TestRouterChatSaveRag(unittest.TestCase):
    """Тестовый набор для валидации эндпоинтов сохранения и целевых RAG баз данных."""

    def setUp(self) -> None:
        """Настройка тестового клиента FastAPI и макетов моделей."""
        self.mock_chat_model = MagicMock()
        self.mock_chat_model.api_key = "fake_key_123"

        self.mock_narrator_model = MagicMock()

        self.app = FastAPI()
        self.app.include_router(init_chat_router(
            chat_model=self.mock_chat_model,
            narrator_model=self.mock_narrator_model,
            plugins={}
        ))
        self.client = TestClient(self.app)

    @patch("src.rag.save_user_approved_response")
    def test_save_for_rag_indexing_explicit_rag_name(self, mock_save: MagicMock) -> None:
        """Проверка работы переименованного эндпоинта /api/chat/save-for-rag-indexing с явным rag_name."""
        mock_save.return_value = True

        payload = {
            "query": "Как настроить GPU в Windows?",
            "chat_text": "Откройте диспетчер устройств...",
            "voice_text": "Откройте диспетчер устройств...",
            "rag_name": "technician"
        }

        response = self.client.post("/api/chat/save-for-rag-indexing", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("rag_name"), "technician")
        mock_save.assert_called_once_with("1", payload["query"], payload["chat_text"], payload["voice_text"], "technician")

    @patch("src.rag.save_user_approved_response")
    def test_save_for_rag_indexing_with_role(self, mock_save: MagicMock) -> None:
        """Проверка работы эндпоинта /api/chat/save-for-rag-indexing и определения RAG по роли."""
        mock_save.return_value = True

        payload = {
            "query": "Составь расписание встреч",
            "chat_text": "Расписание на сегодня...",
            "voice_text": "",
            "role": "secretary"
        }

        response = self.client.post("/api/chat/save-for-rag-indexing", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("rag_name"), "secretary")
        mock_save.assert_called_once_with("1", payload["query"], payload["chat_text"], payload["voice_text"], "secretary")

    @patch("src.rag.index_user_interaction")
    @patch("src.rag.save_user_approved_response")
    def test_save_rag_instant_endpoint(self, mock_save: MagicMock, mock_index: MagicMock) -> None:
        """Проверка мгновенного сохранения /api/chat/save-rag-instant с векторизацией в целевую RAG базу."""
        mock_save.return_value = True
        mock_index.return_value = True

        payload = {
            "query": "Напиши скрипт на Python",
            "chat_text": "def hello(): print('world')",
            "voice_text": "",
            "rag_name": "coder"
        }

        response = self.client.post("/api/chat/save-rag-instant", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("rag_name"), "coder")
        mock_save.assert_called_once_with("1", payload["query"], payload["chat_text"], payload["voice_text"], "coder")
        mock_index.assert_called_once_with("1", "fake_key_123", payload["query"], payload["chat_text"], "coder")

    @patch("src.rag.save_user_approved_response")
    def test_save_rag_default_fallback(self, mock_save: MagicMock) -> None:
        """Проверка fallback значений по умолчанию (default), если rag_name и role не переданы."""
        mock_save.return_value = True

        payload = {
            "query": "Простой запрос",
            "chat_text": "Простой ответ",
            "voice_text": ""
        }

        response = self.client.post("/api/chat/save-for-rag-indexing", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("rag_name"), "default")
        mock_save.assert_called_once_with("1", payload["query"], payload["chat_text"], payload["voice_text"], "default")


if __name__ == "__main__":
    unittest.main()
