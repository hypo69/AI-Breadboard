# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-platform FastAPI launcher using uvicorn
# =============================================================================
# Description:
#   Launcher for running FastAPI application via uvicorn on Windows, Linux, and macOS.
#   Ported from legacy Run-Unicorn.ps1 with support for configurable host and port,
#   port conflict detection and process termination, virtual environment detection.
#
#   Usage:
#       python launchers/run_unicorn.py
#       python launchers/run_unicorn.py --host 127.0.0.1 --port 8000
#
# File: run_unicorn.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import sys
import subprocess
from pathlib import Path

# Adding root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cli.paths import init_paths, get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import get_process_on_port, kill_process

class UnicornLauncher:
    """Launcher for running FastAPI via uvicorn"""
    
    def __init__(self):
        self.paths = init_paths()
        self.config_mgr = get_config_manager()
        self.config = self.config_mgr.load_config()
        self.server_cfg = self.config.get("server", {})
    
    def get_default_host(self) -> str:
        """Getting default host"""
        return str(self.server_cfg.get("host", "0.0.0.0"))
    
    def get_default_port(self) -> int:
        """Getting default port"""
        return int(self.server_cfg.get("port", 8000))
    
    def check_venv(self) -> str:
        """Checking virtual environment"""
        if self.paths.venv_python.exists():
            return str(self.paths.venv_python)
        else:
            return sys.executable
    
    def check_port(self, port: int) -> bool:
        """Checking and freeing port if needed"""
        proc_info = get_process_on_port(port)
        if proc_info:
            pid, proc_name = proc_info
            print(f"    [WARN] Port {port} is occupied by process {proc_name} (PID: {pid})")
            if kill_process(pid, force=False):
                print(f"    [OK] Process terminated")
                return True
            elif kill_process(pid, force=True):
                print(f"    [FORCE] Process forcefully terminated")
                return True
            else:
                print(f"    [ERROR] Failed to free port")
                return False
        return True
    
    def run(self, host: str = "", port: int = 0) -> int:
        """Running uvicorn server"""
        print()
        
        # Определить Parameters
        if not host:
            host = self.get_default_host()
        if port == 0:
            port = self.get_default_port()
        
        print("[1/3] Check виртуального окружения...")
        python_exe = self.check_venv()
        print(f"    [OK] Python: {python_exe}")
        print()
        
        print("[2/3] Check доступности порта...")
        if not self.check_port(port):
            return 1
        print()
        
        print("[3/3] Запуск uvicorn...")
        print()
        
        use_ssl = bool(self.server_cfg.get("use_ssl", True))
        use_reload = bool(self.server_cfg.get("reload", True))
        debug = bool(self.server_cfg.get("debug", True))
        
        # Построить команду uvicorn
        cmd = [
            python_exe,
            "-m", "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
        ]
        
        if use_reload:
            cmd.append("--reload")
        
        if debug:
            cmd.extend(["--log-level", "debug"])
        else:
            cmd.extend(["--log-level", "info"])
        
        # SSL
        if use_ssl:
            certs_dir = self.paths.certs_dir
            cert_file = certs_dir / "localhost+2.pem"
            key_file = certs_dir / "localhost+2-key.pem"
            
            if cert_file.exists() and key_file.exists():
                cmd.extend([
                    "--ssl-keyfile", str(key_file),
                    "--ssl-certfile", str(cert_file),
                ])
        
        print(f"  Хост: {host}")
        print(f"  Порт: {port}")
        print(f"  SSL: {'ВКЛ' if use_ssl else 'ВЫКЛ'}")
        print(f"  АвтоLoading: {'ВКЛ' if use_reload else 'ВЫКЛ'}")
        print(f"  Отладка: {'ВКЛ' if debug else 'ВЫКЛ'}")
        print()
        print("  Нажмите Ctrl+C для остановки сервера")
        print()
        print("=" * 70)
        print()
        
        # Запустить
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
        description="Лончер для запуска FastAPI через uvicorn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launchers/run_unicorn.py
  python launchers/run_unicorn.py --host 0.0.0.0 --port 8000
  python launchers/run_unicorn.py --host 127.0.0.1
        """
    )
    
    parser.add_argument("--host", "-H", type=str, default="", help="IP адрес привязки")
    parser.add_argument("--port", "-P", type=int, default=0, help="Порт сервера")
    
    args = parser.parse_args()
    
    launcher = UnicornLauncher()
    return launcher.run(host=args.host, port=args.port)

if __name__ == "__main__":
    sys.exit(main())
