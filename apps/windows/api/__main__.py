# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api - Main
# =============================================================================
# Description:
#   Точка входа и запуск внутреннего FastAPI сервера Windows System API (TC)
#   через uvicorn с централизованной конфигурацией логирования из модуля logger.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.api.__main__
#   Python API:
#     from apps.windows.api.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:05:00
# =============================================================================

from __future__ import annotations
"""Точка входа внутреннего FastAPI-сервиса Windows System API."""

import argparse
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы работали импорты src.*, apps.*, logger
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from logger import logger, get_uvicorn_log_config

# =============================================================================
# Глобальные константы конфигурации
# =============================================================================
DEFAULT_HOST: str = '127.0.0.1'
DEFAULT_PORT: int = 8001
DEFAULT_LOG_LEVEL: str = 'info'
ALLOWED_HOSTS: tuple[str, ...] = ('127.0.0.1', 'localhost', '::1')
INTERNAL_APP_FACTORY: str = 'apps.windows.api.internal_app:create_internal_app'


def _parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки.

    Returns:
        argparse.Namespace: Распарсенные аргументы.
    """
    parser = argparse.ArgumentParser(
        description='AI-Breadboard Windows Internal API Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help='IP-адрес для прослушивания (только localhost)',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='Порт внутреннего сервиса',
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        default=False,
        help='Включить hot-reload (только для разработки)',
    )
    parser.add_argument(
        '--log-level',
        default=DEFAULT_LOG_LEVEL,
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        help='Уровень логирования uvicorn',
    )
    return parser.parse_args()


def main() -> None:
    """Запускает uvicorn с внутренним FastAPI-сервисом.

    Принудительно ограничивает bind только на localhost.
    """
    args = _parse_args()

    # Защита: запрещаем bind на 0.0.0.0 или внешние адреса
    if args.host not in ALLOWED_HOSTS:
        logger.warning(
            f'  [WARN] Внутренний сервис не может слушать на {args.host}. '
            f'Принудительно используется {DEFAULT_HOST}.'
        )
        args.host = DEFAULT_HOST

    try:
        import uvicorn
    except ImportError:
        logger.error('[ERROR] uvicorn не установлен. Установите: pip install uvicorn')
        sys.exit(1)

    logger.info(f'  [Windows Internal API] Запуск на http://{args.host}:{args.port}')
    logger.info(f'  [Windows Internal API] TC UI: http://{args.host}:{args.port}/tc')
    logger.info(f'  [Windows Internal API] Health: http://{args.host}:{args.port}/health')
    logger.info(f'  [Windows Internal API] Docs:   http://{args.host}:{args.port}/docs')

    uvicorn.run(
        INTERNAL_APP_FACTORY,
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        log_config=get_uvicorn_log_config('windows_api.log'),
        # Заголовок сервера не раскрываем
        server_header=False,
        access_log=True,
    )


if __name__ == '__main__':
    main()
