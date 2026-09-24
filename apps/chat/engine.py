# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Chat Application Engine
# =============================================================================
# Description:
#   Движок приложения AI Chat для управления диалогами, контекстом,
#   историей сессий, интеграцией с RAG и логированием метрик.
#
# File: engine.py
# Project: ai-breadboard
# Package: apps.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from logger import logger
from apps.common.csv_logger import AppCsvLogger
from src.api import chat_sessions_db
from src.config import ai_cfg


class ChatEngine:
    """Движок выполнения диалогов и управления состоянием чата."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Инициализирует экземпляр ChatEngine.

        Args:
            config_path: Необязательный путь к файлу конфигурации.
        """
        self._config_path = config_path or (Path(__file__).parent / "config.json")
        self._csv_logger = AppCsvLogger("chat")
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Загружает параметры конфигурации чат-приложения."""
        if self._config_path.exists():
            try:
                return json.loads(self._config_path.read_text(encoding="utf-8"))
            except Exception as ex:
                logger.warning(f"Не удалось прочитать конфигурацию chat: {ex}")
        return {
            "app_name": "AI Chat Assistant",
            "version": "1.0.0",
            "chat": {
                "default_mode": "chat",
                "rag_enabled": True,
                "top_k": 3,
                "min_score": 0.45,
                "output_mode": "text_and_voice",
            },
        }

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус готовности и текущие параметры чата.

        Returns:
            Dict[str, Any]: Словарь со статусом провайдера ИИ и сессий.
        """
        provider = getattr(ai_cfg, "provider", "gemini")
        sessions_count = 0
        try:
            sessions = chat_sessions_db.list_sessions()
            sessions_count = len(sessions)
        except Exception as ex:
            logger.debug(f"Ошибка получения списка сессий: {ex}")

        return {
            "status": "ready",
            "provider": provider,
            "sessions_count": sessions_count,
            "rag_enabled": self._config.get("chat", {}).get("rag_enabled", True),
            "app_name": self._config.get("app_name", "AI Chat Assistant"),
            "version": self._config.get("version", "1.0.0"),
        }

    def get_config(self) -> Dict[str, Any]:
        """Возвращает текущую конфигурацию приложения.

        Returns:
            Dict[str, Any]: Конфигурация приложения.
        """
        return self._config

    def list_sessions(self, user_id: str = "") -> List[Dict[str, Any]]:
        """Возвращает список всех сохраненных сессий диалогов.

        Args:
            user_id: Идентификатор пользователя для фильтрации (опционально).

        Returns:
            List[Dict[str, Any]]: Список словарей с данными сессий.
        """
        try:
            sessions = chat_sessions_db.list_sessions(user_id=user_id)
            self._csv_logger.log_poll(
                poll_type="sessions",
                metric_name="sessions_count",
                value=len(sessions),
                unit="count",
                status="SUCCESS",
            )
            return sessions
        except Exception as ex:
            logger.error(f"Ошибка при чтении сессий чата: {ex}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные конкретной сессии по ее идентификатору.

        Args:
            session_id: Уникальный идентификатор сессии.

        Returns:
            Optional[Dict[str, Any]]: Данные сессии или пустой словарь.
        """
        if not session_id:
            return None
        try:
            session = chat_sessions_db.get_session(session_id)
            return session if session else None
        except Exception as ex:
            logger.error(f"Ошибка при получении сессии {session_id}: {ex}")
            return None

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Сохраняет или обновляет сессию диалога в базе данных.

        Args:
            session_data: Данные сессии для сохранения.

        Returns:
            bool: True в случае успешного сохранения, False иначе.
        """
        if not session_data or not session_data.get("id"):
            return False
        try:
            saved = chat_sessions_db.save_session(session_data)
            success = bool(saved)
            if success:
                self._csv_logger.log_param_change(
                    param_name=f"session.{session_data.get('id')}",
                    old_value="",
                    new_value=session_data.get("title", "New Chat"),
                    status="SUCCESS",
                    details={"messages_count": len(session_data.get("messages", []))},
                )
            return success
        except Exception as ex:
            logger.error(f"Ошибка при сохранении сессии: {ex}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Удаляет сессию диалога по ее идентификатору.

        Args:
            session_id: Идентификатор удаляемой сессии.

        Returns:
            bool: True в случае успешного удаления, False иначе.
        """
        if not session_id:
            return False
        try:
            success = chat_sessions_db.delete_session(session_id)
            if success:
                self._csv_logger.log_param_change(
                    param_name=f"session.{session_id}",
                    old_value="ACTIVE",
                    new_value="DELETED",
                    status="SUCCESS",
                )
            return success
        except Exception as ex:
            logger.error(f"Ошибка при удалении сессии {session_id}: {ex}")
            return False

    def clear_all_sessions(self) -> bool:
        """Удаляет все сохраненные сессии чата.

        Returns:
            bool: True в случае успешного удаления, False иначе.
        """
        try:
            success = chat_sessions_db.clear_all_sessions()
            if success:
                self._csv_logger.log_param_change(
                    param_name="all_sessions",
                    old_value="ALL",
                    new_value="CLEARED",
                    status="SUCCESS",
                )
            return success
        except Exception as ex:
            logger.error(f"Ошибка при очистке всех сессий: {ex}")
            return False
