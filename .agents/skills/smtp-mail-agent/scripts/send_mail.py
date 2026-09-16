# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Send SMTP Mail CLI
# =============================================================================
# Description:
#   CLI-утилита для отправки писем через SMTP с поддержкой HTML, вложений,
#   копий (CC/BCC) и загрузки учетных данных из secrets.json.
#
# Examples:
#   >>> python send_mail.py --to user@example.com --subject "Тест" --body "Привет"
#   >>> python send_mail.py --to user@example.com --subject "Отчет" --html "<h1>Отчет</h1>" --attach report.pdf --json
#
# File: send_mail.py
# Package: .agents.skills.smtp-mail-agent.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""CLI-утилита отправки электронной почты через SMTP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Добавление родительской директории в sys.path при прямом запуске
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from smtp_core import SmtpClient, load_smtp_config


def main() -> int:
    """Точка входа CLI для отправки письма.

    Returns:
        int: Код возврата процесса (0 - успех, 1 - ошибка).
    """
    parser = argparse.ArgumentParser(
        description="Отправка письма через SMTP сервер с использованием secrets.json"
    )
    parser.add_argument(
        "--to",
        "-t",
        action="append",
        required=True,
        help="Email адрес получателя (можно указывать несколько раз или через запятую)",
    )
    parser.add_argument(
        "--subject",
        "-s",
        required=True,
        help="Тема письма",
    )
    parser.add_argument(
        "--body",
        "-b",
        default="",
        help="Текстовое тело письма (Plain Text)",
    )
    parser.add_argument(
        "--body-file",
        type=str,
        default=None,
        help="Путь к файлу с текстом письма",
    )
    parser.add_argument(
        "--html",
        default=None,
        help="HTML содержимое письма",
    )
    parser.add_argument(
        "--html-file",
        type=str,
        default=None,
        help="Путь к файлу с HTML содержимым письма",
    )
    parser.add_argument(
        "--attach",
        "-a",
        action="append",
        default=[],
        help="Путь к прикрепляемому файлу (можно указывать несколько раз)",
    )
    parser.add_argument(
        "--cc",
        action="append",
        default=[],
        help="Адрес копии (CC)",
    )
    parser.add_argument(
        "--bcc",
        action="append",
        default=[],
        help="Адрес скрытой копии (BCC)",
    )
    parser.add_argument(
        "--secrets",
        type=str,
        default=None,
        help="Путь к файлу secrets.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывод результата в формате JSON",
    )

    args = parser.parse_args()

    # Разворачивание списков адресов, если они переданы через запятую
    def flatten_addresses(items: list[str]) -> list[str]:
        result = []
        for item in items:
            for part in item.split(","):
                part = part.strip()
                if part:
                    result.append(part)
        return result

    to_addrs = flatten_addresses(args.to)
    cc_addrs = flatten_addresses(args.cc)
    bcc_addrs = flatten_addresses(args.bcc)

    # Чтение тела письма из файлов при необходимости
    body_text = args.body
    if args.body_file:
        file_path = Path(args.body_file).resolve()
        if not file_path.is_file():
            err_res = {"status": "error", "message": f"Файл с текстом письма не найден: {file_path}"}
            print(json.dumps(err_res, ensure_ascii=False, indent=2) if args.json else f"❌ {err_res['message']}")
            return 1
        body_text = file_path.read_text(encoding="utf-8")

    body_html = args.html
    if args.html_file:
        html_path = Path(args.html_file).resolve()
        if not html_path.is_file():
            err_res = {"status": "error", "message": f"Файл HTML не найден: {html_path}"}
            print(json.dumps(err_res, ensure_ascii=False, indent=2) if args.json else f"❌ {err_res['message']}")
            return 1
        body_html = html_path.read_text(encoding="utf-8")

    try:
        config = load_smtp_config(args.secrets)
        client = SmtpClient(config)
        result = client.send_mail(
            to=to_addrs,
            subject=args.subject,
            body_text=body_text,
            body_html=body_html,
            attachments=args.attach,
            cc=cc_addrs,
            bcc=bcc_addrs,
        )
    except Exception as exc:
        result = {
            "status": "error",
            "message": f"Ошибка отправки: {exc}",
            "error_type": type(exc).__name__,
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("status") == "success":
            print("✅ Письмо успешно отправлено!")
            print(f"   Кому: {', '.join(result.get('to', []))}")
            print(f"   Тема: {result.get('subject')}")
            print(f"   Message-ID: {result.get('message_id')}")
            if result.get("attachments"):
                print(f"   Вложения: {', '.join(result.get('attachments', []))}")
        else:
            print(f"❌ Ошибка отправки письма: {result.get('message')}")
            if "error_type" in result:
                print(f"   Тип ошибки: {result.get('error_type')}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
