# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector CLI Entry Point
# =============================================================================
# Description:
#   Executable module entry point for launching the interactive System & Hardware
#   Inspector TUI, one-shot hardware audits, or JSON telemetry snapshots.
#
# Examples:
#   $ python -m apps.system_inspector --sort memory --interval 2.0
#   $ python -m apps.system_inspector --diagnose
#   $ python -m apps.system_inspector --hardware
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the System & Hardware Inspector application."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from src.system import SystemAIDiagnostician, SystemCollector
from .tui import run_system_inspector


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json."""
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def main() -> None:
    """Parse command line arguments and execute requested action."""
    parser = argparse.ArgumentParser(
        description="AI Breadboard System & Hardware Inspector (AIDA64 + Wireshark Dual Monitor)"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["dashboard", "server"],
        default="dashboard",
        help="Operation mode (default: dashboard)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=1.0,
        help="Polling interval in seconds for live monitor (default: 1.0)",
    )
    parser.add_argument(
        "--sort",
        "-s",
        type=str,
        choices=["cpu", "memory"],
        default="cpu",
        help="Sort active process stream by 'cpu' or 'memory' (default: cpu)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=20,
        help="Number of active processes to display (default: 20)",
    )
    parser.add_argument(
        "--diagnose",
        "-d",
        action="store_true",
        help="Perform one-shot AI system performance diagnosis and exit",
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Print AIDA64-style hardware specification tree and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw telemetry snapshot as JSON and exit",
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
    collector = SystemCollector()

    if args.json:
        snapshot = collector.get_snapshot(process_limit=args.limit)
        print(snapshot.model_dump_json(indent=2))
        return

    if args.hardware:
        tree = collector.get_hardware_tree()
        print("\n=== AIDA64 Hardware Specification Tree ===")
        for node in tree:
            print(f"\n[{node.category}] {node.name}")
            for k, v in node.properties.items():
                print(f"  • {k}: {v}")
        return

    if args.diagnose:
        snapshot = collector.get_snapshot(process_limit=args.limit)
        diagnostician = SystemAIDiagnostician()
        report = asyncio.run(diagnostician.diagnose(snapshot))
        print("\n=== AI System Performance & Health Audit ===")
        print(f"Health Score: {report.health_score}/100")
        print(f"Summary: {report.summary}")
        if report.anomalies:
            print("\nAnomalies Detected:")
            for a in report.anomalies:
                print(f" - [{a.severity.upper()}] {a.title}: {a.description}")
        print("\nRecommendations:")
        for r in report.recommendations:
            print(f" - {r}")
        return

    if args.mode == "server":
        # Load config and override with CLI args if provided
        config = _load_config()
        server_cfg = getattr(config, "server", SimpleNamespace())
        
        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8102)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)
        
        # Launch as standalone FastAPI server
        _run_standalone_server(host=effective_host, port=effective_port, reload=effective_reload, workers=effective_workers)
        return

    # Default: launch interactive live TUI dashboard
    try:
        asyncio.run(run_system_inspector(interval=args.interval, sort_by=args.sort))
    except KeyboardInterrupt:
        print("\nSystem Inspector closed.")


def _run_standalone_server(host: str = "127.0.0.1", port: int = 8102, reload: bool = False, workers: int = 1) -> None:
    """Launch System Inspector as a standalone FastAPI application.
    
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
        
        print("[System Inspector] Starting standalone FastAPI server...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Reload: {reload}")
        print(f"  Workers: {workers}")
        print(f"\n  Available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        print(f"  Interactive API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc\n")
        
        app = FastAPI(
            title="System Inspector",
            description="Standalone system telemetry, hardware monitoring, AI diagnostics",
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
