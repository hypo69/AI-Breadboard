# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Security_Acl -   Main  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.sdk.modules.security_acl.__main__
#   Python API:
#     from apps.windows.sdk.modules.security_acl.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.security_acl
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import argparse
from logger import logger
from apps.windows.sdk.modules.security_acl.core.manager import SecurityAclManager
from apps.windows.sdk.modules.security_acl.tui import SecurityAclTUI


def main() -> None:
    """Обработка параметров командной строки."""
    parser = argparse.ArgumentParser(description='Windows Security & Access Control (icacls, manage-bde, cipher)')
    parser.add_argument('--mode', type=str, choices=['cli', 'server'], default='cli', help='Режим запуска')
    parser.add_argument('--port', type=int, default=8127, help='Порт сервера')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Хост сервера')
    parser.add_argument('--json', action='store_true', help='Вывод в формате JSON')
    args = parser.parse_args()

    if args.mode == 'server':
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.sdk.modules.security_acl.router import init_router

        app = FastAPI(title='Windows Security & ACL API', version='1.0.0')
        app.include_router(init_router())
        logger.info(f"Запуск Security & ACL сервера на http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    mgr = SecurityAclManager()
    if args.json:
        report = mgr.generate_report()
        print(report.model_dump_json(indent=2))
        return

    tui = SecurityAclTUI(manager=mgr)
    tui.render_dashboard()


if __name__ == '__main__':
    main()
