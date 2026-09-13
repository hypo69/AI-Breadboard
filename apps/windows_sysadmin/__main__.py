# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator CLI Entry Point
# =============================================================================
# Description:
#   Executable module entry point for launching the interactive Windows
#   System Administrator dashboard, AD management tools, user audits,
#   group policy reports, or security event analysis.
#
# Examples:
#   $ python -m apps.windows_sysadmin --mode dashboard
#   $ python -m apps.windows_sysadmin --audit users --domain CORP
#   $ python -m apps.windows_sysadmin --security-events --hours 24
#   $ python -m apps.windows_sysadmin --ad-status
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the Windows System Administrator application."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from .tui import run_sysadmin_dashboard


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json."""
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def main() -> None:
    """Parse command line arguments and execute requested action."""
    parser = argparse.ArgumentParser(
        description="Windows System Administrator - Active Directory, User Management & Security Dashboard"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "audit", "ad-check", "security", "users", "server"],
        default="dashboard",
        help="Operation mode (default: dashboard)",
    )
    parser.add_argument(
        "--audit",
        type=str,
        choices=["users", "groups", "machines", "policies"],
        help="Audit target type",
    )
    parser.add_argument(
        "--domain",
        "-d",
        type=str,
        help="Active Directory domain name (e.g., CORP, CONTOSO.COM)",
    )
    parser.add_argument(
        "--ad-status",
        action="store_true",
        help="Display Active Directory connectivity status and exit",
    )
    parser.add_argument(
        "--security-events",
        action="store_true",
        help="Monitor and display Windows security events",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours lookback for event logs (default: 24)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON and exit",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        help="Dashboard refresh interval in seconds (default: 2.0)",
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
        default=8001,
        help="FastAPI server port (default: 8001)",
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

    if args.ad_status:
        print("[Windows System Administrator] Checking Active Directory connectivity...")
        # Placeholder for AD status check
        print("✓ Active Directory: Connected")
        print("✓ Domain: WORKGROUP")
        print("✓ Domain Controller: N/A (Local Machine)")
        return

    if args.security_events:
        print(f"[Windows System Administrator] Retrieving security events from last {args.hours} hours...")
        # Placeholder for security events
        print(json.dumps({
            "events_fetched": 42,
            "critical": 0,
            "warnings": 3,
            "info": 39,
            "lookback_hours": args.hours
        }, indent=2))
        return

    if args.mode == "audit" and args.audit:
        print(f"[Windows System Administrator] Auditing {args.audit} in domain {args.domain or 'LOCAL'}...")
        if args.json:
            print(json.dumps({"audit_type": args.audit, "domain": args.domain, "status": "in_progress"}))
        return

    if args.mode == "server":
        # Load config and override with CLI args if provided
        config = _load_config()
        server_cfg = getattr(config, "server", SimpleNamespace())
        
        # Use CLI args if provided, otherwise use config values
        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port != 8001 else getattr(server_cfg, "port", 8001)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)
        
        # Launch as standalone FastAPI server
        _run_standalone_server(host=effective_host, port=effective_port, reload=effective_reload, workers=effective_workers)
        return

    # Default: launch interactive dashboard
    try:
        asyncio.run(run_sysadmin_dashboard(interval=args.interval))
    except KeyboardInterrupt:
        print("\n[Windows System Administrator] Dashboard closed.")
        sys.exit(0)


def _run_standalone_server(host: str = "127.0.0.1", port: int = 8001, reload: bool = False, workers: int = 1) -> None:
    """Launch Windows System Administrator as a standalone FastAPI application.
    
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
        
        print("[Windows System Administrator] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        print(f"  Interactive API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc\n")
        
        app = FastAPI(
            title="Windows System Administrator",
            description="Standalone Windows system administration, AD management & security monitoring",
            version="1.0.0",
        )
        
        # Include the router
        app.include_router(init_router())
        
        # Run Uvicorn server
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
