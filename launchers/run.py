# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-platform FastAPI server launcher with setup
# =============================================================================
# Description:
#   Main launcher for starting FastAPI server with interactive setup options.
#   Ported from legacy run.ps1 with support for Windows, Linux and macOS.
#   Provides virtual environment detection, dependency checking, port management,
#   and configuration setup with both interactive and non-interactive modes.
#
#   Usage:
#       python launchers/run.py
#       python launchers/run.py --host 0.0.0.0 --port 8000
#       python launchers/run.py --non-interactive
#       python launchers/run.py --help
#
# File: run.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Adding root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cli.paths import init_paths, get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import (
    find_available_port,
    get_process_on_port,
    kill_process,
    run_command
)

class ServerLauncher:
    """Launcher for starting FastAPI server"""
    
    def __init__(self):
        self.paths = init_paths()
        self.config_mgr = get_config_manager()
        self.config = self.config_mgr.load_config()
        self.server_cfg = self.config.get("server", {})
        self.ai_cfg = self.config.get("ai", {})
    
    def get_default_host(self) -> str:
        """Getting default host from config.json"""
        return str(self.server_cfg.get("host", "0.0.0.0"))
    
    def get_default_port(self) -> int:
        """Getting default port from config.json"""
        return int(self.server_cfg.get("port", 8000))
    
    def get_local_ips(self) -> list:
        """Getting local IP addresses for hints"""
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return [local_ip] if local_ip and local_ip != "127.0.0.1" else []
        except Exception:
            return []
    
    def check_venv(self) -> str:
        """Checking virtual environment"""
        if self.paths.venv_python.exists():
            print(f"    [OK] Virtual environment found")
            print(f"    Python: {self.paths.venv_python}")
            return str(self.paths.venv_python)
        else:
            print(f"    [WARN] Virtual environment not found")
            # Using current Python
            python_exe = sys.executable
            print(f"    Using system Python: {python_exe}")
            return python_exe
    
    def check_dependencies(self, python_exe: str) -> bool:
        """Checking dependencies"""
        print("    [*] Checking dependencies...", end=" ", flush=True)
        try:
            result = subprocess.run(
                [python_exe, "-c", "import fastapi, uvicorn, dotenv, jwt; print('OK')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("[OK]")
                return True
            else:
                print("[WARN] Некоторые зависимости не установлены")
                print("    Установите: pip install -r requirements.txt")
                return False
        except Exception as e:
            print(f"[ERROR] {e}")
            return False
    
    def load_env_vars(self) -> dict:
        """Загрузить переменные окружения из .env"""
        env_vars = {}
        env_file = self.paths.env_file
        
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip().strip('"').strip("'")
            except Exception as e:
                print(f"    [WARN] Error чтения .env: {e}")
        
        return env_vars
    
    def check_port(self, port: int) -> bool:
        """Проверить и освободить порт если нужно"""
        print(f"    [*] Check порта {port}...", end=" ", flush=True)
        
        proc_info = get_process_on_port(port)
        if proc_info:
            pid, proc_name = proc_info
            print(f"\n    [WARN] Порт занят процессом {proc_name} (PID: {pid})")
            print(f"    Shutdown процесса...", end=" ", flush=True)
            
            if kill_process(pid, force=False):
                print("[OK]")
                return True
            else:
                print("[FAILED]")
                # Попробовать force
                if kill_process(pid, force=True):
                    print("    [FORCE] Процесс принудительно завершен")
                    return True
                else:
                    print("    [ERROR] Не удалось освободить порт")
                    return False
        else:
            print("[FREE]")
            return True
    
    def interactive_mode(self, default_host: str, default_port: int) -> Tuple[str, int]:
        """Интерактивный выбор параметров"""
        print()
        print("─" * 70)
        print(" 🌐 ИНТЕРАКТИВНЫЙ ВЫБОР АДРЕСА И ПОРТА")
        print("─" * 70)
        print("Выберите сетевой интерфейс для запуска сервера:")
        print("  [1] 0.0.0.0   - Все сетевые интерфейсы (доступен с других ПК)")
        
        local_ips = self.get_local_ips()
        if local_ips:
            print(f"                  (Ваш IP в локальной сети: {local_ips[0]})")
        
        print("  [2] 127.0.0.1 - Только локально (localhost)")
        print("  [3] Ввести произвольный IP вручную")
        print(f"  [Enter] По умолчанию: {default_host}")
        print()
        
        choice = input("Адрес / Вариант: ").strip()
        
        if choice == "1":
            host = "0.0.0.0"
        elif choice == "2":
            host = "127.0.0.1"
        elif choice == "3":
            custom = input("  Введите IP-адрес или хост: ").strip()
            host = custom if custom else default_host
        elif choice:
            host = choice
        else:
            host = default_host
        
        # Выбор порта
        port_str = input(f"Порт сервера [Enter = {default_port}]: ").strip()
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                port = default_port
        else:
            port = default_port
        
        return host, port
    
    def run_uvicorn(self, python_exe: str, host: str, port: int, ssl: bool = False) -> int:
        """Запустить uvicorn сервер"""
        print()
        print("═" * 70)
        print(" 🚀 ЗАПУСК FastAPI СЕРВЕРА")
        print("═" * 70)
        print()
        
        use_reload = bool(self.server_cfg.get("reload", True))
        debug = bool(self.server_cfg.get("debug", True))
        
        # Построить команду
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
        
        if ssl:
            certs_dir = self.paths.certs_dir
            cert_file = certs_dir / "localhost+2.pem"
            key_file = certs_dir / "localhost+2-key.pem"
            
            if cert_file.exists() and key_file.exists():
                cmd.extend([
                    "--ssl-keyfile", str(key_file),
                    "--ssl-certfile", str(cert_file),
                ])
                print(f"  SSL: ВКЛЮЧЕН")
                print(f"    Сертификат: {cert_file}")
                print(f"    Ключ: {key_file}")
            else:
                print(f"  SSL: ОТКЛЮЧЕН (сертификаты не найдены)")
        
        print(f"  Хост: {host}")
        print(f"  Порт: {port}")
        print(f"  АвтоLoading: {'ВКЛ' if use_reload else 'ВЫКЛ'}")
        print(f"  Отладка: {'ВКЛ' if debug else 'ВЫКЛ'}")
        print()
        print("  Нажмите Ctrl+C для остановки сервера")
        print()
        print("=" * 70)
        print()
        
        # Запустить сервер
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
            print(" ⏹ Сервер остановлен пользователем")
            print("═" * 70)
            return 0
        except Exception as e:
            print(f"ERROR: {e}")
            return 1
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, non_interactive: bool = False) -> int:
        """Главная function запуска"""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " ЗАПУСК FastAPI СЕРВЕРА - ИНТЕРАКТИВНЫЙ ЛОНЧЕР".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        # Check виртуального окружения
        print("[1/5] Check виртуального окружения...")
        python_exe = self.check_venv()
        print()
        
        # Check зависимостей
        print("[2/5] Check зависимостей...")
        if not self.check_dependencies(python_exe):
            print("    [!] Некоторые зависимости могут быть не установлены")
        print()
        
        # Loading конфигурации
        print("[3/5] Loading конфигурации...")
        env_vars = self.load_env_vars()
        use_ssl = bool(self.server_cfg.get("use_ssl", True))
        if "USE_SSL" in env_vars:
            use_ssl = env_vars["USE_SSL"].lower() in ("true", "1", "yes")
        print(f"    [OK] Configuration загружена (SSL: {'ВКЛ' if use_ssl else 'ВЫКЛ'})")
        print()
        
        # Определение параметров
        default_host = self.get_default_host()
        default_port = self.get_default_port()
        
        if host is None:
            host = default_host
        if port is None:
            port = default_port
        
        # Интерактивный выбор
        print("[4/5] Выбор параметров...")
        if not non_interactive and host == default_host:
            host, port = self.interactive_mode(default_host, default_port)
        print(f"    Parameters: {host}:{port}")
        print()
        
        # Check порта
        print("[5/5] Check доступности порта...")
        if not self.check_port(port):
            print("    [ERROR] Не удалось освободить порт")
            return 1
        print()
        
        # Запуск сервера
        return self.run_uvicorn(python_exe, host, port, ssl=use_ssl)

def main():
    """Главная function"""
    parser = argparse.ArgumentParser(
        description="Лончер для запуска FastAPI сервера",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launchers/run.py
  python launchers/run.py --host 0.0.0.0 --port 8000
  python launchers/run.py --non-interactive
  python launchers/run.py --help
        """
    )
    
    parser.add_argument("--host", "-H", type=str, default=None, help="IP адрес привязки (0.0.0.0, 127.0.0.1)")
    parser.add_argument("--port", "-P", type=int, default=None, help="Порт сервера (по умолчанию: из config.json или 8000)")
    parser.add_argument("--non-interactive", action="store_true", help="Пропустить интерактивные запросы")
    
    args = parser.parse_args()
    
    launcher = ServerLauncher()
    return launcher.run(host=args.host, port=args.port, non_interactive=args.non_interactive)

if __name__ == "__main__":
    sys.exit(main())
