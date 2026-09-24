# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Terminal Manager CLI Helper
# =============================================================================
# Description:
#   Utility for generating and executing multi-terminal layouts.
#
# File: terminal_manager.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Terminal manager utility for configuring and launching multi-pane workspaces.

This module inspects system terminal capabilities (e.g. Windows Terminal wt.exe)
and generates launch commands for multi-pane or multi-window layouts.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_terminal_profiles() -> Dict[str, List[Dict[str, str]]]:
    """Return predefined terminal layout profiles.

    Returns:
        Dict[str, List[Dict[str, str]]]: Mapping of profile name to list of pane definitions.
    """
    python_exe = sys.executable

    return {
        "breadboard": [
            {
                "title": "FastAPI Server",
                "command": f'powershell.exe -NoExit -ExecutionPolicy Bypass -File "{PROJECT_ROOT / "launchers" / "Run-Unicorn.ps1"}"',
            },
            {
                "title": "Assist CLI",
                "command": f'powershell.exe -NoExit -ExecutionPolicy Bypass -File "{PROJECT_ROOT / "assist.ps1"}"',
            },
            {
                "title": "Telegram Bot",
                "command": f'powershell.exe -NoExit -ExecutionPolicy Bypass -File "{PROJECT_ROOT / "launchers" / "Run-TelegramBot.ps1"}" -Foreground',
            },
            {
                "title": "System Log Stream",
                "command": f'powershell.exe -NoExit -Command "Get-Content -Path \'{PROJECT_ROOT / "logs" / "app.log"}\' -Wait -Tail 30 -ErrorAction SilentlyContinue"',
            },
        ],
        "trading": [
            {
                "title": "Trading Desk (BTC/USDT)",
                "command": f'"{python_exe}" -m apps.trading_terminal --symbol BTC/USDT',
            },
            {
                "title": "Trading Desk (ETH/USDT)",
                "command": f'"{python_exe}" -m apps.trading_terminal --symbol ETH/USDT',
            },
            {
                "title": "Execution Feed",
                "command": f'powershell.exe -NoExit -Command "Write-Host \'[Execution Feed Active]\' -ForegroundColor Green; Start-Sleep 1"',
            },
        ],
        "network": [
            {
                "title": "Network DPI Terminal",
                "command": f'"{python_exe}" -m apps.windows.network',
            },
            {
                "title": "Network Traffic Stream",
                "command": f'"{python_exe}" -m apps.windows.network --simulate',
            },
        ],
        "cloudflared": [
            {
                "title": "Cloudflared Monitor Dashboard",
                "command": f'"{python_exe}" -m apps.cloudflared_monitor',
            },
            {
                "title": "Cloudflared Live Log Stream",
                "command": f'powershell.exe -NoExit -Command "Get-Content -Path \'{PROJECT_ROOT / "logs" / "cloudflared.log"}\' -Wait -Tail 30 -ErrorAction SilentlyContinue"',
            },
            {
                "title": "Tunnel Launcher Control",
                "command": f'powershell.exe -NoExit -ExecutionPolicy Bypass -File "{PROJECT_ROOT / "launchers" / "Run-Cloudflared.ps1"}"',
            },
        ],
    }


def is_windows_terminal_available() -> bool:
    """Check if Windows Terminal (wt.exe) is available in PATH.

    Returns:
        bool: True if wt.exe is found.
    """
    return shutil.which("wt.exe") is not None or shutil.which("wt") is not None


def build_wt_command(profile_name: str = "breadboard") -> Optional[List[str]]:
    """Build Windows Terminal CLI command arguments for multi-pane layout.

    Args:
        profile_name (str): Profile key.

    Returns:
        Optional[List[str]]: Argument list for wt.exe or None if profile not found.
    """
    profiles = get_terminal_profiles()
    if profile_name not in profiles:
        return None

    panes = profiles[profile_name]
    if not panes:
        return None

    args: List[str] = ["wt.exe", "-d", str(PROJECT_ROOT)]

    for idx, pane in enumerate(panes):
        if idx == 0:
            args.extend(["--title", pane["title"]])
            args.extend(pane["command"].split())
        else:
            # Alternate horizontal and vertical splits for a grid
            split_flag = "-H" if idx % 2 == 1 else "-V"
            args.extend([";", "split-pane", split_flag, "-d", str(PROJECT_ROOT), "--title", pane["title"]])
            args.extend(pane["command"].split())

    return args


def main() -> None:
    """CLI entrypoint for terminal manager."""
    parser = argparse.ArgumentParser(description="Terminal Workspace Manager")
    parser.add_argument("--profile", type=str, default="breadboard", choices=["breadboard", "trading", "network", "cloudflared"], help="Workspace layout profile")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    args = parser.parse_args()

    if args.list:
        profiles = get_terminal_profiles()
        print("Available terminal profiles:")
        for name, panes in profiles.items():
            print(f"  - {name} ({len(panes)} panes)")
        return

    wt_cmd = build_wt_command(args.profile)
    if wt_cmd:
        print(f"Constructed wt command for profile '{args.profile}':")
        print(" ".join(wt_cmd))


if __name__ == "__main__":
    main()
