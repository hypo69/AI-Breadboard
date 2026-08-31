# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Кроссплатформенная система установки AI Breadboard
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: installer.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Кроссплатформенная система установки AI Breadboard.

Портировано со старого install.ps1 для работы на Windows, Linux и macOS.

Использование:
    python scripts/cli/installer.py
    python scripts/cli/installer.py --lang ru
    python scripts/cli/installer.py --skip-models
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cli.paths import get_paths, CrossPlatformPaths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import which, run_command

class Language(Enum):
    """Поддерживаемые языки"""
    EN = "en"
    RU = "ru"
    ES = "es"
    HE = "he"

# Сообщения на разных языках
MESSAGES = {
    "en": {
        "welcome": "🎯 AI Breadboard Installation",
        "step_venv": "[1/6] Creating Python virtual environment...",
        "step_deps": "[2/6] Installing dependencies...",
        "step_certs": "[3/6] Setting up SSL certificates...",
        "step_cli": "[4/6] Configuring CLI assistant...",
        "step_verify": "[5/6] Verifying installation...",
        "step_models": "[6/6] Downloading AI models (optional)...",
        "success": "✅ Installation completed successfully!",
        "error": "❌ Installation failed:",
        "abort": "⚠️  Installation aborted by user",
    },
    "ru": {
        "welcome": "🎯 Установка AI Breadboard",
        "step_venv": "[1/6] Создание виртуального окружения Python...",
        "step_deps": "[2/6] Установка зависимостей...",
        "step_certs": "[3/6] Настройка SSL сертификатов...",
        "step_cli": "[4/6] Configuration CLI ассистента...",
        "step_verify": "[5/6] Check установки...",
        "step_models": "[6/6] Loading моделей ИИ (опционально)...",
        "success": "✅ Установка завершена successfully!",
        "error": "❌ Error при установке:",
        "abort": "⚠️  Установка отменена пользователем",
    },
}

