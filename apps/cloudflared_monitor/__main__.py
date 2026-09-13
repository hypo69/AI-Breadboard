# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cloudflared Monitor CLI Main Entry Point
# =============================================================================
# Description:
#   Executable module entry point for running the interactive Cloudflare Tunnel
#   monitor dashboard, standalone FastAPI server, or one-shot status inspection.
#
# Examples:
#   $ python -m apps.cloudflared_monitor --mode dashboard
#   $ python -m apps.cloudflared_monitor --status --json
#   $ python -m apps.cloudflared_monitor --logs --limit 30
#   $ python -m apps.cloudflared_monitor --mode server --port 8104
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.cloudflared_monitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for Cloudflared Tunnel Monitor."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from .src.state import CloudflaredState
from .tui import run_cloudflared_dashboard


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json.

    Returns:
        SimpleNamespace: Loaded configuration.
    """
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


def _run_standalone_server(
    host: str = "127.0.0.1",
    port: int = 8104,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Launch Cloudflared Monitor as a standalone FastAPI application.

    Args:
        host: Server bind host address.
        port: Server bind port.
        reload: Enable auto-reload for development.
        workers: Number of Uvicorn workers.
    """
    try:
        import uvicorn
        from fastapi import FastAPI
        from .router import init_router

        print("[Cloudflared Monitor] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs\n")

        app = FastAPI(
            title="Cloudflared Tunnel Monitor",
            description="Standalone Cloudflare Tunnel supervisor, log analyzer & AI health diagnostic service",
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
        print("[INFO] Make sure uvicorn and fastapi are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Parse CLI arguments and execute requested action."""
    parser = argparse.ArgumentParser(
        description="AI Breadboard Cloudflare Tunnel Monitor & Diagnostics Workspace"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "server", "status", "logs", "health"],
        default="dashboard",
        help="Operation mode (default: dashboard)",
    )
    parser.add_argument(
        "--status",
        "-s",
        action="store_true",
        help="Print quick one-shot status summary and exit",
    )
    parser.add_argument(
        "--logs",
        "-l",
        action="store_true",
        help="Print recent parsed log lines and exit",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of log lines to retrieve (default: 20)",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run AI/heuristic health diagnostics and print report",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start cloudflared tunnel daemon",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop cloudflared tunnel daemon",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart cloudflared tunnel daemon",
    )
    parser.add_argument(
        "--public-url",
        type=str,
        default="",
        help="Override public tunnel URL to monitor",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        help="Dashboard refresh interval in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Format output as JSON",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="FastAPI server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=0,
        help="FastAPI server port (default: 8104)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development server",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of Uvicorn workers (default: 1)",
    )

    args = parser.parse_args()

    config = _load_config()
    cf_cfg = getattr(config, "cloudflared", SimpleNamespace())
    effective_url = args.public_url or getattr(cf_cfg, "public_url", "https://kino.davidka.net")

    state = CloudflaredState(public_url=effective_url)

    if args.start:
        success, msg = state.start_tunnel()
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        return

    if args.stop:
        success, msg = state.stop_tunnel()
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        return

    if args.restart:
        success, msg = state.restart_tunnel()
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        return

    if args.status or args.mode == "status":
        state.refresh(probe_network=True)
        if args.json:
            data = {
                "is_running": state.process.is_running,
                "pid": state.process.pid,
                "cpu_percent": state.process.cpu_percent,
                "memory_mb": state.process.memory_mb,
                "uptime_seconds": state.process.uptime_seconds,
                "has_token": state.has_token,
                "public_url": state.public_url,
                "endpoint_reachable": state.endpoint.is_reachable,
                "status_code": state.endpoint.status_code,
                "latency_ms": state.endpoint.response_time_ms,
                "health_score": state.report.health_score if state.report else 0,
            }
            print(json.dumps(data, indent=2))
        else:
            print("========================================")
            print("  Cloudflare Tunnel Status Overview")
            print("========================================")
            print(f"  Daemon Running: {'YES' if state.process.is_running else 'NO'}")
            print(f"  Process ID:     {state.process.pid or 'N/A'}")
            print(f"  CPU / Memory:   {state.process.cpu_percent}% / {state.process.memory_mb} MB")
            print(f"  Public Ingress: {state.public_url}")
            print(f"  Endpoint State: {'REACHABLE' if state.endpoint.is_reachable else 'UNREACHABLE'} ({state.endpoint.response_time_ms} ms)")
            print(f"  Health Score:   {state.report.health_score if state.report else 'N/A'}/100 ({state.report.status if state.report else 'N/A'})")
            print("========================================")
        return

    if args.logs or args.mode == "logs":
        logs = state.tail_logs(limit=args.limit)
        if args.json:
            print(json.dumps([{"time": e.timestamp, "level": e.level, "msg": e.message} for e in logs], indent=2))
        else:
            print(f"--- Tail {len(logs)} entries from {state.log_file} ---")
            for entry in logs:
                print(f"[{entry.timestamp}] [{entry.level:5s}] {entry.message}")
        return

    if args.health or args.mode == "health":
        state.refresh(probe_network=True)
        report = state.evaluate_diagnostics()
        if args.json:
            print(
                json.dumps(
                    {
                        "health_score": report.health_score,
                        "status": report.status,
                        "summary": report.summary,
                        "anomalies": [{"title": a.title, "description": a.description, "severity": a.severity} for a in report.anomalies],
                        "recommendations": report.recommendations,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Cloudflare Tunnel Health: {report.status} ({report.health_score}/100)")
            print(f"Summary: {report.summary}\n")
            if report.anomalies:
                print("Anomalies:")
                for a in report.anomalies:
                    print(f"  - [{a.severity.upper()}] {a.title}: {a.description}")
            if report.recommendations:
                print("\nRecommendations:")
                for r in report.recommendations:
                    print(f"  - {r}")
        return

    if args.mode == "server":
        server_cfg = getattr(config, "server", SimpleNamespace())
        server_mode = _get_server_mode(config)
        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8104)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)

        if server_mode == "shared" and args.port == 0:
            print("[Cloudflared Monitor] App configured in 'shared' server mode.")
            print(f"[Cloudflared Monitor] API endpoints are routed via the main server (http://{effective_host}:8000).")

        _run_standalone_server(
            host=effective_host,
            port=effective_port,
            reload=effective_reload,
            workers=effective_workers,
        )
        return

    # Default: Run Live TUI Dashboard
    try:
        asyncio.run(
            run_cloudflared_dashboard(
                interval=args.interval,
                public_url=effective_url,
            )
        )
    except KeyboardInterrupt:
        print("\n[Cloudflared Monitor] Closed gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
