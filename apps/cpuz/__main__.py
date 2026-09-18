# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CPU-Z Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа CLI для CPU-Z Processor App (python -m apps.cpuz).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.cpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для CPU-Z."""

from __future__ import annotations

import argparse
import json

from apps.cpuz.core.cpuz_service import CpuzService


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="CPU-Z Processor Diagnostic App")
    parser.add_argument("--report", action="store_true", help="Сгенерировать текстовый отчет CPU-Z")
    parser.add_argument("--server", action="store_true", help="Запустить выделенный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8122, help="Порт сервера (по умолчанию: 8122)")
    parser.add_argument("--json", action="store_true", help="Форматировать вывод в JSON")

    args = parser.parse_args()
    svc = CpuzService()

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.cpuz.router import init_router
        app = FastAPI(title="CPU-Z Diagnostic Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера CPU-Z на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.report:
        rep = svc.generate_report()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return

    print("=== CPU-Z PROCESSOR APP ===")
    if svc.is_available():
        print(f"Исполняемый файл: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("cpuz")
        print(f"Исполняемый файл: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --report или --server --port 8122")


if __name__ == "__main__":
    main()
