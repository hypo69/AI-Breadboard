# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Кроссплатформенный установщик AI Breadboard
# =============================================================================
# Description:
#   Универсальный установщик для Windows, Linux и macOS с поддержкой
#   мультиязычности (RU/EN/ES/HE) и модульной архитектурой.
#
# Examples:
#   python install.py
#   python install.py --language en --install-dir /opt/ai-breadboard
#
# File: install.py
# Project: AI Breadboard
# Package: Installation
# Module: Core
# Class: Installer
# Function: main
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from enum import StrEnum


class Language(StrEnum):
    """Поддерживаемые языки установщика."""
    RU = "ru"
    EN = "en"
    ES = "es"
    HE = "he"


class I18N:
    """Система мультиязычности установщика."""

    MESSAGES: Dict[str, Dict[str, str]] = {
        "ru": {
            "welcome": "🚀 Добро пожаловать в установщик AI Breadboard",
            "select_lang": "Выберите язык установки / Select language:",
            "lang_selected": "✓ Выбран язык: {lang}",
            "step_1": "[1/6] Проверка Python интерпретатора...",
            "step_1_found": "✓ Найден Python {version}: {path}",
            "step_1_not_found": "✗ Python не найден. Установите Python 3.10+",
            "step_2": "[2/6] Создание виртуального окружения...",
            "step_2_ok": "✓ Виртуальное окружение создано",
            "step_2_exists": "✓ Виртуальное окружение уже существует",
            "step_3": "[3/6] Обновление pip и инструментов...",
            "step_3_ok": "✓ pip обновлен",
            "step_4": "[4/6] Установка зависимостей...",
            "step_4_menu": "Выберите профиль установки:",
            "step_4_opt_1": "[1] Полная установка (рекомендуется)",
            "step_4_opt_2": "[2] Только Core",
            "step_4_opt_3": "[3] Core + AI",
            "step_4_opt_4": "[4] Полная + Dev",
            "step_4_opt_5": "[5] Пропустить",
            "step_4_ok": "✓ Зависимости установлены",
            "step_5": "[5/6] Проверка SSL сертификатов...",
            "step_5_ok": "✓ SSL сертификаты найдены",
            "step_6": "[6/6] Финальная проверка...",
            "step_6_ok": "✓ Окружение готово к работе",
            "finish": "✅ Установка завершена успешно!",
            "error": "✗ Ошибка: {msg}",
        },
        "en": {
            "welcome": "🚀 Welcome to AI Breadboard Installer",
            "select_lang": "Select installation language / Выберите язык:",
            "lang_selected": "✓ Selected language: {lang}",
            "step_1": "[1/6] Checking Python interpreter...",
            "step_1_found": "✓ Found Python {version}: {path}",
            "step_1_not_found": "✗ Python not found. Install Python 3.10+",
            "step_2": "[2/6] Creating virtual environment...",
            "step_2_ok": "✓ Virtual environment created",
            "step_2_exists": "✓ Virtual environment already exists",
            "step_3": "[3/6] Upgrading pip and tools...",
            "step_3_ok": "✓ pip upgraded",
            "step_4": "[4/6] Installing dependencies...",
            "step_4_menu": "Select installation profile:",
            "step_4_opt_1": "[1] Full installation (recommended)",
            "step_4_opt_2": "[2] Core only",
            "step_4_opt_3": "[3] Core + AI",
            "step_4_opt_4": "[4] Full + Dev",
            "step_4_opt_5": "[5] Skip",
            "step_4_ok": "✓ Dependencies installed",
            "step_5": "[5/6] Checking SSL certificates...",
            "step_5_ok": "✓ SSL certificates found",
            "step_6": "[6/6] Final verification...",
            "step_6_ok": "✓ Environment ready",
            "finish": "✅ Installation completed successfully!",
            "error": "✗ Error: {msg}",
        },
        "es": {
            "welcome": "🚀 Bienvenido al instalador de AI Breadboard",
            "select_lang": "Seleccione idioma / Select language:",
            "lang_selected": "✓ Idioma seleccionado: {lang}",
            "step_1": "[1/6] Verificando intérprete Python...",
            "step_1_found": "✓ Python {version} encontrado: {path}",
            "step_1_not_found": "✗ Python no encontrado. Instale Python 3.10+",
            "step_2": "[2/6] Creando entorno virtual...",
            "step_2_ok": "✓ Entorno virtual creado",
            "step_2_exists": "✓ Entorno virtual ya existe",
            "step_3": "[3/6] Actualizando pip...",
            "step_3_ok": "✓ pip actualizado",
            "step_4": "[4/6] Instalando dependencias...",
            "step_4_menu": "Seleccione perfil de instalación:",
            "step_4_opt_1": "[1] Instalación completa (recomendado)",
            "step_4_opt_2": "[2] Solo Core",
            "step_4_opt_3": "[3] Core + AI",
            "step_4_opt_4": "[4] Completo + Dev",
            "step_4_opt_5": "[5] Omitir",
            "step_4_ok": "✓ Dependencias instaladas",
            "step_5": "[5/6] Verificando certificados SSL...",
            "step_5_ok": "✓ Certificados SSL encontrados",
            "step_6": "[6/6] Verificación final...",
            "step_6_ok": "✓ Entorno listo",
            "finish": "✅ ¡Instalación completada exitosamente!",
            "error": "✗ Error: {msg}",
        },
        "he": {
            "welcome": "🚀 ברוכים הבאים למתקין AI Breadboard",
            "select_lang": "בחר שפה / Select language:",
            "lang_selected": "✓ שפה נבחרת: {lang}",
            "step_1": "[1/6] בדיקת מתורגמן Python...",
            "step_1_found": "✓ Python {version} נמצא: {path}",
            "step_1_not_found": "✗ Python לא נמצא. התקן Python 3.10+",
            "step_2": "[2/6] יצירת סביבה וירטואלית...",
            "step_2_ok": "✓ סביבה וירטואלית נוצרה",
            "step_2_exists": "✓ סביבה וירטואלית כבר קיימת",
            "step_3": "[3/6] שדרוג pip...",
            "step_3_ok": "✓ pip שודרג",
            "step_4": "[4/6] התקנת תלויות...",
            "step_4_menu": "בחר פרופיל התקנה:",
            "step_4_opt_1": "[1] התקנה מלאה (מומלץ)",
            "step_4_opt_2": "[2] Core בלבד",
            "step_4_opt_3": "[3] Core + AI",
            "step_4_opt_4": "[4] מלא + Dev",
            "step_4_opt_5": "[5] דלג",
            "step_4_ok": "✓ תלויות הותקנו",
            "step_5": "[5/6] בדיקת תעודות SSL...",
            "step_5_ok": "✓ תעודות SSL נמצאו",
            "step_6": "[6/6] אימות סופי...",
            "step_6_ok": "✓ סביבה מוכנה",
            "finish": "✅ ההתקנה הושלמה בהצלחה!",
            "error": "✗ שגיאה: {msg}",
        },
    }

    def __init__(self, language: Language = Language.EN):
        """Initialization системы мультиязычности.

        Args:
            language (Language): Выбранный язык установки.
        """
        self.language: Language = language

    def msg(self, key: str, **kwargs) -> str:
        """Получение переведенного сообщения.

        Args:
            key (str): Ключ сообщения в словаре.
            **kwargs: Параметры для форматирования строки.

        Returns:
            str: Переведенное сообщение.
        """
        message: str = self.MESSAGES.get(self.language.value, {}).get(key, key)
        return message.format(**kwargs) if kwargs else message


