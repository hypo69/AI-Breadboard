# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Process Inspector Script
# =============================================================================
# Description:
#   Retrieves and displays running process states from the Windows telemetry
#   SQLite database (`telemetry.db`).
#
# File: get_process_state.py
# Project: ai-breadboard
# Package: .skills.telemetry_process_inspector.scripts
# =============================================================================

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve project root for absolute imports
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from apps.windows.telemetry.storage import TelemetryStorage
except ImportError as e:
    print(f"Error: Could not import TelemetryStorage: {e}", file=sys.stderr)
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Inspect process state from telemetry SQLite DB.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of processes to display")
    parser.add_argument("--sort", choices=["cpu", "memory"], default="cpu", help="Sort order (cpu or memory)")
    return parser.parse_args()


def main() -> None:
    """Main execution entry point."""
    args = parse_args()
    
    try:
        storage = TelemetryStorage.get_instance()
        procs = storage.get_latest_processes(limit=args.limit, sort_by=args.sort)
    except Exception as ex:
        print(f"Error accessing telemetry storage: {ex}", file=sys.stderr)
        sys.exit(1)

    print(f"=== TELEMETRY PROCESS INSPECTOR ({storage.db_path}) ===")
    print(f"{'PID':<8} {'Process Name':<25} {'CPU %':<10} {'Memory (MB)':<15} {'Threads':<8} {'User'}")
    print("-" * 85)

    for p in procs:
        pid = p.get("pid", 0)
        name = p.get("name", "unknown")
        cpu = p.get("cpu_percent", 0.0)
        mem = p.get("memory_mb", 0.0)
        threads = p.get("num_threads", 0)
        user = p.get("username", "-") or "-"
        print(f"{pid:<8} {name:<25} {cpu:<10.1f} {mem:<15.1f} {threads:<8} {user}")


if __name__ == "__main__":
    main()
