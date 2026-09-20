# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Mail Watcher Skill & Agent
# =============================================================================
# Description:
#   Комплексные модульные тесты для навыка mail-watcher и агента Mail Watcher:
#   проверка конфигурации, фильтрация по отправителю, декодирование RFC 2047,
#   отслеживание состояния обработанных писем, CLI и LangChain-инструменты.
#
# File: test_mail_watcher.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модульные тесты для навыка и агента мониторинга почты от заданного отправителя."""

from __future__ import annotations

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Добавляем пути к скриптам навыка в sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "mail-watcher"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mail_watcher import (
    MailWatcher,
    MailWatcherConfig,
    WatchedMessage,
    decode_mime_header,
    load_mail_watcher_config,
    parse_sender_info,
    send_windows_notification,
)
from src.skills.registry import SkillRegistry


@pytest.fixture
def mock_secrets_file(tmp_path: Path) -> Path:
    """Создает временный файл secrets.json для тестов."""
    secrets_data = {
        "host": "imap.testmail.com",
        "port": 993,
        "use_ssl": True,
        "username": "tester@testmail.com",
        "password": "secret_app_password_789",
        "folder": "INBOX",
        "target_sender": "boss@company.com",
    }
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps(secrets_data), encoding="utf-8")
    return secrets_file


@pytest.fixture
def mock_mailboxes_file(tmp_path: Path) -> Path:
    """Создает тестовый файл mailboxes.json с несколькими ящиками и алиасами."""
    mailboxes_data = {
        "kazarinov": {
            "description": "Личная почта Казаринова для основных счетов",
            "aliases": ["Сергей", "Казаринов", "Серрежа"],
            "imap_host": "imap.hostinger.com",
            "imap_port": 993,
            "smtp_host": "smtp.hostinger.com",
            "smtp_port": 465,
            "username": "sergey@mymaster.co.il",
            "password": "kaz_password_123",
        },
        "маша": {
            "description": "Личная почта Маши Флоренц",
            "aliases": ["masha", "Мария"],
            "imap_host": "imap.mail.ru",
            "imap_port": 993,
            "smtp_host": "smtp.mail.ru",
            "smtp_port": 465,
            "username": "mariya-florenc@mail.ru",
            "password": "masha_password_456",
        },
    }
    mb_file = tmp_path / "mailboxes.json"
    mb_file.write_text(json.dumps(mailboxes_data, ensure_ascii=False), encoding="utf-8")
    return mb_file


def test_load_config_from_mailboxes_json_by_account_and_alias(mock_mailboxes_file: Path, tmp_path: Path) -> None:
    """Проверка извлечения настроек из mailboxes.json по ключу, русскому алиасу и fallback."""
    state_file = tmp_path / "state.json"

    # 1. По прямому имени аккаунта
    cfg_kaz = load_mail_watcher_config(
        explicit_path=mock_mailboxes_file,
        account="kazarinov",
        state_file=state_file,
    )
    assert cfg_kaz.host == "imap.hostinger.com"
    assert cfg_kaz.username == "sergey@mymaster.co.il"
    assert cfg_kaz.password == "kaz_password_123"

    # 2. По русскому алиасу "Казаринов" (регистронезависимо)
    cfg_alias = load_mail_watcher_config(
        explicit_path=mock_mailboxes_file,
        account="казаринов",
        state_file=state_file,
    )
    assert cfg_alias.host == "imap.hostinger.com"
    assert cfg_alias.username == "sergey@mymaster.co.il"

    # 3. По алиасу "Сергей"
    cfg_sergey = load_mail_watcher_config(
        explicit_path=mock_mailboxes_file,
        account="Сергей",
        state_file=state_file,
    )
    assert cfg_sergey.username == "sergey@mymaster.co.il"

    # 4. По второму ящику "маша"
    cfg_masha = load_mail_watcher_config(
        explicit_path=mock_mailboxes_file,
        account="маша",
        state_file=state_file,
    )
    assert cfg_masha.host == "imap.mail.ru"
    assert cfg_masha.username == "mariya-florenc@mail.ru"

    # 5. Fallback на первый ящик при указании 'default'
    cfg_default = load_mail_watcher_config(
        explicit_path=mock_mailboxes_file,
        account="default",
        state_file=state_file,
    )
    assert cfg_default.username in ("sergey@mymaster.co.il", "mariya-florenc@mail.ru")


