# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Main Entry Point
# =============================================================================
# Description:
#   Точка входа CLI и запуск автономного FastAPI сервера для приложения
#   Windows Startup & Autorun Auditor.
#
# Examples:
#   $ python -m apps.windows_startup_auditor --audit
#   $ python -m apps.windows_startup_auditor --json
#   $ python -m apps.windows_startup_auditor --mode server --port 8112
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI и standalone-сервера Windows Startup Auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.logger import logger
from apps.windows_startup_auditor.core.auditor import StartupAuditor
from apps.windows_startup_auditor.core.manager import StartupManager
from apps.windows_startup_auditor.tui import StartupAuditorTUI


def run_cli() -> None:
    """Обработка аргументов командной строки и запуск приложения."""
    parser = argparse.ArgumentParser(
        description="Windows Startup & Autorun Auditor — аудит всех точек автозагрузки и персистентности Windows",
    )
    parser.add_argument("--audit", action="store_true", help="Запустить аудит и отобразить дашборд в TUI")
    parser.add_argument("--json", action="store_true", help="Вывести отчет аудита в формате JSON")
    parser.add_argument("--csv", action="store_true", help="Вывести отчет аудита в формате CSV")
    parser.add_argument("--export", type=str, help="Путь к файлу для сохранения отчета (.json или .csv)")
    parser.add_argument("--mode", type=str, choices=["cli", "server"], default="cli", help="Режим работы (cli или server)")
    parser.add_argument("--port", type=int, default=8112, help="Порт для запуска автономного FastAPI сервера")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Хост для запуска сервера")

    args = parser.parse_args()

    # Режим standalone сервера
    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.windows_startup_auditor.router import init_router

        app = FastAPI(
            title="Windows Startup Auditor API",
            description="Standalone REST API для аудита и управления автозагрузкой Windows",
            version="1.0.0",
        )
        app.include_router(init_router())

        logger.info(f"Запуск Windows Startup Auditor сервера на http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    # Обработка экспорта или вывода
    auditor = StartupAuditor()
    manager = StartupManager()
    report = auditor.run_audit()

    if args.export:
        target = Path(args.export)
        if target.suffix.lower() == ".csv":
            manager.export_to_csv(report, target)
        else:
            manager.export_to_json(report, target)
        print(f"Отчет успешно сохранен в: {target}")
        return

    if args.json:
        print(manager.export_to_json(report))
        return

    if args.csv:
        print(manager.export_to_csv(report))
        return

    # По умолчанию — красивый TUI дашборд
    tui = StartupAuditorTUI(auditor=auditor)
    tui.render_dashboard()


if __name__ == "__main__":
    run_cli()
