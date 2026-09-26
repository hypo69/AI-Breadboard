# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Control Center CLI Main Entry Point
# =============================================================================
# Description:
#   Точка входа CLI для запуска терминального интерфейса (TUI) или автономного
#   FastAPI сервера для Центра управления системой Windows (System Control Center).
#
# Examples:
#   >>> python -m apps.windows.system_control_center --mode server --port 8109
#   >>> python -m apps.windows.system_control_center --mode dashboard
#
# File: __main__.py
# Project: AI-Breadboard
# Package: apps.windows.system_control_center
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI точка входа для приложения System Control Center."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from .tui import run_control_dashboard


def _load_config() -> SimpleNamespace:
    """Загрузка конфигурации приложения из config.json."""
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def _get_server_mode(config: SimpleNamespace) -> str:
    """Получение режима сервера ('dedicated' или 'shared')."""
    server_val = getattr(config, "server", None)
    if isinstance(server_val, str):
        return server_val.strip().lower()
    if isinstance(server_val, SimpleNamespace):
        dedicated_val = getattr(server_val, "dedicated", None)
        if dedicated_val is not None:
            return "dedicated" if dedicated_val in (True, "true", "True", 1) else "shared"
        mode = getattr(server_val, "mode", getattr(server_val, "type", "dedicated"))
        return str(mode).strip().lower()
    if isinstance(server_val, dict):
        if "dedicated" in server_val:
            return "dedicated" if server_val["dedicated"] in (True, "true", "True", 1) else "shared"
        mode = server_val.get("mode") or server_val.get("type", "dedicated")
        return str(mode).strip().lower()
    return "dedicated"


def main() -> None:
    """Разбор аргументов командной строки и запуск выбранного режима."""
    parser = argparse.ArgumentParser(
        description="System Control Center - Windows Management & Administration Hub"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "server", "tui"],
        default="server",
        help="Режим работы (по умолчанию: server)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Хост FastAPI сервера (по умолчанию: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=0,
        help="Порт FastAPI сервера (по умолчанию: 8109)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Включить авто-перезагрузку для разработки",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Количество воркеров Uvicorn",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        help="Интервал обновления дашборда в секундах",
    )

    args = parser.parse_args()

    if args.mode in ("dashboard", "tui"):
        try:
            asyncio.run(run_control_dashboard(interval=args.interval))
        except KeyboardInterrupt:
            print("\n[System Control Center] Dashboard closed.")
            sys.exit(0)
        return

    # Режим сервера
    config = _load_config()
    server_cfg = getattr(config, "server", SimpleNamespace())

    effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
    effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8109)
    effective_reload = args.reload
    effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)

    _run_standalone_server(
        host=effective_host,
        port=effective_port,
        reload=effective_reload,
        workers=effective_workers,
    )


def _run_standalone_server(
    host: str = "127.0.0.1",
    port: int = 8109,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Запуск System Control Center как автономного FastAPI сервиса."""
    try:
        import uvicorn
        from fastapi import FastAPI
        from .router import init_router

        print("[System Control Center] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs\n")

        app = FastAPI(
            title="System Control Center",
            description="Windows Management, Security & Post-Install Control Hub",
            version="1.0.0",
        )

        app.include_router(init_router())

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level="info",
        )
    except ImportError as e:
        print(f"[ERROR] Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
