# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Real-Time Log Monitor & Stream Watcher
# =============================================================================
# Description:
#   Tails active log files, detects newly emitted warnings/errors,
#   and highlights anomalies in real time.
#
# File: watch_logs.py
# Project: ai-breadboard
# Package: .agents.skills.log-analyzer.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Real-Time Log Monitor & Stream Watcher.

Continuously observes log files in the configured directory and streams
events with color-coded severity tags.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional


def get_default_log_dir() -> Path:
    """Resolve default system log directory.

    Returns:
        Path: Default log directory.
    """
    return Path(tempfile.gettempdir()) / "ai-breadboard" / "logs"


def watch_log_files(
    log_dir: Path, min_level: str = "ALL", poll_interval: float = 1.0
) -> None:
    """Watch and stream log lines from directory.

    Args:
        log_dir: Directory containing log files.
        min_level: Minimum severity level to output (ALL, INFO, WARNING, ERROR).
        poll_interval: Polling interval in seconds.
    """
    if not log_dir.exists():
        print(f"Directory {log_dir} does not exist yet. Waiting...")

    file_offsets: Dict[Path, int] = {}
    print(f"👀 Monitoring logs in: {log_dir} (Filter: {min_level})")
    print("Press Ctrl+C to stop.")

    levels_order = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    min_rank = 0 if min_level == "ALL" else levels_order.get(min_level.upper(), 0)

    try:
        while True:
            if log_dir.exists():
                for log_file in sorted(log_dir.glob("*.log")):
                    if log_file not in file_offsets:
                        # Start at end of existing file or beginning if small
                        file_offsets[log_file] = log_file.stat().st_size

                    curr_size = log_file.stat().st_size
                    prev_offset = file_offsets[log_file]

                    if curr_size > prev_offset:
                        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(prev_offset)
                            new_lines = f.read()
                            file_offsets[log_file] = f.tell()

                        for line in new_lines.splitlines():
                            line_str = line.strip()
                            if not line_str:
                                continue

                            # Detect severity
                            is_err = "ERROR" in line_str or "CRITICAL" in line_str
                            is_warn = "WARNING" in line_str
                            is_info = "INFO" in line_str

                            event_rank = 40 if is_err else (30 if is_warn else (20 if is_info else 10))

                            if event_rank >= min_rank:
                                prefix = "🔴 [ERR]" if is_err else ("🟡 [WRN]" if is_warn else "🟢 [INF]")
                                print(f"{prefix} [{log_file.name}] {line_str}")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n🛑 Stopped log monitor.")


def main() -> int:
    """CLI entry point for watch_logs."""
    parser = argparse.ArgumentParser(description="Live stream & monitor log outputs.")
    parser.add_argument("--log-dir", "-d", help="Custom logs directory.")
    parser.add_argument(
        "--level", "-l", default="ALL", help="Minimum level: ALL, INFO, WARNING, ERROR."
    )
    parser.add_argument(
        "--interval", "-i", type=float, default=1.0, help="Poll interval in seconds."
    )
    args = parser.parse_args()

    target_dir = Path(args.log_dir) if args.log_dir else get_default_log_dir()
    watch_log_files(target_dir, min_level=args.level, poll_interval=args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
