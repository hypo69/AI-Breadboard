# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Invoice Collector CLI Entry Point
# =============================================================================
# Description:
#   Консольная утилита для подключения к почте, поиска входящих счетов
#   (invoices, חשבונית) и экспорта в CSV.
#
# Examples:
#   $ python collect_invoices_cli.py --test-only
#   $ python collect_invoices_cli.py --output "data/invoices.csv"
#   $ python collect_invoices_cli.py --host imap.gmail.com --user me@gmail.com --password "secret"
#
# File: collect_invoices_cli.py
# Package: .agents.skills.mail-invoice-collector.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""CLI интерфейс для сбора счетов-фактур из входящей почты."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Добавляем родительские пути при прямом запуске
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from collector import MailInvoiceCollector
from mail_client import MailClient, load_mail_config, load_mail_config_central


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Сбор счетов-фактур (invoices, חשבונית) из почты в CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--account", type=str, help="Имя или алиас ящика из src/secrets/mailboxes.json")
    parser.add_argument("--host", type=str, help="Хост IMAP-сервера (напр. imap.gmail.com)")
    parser.add_argument("--port", type=int, default=None, help="Порт IMAP (по умолчанию 993)")
    parser.add_argument("--user", "--username", dest="username", type=str, help="Имя пользователя / Email")
    parser.add_argument("--password", type=str, help="Пароль / App Password")
    parser.add_argument("--folder", type=str, default="INBOX", help="Папка почтового ящика")
    parser.add_argument("--secrets", type=str, help="Путь к файлу secrets.json")
    parser.add_argument("--output", "--csv", dest="output_csv", type=str, help="Путь к итоговому CSV файлу")
    parser.add_argument("--max-emails", type=int, default=100, help="Максимальное количество писем для проверки")
    parser.add_argument("--attachments-dir", type=str, help="Директория для сохранения вложений")
    parser.add_argument("--keywords", nargs='+', help="Список ключевых слов для поиска через пробел")
    parser.add_argument("--test-only", action="store_true", help="Только проверить подключение к почте")
    parser.add_argument("--json", action="store_true", help="Вывод результатов в формате JSON")
    return parser.parse_args()


def main() -> int:
    """Главная точка входа CLI."""
    args = parse_args()

    try:
        if args.account:
            config = load_mail_config_central(args.account)
        else:
            config = load_mail_config(
                explicit_path=args.secrets,
                host=args.host,
                username=args.username,
                password=args.password,
                port=args.port,
                folder=args.folder,
            )
    except Exception as ex:
        if args.json:
            print(json.dumps({"success": False, "error": str(ex)}, ensure_ascii=False))
        else:
            print(f"❌ Ошибка конфигурации: {ex}")
            print("💡 Укажите параметры через аргументы CLI (--host, --user, --password) или создайте secrets.json")
        return 1

    if args.test_only:
        client = MailClient(config)
        res = client.test_connection()
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if res.get("success"):
                print(f"✅ Успешное подключение к {res.get('host')}:{res.get('port')} под пользователем {res.get('username')}")
                print(f"📁 Доступно папок: {res.get('folders_count')}")
            else:
                print(f"❌ Ошибка подключения: {res.get('error')}")
        return 0 if res.get("success") else 1

    collector = MailInvoiceCollector(config)
    result = collector.run(
        output_csv=args.output_csv,
        max_emails=args.max_emails,
        attachments_dir=args.attachments_dir,
        keywords=args.keywords,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 70)
        print("📧 РЕЗУЛЬТАТЫ СБОРА СЧЕТОВ-ФАКТУР ИЗ ПОЧТЫ")
        print("=" * 70)
        print(f"Сервер:             {result.get('host')}")
        print(f"Папка:              {result.get('folder')}")
        print(f"Найдено писем:      {result.get('emails_matched')}")
        print(f"Извлечено счетов:   {result.get('invoices_extracted')}")
        print(f"Итоговый CSV:       {result.get('csv_path')}")
        if result.get("attachments_dir"):
            print(f"Папка вложений:     {result.get('attachments_dir')}")
        print("-" * 70)

        records = result.get("records", [])
        if records:
            print(f"{'№':<4} | {'Дата':<10} | {'Номер счета':<15} | {'Поставщик':<25} | {'Сумма':<10} | {'Валюта':<6}")
            print("-" * 75)
            for idx, r in enumerate(records, 1):
                d = (r.get("invoice_date") or r.get("email_date") or "")[:10]
                num = (r.get("invoice_number") or "N/A")[:14]
                vendor = (r.get("vendor_name") or r.get("email_from") or "N/A")[:24]
                amt = (r.get("total_amount") or "0")[:9]
                curr = r.get("currency") or ""
                print(f"{idx:<4} | {d:<10} | {num:<15} | {vendor:<25} | {amt:<10} | {curr:<6}")
        else:
            print("Счетов-фактур во входящих письмах не обнаружено.")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
