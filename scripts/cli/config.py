# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Управление конфигурационными файлами"""
#
# File: config.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Утилиты для работы с конфигурацией (кроссплатформенные).
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.cli.paths import get_paths

class ConfigManager:
    """Управление конфигурационными файлами"""
    
    def __init__(self):
        self.paths = get_paths()
        self._config_cache = {}
        self._env_vars = {}
    
    def load_json(self, filepath: Path) -> dict:
        """Загрузить JSON файл"""
        if not filepath.exists():
            return {}
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def save_json(self, filepath: Path, data: dict, pretty: bool = True) -> bool:
        """Сохранить JSON файл"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2 if pretty else None,
                    ensure_ascii=False
                )
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def load_config(self, force_reload: bool = False) -> dict:
        """
        Загрузить config.json
        
        Args:
            force_reload: Перезагрузить даже если в кэше
        
        Returns:
            Dictionary конфигурации
        """
        if "config" in self._config_cache and not force_reload:
            return self._config_cache["config"]
        
        config = self.load_json(self.paths.config_file)
        self._config_cache["config"] = config
        return config
    
    def save_config(self, config: dict) -> bool:
        """Сохранить config.json"""
        success = self.save_json(self.paths.config_file, config)
        if success:
            self._config_cache["config"] = config
        return success
    
    def load_env_file(self) -> dict:
        """Загрузить .env файл"""
        if not self.paths.env_file.exists():
            return {}
        
        env_vars = {}
        try:
            with open(self.paths.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Error loading .env: {e}")
        
        return env_vars
    
    def save_env_file(self, env_vars: dict) -> bool:
        """Сохранить .env файл"""
        try:
            with open(self.paths.env_file, "w", encoding="utf-8") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            print(f"Error saving .env: {e}")
            return False
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Получить значение из config.json используя нотацию точек.
        
        Пример: get_config_value("server.port", 8000)
        
        Args:
            key_path: Путь ключей через точку
            default: Значение по умолчанию
        
        Returns:
            Значение или default
        """
        config = self.load_config()
        keys = key_path.split(".")
        
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set_config_value(self, key_path: str, value: Any) -> bool:
        """
        Установить значение в config.json используя нотацию точек.
        
        Args:
            key_path: Путь ключей через точку
            value: Новое значение
        
        Returns:
            True если successfully
        """
        config = self.load_config()
        keys = key_path.split(".")
        
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return self.save_config(config)
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Получить переменную окружения (приоритет: os.environ > .env > default).
        
        Args:
            key: Имя переменной
            default: Значение по умолчанию
        
        Returns:
            Значение или None
        """
        # 1. Системная переменная окружения
        if key in os.environ:
            return os.environ[key]
        
        # 2. Из .env файла
        env_vars = self.load_env_file()
        if key in env_vars:
            return env_vars[key]
        
        # 3. Default
        return default
    
    def set_env_var(self, key: str, value: str) -> bool:
        """
        Установить переменную окружения в .env файл.
        
        Args:
            key: Имя переменной
            value: Значение
        
        Returns:
            True если successfully
        """
        env_vars = self.load_env_file()
        env_vars[key] = value
        return self.save_env_file(env_vars)
    
    def get_install_config(self) -> dict:
        """Загрузить конфигурацию установки (install.json)"""
        install_json = self.paths.project_root / "install" / "install.json"
        return self.load_json(install_json)
    
    def adapt_paths_to_platform(self, config: dict) -> dict:
        """
        Адаптировать пути в конфигурации к текущей платформе.
        
        Заменяет Windows пути (%LOCALAPPDATA%, %USERPROFILE%) на Unix-style пути.
        
        Args:
            config: Исходная Configuration
        
        Returns:
            Адаптированная Configuration
        """
        import copy
        adapted = copy.deepcopy(config)
        
        # Маппинг Windows путей на Unix эквиваленты
        replacements = {
            "%LOCALAPPDATA%": str(self.paths.data_dir),
            "%USERPROFILE%": str(Path.home()),
            "\\": "/",
        }
        
        def replace_paths(obj):
            if isinstance(obj, dict):
                return {k: replace_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_paths(item) for item in obj]
            elif isinstance(obj, str):
                result = obj
                for old, new in replacements.items():
                    result = result.replace(old, new)
                return result
            else:
                return obj
        
        return replace_paths(adapted)

# Глобальный экземпляр
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Получить глобальный экземпляр ConfigManager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
