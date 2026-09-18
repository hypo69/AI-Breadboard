# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Software Transparency Scanner Standalone CLI / TUI
# =============================================================================
# Description:
#   Автономный запуск сканера прозрачности ПО с поддержкой rich TUI и CLI аргументов.
#
# Examples:
#   $ python -m apps.software_transparency_scanner --scan
#   $ python -m apps.software_transparency_scanner --serve
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для автономного запуска AI Software Transparency Scanner."""

import argparse
import asyncio
import sys
import uvicorn
from fastapi import FastAPI

from apps.software_transparency_scanner.core.inventory import SoftwareInventory
from apps.software_transparency_scanner.core.storage_analyzer import StorageAnalyzer
from apps.software_transparency_scanner.core.config_inspector import ConfigInspector
from apps.software_transparency_scanner.core.network_tracker import NetworkTracker
from apps.software_transparency_scanner.router import init_router


def run_cli_scan():
    """Выполняет консольное сканирование и выводит результат."""
    print("\\n======================================================")
    print(" 🔍 AI Software Transparency Scanner (Windows CLI)")
    print("======================================================\\n")

    inv = SoftwareInventory()
    storage = StorageAnalyzer()
    cfg_insp = ConfigInspector()
    net = NetworkTracker()

    apps = inv.scan_installed_software()
    print(f"Найдено установленных программ: {len(apps)}\\n")

    for app in apps[:10]:
        dirs = storage.discover_storage_for_app(app)
        cfgs = cfg_insp.inspect_directories_for_configs(dirs)
        endpoints = net.track_app_network(app, cfgs)

        print(f"📦 [{app.name}] v{app.version} ({app.publisher})")
        print(f"   Путь: {app.install_location or 'Не указан'}")
        print(f"   Хранилища: {len(dirs)} каталогов, Конфигов: {len(cfgs)}, Сетевых узлов: {len(endpoints)}")
        if cfgs:
            print(f"   Пример конфига: {cfgs[0].display_path} ({cfgs[0].format})")
        print("-" * 54)


def main():
    parser = argparse.ArgumentParser(description="AI Software Transparency Scanner CLI")
    parser.add_argument("--serve", action="store_true", help="Запустить локальный REST сервер на порту 8115")
    parser.add_argument("--scan", action="store_true", help="Выполнить быстрое сканирование в терминале")
    parser.add_argument("--port", type=int, default=8115, help="Порт сервера (по умолчанию 8115)")

    args = parser.parse_args()

    if args.serve:
        app = FastAPI(title="AI Software Transparency Scanner")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера на http://localhost:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
    else:
        run_cli_scan()


if __name__ == "__main__":
    main()
