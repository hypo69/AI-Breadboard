# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Lightweight FastAPI server launcher with minimal resources
# =============================================================================
# Description:
#   Lightweight launcher for running FastAPI server without auto-loading features.
#   Useful for minimal resource consumption on low-end machines and development environments.
#   Provides quick server startup with port conflict detection and management.
#
#   Usage:
#       python launchers/run_light_server.py
#       python launchers/run_light_server.py --host 127.0.0.1 --port 8000
#
# File: run_light_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cli.paths import init_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import get_process_on_port, kill_process

class LightServerLauncher:
    """Lightweight launcher for FastAPI"""
    
    def __init__(self):
        self.paths = init_paths()
        self.config_mgr = get_config_manager()
        self.config = self.config_mgr.load_config()
        self.server_cfg = self.config.get("server", {})
    
    def run(self, host: str = "", port: int = 0) -> int:
        """Running lightweight server"""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " STARTING LIGHTWEIGHT FastAPI SERVER".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        # Parameters
        if not host:
            host = str(self.server_cfg.get("host", "0.0.0.0"))
        if port == 0:
            port = int(self.server_cfg.get("port", 8000))
        
        python_exe = str(self.paths.venv_python) if self.paths.venv_python.exists() else sys.executable
        
        print(f"[1/2] Checking port {port}...", end=" ", flush=True)
        proc_info = get_process_on_port(port)
        if proc_info:
            pid, proc_name = proc_info
            print(f"[OCCUPIED]")
            if kill_process(pid, force=True):
                print(f"    Process terminated")
            else:
                print(f"    WARN: Failed to free port")
                return 1
        else:
            print("[FREE]")
        print()
        
        print("[2/2] Запуск сервера (облегченный режим)...")
        print()
        
        # Команда (без reload и debug для экономии ресурсов)
        cmd = [
            python_exe,
            "-m", "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
            "--workers", "1",
            "--log-level", "warning",  # Меньше логов
        ]
        
        print(f"  Хост: {host}")
        print(f"  Порт: {port}")
        print(f"  Режим: Облегченный (без reload, 1 worker)")
        print()
        print("=" * 70)
        print()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.paths.project_root),
                check=False
            )
            return result.returncode
        except KeyboardInterrupt:
            print()
            print()
            print("═" * 70)
            print(" ⏹ Сервер остановлен")
            print("═" * 70)
            return 0
        except Exception as e:
            print(f"ERROR: {e}")
            return 1

def main():
    """Главная function"""
    parser = argparse.ArgumentParser(
        description="Облегченный лончер для FastAPI"
    )
    
    parser.add_argument("--host", "-H", type=str, default="", help="IP адрес")
    parser.add_argument("--port", "-P", type=int, default=0, help="Порт")
    
    args = parser.parse_args()
    
    launcher = LightServerLauncher()
    return launcher.run(host=args.host, port=args.port)

if __name__ == "__main__":
    sys.exit(main())
