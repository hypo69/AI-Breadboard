# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for WhatsApp Plugin & Client
# =============================================================================
# Description:
#   Комплексные тесты для плагина WhatsApp: нормализация номеров,
#   отправка сообщений через Meta Cloud API, форматирование дайджестов писем,
#   проверка подключения и выполнение действий BasePlugin.
#
# File: test_whatsapp_plugin.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модульные тесты для плагина интеграции с WhatsApp."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from plugins.whatsapp.client import WhatsAppClient, normalize_phone_number
from plugins.whatsapp.plugin import WhatsAppPlugin


def test_normalize_phone_number() -> None:
    """Проверка нормализации телефонных номеров."""
    assert normalize_phone_number("+7 (999) 123-45-67") == "79991234567"
    assert normalize_phone_number("972-50-1234567") == "972501234567"
    assert normalize_phone_number("8 (800) 555-35-35") == "88005553535"
    assert normalize_phone_number("") == ""


def test_whatsapp_client_config_validation(tmp_path: Path) -> None:
    """Проверка загрузки конфигурации из secrets.json."""
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(
        json.dumps({
            "token": "meta_token_123",
            "phone_number_id": "100200300",
            "provider": "cloud_api",
            "default_recipient": "79991112233",
        }),
        encoding="utf-8",
    )
    client = WhatsAppClient(config_path=secrets_file)
    assert client.token == "meta_token_123"
    assert client.phone_number_id == "100200300"
    assert client.provider == "cloud_api"
    assert client.default_recipient == "79991112233"


@patch("urllib.request.urlopen")
def test_whatsapp_client_send_message_success(mock_urlopen: MagicMock) -> None:
    """Проверка успешной отправки сообщения через Meta Graph API."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "messaging_product": "whatsapp",
        "contacts": [{"input": "79991234567", "wa_id": "79991234567"}],
        "messages": [{"id": "wamid.HBgLMTIzNDU2"}],
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = WhatsAppClient(
        token="test_token",
        phone_number_id="123456",
        provider="cloud_api",
    )
    res = client.send_message(to="+7 (999) 123-45-67", message="Тестовое сообщение")

    assert res["success"] is True
    assert res["recipient"] == "79991234567"
    assert res["whatsapp_message_id"] == "wamid.HBgLMTIzNDU2"


@patch("urllib.request.urlopen")
def test_whatsapp_client_send_email_alert(mock_urlopen: MagicMock) -> None:
    """Проверка форматирования и отправки оповещения о письме."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "messages": [{"id": "wamid.ALERT123"}],
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = WhatsAppClient(
        token="test_token",
        phone_number_id="123456",
        provider="cloud_api",
    )
    email_data = {
        "sender": "Руководитель <boss@company.com>",
        "subject": "Срочный контракт",
        "date": "Sat, 19 Sep 2026 12:00:00",
        "body_text": "Пожалуйста, согласуйте контракт.",
    }
    res = client.send_email_alert(to="79990001122", email_data=email_data)
    assert res["success"] is True
    assert res["whatsapp_message_id"] == "wamid.ALERT123"


def test_whatsapp_client_validation_errors() -> None:
    """Проверка обработки некорректных аргументов при отправке."""
    client = WhatsAppClient(token="", phone_number_id="")
    # 1. Нет номера получателя
    res_no_to = client.send_message(to="", message="Hello")
    assert res_no_to["success"] is False
    assert "получателя" in res_no_to["error"]

    # 2. Пустое сообщение
    res_no_msg = client.send_message(to="79991234567", message="")
    assert res_no_msg["success"] is False
    assert "пустым" in res_no_msg["error"]

    # 3. Нет токена/ID
    res_no_creds = client.send_message(to="79991234567", message="Hello")
    assert res_no_creds["success"] is False


@pytest.mark.asyncio
async def test_whatsapp_plugin_actions() -> None:
    """Проверка регистрации и выполнения действий WhatsAppPlugin."""
    plugin = WhatsAppPlugin(config={"token": "t", "phone_number_id": "123"})
    actions = plugin.get_actions()
    action_names = [a["name"] for a in actions]
    assert "send_message" in action_names
    assert "send_email_alert" in action_names
    assert "test_connection" in action_names

    with patch.object(plugin.client, "send_message", return_value={"success": True, "mock": 1}):
        res = await plugin.execute_action("send_message", {"to": "7999123", "message": "Hi"})
        assert res["success"] is True

    with patch.object(plugin.client, "test_connection", return_value={"success": True}):
        res_conn = await plugin.execute_action("test_connection")
        assert res_conn["success"] is True
