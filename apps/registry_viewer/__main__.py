# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer Main Entry Point
# =============================================================================
# Description:
#   Точка входа CLI и запуск автономного FastAPI сервера для приложения
#   Windows Registry Viewer.
#
# Examples:
#   $ python -m apps.registry_viewer --bookmarks
#   $ python -m apps.registry_viewer --bookmark startup_run
#   $ python -m apps.registry_viewer --view "HKLM\SOFTWARE\Microsoft\Windows"
#   $ python -m apps.registry_viewer --search "Windows" --hive HKLM
#   $ python -m apps.registry_viewer --mode server --port 8114
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI и standalone-сервера Windows Registry Viewer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logger import logger
from apps.registry_viewer.models import RegistryKeyDetailsDTO
from apps.registry_viewer.viewer import RegistryViewer
from apps.registry_viewer.tui import RegistryViewerTUI


def run_cli() -> None:
    """Обработка аргументов командной строки и запуск приложения."""
    parser = argparse.ArgumentParser(
        description="Windows Registry Viewer — безопасный просмотр, аудит и поиск по реестру Windows",
    )
    parser.add_argument("--bookmarks", action="store_true", help="Отобразить список системных закладок")
    parser.add_argument("--bookmark", type=str, help="Открыть раздел по ID закладки (например, startup_run, services, environment)")
    parser.add_argument("--view", type=str, help="Путь к разделу для просмотра (например, 'HKLM\\SOFTWARE' или 'HKCU\\Software')")
    parser.add_argument("--hive", type=str, default="HKEY_LOCAL_MACHINE", help="Корневая ветка реестра (HKLM, HKCU, HKCR, HKU, HKCC)")
    parser.add_argument("--path", type=str, default="", help="Относительный путь к подразделу")
    parser.add_argument("--search", type=str, help="Поисковый запрос по ключам и значениям")
    parser.add_argument("--max-results", type=int, default=50, help="Максимальное количество результатов поиска")
    parser.add_argument("--json", action="store_true", help="Вывести результат в формате JSON")
    parser.add_argument("--csv", action="store_true", help="Вывести параметры в формате CSV")
    parser.add_argument("--export", type=str, help="Сохранить результат в файл (.json или .csv)")
    parser.add_argument("--mode", type=str, choices=["cli", "server"], default="cli", help="Режим работы (cli или server)")
    parser.add_argument("--port", type=int, default=8114, help="Порт для standalone FastAPI сервера")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Хост для запуска сервера")

    args = parser.parse_args()

    # Режим standalone FastAPI сервера
    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.registry_viewer.router import init_router

        app = FastAPI(
            title="Windows Registry Viewer API",
            description="Standalone REST API для безопасного просмотра и поиска по реестру Windows",
            version="1.0.0",
        )
        app.include_router(init_router())

        logger.info(f"Запуск Windows Registry Viewer сервера на http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    viewer = RegistryViewer()
    tui = RegistryViewerTUI(viewer=viewer)

    # 1. Показ закладок
    if args.bookmarks:
        tui.render_bookmarks()
        return

    # 2. Поиск по реестру
    if args.search:
        target_hive = args.hive
        target_path = args.path or "SOFTWARE"
        search_res = viewer.search(
            query=args.search,
            hive=target_hive,
            path=target_path,
            max_results=args.max_results,
        )
        if args.json:
            print(search_res.model_dump_json(indent=2))
        else:
            tui.render_search_results(search_res)
        return

    # 3. Определение ветки и пути для просмотра
    target_hive = args.hive
    target_path = args.path

    if args.bookmark:
        bm = viewer.get_bookmark_by_id(args.bookmark)
        if not bm:
            print(f"Ошибка: Закладка '{args.bookmark}' не найдена. Используйте --bookmarks для списка.")
            sys.exit(1)
        target_hive = bm.hive
        target_path = bm.path
    elif args.view:
        parts = args.view.split("\\", 1)
        target_hive = parts[0]
        target_path = parts[1] if len(parts) > 1 else ""

    # Если ничего конкретного не указано и это просто запуск без аргументов — покажем закладки и базовый HKLM
    if not args.view and not args.bookmark and not args.path:
        tui.render_bookmarks()
        target_hive = "HKEY_LOCAL_MACHINE"
        target_path = "SOFTWARE"

    try:
        key_details = viewer.read_key(hive=target_hive, path=target_path)
    except Exception as e:
        print(f"Ошибка чтения раздела реестра {target_hive}\\{target_path}: {e}")
        sys.exit(1)

    # Экспорт в файл
    if args.export:
        target = Path(args.export)
        if target.suffix.lower() == ".csv":
            viewer.export_key_to_csv(key_details, target)
        else:
            viewer.export_key_to_json(key_details, target)
        print(f"Данные успешно экспортированы в: {target}")
        return

    # JSON вывод
    if args.json:
        print(viewer.export_key_to_json(key_details))
        return

    # CSV вывод
    if args.csv:
        print(viewer.export_key_to_csv(key_details))
        return

    # TUI вывод по умолчанию
    tui.render_key_details(key_details)


if __name__ == "__main__":
    run_cli()
