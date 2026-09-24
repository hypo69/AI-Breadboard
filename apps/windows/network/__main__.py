# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal CLI Main Entry Point
# =============================================================================
# Description:
#   Executable module entry point for running the interactive network terminal TUI.
#
# Examples:
#   $ python -m apps.windows.network --interface 1 --filter "tcp port 80"
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the Network Analyzer Terminal dashboard."""

import argparse
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from .tui import run_network_dashboard
from apps.tshark import TSharkWrapper


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json."""
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def _get_server_mode(config: SimpleNamespace) -> str:
    """Extract server mode ('dedicated' or 'shared') from configuration.

    Args:
        config: Application configuration namespace.

    Returns:
        str: 'dedicated' or 'shared'.
    """
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
    """Parse CLI arguments and launch interactive network terminal dashboard."""
    parser = argparse.ArgumentParser(description="AI Breadboard Network Analyzer Terminal")
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "server"],
        default="dashboard",
        help="Operation mode (default: dashboard)",
    )
    parser.add_argument(
        "--interface",
        "-i",
        type=str,
        default="1",
        help="Capture interface index or name (default: 1)",
    )
    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        default="",
        help="Wireshark display filter string (e.g. 'tcp or udp', 'http', 'tls')",
    )
    parser.add_argument(
        "--simulate",
        "-s",
        action="store_true",
        help="Force simulation mode with synthetic network packet generation",
    )
    parser.add_argument(
        "--list-interfaces",
        "-l",
        action="store_true",
        help="List available network capture interfaces on host and exit",
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

    if args.list_interfaces:
        wrapper = TSharkWrapper()
        if not wrapper.is_available():
            print("[Error] TShark executable not found on host. Please install Wireshark / TShark.")
            sys.exit(1)
        interfaces = wrapper.list_interfaces()
        print(f"Available capture interfaces ({len(interfaces)} found):")
        for iface in interfaces:
            print(f"  [{iface.index}] {iface.name} - {iface.description or 'No description'}")
        sys.exit(0)

    if args.mode == "server":
        # Load config and override with CLI args if provided
        config = _load_config()
        server_cfg = getattr(config, "server", SimpleNamespace())
        server_mode = _get_server_mode(config)
        
        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8101)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)
        
        if server_mode == "shared" and args.port == 0:
            print("[Network Terminal] App configured in 'shared' server mode.")
            print(f"[Network Terminal] API endpoints are routed via the main server (http://{effective_host}:8000).")
        
        # Launch as standalone FastAPI server
        _run_standalone_server(host=effective_host, port=effective_port, reload=effective_reload, workers=effective_workers)
        return

    try:
        asyncio.run(
            run_network_dashboard(
                interface=args.interface,
                display_filter=args.filter,
                simulate=args.simulate,
            )
        )
    except KeyboardInterrupt:
        print("\n[Network Terminal] Closed gracefully.")
        sys.exit(0)


def _run_standalone_server(host: str = "127.0.0.1", port: int = 8101, reload: bool = False, workers: int = 1) -> None:
    """Launch Network Terminal as a standalone FastAPI application.
    
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
        
        print("[Network Terminal] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        print(f"  Interactive API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc\n")
        
        app = FastAPI(
            title="Network Terminal",
            description="Standalone network monitoring, packet capture, traffic statistics & AI security",
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


if __name__ == "__main__":
    main()
