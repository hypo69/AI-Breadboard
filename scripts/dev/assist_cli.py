# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Create state directory for AI assistant persistence
# =============================================================================
# Description:
#   Creates state directory if it doesn't exist for persisting AI provider
#   and model selections across CLI sessions.
#
# File: assist_cli.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI Assistant CLI tool for model and provider management.

Provides command-line interface for managing AI model providers, models,
configuration, and running queries against selected models."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import header
from header import __root__
from dotenv import load_dotenv

# Directory for storing selected provider/model state
_STATE_DIR = __root__ / ".assist_state"
_PROVIDER_FILE = _STATE_DIR / "provider.json"
_MODEL_FILE = _STATE_DIR / "model.json"

def _ensure_state_dir() -> None:
    """Create state directory if not exists."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)

def _get_selected_provider() -> dict:
    """Get currently selected provider.
    
    Returns:
        Dictionary with selected provider info.
    """
    if not _PROVIDER_FILE.exists():
        return {}
    try:
        with open(_PROVIDER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _set_selected_provider(provider_name: str) -> None:
    """Save selected provider.
    
    Args:
        provider_name: Name of provider to select.
    """
    _ensure_state_dir()
    with open(_PROVIDER_FILE, "w", encoding="utf-8") as f:
        json.dump({"provider": provider_name}, f, ensure_ascii=False, indent=2)

def _get_selected_model() -> dict:
    """Get currently selected model.
    
    Returns:
        Dictionary with selected model info.
    """
    if not _MODEL_FILE.exists():
        return {}
    try:
        with open(_MODEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _set_selected_model(model_name: str, provider: str = "") -> None:
    """Save selected model.
    
    Args:
        model_name: Name of model to select.
        provider: Optional provider name.
    """
    _ensure_state_dir()
    data = {"model": model_name}
    if provider:
        data["provider"] = provider
    with open(_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Setup UTF-8 for Windows console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(__root__ / ".env")

# ANSI colors for terminal output
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"
C_MAGENTA = "\033[95m"

def _get_venv_python() -> str:
    """Get Python interpreter path in virtual environment.
    
    Returns:
        Path to Python executable.
    """
    venv_py = __root__ / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable

def _get_config() -> dict:
    """Load configuration from config.json.
    
    Returns:
        Dictionary with configuration or empty dict if not found.
    """
    cfg_path = __root__ / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"{C_RED}Error reading config.json: {e}{C_RESET}")
        return {}

def _get_occupied_port_pids(port: int) -> list[int]:
    """Get process IDs listening on specified port.
    
    Args:
        port: Port number to check.
        
    Returns:
        List of PIDs listening on port.
    """
    pids = []
    if sys.platform.startswith("win"):
        try:
            out = subprocess.check_output(f"netstat -aon", shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.splitlines():
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts and parts[-1].isdigit():
                        pid = int(parts[-1])
                        if pid > 0 and pid not in pids:
                            pids.append(pid)
        except Exception:
            pass
    return pids

def cmd_start(args: argparse.Namespace) -> int:
    """Start project services.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code from subprocess.
    """
    target = getattr(args, "service", "run") or "run"
    target = target.lower()

    script_map = {
        "run": "run.ps1",
        "all": "run.ps1",
        "unicorn": "Run-Unicorn.ps1",
        "uvicorn": "Run-Unicorn.ps1",
        "light": "Run-LightServer.ps1",
        "foundry": "Run-Foundry.ps1",
    }

    script_name = script_map.get(target)
    if not script_name:
        print(f"{C_RED}❌ Unknown startup target: '{target}'{C_RESET}")
        print(f"{C_GRAY}Available targets: run (default), unicorn, light, foundry, all{C_RESET}")
        return 1

    script_path = __root__ / script_name
    if not script_path.exists():
        script_path = __root__ / "launchers" / script_name
    if not script_path.exists():
        print(f"{C_RED}❌ Script not found: {script_path}{C_RESET}")
        return 1

    print(f"{C_CYAN}🚀 Starting: {script_name}...{C_RESET}")
    if script_name == "Run-Foundry.ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path), "-Action", "start"]
    else:
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]

    return subprocess.call(cmd, cwd=str(__root__))

def cmd_stop(args: argparse.Namespace) -> int:
    """Stop server and related processes.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    target = getattr(args, "service", "all") or "all"
    target = target.lower()

    cfg = _get_config()
    server_cfg = cfg.get("server", {})
    port = int(server_cfg.get("port", 8000))

    stopped_any = False

    if target in ("server", "all", "unicorn", "uvicorn", "light"):
        pids = _get_occupied_port_pids(port)
        if pids:
            print(f"{C_YELLOW}⏹ Stopping FastAPI server on port {port} (PID: {pids})...{C_RESET}")
            for pid in pids:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                    print(f"  {C_GREEN}✔ Terminated process PID {pid}{C_RESET}")
                    stopped_any = True
                except Exception as e:
                    print(f"  {C_RED}✖ Failed to terminate PID {pid}: {e}{C_RESET}")
        else:
            print(f"{C_GRAY}Port {port} is free (FastAPI server not running){C_RESET}")

    if target in ("foundry", "all"):
        foundry_script = __root__ / "launchers" / "Run-Foundry.ps1"
        if not foundry_script.exists():
            foundry_script = __root__ / "Run-Foundry.ps1"
        if foundry_script.exists():
            print(f"{C_YELLOW}⏹ Stopping Foundry service...{C_RESET}")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(foundry_script), "-Action", "stop"], cwd=str(__root__))
            stopped_any = True

    if not stopped_any and not pids:
        print(f"{C_GREEN}All services already stopped.{C_RESET}")
    return 0

