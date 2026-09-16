# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SMTP Connection Diagnostics CLI
# =============================================================================
# Description:
#   CLI-утилита для проверки подключения и аутентификации на SMTP-сервере
#   с использованием учетных данных из secrets.json.
#
# Examples:
#   >>> python test_connection.py
#   >>> python test_connection.py --secrets ../secrets.json --json
#
# File: test_connection.py
# Package: .agents.skills.smtp-mail-agent.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""CLI-утилита проверки соединения с SMTP-сервером."""

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
    """Точка входа CLI для тестирования SMTP-соединения.

    Returns:
        int: Код возврата процесса (0 - успех, 1 - ошибка).
    """
    parser = argparse.ArgumentParser(
        description="Проверка доступности и авторизации SMTP-сервера по конфигурации из secrets.json"
    )
    parser.add_argument(
        "--secrets",
        "-s",
        type=str,
        default=None,
        help="Путь к файлу secrets.json (по умолчанию ищется в папке навыка)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывод результата строго в формате JSON",
    )

    args = parser.parse_args()

    try:
        config = load_smtp_config(args.secrets)
        client = SmtpClient(config)
        result = client.test_connection()
    except Exception as exc:
        result = {
            "status": "error",
            "message": f"Ошибка инициализации конфигурации: {exc}",
            "error_type": type(exc).__name__,
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("status") == "success":
            print(f"✅ [OK] {result.get('message')}")
            print(f"   Сервер: {result.get('host')}:{result.get('port')}")
            print(f"   Пользователь: {result.get('authenticated_user')}")
            print(f"   TLS: {result.get('tls_enabled')}, SSL: {result.get('ssl_enabled')}")
        else:
            print(f"❌ [FAIL] {result.get('message')}")
            if "error_type" in result:
                print(f"   Тип ошибки: {result.get('error_type')}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
