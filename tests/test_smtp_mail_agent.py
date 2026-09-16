# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for SMTP Mail Agent
# =============================================================================
# Description:
#   Комплексные модульные тесты для навыка smtp-mail-agent:
#   загрузка secrets.json, проверка подключения, отправка писем, вложения и CLI.
#
# File: test_smtp_mail_agent.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Тестирование SMTP-агента и модулей работы с почтой."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Добавляем путь к скриптам агента в sys.path для импортов
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "smtp-mail-agent"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from smtp_core import SmtpClient, SmtpConfig, find_secrets_file, load_smtp_config
from src.skills.registry import SkillRegistry


@pytest.fixture
def mock_secrets_file(tmp_path: Path) -> Path:
    """Фикстура создаёт временный валидный secrets.json."""
    secrets_data = {
        "smtp": {
            "host": "smtp.testserver.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "username": "tester@testserver.com",
            "password": "secret_password_123",
            "from_email": "tester@testserver.com",
            "from_name": "Test Bot",
            "timeout": 15,
        }
    }
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps(secrets_data), encoding="utf-8")
    return secrets_file


def test_load_smtp_config_from_file(mock_secrets_file: Path) -> None:
    """Проверка успешной загрузки конфигурации из файла secrets.json."""
    config = load_smtp_config(mock_secrets_file)
    assert config.host == "smtp.testserver.com"
    assert config.port == 587
    assert config.use_tls is True
    assert config.use_ssl is False
    assert config.username == "tester@testserver.com"
    assert config.password == "secret_password_123"
    assert config.from_email == "tester@testserver.com"
    assert config.from_name == "Test Bot"
    assert config.timeout == 15


def test_load_smtp_config_not_found(tmp_path: Path) -> None:
    """Проверка поведения при отсутствии файла secrets.json и без env-переменных."""
    non_existent = tmp_path / "absent_secrets.json"
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(FileNotFoundError):
            load_smtp_config(non_existent)


def test_load_smtp_config_env_fallback() -> None:
    """Проверка fallback-загрузки из переменных окружения при отсутствии файла."""
    env_vars = {
        "SMTP_HOST": "env.smtp.com",
        "SMTP_PORT": "465",
        "SMTP_USE_TLS": "false",
        "SMTP_USE_SSL": "true",
        "SMTP_USER": "env_user@env.com",
        "SMTP_PASSWORD": "env_password",
        "SMTP_FROM_EMAIL": "env_sender@env.com",
        "SMTP_FROM_NAME": "Env Sender",
    }
    with patch("smtp_core.find_secrets_file", side_effect=FileNotFoundError("No secrets.json")):
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_smtp_config()
            assert config.host == "env.smtp.com"
            assert config.port == 465
            assert config.use_ssl is True
            assert config.use_tls is False
            assert config.username == "env_user@env.com"


@patch("smtplib.SMTP")
def test_smtp_client_test_connection_success(mock_smtp: MagicMock) -> None:
    """Проверка успешного тестирования SMTP-подключения."""
    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        use_tls=True,
        username="user@example.com",
        password="pass",
    )
    client = SmtpClient(config)
    result = client.test_connection()

    assert result["status"] == "success"
    assert "smtp.example.com" in result["message"]
    mock_instance.ehlo.assert_called()
    mock_instance.starttls.assert_called()
    mock_instance.login.assert_called_with("user@example.com", "pass")
    mock_instance.noop.assert_called()


@patch("smtplib.SMTP_SSL")
def test_smtp_client_test_connection_ssl(mock_smtp_ssl: MagicMock) -> None:
    """Проверка тестирования подключения через прямое SSL-соединение."""
    mock_instance = MagicMock()
    mock_smtp_ssl.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    config = SmtpConfig(
        host="smtp.example.com",
        port=465,
        use_ssl=True,
        username="user@example.com",
        password="pass",
    )
    client = SmtpClient(config)
    result = client.test_connection()

    assert result["status"] == "success"
    mock_instance.login.assert_called_with("user@example.com", "pass")


