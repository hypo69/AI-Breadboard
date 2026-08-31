# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Набор тестов для эндпоинта проверочного запроса к 
# =============================================================================
# Description:
#   Исчерпывающее тестирование эндпоинтов /api/chat/test-model и /api/chat/models.
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

from core.fastapi.router_chat import TestModelRequest, init_router

class TestRouterChatTestModel(unittest.TestCase):
    """Набор тестов для эндпоинта проверочного запроса к моделям /api/chat/test-model."""

    def setUp(self) -> None:
        """Подготовка тестового приложения FastAPI и клиента перед каждым тестом."""
        # Создание заглушек моделей чата и диктора
        self.mock_chat_model: MagicMock = MagicMock()
        self.mock_chat_model.api_key = "fake_key_123"
        self.mock_narrator_model: MagicMock = MagicMock()
        self.mock_plugins: dict = {}

        # Initialization роутера чата с внедрением зависимостей
        self.router = init_router(
            chat_model=self.mock_chat_model,
            narrator_model=self.mock_narrator_model,
            plugins=self.mock_plugins,
        )

        # Создание изолированного приложения FastAPI для тестирования
        self.app: FastAPI = FastAPI()
        self.app.include_router(self.router)
        self.client: TestClient = TestClient(self.app)

    # =========================================================================
    # 1. Happy Path Scenarios
    # =========================================================================

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_gemini_happy_path(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование успешного выполнения проверочного запроса к модели Gemini.

        Check: эндпоинт Returns status success, ответ модели и время выполнения.
        """
        # --- Подготовка входных данных (Arrange) ---
        # Initialization мока модели ИИ с методом ask
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Тест связи успешен. Я модель Gemini.")
        mock_get_chat_model.return_value = mock_instance

        # Подготовка полезной нагрузки запроса
        payload: dict[str, str] = {
            "model": "gemini-3.7-flash",
            "provider": "gemini",
            "message": "Привет! Назови свою модель.",
            "system_instruction": "You are a tester."
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Код ответа должен быть 200 OK")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Status ответа должен быть success")
        self.assertEqual(data.get("model", ""), "gemini-3.7-flash", "Имя модели должно соответствовать запросу")
        self.assertEqual(data.get("provider", ""), "gemini", "Имя провайдера должно соответствовать запросу")
        self.assertIn("Тест связи успешен", data.get("response", ""), "Ответ должен содержать текст генерации")
        self.assertGreaterEqual(data.get("duration_ms", 0.0), 0.0, "Время выполнения должно быть неотрицательным")

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_foundry_chat_method_happy_path(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование успешного проверочного запроса через method chat (Foundry/Ollama).

        Check: если модель поддерживает только method chat, запрос выполняется successfully.
        """
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock(spec=["chat"])
        mock_instance.chat = AsyncMock(return_value="Foundry local model response OK.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "qwen2.5-1.5b-instruct-generic-cpu:4",
            "provider": "foundry",
            "message": "Check Foundry",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Код ответа должен быть 200 OK")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Status ответа должен быть success")
        self.assertEqual(data.get("model", ""), "foundry:qwen2.5-1.5b-instruct-generic-cpu:4", "Префикс foundry должен быть добавлен")
        self.assertEqual(data.get("response", ""), "Foundry local model response OK.", "Ответ должен совпадать")

    # =========================================================================
    # 2. Edge Cases Scenarios
    # =========================================================================

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_empty_message_uses_default_prompt(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование отправки запроса с пустым сообщением.

        Check: при empty строке сообщения используется стандартный проверочный текст.
        """
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Стандартный ответ получен.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "gemini-3.7-flash",
            "provider": "gemini",
            "message": "   ",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Код ответа должен быть 200 OK")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Запрос должен завершиться successfully")
        # Check, что в ask был передан дефолтный текст
        mock_instance.ask.assert_called_once()
        called_arg = mock_instance.ask.call_args[0][0]
        self.assertIn("Назови свою модель", called_arg, "Дефолтный промпт должен содержать проверочный вопрос")

    def test_test_model_empty_model_returns_error(self) -> None:
        """Тестирование передачи запроса с empty моделью.

        Check: Returnsся status error с сообщением об отсутствии модели.
        """
        # --- Подготовка входных данных (Arrange) ---
        payload: dict[str, str] = {
            "model": "",
            "provider": "gemini",
            "message": "Привет",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Код ответа 200")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "error", "Status должен быть error")
        self.assertIn("не указано", data.get("message", ""), "Сообщение об ошибке должно указывать на отсутствие модели")

    # =========================================================================
    # 3. Type Variants & Provider Prefixes
    # =========================================================================

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_ollama_prefix_injection(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование автоматического добавления префикса ollama: к модели."""
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Ollama is alive.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "llama3.1",
            "provider": "ollama",
            "message": "Status ping",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Status должен быть success")
        self.assertEqual(data.get("model", ""), "ollama:llama3.1", "Префикс ollama: должен быть добавлен к имени модели")

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_agy_prefix_injection(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование автоматического добавления префикса agy- к модели."""
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="AGY Agent operational.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "gemini-3.7-flash",
            "provider": "agy",
            "message": "Ping",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Status должен быть success")
        self.assertEqual(data.get("model", ""), "agy-gemini-3.7-flash", "Префикс agy- должен быть добавлен к имени модели")

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_gemini_cli_prefix_injection(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование автоматического добавления префикса gemini_cli: к модели."""
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Gemini CLI OK.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "gemini-3.1-flash-lite",
            "provider": "gemini_cli",
            "message": "Ping CLI",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "success", "Status должен быть success")
        self.assertEqual(data.get("model", ""), "gemini_cli:gemini-3.1-flash-lite", "Префикс gemini_cli: должен быть добавлен")

    # =========================================================================
    # 4. Boundary Values
    # =========================================================================

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_already_prefixed_model_name(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование передачи модели, уже содержащей префикс провайдера."""
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(return_value="Response OK.")
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "foundry:custom-model-id",
            "provider": "foundry",
            "message": "Ping",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        data: dict = response.json()
        self.assertEqual(data.get("model", ""), "foundry:custom-model-id", "Префикс не должен дублироваться")

    # =========================================================================
    # 5. Error Scenarios
    # =========================================================================

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_test_model_exception_handling(self, mock_get_chat_model: MagicMock) -> None:
        """Тестирование перехвата исключения при сбое обращения к модели."""
        # --- Подготовка входных данных (Arrange) ---
        mock_instance: MagicMock = MagicMock()
        mock_instance.ask = AsyncMock(side_effect=ConnectionRefusedError("Сервер Ollama недоступен на порту 11434"))
        mock_get_chat_model.return_value = mock_instance

        payload: dict[str, str] = {
            "model": "ollama:llama3.1",
            "provider": "ollama",
            "message": "Ping",
            "system_instruction": ""
        }

        # --- Выполнение действия (Act) ---
        response = self.client.post("/api/chat/test-model", json=payload)

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Эндпоинт Returns 200 с описанием ошибки")
        data: dict = response.json()
        self.assertEqual(data.get("status", ""), "error", "Status ответа должен быть error")
        self.assertIn("11434", data.get("message", ""), "Сообщение об ошибке должно содержать детали исключения")
        self.assertGreaterEqual(data.get("duration_ms", 0.0), 0.0, "Замер времени должен присутствовать даже при ошибке")

    # =========================================================================
    # 6. Regression Scenarios (GET /api/chat/models?refresh=true)
    # =========================================================================

    @patch("core.ai.model_manager.get_available_models")
    def test_get_models_with_refresh_flag(self, mock_get_available_models: MagicMock) -> None:
        """Тестирование передачи параметра refresh=true в эндпоинт /api/chat/models."""
        # --- Подготовка входных данных (Arrange) ---
        mock_get_available_models.return_value = ["model-a", "model-b"]

        # --- Выполнение действия (Act) ---
        response = self.client.get("/api/chat/models?refresh=true")

        # --- Check результатов (Assert) ---
        self.assertEqual(response.status_code, 200, "Код ответа должен быть 200")
        data: dict = response.json()
        self.assertIn("models", data, "Ответ должен содержать ключ models")
        self.assertIn("gemini", data["models"], "Провайдер gemini должен присутствовать")
        self.assertIn("foundry", data["models"], "Провайдер foundry должен присутствовать")
        self.assertIn("ollama", data["models"], "Провайдер ollama должен присутствовать")
        self.assertIn("agy", data["models"], "Провайдер agy должен присутствовать")
        self.assertIn("gemini_cli", data["models"], "Провайдер gemini_cli должен присутствовать")

        # Check, что get_available_models вызывался с force_refresh=True
        calls = mock_get_available_models.call_args_list
        self.assertTrue(any(call.kwargs.get("force_refresh") is True for call in calls), "force_refresh должен быть True")

if __name__ == "__main__":
    unittest.main()
