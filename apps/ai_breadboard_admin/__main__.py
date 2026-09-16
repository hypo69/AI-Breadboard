# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Breadboard Admin Application Main Entry Point
# =============================================================================
# Description:
#   Точка входа CLI для запуска терминального интерфейса (TUI), вывода статуса
#   системы или запуска автономного FastAPI сервера администрирования.
#
# Examples:
#   >>> python -m apps.ai_breadboard_admin --mode tui
#   >>> python -m apps.ai_breadboard_admin --mode server --port 8110
#   >>> python -m apps.ai_breadboard_admin --mode status
#
# File: __main__.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.ai_breadboard_admin.src import (
    AdminConfigManager,
    InstructionsManager,
    SourcesManager,
    UserAdminService,
)
from apps.ai_breadboard_admin.tui import run_admin_tui


def main() -> None:
    """Разбор аргументов командной строки и запуск выбранного режима."""
    parser = argparse.ArgumentParser(
        description="AI Breadboard Admin - Центральная панель управления и настроек",
    )
    parser.add_argument(
        "--mode",
        choices=["tui", "server", "status"],
        default="tui",
        help="Режим выполнения (по умолчанию: tui)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Хост сервера (для режима server)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8110,
        help="Порт сервера (для режима server)",
    )

    args = parser.parse_args()

    if args.mode == "status":
        cfg_mgr = AdminConfigManager()
        user_svc = UserAdminService()
        status_info = {
            "service": "ai_breadboard_admin",
            "rag": cfg_mgr.get_rag_config(),
            "web_search": cfg_mgr.get_web_search_config(),
            "users": user_svc.get_users_list().get("stats", {}),
        }
        print(json.dumps(status_info, indent=2, ensure_ascii=False))
        return

    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.ai_breadboard_admin.router import init_router

        app = FastAPI(title="AI Breadboard Admin Standalone API")
        app.include_router(init_router())
        print(f"Запуск автономного сервера AI Breadboard Admin на http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    # По умолчанию: Интерактивный TUI
    asyncio.run(run_admin_tui())


if __name__ == "__main__":
    main()
