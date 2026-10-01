# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Main
# =============================================================================
# Description:
#   Главная точка входа для запуска Web GUI и FastAPI сервиса исследования телеметрии.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.telemetry_research.main
#   Python API:
#     from apps.windows.telemetry_research.main import parse_args
#
#     res = parse_args()
#
# File: main.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Главная точка входа для запуска Web GUI и FastAPI сервиса исследования телеметрии."""

import argparse
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from logger import logger
except ImportError:
    from logger import logger


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов запуска веб-сервера."""
    parser = argparse.ArgumentParser(
        description="Запуск Web GUI и FastAPI сервера исследования телеметрии",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Хост для биндинга (по умолчанию: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8090, help="Порт для веб-сервера (по умолчанию: 8090)")
    parser.add_argument("--reload", action="store_true", help="Включить автоперезагрузку при изменении кода")
    return parser.parse_args()


def main() -> int:
    """Запуск FastAPI сервера через Uvicorn."""
    args = parse_args()
    try:
        import uvicorn
    except ImportError:
        logger.error("Для запуска Web GUI необходим пакет 'uvicorn'. Установите его: pip install uvicorn")
        print("❌ Ошибка: пакет 'uvicorn' не установлен. Установите: pip install uvicorn")
        return 1

    logger.info("=" * 65)
    logger.info(f"🚀 Запуск Web GUI исследования телеметрии на http://{args.host}:{args.port}")
    logger.info("=" * 65)
    print("\n" + "=" * 65)
    print(f"🔬 Web GUI исследования телеметрии доступен по адресу:")
    print(f"👉 http://{args.host}:{args.port}")
    print("=" * 65 + "\n")

    uvicorn.run(
        "apps.windows.telemetry_research.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
