# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Application CLI Entry Point
# =============================================================================
# Description:
#   Command-line interface to launch the Helpdesk TUI dashboard, inspect ticket
#   statistics, list active tickets, or start the dedicated FastAPI microservice server.
#
# Examples:
#   >>> python -m apps.helpdesk
#   >>> python -m apps.helpdesk --stats
#   >>> python -m apps.helpdesk --list
#   >>> python -m apps.helpdesk --mode server --port 8110
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for Helpdesk Support Desk application."""

from __future__ import annotations

import argparse
import json
import sys

from apps.helpdesk.tui import HelpdeskTUI, run_tui
from src.api.helpdesk.database import init_db, get_db
from src.logger import logger


def main() -> None:
    """Parse CLI arguments and dispatch Helpdesk application commands."""
    parser = argparse.ArgumentParser(
        prog="apps.helpdesk",
        description="Helpdesk Support Desk: Ticket Management, Operator Hub & Live Support",
    )
    parser.add_argument(
        "--mode",
        choices=["tui", "server"],
        default="tui",
        help="Operation mode: interactive TUI dashboard or FastAPI server (default: tui)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8110,
        help="Server port when running in server mode (default: 8110)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server bind host (default: 127.0.0.1)",
    )
    parser.add_argument("--stats", action="store_true", help="Print aggregate KPI ticket statistics")
    parser.add_argument("--list", action="store_true", help="List recent support tickets")
    parser.add_argument("--json", action="store_true", help="Format CLI output as JSON")

    args = parser.parse_args()

    init_db()
    tui = HelpdeskTUI()

    if args.stats:
        stats = tui.get_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n📊 Helpdesk Statistics:")
            print(f"  • Всего тикетов:     {stats['total']}")
            print(f"  • Открыто:           {stats['open']}")
            print(f"  • В обработке:       {stats['in_progress']}")
            print(f"  • Решено:            {stats['resolved']}")
            print(f"  • Срочных:           {stats['urgent']}\n")
        return

    if args.list:
        tickets = tui.get_tickets()
        if args.json:
            print(json.dumps(tickets, indent=2))
        else:
            tui.render_rich()
        return

    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from src.api.helpdesk.router_helpdesk import router as core_router
        from apps.helpdesk.router import router as v1_router

        app = FastAPI(
            title="Helpdesk Support Desk API",
            description="Standalone Helpdesk Support Management Microservice",
            version="1.0.0",
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.include_router(core_router)
        app.include_router(v1_router)

        print(f"🚀 Запуск автономного микросервиса Helpdesk на http://{args.host}:{args.port}...")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        return

    # Default: Interactive TUI
    run_tui()


if __name__ == "__main__":
    main()