def test_mail_watcher_config_validation() -> None:
    """Проверка валидации обязательных параметров конфигурации."""
    with pytest.raises(ValueError, match="host"):
        MailWatcherConfig(host="", username="u", password="p")

    with pytest.raises(ValueError, match="username"):
        MailWatcherConfig(host="h", username="", password="p")

    with pytest.raises(ValueError, match="password"):
        MailWatcherConfig(host="h", username="u", password="")


def test_decode_mime_header_and_sender_parsing() -> None:
    """Проверка декодирования MIME заголовков и разбора отправителя."""
    from email.header import Header

    encoded_name = Header("Иван Иванов", "utf-8").encode()
    raw_from = f"{encoded_name} <ivan@example.com>"

    full, name, addr = parse_sender_info(raw_from)
    assert name == "Иван Иванов"
    assert addr == "ivan@example.com"
    assert "Иван Иванов" in full

    assert decode_mime_header("Simple Subject") == "Simple Subject"
    assert decode_mime_header(None) == ""


def test_watched_message_format_alert() -> None:
    """Проверка форматирования текста уведомления о письме."""
    msg = WatchedMessage(
        msg_id="<msg123@domain.com>",
        date="Sat, 19 Sep 2026 10:00:00 +0300",
        sender="Руководитель <boss@company.com>",
        sender_name="Руководитель",
        sender_email="boss@company.com",
        subject="Срочный отчет по проекту",
        body_text="Пожалуйста, подготовьте отчет до конца дня.",
        attachments_count=1,
    )
    alert_text = msg.format_alert()
    assert "boss@company.com" in alert_text
    assert "Срочный отчет по проекту" in alert_text
    assert "вложений: 1" in alert_text
    assert msg.to_dict()["msg_id"] == "<msg123@domain.com>"


def test_matches_sender_filter() -> None:
    """Проверка различных сценариев фильтрации по отправителю."""
    cfg = MailWatcherConfig(host="h", username="u", password="p")
    watcher = MailWatcher(cfg)

    # 1. Поиск по точному email
    assert watcher._matches_sender("Alice <alice@work.com>", "Alice", "alice@work.com", "alice@work.com")
    # 2. Поиск по подстроке email
    assert watcher._matches_sender("Alice <alice@work.com>", "Alice", "alice@work.com", "alice")
    # 3. Поиск по имени
    assert watcher._matches_sender("Alice Smith <asmith@work.com>", "Alice Smith", "asmith@work.com", "Alice")
    # 4. Несовпадение
    assert not watcher._matches_sender("Bob <bob@work.com>", "Bob", "bob@work.com", "alice")
    # 5. Пустой целевой отправитель совпадает со всеми
    assert watcher._matches_sender("Bob <bob@work.com>", "Bob", "bob@work.com", "")


@patch("imaplib.IMAP4_SSL")
def test_mail_watcher_test_connection_success(mock_imap: MagicMock) -> None:
    """Проверка успешного тестирования подключения к IMAP."""
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"'])

    cfg = MailWatcherConfig(
        host="imap.example.com",
        username="user@example.com",
        password="secret_password",
    )
    watcher = MailWatcher(cfg)
    result = watcher.test_connection()

    assert result["success"] is True
    assert result["host"] == "imap.example.com"
    assert result["folders_count"] == 1
    mock_instance.login.assert_called_with("user@example.com", "secret_password")


@patch("imaplib.IMAP4_SSL")
def test_mail_watcher_test_connection_failure(mock_imap: MagicMock) -> None:
    """Проверка обработки ошибки при сбое подключения к IMAP."""
    mock_imap.side_effect = ConnectionRefusedError("Connection refused")

    cfg = MailWatcherConfig(host="imap.badhost.com", username="u", password="p")
    watcher = MailWatcher(cfg)
    result = watcher.test_connection()

    assert result["success"] is False
    assert "Connection refused" in result["error"]


