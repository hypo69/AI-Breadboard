# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Watcher CLI Utility
# =============================================================================
# Description:
#   Консольная утилита для проверки почты и мониторинга поступления писем
#   от заданного адресата с выводом уведомлений и отчетов.
#
# Usage:
#   python mail_watcher_cli.py --sender "boss@example.com" --check-once
#   python mail_watcher_cli.py --sender "boss@example.com" --interval 60 --toast
#   python mail_watcher_cli.py --test-connection
#
# File: mail_watcher_cli.py
# Package: .agents.skills.mail-watcher.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Консольная точка входа для навыка mail-watcher."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mail_watcher import (
    MailWatcher,
    load_mail_watcher_config,
)


def create_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Утилита мониторинга почтового ящика и оповещения о письмах от определенного адресата."
    )
    parser.add_argument(
        "--sender",
        "-s",
        type=str,
        default="",
        help="Email адрес или имя отправителя для отслеживания.",
    )
    parser.add_argument(
        "--account",
        "--mailbox",
        dest="account",
        type=str,
        default="",
        help="Имя или алиас почтового ящика из src/secrets/mailboxes.json (например, 'kazarinov', 'Сергей', 'маша').",
    )
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Выполнить разовую проверку ящика и завершить работу.",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=60,
        help="Интервал проверки ящика в секундах при циклическом мониторинге (по умолчанию 60).",
    )
    parser.add_argument(
        "--unread-only",
        action="store_true",
        default=True,
        help="Проверять только непрочитанные письма (по умолчанию включено).",
    )
    parser.add_argument(
        "--all-emails",
        dest="unread_only",
        action="store_false",
        help="Проверять все письма (включая прочитанные).",
    )
    parser.add_argument(
        "--mark-read",
        action="store_true",
        help="Помечать найденные письма как прочитанные на сервере.",
    )
    parser.add_argument(
        "--toast",
        action="store_true",
        help="Показывать всплывающее системное уведомление Windows Toast.",
    )
    parser.add_argument(
        "--whatsapp",
        "-w",
        type=str,
        default="",
        help="Номер телефона WhatsApp для пересылки содержимого писем (например, +79991234567).",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Проверить подключение к почтовому серверу и выйти.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывести результат в формате JSON.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="",
        help="Путь к файлу для сохранения отчета о найденных письмах.",
    )
    parser.add_argument(
        "--secrets",
        type=str,
        default="",
        help="Путь к пользовательскому файлу secrets.json.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="",
        help="IMAP сервер (переопределяет secrets.json).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="IMAP порт (по умолчанию 993).",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="",
        help="Имя пользователя/логин почты.",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="",
        help="Пароль приложения к почтовому ящику.",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="INBOX",
        help="Папка в почтовом ящике (по умолчанию INBOX).",
    )
    parser.add_argument(
        "--max-emails",
        type=int,
        default=50,
        help="Максимальное количество последних писем для анализа.",
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default="",
        help="Пользовательский путь к файлу сохранения состояния обработанных писем.",
    )
    return parser


def main() -> int:
    """Основная функция запуска CLI утилиты."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        cfg = load_mail_watcher_config(
            explicit_path=args.secrets or None,
            account=args.account or None,
            sender=args.sender,
            host=args.host or None,
            username=args.user or None,
            password=args.password or None,
            port=args.port,
            folder=args.folder or None,
            unread_only=args.unread_only,
            mark_as_read=args.mark_read,
            max_emails=args.max_emails,
            whatsapp_recipient=args.whatsapp or None,
            state_file=Path(args.state_file) if args.state_file else None,
        )
    except Exception as ex:
        print(f"❌ Ошибка конфигурации: {ex}", file=sys.stderr)
        return 1

    watcher = MailWatcher(cfg)

    # Режим проверки соединения
    if args.test_connection:
        result = watcher.test_connection()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get("success"):
                print(f"✅ Успешное подключение к {result.get('host')}! Папок обнаружено: {result.get('folders_count')}")
            else:
                print(f"❌ Ошибка подключения: {result.get('error')}", file=sys.stderr)
        return 0 if result.get("success") else 1

    # Режим разовой проверки
    if args.check_once or not args.interval:
        messages = watcher.check_messages(
            sender=args.sender or None,
            unread_only=args.unread_only,
            notify_toast=args.toast,
            forward_whatsapp=args.whatsapp or None,
        )

        msg_dicts = [m.to_dict() for m in messages]
        report = {
            "target_sender": args.sender or cfg.target_sender,
            "folder": cfg.folder,
            "found_count": len(messages),
            "messages": msg_dicts,
            "whatsapp_forwarded_to": args.whatsapp or cfg.whatsapp_recipient or None,
        }

        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            if messages:
                print(f"📬 Найдено писем от '{args.sender or cfg.target_sender}': {len(messages)}")
                if args.whatsapp or cfg.whatsapp_recipient:
                    print(f"📲 Письма пересланы в WhatsApp на номер: {args.whatsapp or cfg.whatsapp_recipient}")
                print("-" * 60)
                for m in messages:
                    print(m.format_alert())
                    print("-" * 60)
            else:
                print(f"ℹ️ Новых писем от '{args.sender or cfg.target_sender}' не обнаружено.")

        return 0

    # Режим циклического мониторинга
    print(f"🚀 Запуск фонового мониторинга для отправителя: '{args.sender or cfg.target_sender}'...")
    if args.whatsapp or cfg.whatsapp_recipient:
        print(f"📲 Включена пересылка в WhatsApp на номер: {args.whatsapp or cfg.whatsapp_recipient}")
    print(f"⏱️ Интервал проверки: {args.interval} сек. Нажмите Ctrl+C для остановки.")

    def on_message_found(msg):
        print("\n" + "=" * 60)
        print("🔔 ПОЛУЧЕНО НОВОЕ СООБЩЕНИЕ!")
        print(msg.format_alert())
        print("=" * 60 + "\n")

    try:
        watcher.watch_loop(
            sender=args.sender or None,
            interval=args.interval,
            callback=on_message_found,
            notify_toast=args.toast,
            forward_whatsapp=args.whatsapp or None,
        )
    except KeyboardInterrupt:
        print("\nМониторинг завершен.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
