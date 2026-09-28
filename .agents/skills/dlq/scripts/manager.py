"""CLI Менеджер для выполнения операций над Dead Letter Queue (DLQ)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import DLQStorage
from tui import run_dlq_tui


def main() -> None:
    """Главная точка входа для консольных команд управления DLQ."""
    parser = argparse.ArgumentParser(
        description="DLQ CLI Manager — управление тупиковой очередью сообщений и вызовом TUI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда: push
    push_parser = subparsers.add_parser("push", help="Добавить сбойное сообщение в DLQ")
    push_parser.add_argument("--source", required=True, help="Источник ошибки (например, 'gemini-cli', 'subagent-research')")
    push_parser.add_argument("--error", required=True, help="Текст или traceback ошибки")
    push_parser.add_argument("--payload", default="{}", help="Контекст/payload в формате JSON строки")

    # Команда: list
    list_parser = subparsers.add_parser("list", help="Вывести список записей DLQ")
    list_parser.add_argument("--status", help="Фильтр по статусу ('PENDING', 'RETRYING', 'RESOLVED', 'FAILED')")
    list_parser.add_argument("--source", help="Фильтр по источнику")
    list_parser.add_argument("--limit", type=int, default=50, help="Лимит строк")
    list_parser.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # Команда: retry
    retry_parser = subparsers.add_parser("retry", help="Пометить сообщение для повторной обработки (retry)")
    retry_parser.add_argument("--id", type=int, required=True, help="ID сообщения DLQ")

    # Команда: set-status
    status_parser = subparsers.add_parser("set-status", help="Изменить статус сообщения DLQ")
    status_parser.add_argument("--id", type=int, required=True, help="ID сообщения DLQ")
    status_parser.add_argument("--status", required=True, choices=["PENDING", "RETRYING", "RESOLVED", "FAILED"], help="Новый статус")

    # Команда: purge
    purge_parser = subparsers.add_parser("purge", help="Очистить записи DLQ")
    purge_parser.add_argument("--status", help="Удалить только записи с конкретным статусом")

    # Команда: tui
    tui_parser = subparsers.add_parser("tui", help="Запустить интерактивный TUI интерфейс")
    tui_parser.add_argument("--once", action="store_true", help="Отобразить один кадр TUI и выйти")

    args = parser.parse_args()
    storage = DLQStorage()

    if args.command == "push":
        try:
            payload_data = json.loads(args.payload)
        except json.JSONDecodeError:
            payload_data = {"raw_payload": args.payload}
        msg_id = storage.push(source=args.source, error_message=args.error, payload=payload_data)
        print(f"[SUCCESS] Сообщение успешно добавлено в DLQ (ID: {msg_id})")

    elif args.command == "list":
        messages = storage.list_all(status=args.status, source=args.source, limit=args.limit)
        if args.json:
            print(json.dumps(messages, ensure_ascii=False, indent=2))
        else:
            if not messages:
                print("Очередь DLQ пуста.")
                return
            print(f"{'ID':<6} {'STATUS':<10} {'SOURCE':<18} {'RETRIES':<8} {'ERROR'}")
            print("─" * 70)
            for m in messages:
                err_summary = m['error_message'][:35] + ("..." if len(m['error_message']) > 35 else "")
                print(f"{m['id']:<6} {m['status']:<10} {m['source']:<18} {m['retry_count']:<8} {err_summary}")

    elif args.command == "retry":
        success = storage.increment_retry(args.id)
        if success:
            print(f"[SUCCESS] Счетчик retry увеличен, статус записи ID {args.id} изменен на 'RETRYING'")
        else:
            print(f"[ERROR] Запись с ID {args.id} не найдена.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "set-status":
        success = storage.update_status(args.id, args.status)
        if success:
            print(f"[SUCCESS] Статус записи ID {args.id} изменен на '{args.status.upper()}'")
        else:
            print(f"[ERROR] Запись с ID {args.id} не найдена.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "purge":
        count = storage.purge(status=args.status)
        print(f"[SUCCESS] Удалено записей из DLQ: {count}")

    elif args.command == "tui":
        run_dlq_tui(once=args.once, storage=storage)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
