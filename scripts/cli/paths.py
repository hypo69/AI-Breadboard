# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Кроссплатформенная система управления путями.
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: paths.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Кроссплатформенная система управления путями.
Автоматически определяет правильные пути для Windows, Linux, macOS.
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import platformdirs
    HAS_PLATFORMDIRS = True
except ImportError:
    HAS_PLATFORMDIRS = False

class CrossPlatformPaths:
    """
    Централизованная система путей для всех платформ.
    
    Использует:
    - Windows: %LOCALAPPDATA%, %USERPROFILE%
    - Linux/macOS: ~/.local/share, ~/.config, ~/.cache
    """
    
    def __init__(self, app_name: str = "AI-Breadboard", app_author: str = "hypo69"):
        self.app_name = app_name
        self.app_author = app_author
        self._project_root = self._find_project_root()
        self._cache = {}
    
    @staticmethod
    def _find_project_root() -> Path:
        """Находит корень проекта по наличию main.py или config.json"""
        current = Path(__file__).parent
        for _ in range(10):  # Поиск до 10 уровней вверх
            if (current / "main.py").exists() or (current / "config.json").exists():
                return current
            current = current.parent
        # Fallback на AIBREADBOARD_DIR или текущую директорию
        return Path(os.environ.get("AIBREADBOARD_DIR", os.getcwd()))
    
    @property
    def project_root(self) -> Path:
        """Корень проекта"""
        return self._project_root
    
    @property
    def data_dir(self) -> Path:
        """
        Директория для данных приложения:
        - Windows: %LOCALAPPDATA%\AI-Breadboard
        - Linux: ~/.local/share/AI-Breadboard
        - macOS: ~/Library/Application Support/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_data_dir(self.app_name, self.app_author))
        
        # Fallback для систем без platformdirs
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(base) / self.app_name
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / self.app_name
        else:
            return Path.home() / ".local" / "share" / self.app_name
    
    @property
    def config_dir(self) -> Path:
        """
        Директория конфигурации:
        - Windows: %LOCALAPPDATA%\AI-Breadboard\config
        - Linux: ~/.config/AI-Breadboard
        - macOS: ~/Library/Preferences/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_config_dir(self.app_name, self.app_author))
        
        if sys.platform == "win32":
            return self.data_dir / "config"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Preferences" / self.app_name
        else:
            return Path.home() / ".config" / self.app_name
    
    @property
    def cache_dir(self) -> Path:
        """
        Директория кэша:
        - Windows: %LOCALAPPDATA%\AI-Breadboard\Cache
        - Linux: ~/.cache/AI-Breadboard
        - macOS: ~/Library/Caches/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_cache_dir(self.app_name, self.app_author))
        
        if sys.platform == "win32":
            return self.data_dir / "Cache"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Caches" / self.app_name
        else:
            return Path.home() / ".cache" / self.app_name
    
    @property
    def certs_dir(self) -> Path:
        """
        Директория SSL сертификатов:
        - Windows: %USERPROFILE%\.certs
        - Linux: ~/.local/share/ca-certificates (системная) или ~/.certs (пользовательская)
        - macOS: ~/Library/Certs
        """
        if sys.platform == "win32":
            return Path.home() / ".certs"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Certs"
        else:
            # Linux: используем ~/.local/share/ca-certificates для системного уровня
            # но также поддерживаем ~/.certs для пользовательского
            return Path.home() / ".local" / "share" / "ca-certificates"
    
    @property
    def certs_user_dir(self) -> Path:
        """Альтернативная директория для пользовательских сертификатов"""
        return Path.home() / ".certs"
    
    @property
    def bin_dir(self) -> Path:
        """
        Директория для исполняемых файлов:
        - Windows: %USERPROFILE%\.local\bin
        - Linux/macOS: ~/.local/bin
        """
        if sys.platform == "win32":
            return Path.home() / ".local" / "bin"
        else:
            return Path.home() / ".local" / "bin"
    
    @property
    def venv_dir(self) -> Path:
        """Директория виртуального окружения Python"""
        return self.project_root / "venv"
    
    @property
    def venv_python(self) -> Path:
        """Интерпретатор Python в виртуальном окружении"""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"
    
    @property
    def secrets_dir(self) -> Path:
        """Директория для секретов (API-ключей)"""
        return self.project_root / "core" / "secrets"
    
    @property
    def env_file(self) -> Path:
        """Файл .env"""
        return self.project_root / ".env"
    
    @property
    def config_file(self) -> Path:
        """Файл config.json"""
        return self.project_root / "config.json"
    
    @property
    def requirements_main(self) -> Path:
        """Главный файл requirements.txt"""
        return self.project_root / "requirements.txt"
    
    @property
    def requirements_core(self) -> Path:
        """requirements-core.txt"""
        return self.project_root / "install" / "req" / "requirements-core.txt"
    
    @property
    def requirements_ai(self) -> Path:
        """requirements-ai.txt"""
        return self.project_root / "install" / "req" / "requirements-ai.txt"
    
    @property
    def requirements_test(self) -> Path:
        """requirements-test.txt"""
        return self.project_root / "install" / "req" / "requirements-test.txt"
    
    @property
    def requirements_docs(self) -> Path:
        """requirements-docs.txt"""
        return self.project_root / "install" / "req" / "requirements-docs.txt"
    
    def get_env_vars(self) -> dict:
        """Returns необходимые переменные окружения"""
        return {
            "AIBREADBOARD_DIR": str(self.project_root),
            "ASSIST_DIR": str(self.project_root),
            "PYTHONUTF8": "1",
            "PYTHONPATH": f"{self.project_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
        }
    
    def setup_env(self) -> None:
        """Sets переменные окружения"""
        for key, value in self.get_env_vars().items():
            if value:
                os.environ[key] = value
    
    def ensure_dirs(self) -> None:
        """Creates необходимые директории"""
        dirs = [
            self.data_dir,
            self.config_dir,
            self.cache_dir,
            self.certs_dir,
            self.certs_user_dir,
            self.bin_dir,
            self.secrets_dir,
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

# Глобальный экземпляр
_paths_instance: Optional[CrossPlatformPaths] = None

def get_paths() -> CrossPlatformPaths:
    """Получить глобальный экземпляр CrossPlatformPaths"""
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = CrossPlatformPaths()
    return _paths_instance

def init_paths() -> CrossPlatformPaths:
    """Инициализировать пути и установить переменные окружения"""
    paths = get_paths()
    paths.setup_env()
    paths.ensure_dirs()
    return paths
