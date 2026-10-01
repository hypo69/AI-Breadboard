# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Servicing_Integrity -   Main  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.modules.servicing_integrity.__main__
#   Python API:
#     from apps.windows.modules.servicing_integrity.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.modules.servicing_integrity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import argparse
from logger import logger
from apps.windows.modules.servicing_integrity.core.manager import ServicingIntegrityManager
from apps.windows.modules.servicing_integrity.tui import ServicingIntegrityTUI


def main() -> None:
    """Обработка параметров командной строки."""
    parser = argparse.ArgumentParser(description='Windows Servicing & System Integrity (SFC & DISM)')
    parser.add_argument('--mode', type=str, choices=['cli', 'server'], default='cli', help='Режим запуска')
    parser.add_argument('--port', type=int, default=8122, help='Порт сервера')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Хост сервера')
    parser.add_argument('--json', action='store_true', help='Вывод в формате JSON')
    args = parser.parse_args()

    if args.mode == 'server':
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.modules.servicing_integrity.router import init_router

        app = FastAPI(title='Windows Servicing Integrity API', version='1.0.0')
        app.include_router(init_router())
        logger.info(f"Запуск Servicing Integrity сервера на http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    mgr = ServicingIntegrityManager()
    if args.json:
        report = mgr.generate_report()
        print(report.model_dump_json(indent=2))
        return

    tui = ServicingIntegrityTUI(manager=mgr)
    tui.render_dashboard()


if __name__ == '__main__':
    main()
