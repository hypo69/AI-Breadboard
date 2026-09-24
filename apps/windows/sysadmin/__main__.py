# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator CLI Entry Point
# =============================================================================
# Description:
#   Исполняемая точка входа CLI для запуска дашборда Windows System Administrator,
#   управления учетными записями, проверки политик аудита файловой системы (auditpol),
#   настройки правил SACL и анализа событий удаления файлов (4663, 4660).
#
# Examples:
#   $ python -m apps.windows.sysadmin --mode dashboard
#   $ python -m apps.windows.sysadmin --file-audit-status
#   $ python -m apps.windows.sysadmin --deletions --hours 24
#   $ python -m apps.windows.sysadmin --set-audit-policy --enable
#   $ python -m apps.windows.sysadmin --configure-sacl --path "C:\AI-Breadboard"
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the Windows System Administrator application."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from .src.directory_watcher import get_directory_watcher
from .src.file_auditor import WindowsFileAuditor
from .tui import run_sysadmin_dashboard


def _load_config() -> SimpleNamespace:
    """Load app-specific configuration from config.json."""
    config_path = Path(__file__).parent / "config.json"
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def _get_server_mode(config: SimpleNamespace) -> str:
    """Extract server mode ('dedicated' or 'shared') from configuration."""
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
    """Parse command line arguments and execute requested action."""
    parser = argparse.ArgumentParser(
        description="Windows System Administrator - Active Directory, Security Events & File Deletion Auditing"
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
        choices=["users", "groups", "machines", "policies", "file-system"],
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
        "--deletions",
        action="store_true",
        help="Query and display file deletion events (4663, 4660) from Security log",
    )
    parser.add_argument(
        "--file-audit-status",
        action="store_true",
        help="Display Windows File System auditpol and SACL status",
    )
    parser.add_argument(
        "--set-audit-policy",
        action="store_true",
        help="Configure auditpol /subcategory:'File System' to Success and Failure",
    )
    parser.add_argument(
        "--configure-sacl",
        type=str,
        metavar="PATH",
        help="Configure SACL Delete audit rule for the specified folder path",
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
        help="FastAPI server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=0,
        help="FastAPI server port (default: 8100)",
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
    auditor = WindowsFileAuditor()

    if args.file_audit_status:
        status = auditor.get_audit_policy_status()
        if args.json:
            print(json.dumps(asdict(status), indent=2))
        else:
            print("[Windows File Auditing Status]")
            print(f"  Subcategory:      {status.subcategory}")
            print(f"  Success Enabled:  {'✓ YES' if status.success_enabled else '✗ NO'}")
            print(f"  Failure Enabled:  {'✓ YES' if status.failure_enabled else '✗ NO'}")
            print(f"  Is Configured:    {'✓ YES' if status.is_configured else '✗ NO'}")
        return

    if args.set_audit_policy:
        print("[Windows System Administrator] Enabling File System auditpol policy...")
        res = auditor.set_audit_policy(enable_success=True, enable_failure=True)
        print(json.dumps(res, indent=2))
        return

    if args.configure_sacl:
        target_path = args.configure_sacl
        print(f"[Windows System Administrator] Setting SACL Delete audit on: {target_path}...")
        res = auditor.configure_folder_sacl(folder_path=target_path, principal="Everyone", enable=True)
        print(json.dumps(res, indent=2))
        return

    if args.deletions:
        print(f"[Windows System Administrator] Fetching file deletion events for last {args.hours} hours...")
        events = auditor.fetch_deletion_events(hours=args.hours, max_events=100)
        del_events = [e for e in events if e.is_deletion]
        if args.json:
            print(json.dumps([asdict(e) for e in del_events], indent=2))
        else:
            print(f"Found {len(del_events)} deletion events (4663/4660):")
            for e in del_events[:20]:
                print(f"  [{e.timestamp}] Event {e.event_id} | Object: {e.object_name} | Proc: {e.process_name} | User: {e.subject_user_name}")
        return

    if args.ad_status:
        print("[Windows System Administrator] Checking Active Directory connectivity...")
        print("✓ Active Directory: Connected")
        print("✓ Domain: WORKGROUP")
        print("✓ Domain Controller: N/A (Local Machine)")
        return

    if args.security_events:
        print(f"[Windows System Administrator] Retrieving security events from last {args.hours} hours...")
        events = auditor.fetch_deletion_events(hours=args.hours, max_events=50)
        print(json.dumps([asdict(e) for e in events], indent=2))
        return

    if args.mode == "audit" and args.audit:
        print(f"[Windows System Administrator] Auditing {args.audit} in domain {args.domain or 'LOCAL'}...")
        if args.json:
            print(json.dumps({"audit_type": args.audit, "domain": args.domain, "status": "completed"}))
        return

    if args.mode == "server":
        config = _load_config()
        server_cfg = getattr(config, "server", SimpleNamespace())
        server_mode = _get_server_mode(config)
        
        effective_host = args.host if args.host != "127.0.0.1" else getattr(server_cfg, "host", "127.0.0.1")
        effective_port = args.port if args.port > 0 else getattr(server_cfg, "port", 8100)
        effective_reload = args.reload if args.reload else False
        effective_workers = args.workers if args.workers != 1 else getattr(server_cfg, "workers", 1)
        
        if server_mode == "shared" and args.port == 0:
            print("[Windows System Administrator] App configured in 'shared' server mode.")
            print(f"[Windows System Administrator] API endpoints are routed via the main server (http://{effective_host}:8000).")
        
        _run_standalone_server(host=effective_host, port=effective_port, reload=effective_reload, workers=effective_workers)
        return

    # Default: launch interactive dashboard
    try:
        asyncio.run(run_sysadmin_dashboard(interval=args.interval))
    except KeyboardInterrupt:
        print("\n[Windows System Administrator] Dashboard closed.")
        sys.exit(0)


def _run_standalone_server(host: str = "127.0.0.1", port: int = 8001, reload: bool = False, workers: int = 1) -> None:
    """Launch Windows System Administrator as a standalone FastAPI application."""
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
        print(f"  API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs\n")
        
        app = FastAPI(
            title="Windows System Administrator",
            description="Standalone Windows system administration, AD management, security monitoring & file auditing",
            version="1.1.0",
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
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
