# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Terminal CLI Main Entry Point
# =============================================================================
# Description:
#   Executable module entry point for running the interactive trading desk TUI.
#
# Examples:
#   $ python -m apps.trading_terminal --symbol BTC/USDT --interval 0.5
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the trading terminal dashboard."""

import argparse
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from .tui import run_dashboard


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json.

    Returns:
        SimpleNamespace: Loaded configuration namespace.
    """
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def _run_standalone_server(host: str = "127.0.0.1", port: int = 8103, reload: bool = False, workers: int = 1) -> None:
    """Launch Trading Terminal as a standalone FastAPI application.

    Args:
        host: Server bind address
        port: Server bind port
        reload: Enable auto-reload for development
        workers: Number of Uvicorn workers
    """
    try:
        import uvicorn
        from fastapi import FastAPI
        from .router import init_router

        print("[Trading Terminal] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        print(f"  Interactive API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc\n")

        app = FastAPI(
            title="Exchange Trading Terminal",
            description="Standalone exchange trading desk, real-time ticker stream & portfolio manager",
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
        print("[INFO] Make sure uvicorn and fastapi are installed: pip install uvicorn fastapi")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Parse CLI arguments and launch interactive trading dashboard or server."""
    parser = argparse.ArgumentParser(description="AI Breadboard Exchange Trading Terminal")
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "server"],
        default="dashboard",
        help="Operation mode (default: dashboard)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/USDT",
        help="Trading pair symbol (e.g. BTC/USDT, ETH/USDT, SOL/USDT)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Dashboard refresh interval in seconds",
    )
    parser.add_argument(
        "--balance",
        type=float,
        default=10000.0,
        help="Initial simulated starting account balance in USD",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="FastAPI server host (default: 127.0.0.1, use 0.0.0.0 for external access)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=0,
        help="FastAPI server port (default: read from config.json)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (only with --mode server)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of Uvicorn workers (default: 1)",
    )
    args = parser.parse_args()

    if args.mode == "server":
        config = _load_config()
        server_cfg = getattr(config, "server", SimpleNamespace())

        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8103)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)

        _run_standalone_server(host=effective_host, port=effective_port, reload=effective_reload, workers=effective_workers)
        return

    try:
        asyncio.run(run_dashboard(symbol=args.symbol, interval=args.interval))
    except KeyboardInterrupt:
        print("\n[Trading Terminal] Closed gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
