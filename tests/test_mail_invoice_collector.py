# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Mail Invoice Collector Skill
# =============================================================================
# Description:
#   Комплексные модульные тесты для навыка mail-invoice-collector:
#   конфигурация подключения к почте, поиск писем со счетами,
#   мультиязычный парсинг (RU, EN, HE), формирование CSV и CLI.
#
# File: test_mail_invoice_collector.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модульные тесты для навыка сбора счетов-фактур из входящей почты в CSV."""

from __future__ import annotations

import csv
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
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "mail-invoice-collector"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from collector import MailInvoiceCollector
from invoice_parser import INVOICE_CSV_COLUMNS, InvoiceParser
from mail_client import MailAccountConfig, MailClient, decode_mime_header, load_mail_config
from src.skills.registry import SkillRegistry


@pytest.fixture
def mock_secrets_file(tmp_path: Path) -> Path:
    """Создает временный файл secrets.json для тестов."""
    secrets_data = {
        "host": "imap.testmail.com",
        "port": 993,
        "use_ssl": True,
        "username": "tester@testmail.com",
        "password": "secret_app_password_456",
        "folder": "INBOX",
    }
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps(secrets_data), encoding="utf-8")
    return secrets_file


def test_load_mail_config_from_file(mock_secrets_file: Path) -> None:
    """Проверка загрузки параметров подключения из файла secrets.json."""
    cfg = load_mail_config(mock_secrets_file)
    assert cfg.host == "imap.testmail.com"
    assert cfg.port == 993
    assert cfg.username == "tester@testmail.com"
    assert cfg.password == "secret_app_password_456"
    assert cfg.use_ssl is True
    assert cfg.folder == "INBOX"


def test_load_mail_config_validation() -> None:
    """Проверка валидации обязательных параметров конфигурации."""
    with pytest.raises(ValueError, match="host"):
        MailAccountConfig(host="", username="u", password="p")

    with pytest.raises(ValueError, match="username"):
        MailAccountConfig(host="h", username="", password="p")

    with pytest.raises(ValueError, match="password"):
        MailAccountConfig(host="h", username="u", password="")


def test_decode_mime_header() -> None:
    """Проверка корректного декодирования MIME-заголовков."""
    from email.header import Header

    encoded_ru = Header("Счет-фактура", "utf-8").encode()
    encoded_he = Header("חשבונית מס", "utf-8").encode()

    assert decode_mime_header(encoded_ru) == "Счет-фактура"
    assert decode_mime_header(encoded_he) == "חשבונית מס"
    assert decode_mime_header("Standard English Subject") == "Standard English Subject"
    assert decode_mime_header(None) == ""


@patch("imaplib.IMAP4_SSL")
def test_mail_client_test_connection_success(mock_imap: MagicMock) -> None:
    """Проверка успешного тестирования IMAP-подключения."""
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"'])

    cfg = MailAccountConfig(
        host="imap.example.com",
        username="user@example.com",
        password="secret_password",
    )
    client = MailClient(cfg)
    result = client.test_connection()

    assert result["success"] is True
    assert result["host"] == "imap.example.com"
    assert result["folders_count"] == 1
    mock_instance.login.assert_called_with("user@example.com", "secret_password")


@patch("imaplib.IMAP4_SSL")
def test_mail_client_test_connection_failure(mock_imap: MagicMock) -> None:
    """Проверка обработки ошибки при подключении к IMAP."""
    mock_imap.side_effect = ConnectionRefusedError("Connection refused")

    cfg = MailAccountConfig(host="imap.badhost.com", username="u", password="p")
    client = MailClient(cfg)
    result = client.test_connection()

    assert result["success"] is False
    assert "Connection refused" in result["error"]


