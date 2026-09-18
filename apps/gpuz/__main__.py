# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU-Z Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа CLI для GPU-Z Graphics App (python -m apps.gpuz).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.gpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для GPU-Z."""

from __future__ import annotations

import argparse
import json

from apps.gpuz.core.gpuz_service import GpuzService


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="GPU-Z Graphics Diagnostic App")
    parser.add_argument("--sensors", action="store_true", help="Прочитать данные из лога сенсоров GPU-Z")
    parser.add_argument("--log-path", type=str, help="Путь к файлу лога GPU-Z Sensor Log.txt")
    parser.add_argument("--server", action="store_true", help="Запустить выделенный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8123, help="Порт сервера (по умолчанию: 8123)")
    parser.add_argument("--json", action="store_true", help="Форматировать вывод в JSON")

    args = parser.parse_args()
    svc = GpuzService()

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.gpuz.router import init_router
        app = FastAPI(title="GPU-Z Diagnostic Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера GPU-Z на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.sensors:
        sens = svc.parse_sensor_log(args.log_path)
        print(json.dumps(sens, ensure_ascii=False, indent=2))
        return

    print("=== GPU-Z GRAPHICS APP ===")
    if svc.is_available():
        print(f"Исполняемый файл: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("gpuz")
        print(f"Исполняемый файл: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --sensors или --server --port 8123")


if __name__ == "__main__":
    main()