@patch("smtplib.SMTP")
def test_smtp_client_test_connection_error(mock_smtp: MagicMock) -> None:
    """Проверка обработки ошибки при подключении к SMTP."""
    mock_smtp.side_effect = ConnectionRefusedError("Connection refused by host")

    config = SmtpConfig(host="smtp.error.com")
    client = SmtpClient(config)
    result = client.test_connection()

    assert result["status"] == "error"
    assert "ConnectionRefusedError" in result["error_type"]


@patch("smtplib.SMTP")
def test_smtp_client_send_mail_plain(mock_smtp: MagicMock) -> None:
    """Проверка отправки простого текстового письма."""
    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    config = SmtpConfig(
        host="smtp.test.com",
        username="sender@test.com",
        password="password",
        from_email="sender@test.com",
    )
    client = SmtpClient(config)
    result = client.send_mail(
        to="recipient@test.com",
        subject="Заголовок теста",
        body_text="Простой текст сообщения",
        cc="copy@test.com",
    )

    assert result["status"] == "success"
    assert result["to"] == ["recipient@test.com"]
    assert result["cc"] == ["copy@test.com"]
    assert mock_instance.sendmail.called
    args, _ = mock_instance.sendmail.call_args
    assert args[0] == "sender@test.com"
    assert set(args[1]) == {"recipient@test.com", "copy@test.com"}


@patch("smtplib.SMTP")
def test_smtp_client_send_mail_with_attachment(mock_smtp: MagicMock, tmp_path: Path) -> None:
    """Проверка отправки HTML-письма с прикрепленным файлом."""
    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    sample_file = tmp_path / "document.txt"
    sample_file.write_text("Тестовое вложение", encoding="utf-8")

    config = SmtpConfig(
        host="smtp.test.com",
        username="sender@test.com",
        password="password",
        from_email="sender@test.com",
    )
    client = SmtpClient(config)
    result = client.send_mail(
        to=["user1@test.com", "user2@test.com"],
        subject="Письмо с файлом",
        body_text="Текст",
        body_html="<h1>Заголовок HTML</h1>",
        attachments=[sample_file],
    )

    assert result["status"] == "success"
    assert "document.txt" in result["attachments"]
    assert mock_instance.sendmail.called


def test_smtp_client_send_mail_no_recipients() -> None:
    """Проверка валидации при отсутствии адресатов."""
    config = SmtpConfig(host="smtp.test.com")
    client = SmtpClient(config)
    result = client.send_mail(to=[], subject="Тест", body_text="Тест")
    assert result["status"] == "error"
    assert "Не указан ни один адрес" in result["message"]


def test_skill_registry_discovers_smtp_agent() -> None:
    """Проверка того, что SkillRegistry успешно находит и парсит навык smtp-mail-agent."""
    registry = SkillRegistry()
    skill = registry.get("smtp-mail-agent")
    assert skill.name == "smtp-mail-agent"
    assert "smtp" in skill.description.lower()
    assert "ru" in skill.descriptions_i18n
    assert "secrets.json" in skill.instructions


@patch("smtplib.SMTP")
def test_cli_test_connection_main(mock_smtp: MagicMock, mock_secrets_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверка CLI test_connection.py."""
    import test_connection

    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    monkeypatch.setattr(sys, "argv", ["test_connection.py", "--secrets", str(mock_secrets_file), "--json"])
    exit_code = test_connection.main()
    assert exit_code == 0


@patch("smtplib.SMTP")
def test_cli_send_mail_main(mock_smtp: MagicMock, mock_secrets_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверка CLI send_mail.py."""
    import send_mail

    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    mock_instance.__enter__.return_value = mock_instance

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_mail.py",
            "--secrets", str(mock_secrets_file),
            "--to", "dest@example.com",
            "--subject", "CLI Test",
            "--body", "Hello from CLI",
            "--json",
        ],
    )
    exit_code = send_mail.main()
    assert exit_code == 0

