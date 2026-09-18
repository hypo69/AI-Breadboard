# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HWiNFO Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа для запуска HWiNFO Diagnostic App (python -m apps.hwinfo).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.hwinfo
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для HWiNFO."""

from __future__ import annotations

import argparse
import json

from apps.hwinfo.core.hwinfo_service import HwinfoService


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="HWiNFO Diagnostic App")
    parser.add_argument("--sensors", action="store_true", help="Собрать сенсоры HWiNFO")
    parser.add_argument("--inventory", action="store_true", help="Собрать JSON инвентарь оборудования")
    parser.add_argument("--server", action="store_true", help="Запустить выделенный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8121, help="Порт сервера (по умолчанию: 8121)")
    parser.add_argument("--json", action="store_true", help="Форматировать вывод в JSON")

    args = parser.parse_args()
    svc = HwinfoService()

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.hwinfo.router import init_router
        app = FastAPI(title="HWiNFO Diagnostic Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера HWiNFO на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.sensors:
        sensors = svc.get_live_sensors()
        print(json.dumps(sensors, ensure_ascii=False, indent=2))
        return

    if args.inventory:
        inv = svc.generate_json_report()
        print(json.dumps(inv, ensure_ascii=False, indent=2))
        return

    print("=== HWiNFO DIAGNOSTIC APP ===")
    print(f"Статус Shared Memory: {'🟢 Активна' if svc.is_running() else '⚪ Неактивна'}")
    if svc.is_binary_available():
        print(f"Исполняемый файл: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("hwinfo")
        print(f"Исполняемый файл: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --sensors, --inventory или --server --port 8121")


if __name__ == "__main__":
    main()