def test_invoice_parser_multilingual() -> None:
    """Проверка мультиязычного извлечения реквизитов (RU, EN, HE)."""
    parser = InvoiceParser()

    # 1. Hebrew Invoice: חשבונית מס
    hebrew_text = """
    חברת אלפא בע"מ
    חשבונית מס / קבלה מספר: INV-HE-9988
    תאריך: 15/09/2026
    עוסק מורשה: 515887766
    פירוט: שירותי ייעוץ תוכנה
    סה"כ לתשלום: 2,450.00 ש"ח
    מע"מ: 355.00 ש"ח
    """
    res_he = parser.parse_text(hebrew_text)
    assert res_he["invoice_number"] == "INV-HE-9988"
    assert res_he["invoice_date"] == "15/09/2026"
    assert res_he["vendor_tax_id"] == "515887766"
    assert res_he["currency"] == "ILS"
    assert "2450.00" in res_he["total_amount"]
    assert "355.00" in res_he["tax_amount"]

    # 2. Russian Invoice: Счет-фактура
    russian_text = """
    Поставщик: ООО "Технологии Будущего"
    Счет-фактура № 741-RU от 12.08.2026
    ИНН 7701234567
    Наименование товара: Подписка на облачный сервер
    Итого к оплате: 15 000.00 руб
    В том числе НДС: 2 500.00
    """
    res_ru = parser.parse_text(russian_text)
    assert res_ru["invoice_number"] == "741-RU"
    assert res_ru["invoice_date"] == "12.08.2026"
    assert res_ru["vendor_tax_id"] == "7701234567"
    assert res_ru["currency"] == "RUB"
    assert "15000.00" in res_ru["total_amount"]
    assert "2500.00" in res_ru["tax_amount"]

    # 3. English Invoice: Tax Invoice
    english_text = """
    Vendor: Acme Cloud Services Inc.
    Tax Invoice Number: INV-2026-US44
    Date: 2026-07-20
    VAT ID: US99887766
    Description: Monthly GPU compute instance
    Total Amount: $1,200.50 USD
    Tax Amount: $120.00
    """
    res_en = parser.parse_text(english_text)
    assert res_en["invoice_number"] == "INV-2026-US44"
    assert res_en["invoice_date"] == "2026-07-20"
    assert res_en["vendor_tax_id"] == "US99887766"
    assert res_en["currency"] == "USD"
    assert "1200.50" in res_en["total_amount"]
    assert "120.00" in res_en["tax_amount"]


@patch("imaplib.IMAP4_SSL")
def test_collector_orchestration_and_csv(mock_imap: MagicMock, tmp_path: Path) -> None:
    """Проверка полного цикла работы коллектора с созданием CSV-файла."""
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"101"])

    # Создаем mock email сообщение со счетом
    msg = MIMEMultipart()
    msg["Subject"] = "חשבונית מס עבור חודש ספטמבר"
    msg["From"] = "billing@provider.il"
    msg["Date"] = "Wed, 16 Sep 2026 10:00:00 +0300"
    body = "שלום רב,\nמצורפת חשבונית מס מספר 554433 סה\"כ לתשלום: 800.00 ש\"ח\nתודה."
    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw_msg_bytes = msg.as_bytes()
    mock_instance.fetch.return_value = ("OK", [(b"101 (RFC822 {100})", raw_msg_bytes)])

    cfg = MailAccountConfig(
        host="imap.testserver.com",
        username="user@testserver.com",
        password="password123",
    )
    collector = MailInvoiceCollector(cfg)
    output_csv = tmp_path / "invoices_result.csv"

    result = collector.run(
        output_csv=output_csv,
        max_emails=10,
        download_attachments=False,
    )

    assert result["success"] is True
    assert result["invoices_extracted"] == 1
    assert output_csv.exists()

    # Проверяем содержимое созданного CSV файла
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["invoice_number"] == "554433"
        assert rows[0]["currency"] == "ILS"
        assert "800.00" in rows[0]["total_amount"]
        assert rows[0]["email_from"] == "billing@provider.il"


def test_skill_registry_discovers_mail_invoice_collector() -> None:
    """Проверка обнаружения навыка mail-invoice-collector реестром навыков."""
    registry = SkillRegistry()
    skill = registry.get("mail-invoice-collector")
    assert skill.name == "mail-invoice-collector"
    assert "invoice" in skill.description.lower()
    assert "ru" in skill.descriptions_i18n
    assert "חשבונית" in skill.instructions or "invoices" in skill.instructions


@patch("imaplib.IMAP4_SSL")
def test_cli_collect_invoices(mock_imap: MagicMock, mock_secrets_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверка запуска CLI утилиты collect_invoices_cli.py."""
    import collect_invoices_cli

    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance
    mock_instance.select.return_value = ("OK", [b"1"])
    mock_instance.search.return_value = ("OK", [b"201"])

    msg = MIMEMultipart()
    msg["Subject"] = "Invoice # INV-8899"
    msg["From"] = "service@cloud.com"
    msg["Date"] = "Tue, 15 Sep 2026 12:00:00 +0000"
    msg.attach(MIMEText("Your invoice # INV-8899 total amount: $500.00 USD", "plain", "utf-8"))
    mock_instance.fetch.return_value = ("OK", [(b"201 (RFC822 {100})", msg.as_bytes())])

    output_csv = tmp_path / "cli_out.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "collect_invoices_cli.py",
            "--secrets", str(mock_secrets_file),
            "--output", str(output_csv),
            "--json",
        ],
    )

    exit_code = collect_invoices_cli.main()
    assert exit_code == 0
    assert output_csv.exists()
