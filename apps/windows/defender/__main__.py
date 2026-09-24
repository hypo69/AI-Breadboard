# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа для автономного запуска приложения Windows Defender
#   (python -m apps.windows.defender). Поддерживает запуск консольного дашборда,
#   сканирования системы, обновления баз сигнатур и выделенного uvicorn сервера.
#
# Examples:
#   python -m apps.windows.defender
#   python -m apps.windows.defender --scan quick
#   python -m apps.windows.defender --update
#   python -m apps.windows.defender --server --port 8113
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.defender
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа для запуска Windows Defender & Security Center."""

from __future__ import annotations

import argparse
import sys

from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.models import ScanRequest, ScanType
from apps.windows.defender.tui import DefenderTUI


def main() -> None:
    """Основная функция запуска CLI/TUI Windows Defender."""
    parser = argparse.ArgumentParser(description="Microsoft Defender & AI Security Diagnostic Center")
    parser.add_argument("--scan", choices=["quick", "full", "custom", "offline"], help="Запуск антивирусного сканирования")
    parser.add_argument("--path", type=str, help="Путь для выборочного сканирования (custom)")
    parser.add_argument("--update", action="store_true", help="Обновление антивирусных баз сигнатур")
    parser.add_argument("--server", action="store_true", help="Запуск выделенного HTTP API сервера")
    parser.add_argument("--port", type=int, default=8113, help="Порт для выделенного сервера (по умолчанию 8113)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Хост для выделенного сервера")

    args = parser.parse_args()

    svc = DefenderService()

    if args.update:
        print("Обновление баз сигнатур Microsoft Defender...")
        resp = svc.update_signatures()
        print(f"Результат: {resp.message}")
        if resp.output:
            print(resp.output)
        return

    if args.scan:
        st_map = {
            "quick": ScanType.QUICK,
            "full": ScanType.FULL,
            "custom": ScanType.CUSTOM,
            "offline": ScanType.OFFLINE,
        }
        req = ScanRequest(scan_type=st_map[args.scan], target_path=args.path)
        print(f"Запуск сканирования ({args.scan})...")
        resp = svc.trigger_scan(req)
        print(f"Результат: {resp.message}")
        if resp.output:
            print(resp.output)
        return

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.defender.router import init_router

        app = FastAPI(title="Windows Defender Security API", version="1.0.0")
        app.include_router(init_router())
        print(f"Запуск сервера Windows Defender API на http://{args.host}:{args.port} ...")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    # По умолчанию отображаем TUI дашборд
    tui = DefenderTUI()
    tui.render_dashboard()


if __name__ == "__main__":
    main()
