# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: smartmontools Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа CLI для smartmontools Diagnostic App (python -m apps.smartmontools).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.smartmontools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для smartmontools."""

from __future__ import annotations

import argparse
import json

from apps.smartmontools.core.smartctl_service import SmartctlService


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="smartmontools Storage Diagnostic App")
    parser.add_argument("--scan", action="store_true", help="Сканировать подключенные накопители")
    parser.add_argument("--device", type=str, help="Получить SMART диагностику по диску (напр. /dev/sda или /dev/nvme0)")
    parser.add_argument("--server", action="store_true", help="Запустить выделенный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8124, help="Порт сервера (по умолчанию: 8124)")
    parser.add_argument("--json", action="store_true", help="Форматировать вывод в JSON")

    args = parser.parse_args()
    svc = SmartctlService()

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.smartmontools.router import init_router
        app = FastAPI(title="smartmontools Diagnostic Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера smartmontools на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.scan:
        devs = svc.scan_devices()
        print(json.dumps(devs, ensure_ascii=False, indent=2))
        return

    if args.device:
        info = svc.get_device_health(args.device)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print("=== SMARTMONTOOLS DIAGNOSTIC APP ===")
    if svc.is_available():
        print(f"Исполняемый файл smartctl: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("smartmontools")
        print(f"Исполняемый файл smartctl: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --scan, --device /dev/sda или --server --port 8124")


if __name__ == "__main__":
    main()
