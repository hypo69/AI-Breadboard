# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api - Main
# =============================================================================
# Description:
#   Точка входа и запуск внутреннего FastAPI сервера Windows System API (TC)
#   через uvicorn с поддержкой форматирования логов с временными метками.
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
# Updated: 2026-10-08 01:30:00
# =============================================================================

from __future__ import annotations
"""Точка входа внутреннего FastAPI-сервиса Windows System API."""

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Dict

# Добавляем корень проекта в sys.path, чтобы работали импорты src.*, apps.*
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _build_log_config() -> Dict[str, Any]:
    """Формирует конфигурацию логирования uvicorn с временными метками.

    Returns:
        Dict[str, Any]: Конфигурация логирования uvicorn с форматом даты и времени.
    """
    import uvicorn.config

    log_config: Dict[str, Any] = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    log_config['formatters']['default']['fmt'] = '%(asctime)s %(levelprefix)s %(message)s'
    log_config['formatters']['default']['datefmt'] = '%Y-%m-%d %H:%M:%S'
    log_config['formatters']['access']['fmt'] = (
        '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    log_config['formatters']['access']['datefmt'] = '%Y-%m-%d %H:%M:%S'
    return log_config


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
        default='127.0.0.1',
        help='IP-адрес для прослушивания (только localhost)',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8001,
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
        default='info',
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
    if args.host not in ('127.0.0.1', 'localhost', '::1'):
        print(
            f'[WARN] Внутренний сервис не может слушать на {args.host}. '
            'Принудительно используется 127.0.0.1.',
            file=sys.stderr,
        )
        args.host = '127.0.0.1'

    try:
        import uvicorn
    except ImportError:
        print('[ERROR] uvicorn не установлен. Установите: pip install uvicorn', file=sys.stderr)
        sys.exit(1)

    print(f'  [Windows Internal API] Запуск на http://{args.host}:{args.port}')
    print(f'  [Windows Internal API] TC UI: http://{args.host}:{args.port}/tc')
    print(f'  [Windows Internal API] Health: http://{args.host}:{args.port}/health')
    print(f'  [Windows Internal API] Docs:   http://{args.host}:{args.port}/docs')

    uvicorn.run(
        'apps.windows.api.internal_app:create_internal_app',
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        log_config=_build_log_config(),
        # Заголовок сервера не раскрываем
        server_header=False,
        access_log=True,
    )


if __name__ == '__main__':
    main()

