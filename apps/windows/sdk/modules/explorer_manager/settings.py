# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Modules Explorer - Settings Manager
# =============================================================================
# Description:
#   Менеджер настроек Проводника Windows (Folder Options / File Explorer Options).
#   Позволяет просматривать и изменять параметры Folder Options, включая скрытые файлы,
#   расширения, защищенные системные файлы и параметры навигации.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.explorer_manager.settings import ExplorerSettingsManager
#
#     manager = ExplorerSettingsManager()
#     settings = manager.get_all_settings()
#     manager.set_setting('show_hidden_files', True)
#
# File: settings.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.explorer_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:15:00
# =============================================================================

from __future__ import annotations
"""Менеджер настроек Проводника Windows (Folder Options / File Explorer Options)."""

import logging
import winreg
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ADVANCED_REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
EXPLORER_REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer'

EXPLORER_SETTINGS_CATALOG: Dict[str, Dict[str, Any]] = {
    'show_hidden_files': {
        'title': 'Показывать скрытые файлы, папки и диски',
        'category': 'View',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'Hidden',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 2,
        'default_val': 2,
    },
    'hide_file_extensions': {
        'title': 'Скрывать расширения для зарегистрированных типов файлов',
        'category': 'View',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'HideFileExt',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 1,
    },
    'show_protected_system_files': {
        'title': 'Скрывать защищенные системные файлы',
        'category': 'View',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'ShowSuperHidden',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 0,
    },
    'show_checkboxes': {
        'title': 'Использовать флажки для выбора элементов',
        'category': 'View',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'UseCheckboxes',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 0,
    },
    'expand_to_current_folder': {
        'title': 'Разворачивать до открытой папки в области навигации',
        'category': 'Navigation',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'NavPaneExpandToCurrentFolder',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 0,
    },
    'show_recent_files': {
        'title': 'Показывать недавно использовавшиеся файлы',
        'category': 'General',
        'registry_path': EXPLORER_REG_PATH,
        'registry_value': 'ShowRecent',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 1,
    },
    'show_frequent_folders': {
        'title': 'Показывать часто используемые папки',
        'category': 'General',
        'registry_path': EXPLORER_REG_PATH,
        'registry_value': 'ShowFrequent',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 1,
    },
    'separate_folder_process': {
        'title': 'Запускать окна с папками в отдельном процессе',
        'category': 'General',
        'registry_path': ADVANCED_REG_PATH,
        'registry_value': 'SeparateProcess',
        'type': 'dword',
        'enabled_val': 1,
        'disabled_val': 0,
        'default_val': 0,
    },
}


def get_all_explorer_settings() -> List[Dict[str, Any]]:
    """Получить текущие значения всех параметров Folder Options из реестра.

    Returns:
        list[dict]: Список настроек с их статусом, именами и значением.
    """
    results: List[Dict[str, Any]] = []

    for setting_id, meta in EXPLORER_SETTINGS_CATALOG.items():
        reg_path = meta['registry_path']
        val_name = meta['registry_value']

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                reg_path,
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, val_name)

            is_enabled = (val == meta['enabled_val'])
            status = 'ok'
        except FileNotFoundError:
            val = None
            is_enabled = (meta['default_val'] == meta['enabled_val'])
            status = 'not_configured'
        except OSError as err:
            logger.warning("Ошибка чтения параметра реестра %s: %s", val_name, err)
            val = None
            is_enabled = False
            status = 'error'

        results.append({
            'setting_id': setting_id,
            'title': meta['title'],
            'category': meta['category'],
            'registry_path': reg_path,
            'registry_value': val_name,
            'raw_value': val,
            'is_enabled': is_enabled,
            'status': status,
        })

    return results


def set_explorer_setting(setting_id: str, enable: bool) -> Dict[str, Any]:
    """Изменить значение отдельного параметра Проводника в реестре.

    Args:
        setting_id: Идентификатор настройки из каталога.
        enable: Включить (True) или выключить (False).

    Returns:
        dict: Результат операции.

    Raises:
        KeyError: Если настройка с таким ID не найдена.
        OSError: При ошибке записи в реестр.
    """
    if setting_id not in EXPLORER_SETTINGS_CATALOG:
        raise KeyError(f"Неизвестная настройка Explorer: {setting_id!r}")

    meta = EXPLORER_SETTINGS_CATALOG[setting_id]
    target_val = meta['enabled_val'] if enable else meta['disabled_val']
    reg_path = meta['registry_path']
    val_name = meta['registry_value']

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        reg_path,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(
            key,
            val_name,
            0,
            winreg.REG_DWORD,
            target_val,
        )

    logger.info("Настройка Explorer '%s' была установлена в %s (значение=%d)", setting_id, enable, target_val)
    return {
        'status': 'ok',
        'setting_id': setting_id,
        'enabled': enable,
        'raw_value': target_val,
        'restart_required': False,
    }


class ExplorerSettingsManager:
    """Менеджер параметров Folder Options Проводника."""

    def get_all_settings(self) -> List[Dict[str, Any]]:
        return get_all_explorer_settings()

    def set_setting(self, setting_id: str, enable: bool) -> Dict[str, Any]:
        return set_explorer_setting(setting_id, enable)


__all__ = [
    'ExplorerSettingsManager',
    'get_all_explorer_settings',
    'set_explorer_setting',
    'EXPLORER_SETTINGS_CATALOG',
]