@patch("imaplib.IMAP4_SSL")
def test_mail_watcher_check_messages_and_state(mock_imap: MagicMock, tmp_path: Path) -> None:
    """Проверка поиска писем от заданного отправителя и сохранения состояния."""
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"2"])
    mock_instance.search.return_value = ("OK", [b"1 2"])

    # Письмо 1: от целевого отправителя
    msg1 = MIMEMultipart()
    msg1["Message-ID"] = "<id_001@company.com>"
    msg1["Subject"] = "Важное сообщение"
    msg1["From"] = "Boss <boss@company.com>"
    msg1["Date"] = "Sat, 19 Sep 2026 12:00:00 +0300"
    msg1.attach(MIMEText("Текст письма от руководителя", "plain", "utf-8"))

    # Письмо 2: от другого отправителя
    msg2 = MIMEMultipart()
    msg2["Message-ID"] = "<id_002@other.com>"
    msg2["Subject"] = "Новости сервиса"
    msg2["From"] = "News <news@other.com>"
    msg2["Date"] = "Sat, 19 Sep 2026 12:05:00 +0300"
    msg2.attach(MIMEText("Текст новостной рассылки", "plain", "utf-8"))

    def mock_fetch(msg_id_bytes, spec):
        msg_id_str = msg_id_bytes.decode() if isinstance(msg_id_bytes, bytes) else str(msg_id_bytes)
        if msg_id_str == "1":
            return ("OK", [(b"1 (RFC822 {100} FLAGS (\\Recent))", msg1.as_bytes())])
        return ("OK", [(b"2 (RFC822 {100} FLAGS (\\Recent))", msg2.as_bytes())])

    mock_instance.fetch.side_effect = mock_fetch

    state_file = tmp_path / "seen_state.json"
    cfg = MailWatcherConfig(
        host="imap.test.com",
        username="u@test.com",
        password="p",
        target_sender="boss@company.com",
        state_file=state_file,
    )
    watcher = MailWatcher(cfg)

    # Первая проверка: должно найти письмо 1
    found = watcher.check_messages(sender="boss@company.com")
    assert len(found) == 1
    assert found[0].msg_id == "<id_001@company.com>"
    assert found[0].subject == "Важное сообщение"
    assert "Текст письма от руководителя" in found[0].body_text
    assert state_file.exists()

    # Вторая проверка: письмо 1 уже в seen_ids, повторных уведомлений быть не должно
    found_again = watcher.check_messages(sender="boss@company.com")
    assert len(found_again) == 0


@patch("subprocess.run")
def test_send_windows_notification(mock_run: MagicMock) -> None:
    """Проверка вызова отправки уведомления Windows Toast."""
    mock_run.return_value = MagicMock(returncode=0)
    res = send_windows_notification("Заголовок", "Текст сообщения")
    assert res is True
    assert mock_run.called


def test_skill_registry_discovers_mail_watcher() -> None:
    """Проверка обнаружения навыка mail-watcher в системном реестре навыков."""
    registry = SkillRegistry()
    skill = registry.get("mail-watcher")
    assert skill.name == "mail-watcher"
    assert "mail" in skill.description.lower()
    assert "ru" in skill.descriptions_i18n
    assert "отправител" in skill.instructions.lower() or "sender" in skill.instructions.lower()


@patch("imaplib.IMAP4_SSL")
def test_cli_mail_watcher(mock_imap: MagicMock, mock_secrets_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверка работы консольной утилиты mail_watcher_cli.py."""
    import mail_watcher_cli

    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"10"])

    msg = MIMEMultipart()
    msg["Message-ID"] = "<id_cli_1@company.com>"
    msg["Subject"] = "Письмо из CLI"
    msg["From"] = "Boss <boss@company.com>"
    msg["Date"] = "Sat, 19 Sep 2026 14:00:00 +0000"
    msg.attach(MIMEText("Текст из CLI", "plain", "utf-8"))

    mock_instance.fetch.return_value = ("OK", [(b"10 (RFC822 {100} FLAGS ())", msg.as_bytes())])

    output_json = tmp_path / "cli_output.json"
    state_json = tmp_path / "cli_state.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mail_watcher_cli.py",
            "--secrets", str(mock_secrets_file),
            "--sender", "boss@company.com",
            "--state-file", str(state_json),
            "--check-once",
            "--output", str(output_json),
            "--json",
        ],
    )

    exit_code = mail_watcher_cli.main()
    assert exit_code == 0
    assert output_json.exists()
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["found_count"] == 1
    assert data["messages"][0]["subject"] == "Письмо из CLI"


@patch("imaplib.IMAP4_SSL")
def test_cli_mail_watcher_with_mailboxes_account(
    mock_imap: MagicMock,
    mock_mailboxes_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверка работы CLI с выбором конкретного аккаунта из mailboxes.json по алиасу."""
    import mail_watcher_cli

    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"15"])

    msg = MIMEMultipart()
    msg["Message-ID"] = "<id_cli_acc@mymaster.co.il>"
    msg["Subject"] = "Письмо для Казаринова"
    msg["From"] = "Boss <boss@company.com>"
    msg["Date"] = "Sat, 19 Sep 2026 14:30:00 +0000"
    msg.attach(MIMEText("Текст для Казаринова", "plain", "utf-8"))

    mock_instance.fetch.return_value = ("OK", [(b"15 (RFC822 {100} FLAGS ())", msg.as_bytes())])

    output_json = tmp_path / "cli_acc_output.json"
    state_json = tmp_path / "cli_acc_state.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mail_watcher_cli.py",
            "--secrets", str(mock_mailboxes_file),
            "--account", "Казаринов",
            "--sender", "boss@company.com",
            "--state-file", str(state_json),
            "--check-once",
            "--output", str(output_json),
            "--json",
        ],
    )

    exit_code = mail_watcher_cli.main()
    assert exit_code == 0
    mock_instance.login.assert_called_with("sergey@mymaster.co.il", "kaz_password_123")
    assert output_json.exists()
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["found_count"] == 1


