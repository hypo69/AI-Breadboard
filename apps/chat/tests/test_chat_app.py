# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Chat Application Unit Tests
# =============================================================================
# Description:
#   Тесты для движка и REST API роутера приложения apps/chat.
#
# File: test_chat_app.py
# Package: apps.chat.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.chat.engine import ChatEngine
from apps.chat.router import init_router


class TestChatApp(unittest.TestCase):
    """Набор тестов для приложения AI Chat."""

    def setUp(self) -> None:
        """Инициализация тестового окружения."""
        self.engine = ChatEngine()
        self.app = FastAPI()
        self.app.include_router(init_router())
        self.client = TestClient(self.app)

    def test_engine_status(self) -> None:
        """Проверка получения статуса чата через движок."""
        status = self.engine.get_status()
        self.assertEqual(status.get("status"), "ready")
        self.assertIn("provider", status)
        self.assertIn("sessions_count", status)

    def test_engine_config(self) -> None:
        """Проверка получения конфигурации через движок."""
        cfg = self.engine.get_config()
        self.assertIn("app_name", cfg)
        self.assertIn("chat", cfg)

    def test_router_status_endpoint(self) -> None:
        """Проверка REST эндпоинта /api/v1/apps/chat/status."""
        response = self.client.get("/api/v1/apps/chat/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ready")

    def test_router_config_endpoint(self) -> None:
        """Проверка REST эндпоинта /api/v1/apps/chat/config."""
        response = self.client.get("/api/v1/apps/chat/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("app_name", data)

    def test_router_sessions_crud(self) -> None:
        """Проверка CRUD операций с сессиями через REST эндпоинты."""
        test_session_id = "test-session-unit-123"
        payload = {
            "id": test_session_id,
            "title": "Тестовый диалог",
            "messages": [{"role": "user", "content": "Привет"}],
            "chatHistory": [],
        }

        # 1. Save session
        save_resp = self.client.post("/api/v1/apps/chat/sessions", json=payload)
        self.assertEqual(save_resp.status_code, 200)
        self.assertEqual(save_resp.json().get("status"), "ok")

        # 2. Get session
        get_resp = self.client.get(f"/api/v1/apps/chat/sessions/{test_session_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json().get("id"), test_session_id)

        # 3. List sessions
        list_resp = self.client.get("/api/v1/apps/chat/sessions")
        self.assertEqual(list_resp.status_code, 200)
        session_ids = [s.get("id") for s in list_resp.json()]
        self.assertIn(test_session_id, session_ids)

        # 4. Delete session
        del_resp = self.client.delete(f"/api/v1/apps/chat/sessions/{test_session_id}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json().get("status"), "ok")


if __name__ == "__main__":
    unittest.main()
