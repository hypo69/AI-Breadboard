# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Chat History Management
# =============================================================================
# Description:
#   Management of chat history and session state for Google Generative AI.
#   Provides methods for restoring, clearing, and managing chat history.
#
# File: history.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from typing import Any

from google.genai import types

from .config import GoogleGenerativeAIConfigMixin


class GoogleGenerativeAIHistoryMixin:
    """Mixin class for chat history management in GoogleGenerativeAI.

    Provides methods for managing chat history and session state.
    """

    def __init__(self) -> None:
        """Initialization chat history attributes."""
        self.chat_history: list[dict] = []
        self._chat: Any = False

    def clear_history(self) -> None:
        """Clearing of local dialog history in operational memory."""
        self.chat_history = []

    def _restore_chat_from_history(self) -> None:
        """Restoration of chat session state from accumulated message history."""
        history_contents: list[types.Content] = []
        for entry in self.chat_history:
            role: str = entry.get('role', 'user')
            if role == 'assistant':
                role = 'model'
            parts: list = entry.get('parts', [])
            parts_objects: list[types.Part] = []
            for p in parts:
                if isinstance(p, str):
                    parts_objects.append(types.Part.from_text(text=p))
                elif isinstance(p, dict) and 'text' in p:
                    parts_objects.append(types.Part.from_text(text=p['text']))
            history_contents.append(types.Content(role=role, parts=parts_objects))

        self._chat = self._start_chat(history=history_contents)

    def _prepare_contents(self, q: str, history: list[dict] = ()) -> list[types.Content]:
        """Подготовка списка объектов Content для передачи в stateless API-запросы.

        Args:
            q (str): Текущий текстовый запрос пользователя.
            history (list[dict]): История предыдущих сообщений.

        Returns:
            list[types.Content]: List объектов Content.
        """
        contents: list[types.Content] = []
        if history:
            for entry in history:
                role: str = entry.get('role', '')
                if not role:
                    continue
                if role == 'assistant':
                    role = 'model'

                parts = entry.get('parts')
                if not parts:
                    content_str: str = entry.get('content', '')
                    if content_str:
                        parts = [types.Part.from_text(text=content_str)]
                else:
                    new_parts: list = []
                    for p in parts:
                        if isinstance(p, str):
                            new_parts.append(types.Part.from_text(text=p))
                        elif isinstance(p, dict) and 'text' in p:
                            new_parts.append(types.Part.from_text(text=p['text']))
                        else:
                            new_parts.append(p)
                    parts = new_parts

                if parts:
                    contents.append(types.Content(role=role, parts=parts))

        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=q)]))
        return contents

    def _start_chat(self, history: list = ()) -> Any:
        """Initialization сессии чата с поддержкой сохранения истории.

        Args:
            history (list): Начальная история сообщений.

        Returns:
            Any: Экземпляр чата Google GenAI или False если история отключена.
        """
        if not self.save_history_chat:
            return False

        config = self._build_content_config()
        if history:
            return self._client.chats.create(model=self.model_name, config=config, history=list(history))
        return self._client.chats.create(model=self.model_name, config=config)
