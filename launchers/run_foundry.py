# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Microsoft AI Foundry launcher for multiple platforms
# =============================================================================
# Description:
#   Launcher for running Microsoft AI Foundry with cross-platform support.
#   Supports Windows, Linux and macOS with configuration-driven startup
#   and process management capabilities.
#
#   Usage:
#       python launchers/run_foundry.py start
#       python launchers/run_foundry.py stop
#
# File: run_foundry.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import sys
import subprocess
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cli.paths import init_paths
from scripts.cli.config import get_config_manager

class FoundryLauncher:
    """Launcher for running AI Foundry"""
    
    def __init__(self):
        self.paths = init_paths()
        self.config_mgr = get_config_manager()
        self.config = self.config_mgr.load_config()
        self.ai_cfg = self.config.get("ai", {})
    
    def start(self, action: str = "start") -> int:
        """Starting or stopping Foundry"""
        foundry_url = str(self.ai_cfg.get("foundry_base_url", "http://localhost:54837"))
        use_foundry = bool(self.ai_cfg.get("use_foundry", False))
        
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + f" {action.upper()} MICROSOFT AI FOUNDRY".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        if not use_foundry:
            print("⚠️  Microsoft AI Foundry is disabled in config.json")
            print("   Enable it: assist config set ai.use_foundry true")
            print()
            return 1
        
        print(f"Foundry URL: {foundry_url}")
        print()
        
        # Linux/macOS requires foundry CLI installation
        if sys.platform != "win32":
            print("ℹ️  On Linux/macOS use:")
            print("   pip install microsoft-ai-foundry")
            print("   foundry server start")
            print()
            print("ℹ️  Or use Docker:")
            print("   docker run -p 54837:54837 mcr.microsoft.com/windows/servercore:latest")
            print()
            print("TODO: Implement cross-platform Foundry support")
            return 1
        
        # Windows
        print("[*] Starting Foundry on Windows...")
        
        # Attempting to find foundry.exe
        try:
            result = subprocess.run(
                ["foundry", "server", action],
                check=False,
                capture_output=False
            )
            return result.returncode
        except FileNotFoundError:
            print("ERROR: foundry не найдена в PATH")
            print("Установка: https://github.com/microsoft/ai-foundry")
            return 1
        except Exception as e:
            print(f"ERROR: {e}")
            return 1
    
    def stop(self) -> int:
        """Остановить Foundry"""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " ОСТАНОВКА MICROSOFT AI FOUNDRY".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        # Windows
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["foundry", "server", "stop"],
                    check=False,
                    capture_output=False
                )
                return result.returncode
            except Exception as e:
                print(f"ERROR: {e}")
                return 1
        else:
            print("TODO: Реализовать остановку на Linux/macOS")
            return 1

def main():
    """Главная function"""
    parser = argparse.ArgumentParser(
        description="Лончер для Microsoft AI Foundry"
    )
    
    parser.add_argument(
        "action",
        nargs="?",
        default="start",
        choices=["start", "stop"],
        help="Действие (start или stop)"
    )
    
    args = parser.parse_args()
    
    launcher = FoundryLauncher()
    
    if args.action == "start":
        return launcher.start()
    elif args.action == "stop":
        return launcher.stop()
    else:
        return launcher.start()

if __name__ == "__main__":
    sys.exit(main())