class Installer:
    """Основной класс установщика AI Breadboard."""

    def __init__(self, language: Language = Language.EN):
        """Initialization установщика.

        Args:
            language (Language): Язык установки.
        """
        self.i18n: I18N = I18N(language)
        self.platform_name: str = platform.system()
        self.install_dir: Path = Path()
        self.venv_dir: Path = Path()
        self.python_path: Path = Path()

    def msg(self, key: str, **kwargs) -> str:
        """Получение сообщения через i18n.

        Args:
            key (str): Ключ сообщения.
            **kwargs: Параметры форматирования.

        Returns:
            str: Переведенное сообщение.
        """
        return self.i18n.msg(key, **kwargs)

    def find_python(self) -> Optional[Path]:
        """Поиск интерпретатора Python.

        Returns:
            Optional[Path]: Путь к Python или пустое значение.

        Examples:
            >>> installer = Installer()
            >>> python_path = installer.find_python()
            >>> print(python_path)
        """
        print(self.msg("step_1"))

        preferred_versions: List[str] = ["3.13", "3.12", "3.11", "3.10"]

        for version in preferred_versions:
            try:
                result: subprocess.CompletedProcess = subprocess.run(
                    ["python" + version, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    python_exe: Path = shutil.which("python" + version)
                    if python_exe:
                        print(self.msg("step_1_found", version=version, path=python_exe))
                        return Path(python_exe)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        python_exe: Optional[str] = shutil.which("python")
        if python_exe:
            print(self.msg("step_1_found", version="3.x", path=python_exe))
            return Path(python_exe)

        print(self.msg("step_1_not_found"))
        return False

    def create_venv(self, python_path: Path) -> bool:
        """Создание виртуального окружения.

        Args:
            python_path (Path): Путь к интерпретатору Python.

        Returns:
            bool: Успешность создания.

        Examples:
            >>> installer = Installer()
            >>> success = installer.create_venv(Path("/usr/bin/python3"))
            >>> print(success)
        """
        print(self.msg("step_2"))

        if self.venv_dir.exists():
            print(self.msg("step_2_exists"))
            return True

        try:
            subprocess.run(
                [str(python_path), "-m", "venv", str(self.venv_dir)],
                check=True,
                timeout=60
            )
            print(self.msg("step_2_ok"))
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def upgrade_pip(self) -> bool:
        """Обновление pip и инструментов.

        Returns:
            bool: Успешность обновления.

        Examples:
            >>> installer = Installer()
            >>> success = installer.upgrade_pip()
            >>> print(success)
        """
        print(self.msg("step_3"))

        try:
            subprocess.run(
                [str(self.python_path), "-m", "pip", "install", "--upgrade",
                 "pip", "setuptools", "wheel"],
                check=True,
                timeout=120
            )
            print(self.msg("step_3_ok"))
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def install_dependencies(self, profile: str = "1") -> bool:
        """Установка зависимостей.

        Args:
            profile (str): Профиль установки (1-5).

        Returns:
            bool: Успешность установки.

        Examples:
            >>> installer = Installer()
            >>> success = installer.install_dependencies("1")
            >>> print(success)
        """
        print(self.msg("step_4"))

        requirements_map: Dict[str, List[str]] = {
            "1": ["requirements.txt"],
            "2": ["install/req/requirements-core.txt"],
            "3": ["install/req/requirements-core.txt", "install/req/requirements-ai.txt"],
            "4": ["requirements.txt", "install/req/requirements-test.txt",
                  "install/req/requirements-docs.txt"],
            "5": [],
        }

        req_files: List[str] = requirements_map.get(profile, [])

        if not req_files:
            return True

        try:
            cmd: List[str] = [str(self.python_path), "-m", "pip", "install"]
            for req_file in req_files:
                req_path: Path = self.install_dir / req_file
                if req_path.exists():
                    cmd.extend(["-r", str(req_path)])

            subprocess.run(cmd, check=True, timeout=600)
            print(self.msg("step_4_ok"))
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def verify_environment(self) -> bool:
        """Финальная проверка окружения.

        Returns:
            bool: Успешность проверки.

        Examples:
            >>> installer = Installer()
            >>> success = installer.verify_environment()
            >>> print(success)
        """
        print(self.msg("step_6"))

        modules: List[str] = ["fastapi", "uvicorn", "dotenv", "pydantic"]

        try:
            for module in modules:
                subprocess.run(
                    [str(self.python_path), "-c", f"import {module}"],
                    check=True,
                    timeout=10
                )
            print(self.msg("step_6_ok"))
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def run(self, install_dir: Optional[str] = '') -> bool:
        """Запуск процесса установки.

        Args:
            install_dir (Optional[str]): Директория установки.

        Returns:
            bool: Успешность установки.

        Examples:
            >>> installer = Installer(Language.RU)
            >>> success = installer.run("/opt/ai-breadboard")
            >>> print(success)
        """
        print(self.msg("welcome"))

        self.install_dir = Path(install_dir) if install_dir else Path.cwd()
        self.venv_dir = self.install_dir / "venv"

        if self.platform_name == "Windows":
            self.python_path = self.venv_dir / "Scripts" / "python.exe"
        else:
            self.python_path = self.venv_dir / "bin" / "python"

        python_exe: Optional[Path] = self.find_python()
        if not python_exe:
            return False

        if not self.create_venv(python_exe):
            return False

        if not self.upgrade_pip():
            return False

        print(self.msg("step_4_menu"))
        print(self.msg("step_4_opt_1"))
        print(self.msg("step_4_opt_2"))
        print(self.msg("step_4_opt_3"))
        print(self.msg("step_4_opt_4"))
        print(self.msg("step_4_opt_5"))

        profile: str = input("Choice [1]: ").strip() or "1"

        if not self.install_dependencies(profile):
            return False

        if not self.verify_environment():
            return False

        print(self.msg("finish"))
        return True


def select_language() -> Language:
    """Выбор языка установки.

    Returns:
        Language: Выбранный язык.

    Examples:
        >>> lang = select_language()
        >>> print(lang)
    """
    print("Select language / Выберите язык / Seleccione idioma / בחר שפה:")
    print("[1] English")
    print("[2] Русский")
    print("[3] Español")
    print("[4] עברית")

    choice: str = input("Choice [1]: ").strip() or "1"

    language_map: Dict[str, Language] = {
        "1": Language.EN,
        "2": Language.RU,
        "3": Language.ES,
        "4": Language.HE,
    }

    return language_map.get(choice, Language.EN)


def main() -> int:
    """Главная функция установщика.

    Returns:
        int: Код выхода (0 — успех, 1 — ошибка).

    Examples:
        >>> exit_code = main()
        >>> sys.exit(exit_code)
    """
    try:
        language: Language = select_language()
        installer: Installer = Installer(language)

        install_dir: str = input("Installation directory [current]: ").strip() or ""

        success: bool = installer.run(install_dir)
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nInstallation cancelled.")
        return 1
    except Exception as ex:
        print(f"Installation failed: {ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
