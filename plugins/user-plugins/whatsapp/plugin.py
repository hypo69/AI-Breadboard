# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: WhatsApp Modular Plugin Implementation
# =============================================================================
# Description:
#   Модульный плагин WhatsApp для AI Breadboard, реализующий интерфейс BasePlugin,
#   управление конфигурацией, отправку текстовых сообщений и пересылку писем.
#
# File: plugin.py
# Package: plugins.whatsapp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Реализация модульного плагина WhatsApp для платформы AI Breadboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.base import BasePlugin
from .client import WhatsAppClient
from logger import logger


class WhatsAppPlugin(BasePlugin):
    """Модульный плагин интеграции с мессенджером WhatsApp.

    Attributes:
        name (str): 'whatsapp'.
        title (str): 'WhatsApp Messenger'.
        version (str): '1.0.0'.
        description (str): 'Отправка сообщений, оповещений и пересылка писем в WhatsApp.'.
        icon (str): '💬'.
        category (str): 'communication'.
    """

    name: str = "whatsapp"
    title: str = "WhatsApp Messenger"
    title_i18n: Dict[str, str] = {
        "ru": "Мессенджер WhatsApp",
        "en": "WhatsApp Messenger",
    }
    version: str = "1.0.0"
    description: str = "Отправка сообщений, оповещений и пересылка содержимого писем в WhatsApp."
    description_i18n: Dict[str, str] = {
        "ru": "Отправка сообщений, оповещений и пересылка содержимого писем в WhatsApp.",
        "en": "Send messages, alerts, and forward email contents to WhatsApp.",
    }
    icon: str = "💬"
    category: str = "communication"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализация плагина WhatsApp.

        Args:
            ai_model (Any): Опциональная модель ИИ.
            config (Optional[Dict[str, Any]]): Параметры конфигурации.
        """
        defaults = self._load_default_config()
        if config:
            defaults.update(config)
        super().__init__(ai_model=ai_model, config=defaults)

        self.client = WhatsAppClient(
            token=self.config.get("token") or self.config.get("access_token"),
            phone_number_id=self.config.get("phone_number_id"),
            api_version=self.config.get("api_version", "v18.0"),
            provider=self.config.get("provider", "cloud_api"),
            timeout=int(self.config.get("timeout", 15)),
        )

    def _load_default_config(self) -> Dict[str, Any]:
        """Загружает параметры по умолчанию из config.json."""
        config_file = Path(__file__).resolve().parent / "config.json"
        if config_file.is_file():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                logger.warning(f"[whatsapp_plugin] Не удалось прочитать config.json: {ex}")
        return {}

    def get_actions(self) -> List[Dict[str, Any]]:
        """Возвращает список поддерживаемых действий плагина.

        Returns:
            List[Dict[str, Any]]: Список описаний действий.
        """
        return [
            {
                "name": "send_message",
                "title": "Отправить сообщение в WhatsApp",
                "description": "Отправляет текстовое сообщение на указанный номер WhatsApp.",
                "parameters": {
                    "to": {"type": "string", "required": True, "description": "Номер получателя в международном формате."},
                    "message": {"type": "string", "required": True, "description": "Текст сообщения."},
                },
            },
            {
                "name": "send_email_alert",
                "title": "Переслать письмо в WhatsApp",
                "description": "Форматирует и отправляет сводку о входящем письме в WhatsApp.",
                "parameters": {
                    "to": {"type": "string", "required": True, "description": "Номер получателя."},
                    "email_data": {"type": "object", "required": True, "description": "Данные письма (sender, subject, date, body_text)."},
                },
            },
            {
                "name": "test_connection",
                "title": "Проверить подключение",
                "description": "Проверяет валидность токена и доступность API WhatsApp.",
                "parameters": {},
            },
        ]

    async def execute_action(self, action_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Выполняет действие плагина по имени.

        Args:
            action_name (str): Имя действия.
            params (Optional[Dict[str, Any]]): Параметры вызова.

        Returns:
            Any: Результат выполнения действия.
        """
        params = params or {}
        if action_name == "send_message":
            return self.client.send_message(
                to=params.get("to", ""),
                message=params.get("message", ""),
            )
        elif action_name == "send_email_alert":
            return self.client.send_email_alert(
                to=params.get("to", ""),
                email_data=params.get("email_data", {}),
            )
        elif action_name == "test_connection":
            return self.client.test_connection()
        else:
            return {"success": False, "error": f"Неизвестное действие: {action_name}"}

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Обработка входящего сообщения и отправка через WhatsApp.

        Args:
            message (str): Текст сообщения.
            **kwargs: Дополнительные параметры (включая 'to' - телефон получателя).

        Yields:
            Dict[str, Any]: Результат отправки.
        """
        to = kwargs.get("to") or self.config.get("default_recipient", "")
        res = self.client.send_message(to=to, message=message)
        yield {"status": "complete", "result": res}