@patch("imaplib.IMAP4_SSL")
def test_langchain_mail_watcher_tools(mock_imap: MagicMock, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Проверка вызова инструментов LangChain mail_watch_test_connection и mail_watch_check_sender."""
    from src.ai.agents.tools import mail_watch_check_sender, mail_watch_test_connection

    monkeypatch.setenv("MAIL_IMAP_HOST", "imap.tooltest.com")
    monkeypatch.setenv("MAIL_USERNAME", "tester@tooltest.com")
    monkeypatch.setenv("MAIL_PASSWORD", "tool_secret_pass")
    monkeypatch.setenv("MAIL_WATCHER_STATE_FILE", str(tmp_path / "langchain_state.json"))

    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"55"])

    msg = MIMEMultipart()
    msg["Message-ID"] = "<agent_msg_1@domain.com>"
    msg["Subject"] = "Агентский тест"
    msg["From"] = "Partner <partner@domain.com>"
    msg["Date"] = "Sat, 19 Sep 2026 15:00:00 +0000"
    msg.attach(MIMEText("Сообщение для агента", "plain", "utf-8"))

    mock_instance.fetch.return_value = ("OK", [(b"55 (RFC822 {100} FLAGS ())", msg.as_bytes())])

    # Тест инструмента проверки соединения
    res_conn = mail_watch_test_connection.invoke({})
    data_conn = json.loads(res_conn)
    assert data_conn["success"] is True

    # Тест инструмента поиска сообщений
    res_check = mail_watch_check_sender.invoke({"sender": "partner@domain.com"})
    data_check = json.loads(res_check)
    assert data_check["success"] is True
    assert data_check["found_count"] == 1
    assert len(data_check["alerts"]) == 1
    assert "Агентский тест" in data_check["alerts"][0]


@patch("imaplib.IMAP4_SSL")
def test_mail_watcher_whatsapp_forwarding(mock_imap: MagicMock, tmp_path: Path) -> None:
    """Проверка автоматической пересылки входящего письма в WhatsApp."""
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"77"])

    msg = MIMEMultipart()
    msg["Message-ID"] = "<wa_forward_msg_1@domain.com>"
    msg["Subject"] = "Письмо для WhatsApp"
    msg["From"] = "Boss <boss@company.com>"
    msg["Date"] = "Sat, 19 Sep 2026 16:00:00 +0000"
    msg.attach(MIMEText("Текст для пересылки в мессенджер", "plain", "utf-8"))

    mock_instance.fetch.return_value = ("OK", [(b"77 (RFC822 {100} FLAGS ())", msg.as_bytes())])

    state_file = tmp_path / "wa_state.json"
    cfg = MailWatcherConfig(
        host="imap.test.com",
        username="u@test.com",
        password="p",
        target_sender="boss@company.com",
        whatsapp_recipient="79991112233",
        state_file=state_file,
    )
    watcher = MailWatcher(cfg)

    with patch.object(watcher, "forward_to_whatsapp", return_value={"success": True}) as mock_forward:
        messages = watcher.check_messages(sender="boss@company.com")
        assert len(messages) == 1
        assert mock_forward.called
        call_args = mock_forward.call_args[0]
        assert call_args[0].subject == "Письмо для WhatsApp"
        assert call_args[1] == "79991112233"


def test_langchain_whatsapp_tools() -> None:
    """Проверка работы инструментов WhatsApp в LangChain."""
    from src.ai.agents.tools import whatsapp_send_message, whatsapp_test_connection

    with patch("plugins.whatsapp.client.WhatsAppClient.test_connection", return_value={"success": True}):
        res_test = whatsapp_test_connection.invoke({})
        assert json.loads(res_test)["success"] is True

    with patch("plugins.whatsapp.client.WhatsAppClient.send_message", return_value={"success": True, "recipient": "79991234567"}):
        res_send = whatsapp_send_message.invoke({"to": "+7 (999) 123-45-67", "message": "Привет!"})
        data = json.loads(res_send)
        assert data["success"] is True
        assert data["recipient"] == "79991234567"

