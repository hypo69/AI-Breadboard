# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dynamic Plugin Loader and Registry
# =============================================================================
# Description:
#   Discovers, dynamically imports, initializes, and manages all extension plugins
#   in the AI Breadboard environment with configuration and environment overrides.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Dynamic plugin loader and registry package.

Provides automated discovery and loading of BasePlugin instances from subdirectories
under plugins/, checking configuration toggles and environment variables.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import pkgutil
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger import logger
from src.config import global_settings
from plugins.base import BasePlugin

# Extend __path__ to include all plugin subcategory folders (e.g. user-plugins, developer-plugins, system-plugins)
_plugins_dir: Path = __root__ / "plugins"
if _plugins_dir.exists() and _plugins_dir.is_dir():
    for _sub in _plugins_dir.iterdir():
        if _sub.is_dir() and not _sub.name.startswith(("_", ".")):
            if str(_sub) not in __path__:
                __path__.append(str(_sub))

__all__ = ["BasePlugin", "load_plugins"]


def _discover_plugin_directories(plugins_dir: Path) -> List[Path]:
    """Discover all valid plugin directories either directly under plugins/ or inside category folders.

    Args:
        plugins_dir (Path): Root plugins directory.

    Returns:
        List[Path]: List of plugin directories containing an __init__.py file.
    """
    discovered: List[Path] = []
    if not plugins_dir.exists() or not plugins_dir.is_dir():
        return discovered

    for item in plugins_dir.iterdir():
        if not item.is_dir() or item.name.startswith(("_", ".")):
            continue
        # Direct plugin folder
        if (item / "__init__.py").exists():
            discovered.append(item)
        else:
            # Subcategory folder (e.g., developer-plugins, system-plugins, user-plugins)
            for sub_item in item.iterdir():
                if sub_item.is_dir() and not sub_item.name.startswith(("_", ".")) and (sub_item / "__init__.py").exists():
                    discovered.append(sub_item)
    return discovered


def _parse_plugins_config(plugins_cfg: Any) -> tuple[Optional[set[str]], set[str], Dict[str, Any]]:
    """Парсинг секции конфигурации плагинов (списки enabled/disabled, плоский список или словарь).

    Args:
        plugins_cfg (Any): Данные конфигурации плагинов из config.json.

    Returns:
        tuple[Optional[set[str]], set[str], Dict[str, Any]]:
            Кортеж из (множество включенных плагинов или None, множество отключенных, словарь индивидуальных настроек).
    """
    enabled_set: Optional[set[str]] = None
    disabled_set: set[str] = set()
    plugin_configs: Dict[str, Any] = {}

    if isinstance(plugins_cfg, list):
        # Формат плоского списка активных плагинов
        enabled_set = {str(item).strip().lower() for item in plugins_cfg if item}
    elif isinstance(plugins_cfg, dict):
        has_enabled_key = "enabled" in plugins_cfg and isinstance(plugins_cfg["enabled"], list)
        has_disabled_key = "disabled" in plugins_cfg and isinstance(plugins_cfg["disabled"], list)

        if has_enabled_key:
            enabled_set = {str(item).strip().lower() for item in plugins_cfg["enabled"] if item}
        if has_disabled_key:
            disabled_set = {str(item).strip().lower() for item in plugins_cfg["disabled"] if item}

        # Сбор индивидуальных конфигураций плагинов, если они заданы как вложенные словари
        for k, v in plugins_cfg.items():
            if k not in ("enabled", "disabled") and isinstance(v, dict):
                plugin_configs[k.strip().lower()] = v
    return enabled_set, disabled_set, plugin_configs