def cmd_restart(args: argparse.Namespace) -> int:
    """Restart server.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    print(f"{C_CYAN}🔄 Restarting services...{C_RESET}")
    cmd_stop(args)
    return cmd_start(args)

def cmd_status(args: argparse.Namespace) -> int:
    """Check current server status.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    cfg = _get_config()
    server_cfg = cfg.get("server", {})
    port = int(server_cfg.get("port", 8000))
    use_ssl = bool(server_cfg.get("use_ssl", False))
    mode = str(server_cfg.get("mode", "DEV"))
    reload_on = bool(server_cfg.get("reload", True))

    proto = "https" if use_ssl else "http"
    local_url = f"{proto}://localhost:{port}/"

    print(f"\n{C_BOLD}{C_CYAN}Server Status Report{C_RESET}\n")
    
    pids = _get_occupied_port_pids(port)
    if pids:
        print(f"  {C_BOLD}FastAPI Server:{C_RESET}     {C_GREEN}● RUNNING{C_RESET}")
        print(f"  {C_BOLD}URL:{C_RESET}                {C_CYAN}{local_url}{C_RESET}")
        print(f"  {C_BOLD}Process IDs:{C_RESET}        {', '.join(str(p) for p in pids)}")
    else:
        print(f"  {C_BOLD}FastAPI Server:{C_RESET}     {C_RED}○ STOPPED{C_RESET}")
        print(f"  {C_BOLD}Expected port:{C_RESET}      {port}")

    print(f"  {C_BOLD}Mode / SSL:{C_RESET}         {mode} | SSL: {'ON' if use_ssl else 'OFF'} | Autoreload: {'ON' if reload_on else 'OFF'}")
    print("")
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Assistant CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("service", nargs="?", help="Service to start")
    start_parser.set_defaults(func=cmd_start)
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("service", nargs="?", help="Service to stop")
    stop_parser.set_defaults(func=cmd_stop)
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart services")
    restart_parser.add_argument("service", nargs="?", help="Service to restart")
    restart_parser.set_defaults(func=cmd_restart)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show status")
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if hasattr(args, "func"):
        return args.func(args)
    return 0

if __name__ == "__main__":
    sys.exit(main())
