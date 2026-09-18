# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 Standalone CLI & Runner
# =============================================================================
# Description:
#   Точка входа для запуска AIDA64 Diagnostic App (python -m apps.aida64).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.aida64
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для запуска приложения AIDA64."""

from __future__ import annotations

import argparse
import json
import sys

from apps.aida64.core.aida64_service import Aida64Service


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="AIDA64 Diagnostic App")
    parser.add_argument("--sensors", action="store_true", help="Вывести текущие показания сенсоров")
    parser.add_argument("--report", choices=["ALL", "HW", "SW", "SUM"], help="Сгенерировать отчет через CLI")
    parser.add_argument("--server", action="store_true", help="Запустить автономный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8120, help="Порт сервера (по умолчанию: 8120)")
    parser.add_argument("--json", action="store_true", help="Форматировать вывод в JSON")

    args = parser.parse_args()
    svc = Aida64Service()

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.aida64.router import init_router
        app = FastAPI(title="AIDA64 Diagnostic Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера AIDA64 на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.sensors:
        sensors = svc.get_live_sensors()
        if args.json:
            print(json.dumps(sensors, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== ПОКАЗАНИЯ ДАТЧИКОВ AIDA64 ({len(sensors)}) ===")
            for s in sensors:
                print(f" • [{s['type']}] {s['label']}: {s['value']} {s['unit']}")
        return

    if args.report:
        print(f"Генерация отчета AIDA64 ({args.report})...")
        rep = svc.generate_report(report_type=args.report)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return

    print("=== AIDA64 DIAGNOSTIC APP ===")
    print(f"Статус Shared Memory: {'🟢 Активна' if svc.is_running() else '⚪ Неактивна'}")
    if svc.is_binary_available():
        print(f"Исполняемый файл: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("aida64")
        print(f"Исполняемый файл: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --sensors, --report HW или --server --port 8120")


if __name__ == "__main__":
    main()
