# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - History Module
# =============================================================================
# Description:
#   Миксин для управления историей диалогов в GoogleGenerativeAI.
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.history import GoogleGenerativeAIHistoryMixin
#
#     service = GoogleGenerativeAIHistoryMixin()
#     result = service.clear_history()
#     print(result)
#
# File: history.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Миксин для управления историей диалогов в GoogleGenerativeAI."""

from typing import Any
from google.genai import types
from .config import GoogleGenerativeAIConfigMixin


class GoogleGenerativeAIHistoryMixin:
    """Миксин для управления историей диалогов в GoogleGenerativeAI.

    Предоставляет методы для управления историей сообщений и состоянием сессии чата.
    """

    def __init__(self) -> None:
        """Initialization chat history attributes."""
        self.chat_history: list[dict] = []
        self._chat: Any = False

    def clear_history(self) -> None:
        """Clearing of local dialog history in operational memory."""
        self.chat_history = []

    def _convert_history_to_contents(self, history: list[dict] = ()) -> list[types.Content]:
        """Преобразование списка словарей истории диалога в список объектов types.Content.

        Args:
            history (list[dict]): История сообщений в виде словарей.

        Returns:
            list[types.Content]: Список объектов Content для передачи в сессию чата.
        """
        history_contents: list[types.Content] = []
        if not history:
            return history_contents

        for entry in history:
            if not isinstance(entry, dict):
                continue
            role: str = entry.get('role', 'user')
            if role == 'assistant':
                role = 'model'

            parts = entry.get('parts')
            if not parts:
                content_str: str = entry.get('content', '')
                if content_str:
                    parts = [types.Part.from_text(text=content_str)]
                else:
                    parts = []
            else:
                parts_objects: list[types.Part] = []
                for p in parts:
                    if isinstance(p, str):
                        parts_objects.append(types.Part.from_text(text=p))
                    elif isinstance(p, dict) and 'text' in p:
                        parts_objects.append(types.Part.from_text(text=p['text']))
                    elif isinstance(p, types.Part):
                        parts_objects.append(p)
                    else:
                        parts_objects.append(types.Part.from_text(text=str(p)))
                parts = parts_objects

            if parts:
                history_contents.append(types.Content(role=role, parts=parts))

        return history_contents

    def _restore_chat_from_history(self) -> None:
        """Восстановление состояния сессии чата из накопленной истории сообщений."""
        history_contents = self._convert_history_to_contents(self.chat_history)
        self._chat = self._start_chat(history=history_contents)

    def _prepare_contents(self, q: str, history: list[dict] = ()) -> list[types.Content]:
        """Подготовка списка объектов Content для передачи в stateless API-запросы.

        Args:
            q (str): Текущий текстовый запрос пользователя.
            history (list[dict]): История предыдущих сообщений.

        Returns:
            list[types.Content]: Список объектов Content.
        """
        contents = self._convert_history_to_contents(history)
        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=q)]))
        return contents

    def _start_chat(
        self,
        history: list = (),
        config: types.GenerateContentConfig | None = None,
        model_name: str = '',
    ) -> Any:
        """Инициализация синхронной сессии чата с поддержкой сохранения истории.

        Args:
            history (list): Начальная история сообщений (types.Content или словари).
            config (types.GenerateContentConfig | None): Конфигурация генерации.
            model_name (str): Наименование модели.

        Returns:
            Any: Экземпляр синхронного чата google.genai.chats.Chat или False.
        """
        if not self.save_history_chat:
            return False
        cfg = config or self._build_content_config()
        active_model = model_name or self.model_name
        contents_hist = self._convert_history_to_contents(history) if history and isinstance(history[0], dict) else list(history)
        if contents_hist:
            return self._client.chats.create(model=active_model, config=cfg, history=contents_hist)
        return self._client.chats.create(model=active_model, config=cfg)

    def _start_async_chat(
        self,
        history: list = (),
        config: types.GenerateContentConfig | None = None,
        model_name: str = '',
    ) -> Any:
        """Инициализация нативного асинхронного чата (AsyncChat) для стриминга и AFC.

        Создаёт сессию google.genai.chats.AsyncChat, обеспечивающую безопасное сохранение
        контекста диалога, автоматический вызов функций (AFC) и стриминг ответов.

        Args:
            history (list): Начальная история сообщений (types.Content или словари).
            config (types.GenerateContentConfig | None): Конфигурация генерации.
            model_name (str): Наименование модели.

        Returns:
            Any: Экземпляр google.genai.chats.AsyncChat.
        """
        cfg = config or self._build_content_config()
        active_model = model_name or self.model_name
        contents_hist = self._convert_history_to_contents(history) if history and isinstance(history[0], dict) else list(history)
        if hasattr(self._client, 'aio') and hasattr(self._client.aio, 'chats'):
            if contents_hist:
                return self._client.aio.chats.create(model=active_model, config=cfg, history=contents_hist)
            return self._client.aio.chats.create(model=active_model, config=cfg)
        return False