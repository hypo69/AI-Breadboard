# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Modules Explorer - Startup Manager
# =============================================================================
# Description:
#   Управление стартовым представлением Windows File Explorer.
#   Модуль отвечает за чтение и изменение настройки LaunchTo (Главная / Этот компьютер),
#   резервное копирование и восстановление параметров, а также безопасный запуск
#   Проводника для открытия физических каталогов и Shell URI.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.explorer_manager.startup import ExplorerStartupManager
#
#     manager = ExplorerStartupManager()
#     current = manager.get_startup_view()
#     manager.set_startup_view('this_pc')
#
# File: startup.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.explorer_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:15:00
# =============================================================================

from __future__ import annotations
"""Управление стартовым представлением Windows File Explorer."""

import logging
import os
import subprocess
import winreg
from pathlib import Path
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger(__name__)

StartupView = Literal['home', 'this_pc']

REGISTRY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
REGISTRY_VALUE = 'LaunchTo'

STARTUP_VALUES: Dict[str, int] = {
    'this_pc': 1,
    'home': 2,
}


def get_startup_view() -> Dict[str, Any]:
    """Получить настройку стартового представления Explorer.

    Returns:
        dict: Текущее представление ('home', 'this_pc' или None),
              сырое значение реестра, тип записи и статус операции.
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ,
        ) as key:
            value, value_type = winreg.QueryValueEx(key, REGISTRY_VALUE)

        view = next(
            (
                name
                for name, reg_val in STARTUP_VALUES.items()
                if reg_val == value
            ),
            None,
        )

        result = {
            'view': view,
            'raw_value': value,
            'registry_type': value_type,
            'status': 'ok' if view else 'unknown_value',
        }
        logger.debug("Конфигурация старта Explorer: %s", result)
        return result

    except FileNotFoundError:
        return {
            'view': None,
            'raw_value': None,
            'registry_type': None,
            'status': 'not_configured',
        }
    except OSError as err:
        logger.exception("Ошибка при чтении настройки старта Explorer: %s", err)
        raise


def set_startup_view(view: StartupView) -> Dict[str, Any]:
    """Изменить стартовое представление Explorer ('home' или 'this_pc').

    Args:
        view: 'home' или 'this_pc'.

    Returns:
        dict: Результат изменения, предыдущее и текущее состояние.

    Raises:
        ValueError: Если передано неподдерживаемое представление.
        RuntimeError: Если проверка записанного значения не прошла.
        OSError: При ошибке доступа к реестру.
    """
    if view not in STARTUP_VALUES:
        raise ValueError(f"Неподдерживаемое представление Explorer: {view!r}")

    previous = get_startup_view()
    target_val = STARTUP_VALUES[view]

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        REGISTRY_PATH,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(
            key,
            REGISTRY_VALUE,
            0,
            winreg.REG_DWORD,
            target_val,
        )

    current = get_startup_view()
    if current.get('raw_value') != target_val:
        raise RuntimeError("Проверка записанного значения LaunchTo завершилась с ошибкой")

    result = {
        'status': 'ok',
        'previous': previous,
        'current': current,
        'restart_required': False,
    }
    logger.info("Стартовое представление Explorer изменено на %s", view)
    return result


def restore_startup_view(previous_state: Dict[str, Any]) -> Dict[str, Any]:
    """Восстановить предыдущее значение настройки стартового представления.

    Args:
        previous_state: Словарь со снимком предыдущего состояния (из get_startup_view()).

    Returns:
        dict: Результат операции восстановления.
    """
    raw_val = previous_state.get('raw_value')
    if raw_val is None:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, REGISTRY_VALUE)
        except FileNotFoundError:
            pass
        return {'status': 'restored_absent'}

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        REGISTRY_PATH,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(
            key,
            REGISTRY_VALUE,
            0,
            winreg.REG_DWORD,
            int(raw_val),
        )
    return {'status': 'ok', 'current': get_startup_view()}


def open_location(location: str) -> Dict[str, Any]:
    """Открыть физическую папку или Shell URI в Проводнике.

    Args:
        location: Физический путь или Shell URI (например shell:Downloads или shell:::{...}).

    Returns:
        dict: Результат запуска процесса explorer.exe.

    Raises:
        ValueError: Если путь пуст.
        FileNotFoundError: Если локальный каталог не существует.
    """
    if not location or not location.strip():
        raise ValueError("Локация не должна быть пустой")

    loc = location.strip()

    if loc.lower().startswith("shell:") or loc.startswith("shell:::"):
        target = loc
    else:
        path = Path(os.path.expandvars(loc)).expanduser()
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Каталог не найден: {path}")
        target = str(path.resolve())

    proc = subprocess.Popen(['explorer.exe', target], shell=False)
    logger.info("Explorer открыл локацию: %s (PID: %d)", target, proc.pid)
    return {
        'status': 'ok',
        'target': target,
        'pid': proc.pid,
    }


class ExplorerStartupManager:
    """Менеджер стартового представления и навигации Проводника."""

    def get_startup_view(self) -> Dict[str, Any]:
        return get_startup_view()

    def set_startup_view(self, view: StartupView) -> Dict[str, Any]:
        return set_startup_view(view)

    def restore_startup_view(self, previous_state: Dict[str, Any]) -> Dict[str, Any]:
        return restore_startup_view(previous_state)

    def open_location(self, location: str) -> Dict[str, Any]:
        return open_location(location)


__all__ = [
    'ExplorerStartupManager',
    'get_startup_view',
    'set_startup_view',
    'restore_startup_view',
    'open_location',
    'STARTUP_VALUES',
]