class Installer:
    """Главный class установщика"""
    
    def __init__(self, language: str = "en", install_dir: Optional[Path] = None):
        self.language = Language[language.upper()] if language.upper() in Language.__members__ else Language.EN
        self.messages = MESSAGES.get(self.language.value, MESSAGES["en"])
        self.install_dir = install_dir or self._get_default_install_dir()
        self.venv_dir = self.install_dir / "venv"
        self.config_mgr = get_config_manager()
    
    def msg(self, key: str) -> str:
        """Получить сообщение на текущем языке"""
        return self.messages.get(key, key)
    
    @staticmethod
    def _get_default_install_dir() -> Path:
        """Получить директорию установки по умолчанию"""
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\AI-Breadboard
            localappdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(localappdata) / "AI-Breadboard"
        else:
            # Linux/macOS: ~/AI-Breadboard или ~/.local/share/AI-Breadboard
            return Path.home() / "AI-Breadboard"
    
    def print_header(self):
        """Печать заголовка установки"""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + self.msg("welcome").center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"Установка в: {self.install_dir}")
        print()
    
    def create_venv(self) -> bool:
        """Создать виртуальное окружение"""
        print(self.msg("step_venv"))
        
        try:
            # Удалить старое venv если существует
            if self.venv_dir.exists():
                print(f"  Удаление старого venv...", end=" ", flush=True)
                shutil.rmtree(self.venv_dir)
                print("[OK]")
            
            # Создать новое venv
            print(f"  Создание venv...", end=" ", flush=True)
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_dir)],
                check=True,
                capture_output=True
            )
            print("[OK]")
            print()
            return True
        
        except Exception as e:
            print(f"[ERROR] {e}")
            print()
            return False
    
    def install_dependencies(self) -> bool:
        """Установить зависимости"""
        print(self.msg("step_deps"))
        
        try:
            # Получить путь до pip в venv
            if sys.platform == "win32":
                pip_exe = self.venv_dir / "Scripts" / "pip.exe"
            else:
                pip_exe = self.venv_dir / "bin" / "pip"
            
            if not pip_exe.exists():
                print(f"  [ERROR] pip не найден в venv")
                print()
                return False
            
            # Файлы requirements
            req_files = [
                self.install_dir / "requirements.txt",
                self.install_dir / "install" / "req" / "requirements-core.txt",
                self.install_dir / "install" / "req" / "requirements-ai.txt",
            ]
            
            for req_file in req_files:
                if req_file.exists():
                    print(f"  Установка из {req_file.name}...", end=" ", flush=True)
                    result = subprocess.run(
                        [str(pip_exe), "install", "-r", str(req_file)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print("[OK]")
                    else:
                        print(f"[WARN]")
                        if result.stderr:
                            print(f"    {result.stderr[:100]}")
            
            print()
            return True
        
        except Exception as e:
            print(f"[ERROR] {e}")
            print()
            return False
    
    def setup_ssl_certificates(self) -> bool:
        """Настроить SSL сертификаты"""
        print(self.msg("step_certs"))
        
        try:
            certs_dir = CrossPlatformPaths().certs_dir
            certs_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"  Директория сертификатов: {certs_dir}")
            
            # Проверить наличие mkcert
            if which("mkcert"):
                print(f"  mkcert найден, генерация сертификатов...", end=" ", flush=True)
                subprocess.run(
                    ["mkcert", "-install"],
                    cwd=str(certs_dir),
                    capture_output=True
                )
                subprocess.run(
                    ["mkcert", "-key-file", str(certs_dir / "localhost+2-key.pem"), 
                     "-cert-file", str(certs_dir / "localhost+2.pem"),
                     "localhost", "127.0.0.1", "::1"],
                    cwd=str(certs_dir),
                    capture_output=True
                )
                print("[OK]")
            else:
                print(f"  mkcert не установлен (опционально)")
                print(f"  Установка: https://github.com/FiloSottile/mkcert")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] Error при настройке сертификатов: {e}")
            print()
            return True  # Не критично
    
    def configure_cli(self) -> bool:
        """Configuration CLI ассистента"""
        print(self.msg("step_cli"))
        
        try:
            from scripts.cli.utils import ensure_in_path, add_to_env_var
            
            # Добавить в PATH
            print(f"  Добавление в PATH...", end=" ", flush=True)
            if ensure_in_path(self.install_dir / "assist"):
                print("[OK]")
            else:
                print("[WARN]")
            
            # Установить переменные окружения
            print(f"  Установка переменных окружения...", end=" ", flush=True)
            add_to_env_var("AIBREADBOARD_DIR", str(self.install_dir))
            add_to_env_var("PYTHONPATH", str(self.install_dir))
            print("[OK]")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] {e}")
            print()
            return True  # Не критично
    
    def verify_installation(self) -> bool:
        """Проверить установку"""
        print(self.msg("step_verify"))
        
        try:
            # Получить Python в venv
            if sys.platform == "win32":
                python_exe = self.venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_dir / "bin" / "python"
            
            if not python_exe.exists():
                print(f"  [ERROR] Python не найден в venv")
                print()
                return False
            
            # Проверить основные модули
            print(f"  Check зависимостей...", end=" ", flush=True)
            result = subprocess.run(
                [str(python_exe), "-c", "import fastapi, uvicorn, dotenv; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "OK" in result.stdout:
                print("[OK]")
            else:
                print("[WARN] Некоторые зависимости могут быть не установлены")
            
            # Проверить assist
            assist_file = self.install_dir / "assist"
            if assist_file.exists() or (self.install_dir / "assist.cmd").exists():
                print(f"  Check assist CLI...", end=" ", flush=True)
                print("[OK]")
            else:
                print(f"  [WARN] assist не найден")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] {e}")
            print()
            return True  # Не критично
    
    def download_models(self, skip: bool = False) -> bool:
        """Загрузить модели (опционально)"""
        if skip:
            print(self.msg("step_models"))
            print(f"  Пропуск (использовано --skip-models)")
            print()
            return True
        
        print(self.msg("step_models"))
        
        # TODO: Реализовать загрузку моделей
        print(f"  TODO: Реализовать загрузку моделей")
        print()
        return True
    
    def run(self, skip_models: bool = False, skip_venv: bool = False, 
            skip_deps: bool = False, skip_certs: bool = False) -> int:
        """Запустить установку"""
        self.print_header()
        
        try:
            # Создать директорию установки
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Шаги установки
            steps = [
                (not skip_venv, self.create_venv, "venv"),
                (not skip_deps, self.install_dependencies, "dependencies"),
                (not skip_certs, self.setup_ssl_certificates, "SSL certificates"),
                (True, self.configure_cli, "CLI"),
                (True, self.verify_installation, "verification"),
                (True, lambda: self.download_models(skip=skip_models), "models"),
            ]
            
            for should_run, step_func, step_name in steps:
                if should_run:
                    if not step_func():
                        print(f"{self.msg('error')} {step_name}")
                        return 1
            
            # Success
            print("╔" + "═" * 68 + "╗")
            print("║" + self.msg("success").center(68) + "║")
            print("╚" + "═" * 68 + "╝")
            print()
            print(f"Далее:")
            print(f"  1. Перейдите в директорию установки:")
            print(f"     cd {self.install_dir}")
            print(f"  2. Активируйте venv:")
            if sys.platform == "win32":
                print(f"     venv\\Scripts\\activate")
            else:
                print(f"     source venv/bin/activate")
            print(f"  3. Запустите сервер:")
            print(f"     python run.py")
            print()
            return 0
        
        except KeyboardInterrupt:
            print()
            print(self.msg("abort"))
            print()
            return 1
        except Exception as e:
            print(f"{self.msg('error')} {e}")
            return 1

def main():
    """Главная function"""
    parser = argparse.ArgumentParser(
        description="Установщик AI Breadboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cli/installer.py
  python scripts/cli/installer.py --lang ru
  python scripts/cli/installer.py --install-dir /path/to/install
  python scripts/cli/installer.py --skip-models
        """
    )
    
    parser.add_argument(
        "--lang",
        choices=["en", "ru", "es", "he"],
        default="en",
        help="Язык установки (по умолчанию: en)"
    )
    
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=None,
        help="Директория установки"
    )
    
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Пропустить загрузку моделей"
    )
    
    parser.add_argument(
        "--skip-venv",
        action="store_true",
        help="Пропустить создание venv"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Пропустить установку зависимостей"
    )
    
    parser.add_argument(
        "--skip-certs",
        action="store_true",
        help="Пропустить настройку сертификатов"
    )
    
    args = parser.parse_args()
    
    installer = Installer(
        language=args.lang,
        install_dir=args.install_dir
    )
    
    return installer.run(
        skip_models=args.skip_models,
        skip_venv=args.skip_venv,
        skip_deps=args.skip_deps,
        skip_certs=args.skip_certs,
    )

if __name__ == "__main__":
    sys.exit(main())