def load_plugins(ai_model: Any = None) -> Dict[str, BasePlugin]:
    """Обнаружение, загрузка и инициализация всех доступных плагинов в директории plugins.

    Выполняет сканирование папки plugins/ и категориальных поддиректорий, импортирует модули,
    создает экземпляры через фабрику module.plugin(ai_model=ai_model) и определяет статус активности
    на основе секции plugins в config.json (списки enabled/disabled) и переменной окружения DISABLED_PLUGINS.

    Args:
        ai_model (Any): Опциональный экземпляр модели ИИ для внедрения в плагины.

    Returns:
        Dict[str, BasePlugin]: Словарь соответствия имен плагинов их инициализированным экземплярам.

    Examples:
        >>> from plugins import load_plugins
        >>> plugins_dict = load_plugins()
        >>> 'telegram_bot' in plugins_dict
        True
    """
    plugins_dir: Path = __root__ / "plugins"
    plugins: Dict[str, BasePlugin] = {}

    if not plugins_dir.exists() or not plugins_dir.is_dir():
        logger.warning(f"Директория плагинов не найдена по пути {plugins_dir}")
        return plugins

    # Переменная окружения для отключения плагинов (через запятую или пробел)
    disabled_env_raw = os.getenv("DISABLED_PLUGINS", "")
    disabled_env = {
        name.strip().lower()
        for name in disabled_env_raw.replace(",", " ").split()
        if name.strip()
    }

    # Чтение секции plugins из активного конфигурационного файла
    cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    active_path: Optional[Path] = None
    if cfg_env:
        p = Path(cfg_env)
        active_path = p if p.is_absolute() else (__root__ / cfg_env)

    if not active_path or not active_path.exists():
        if (__root__ / "config_tc.json").exists() and not (__root__ / "config.json").exists():
            active_path = __root__ / "config_tc.json"
        else:
            active_path = __root__ / "config.json"

    raw_plugins_cfg: Any = {}
    if active_path and active_path.exists():
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                root_cfg = json.load(f)
                raw_plugins_cfg = root_cfg.get("plugins", {})
        except Exception as e:
            logger.error(f"Ошибка чтения конфигурации плагинов из {active_path}: {e}")
    else:
        raw_plugins_cfg = getattr(global_settings, "plugins", {})
        if hasattr(raw_plugins_cfg, "__dict__"):
            raw_plugins_cfg = dict(raw_plugins_cfg.__dict__)

    if hasattr(raw_plugins_cfg, "__dict__"):
        raw_plugins_cfg = dict(raw_plugins_cfg.__dict__)

    enabled_set, disabled_set, plugin_configs = _parse_plugins_config(raw_plugins_cfg)

    for item in _discover_plugin_directories(plugins_dir):
        plugin_key = item.name.lower()

        # Быстрая предварительная фильтрация по имени директории плагина
        if plugin_key in disabled_env:
            logger.debug(f"Плагин '{plugin_key}' отключен переменной DISABLED_PLUGINS (пропуск загрузки).")
            continue
        if plugin_key in disabled_set:
            logger.debug(f"Плагин '{plugin_key}' отключен в конфигурации (disabled) (пропуск загрузки).")
            continue
        if enabled_set is not None and plugin_key not in enabled_set:
            # Проверим, вдруг имя плагина внутри отличается от имени папки
            # Если enabled_set пустой (enabled: []), то ни один плагин не должен загружаться
            if len(enabled_set) == 0:
                logger.debug(f"Список enabled пуст, плагин '{plugin_key}' не загружается.")
                continue

        plugin_mod_name = f"plugins.{item.name}"
        try:
            module = importlib.import_module(plugin_mod_name)
            if not hasattr(module, "plugin") or not callable(module.plugin):
                logger.debug(f"Модуль {plugin_mod_name} не предоставляет вызываемую фабрику 'plugin'.")
                continue

            instance: BasePlugin = module.plugin(ai_model=ai_model)
            if not isinstance(instance, BasePlugin):
                logger.warning(
                    f"Фабрика {plugin_mod_name}.plugin() вернула объект типа {type(instance)}, ожидался BasePlugin."
                )
                continue

            # Определение псевдонимов и ключей плагина
            aliases = {instance.name.lower(), item.name.lower()}
            plugin_specific_cfg = plugin_configs.get(instance.name.lower()) or plugin_configs.get(item.name.lower()) or {}

            # 1. Проверка переменной окружения DISABLED_PLUGINS
            if aliases.intersection(disabled_env):
                logger.debug(f"Плагин '{instance.name}' отключен через DISABLED_PLUGINS (пропуск).")
                continue
            # 2. Проверка списка disabled в конфигурации (наивысший приоритет)
            if aliases.intersection(disabled_set):
                logger.debug(f"Плагин '{instance.name}' отключен через disabled список (пропуск).")
                continue
            # 3. Проверка списка enabled в конфигурации: если задан список enabled, загружаем ТОЛЬКО перечисленные
            if enabled_set is not None and not aliases.intersection(enabled_set):
                logger.debug(f"Плагин '{instance.name}' отсутствует в списке enabled (пропуск).")
                continue
            # 4. Проверка индивидуального флага в legacy словаре настроек
            if isinstance(plugin_specific_cfg, dict) and plugin_specific_cfg.get("enabled") is False:
                logger.debug(f"Плагин '{instance.name}' отключен через plugin_specific_cfg.enabled=False (пропуск).")
                continue

            # 5. Проверка локального config.json плагина на явное отключение
            local_cfg_path = item / "config.json"
            if local_cfg_path.exists():
                try:
                    with open(local_cfg_path, "r", encoding="utf-8") as lf:
                        local_data = json.load(lf)
                        if local_data.get("enabled") is False or local_data.get("active") is False:
                            logger.debug(f"Плагин '{instance.name}' отключен в локальном config.json (пропуск).")
                            continue
                except Exception:
                    pass

            instance.enabled = True

            # Объединение настроек из глобальной конфигурации
            if isinstance(plugin_specific_cfg, dict) and "config" in plugin_specific_cfg:
                instance.update_config(plugin_specific_cfg["config"])

            plugins[instance.name] = instance
            logger.info(f"Загружен плагин: '{instance.name}' (v{instance.version}, enabled={instance.enabled})")

        except Exception as exc:
            logger.error(f"Не удалось загрузить плагин из '{item.name}': {exc}", exc_info=True)

    return plugins
