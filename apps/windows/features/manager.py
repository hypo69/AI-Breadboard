# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Features - Manager
# =============================================================================
# Description:
#   Управление Windows Optional Features через PowerShell/DISM.
#   Предоставляет функции получения списка, включения и отключения
#   компонентов Windows. Используется FastAPI-роутером.
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.features
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 11:25:00
# =============================================================================

"""Модуль менеджера Windows Optional Features.

Содержит три публичные функции:
- ``get_windows_features()`` – возвращает список всех optional features
  с их состоянием (Enabled/Disabled) в виде списка словарей.
- ``enable_windows_feature(name: str, all: bool = True)`` – включает указанный
  компонент.
- ``disable_windows_feature(name: str)`` – отключает указанный компонент.

Функции вызывают PowerShell‑команды ``Get-WindowsOptionalFeature``,
``Enable-WindowsOptionalFeature`` и ``Disable-WindowsOptionalFeature``.
Все вызовы выполняются в режиме non‑interactive, без профиля, что позволяет
работать в сервисных контекстах. При ошибке выбрасывается ``RuntimeError``
с сообщением stderr.
"""

from __future__ import annotations

import json
import subprocess
from typing import List, Dict

from logger import logger

_POWER_SHELL = "powershell.exe"

def _run_powershell(command: str) -> str:
    """Выполняет переданную команду PowerShell и возвращает stdout.

    Args:
        command: Команда без обёртки ``powershell.exe``.
    Returns:
        Строка stdout.
    Raises:
        RuntimeError: Если процесс завершился с ненулевым кодом.
    """
    cmd = [
        _POWER_SHELL,
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        command,
    ]
    logger.debug(f"[WindowsFeatures] Запуск PowerShell: {command}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell command failed")
    return result.stdout.strip()


def get_windows_features() -> List[Dict[str, str]]:
    """Возвращает список всех optional features с их состоянием.

    Возвращаемый список содержит словари с минимумом полей:
    ``FeatureName`` – техническое имя, ``State`` – состояние.
    """
    ps_cmd = (
        "Get-WindowsOptionalFeature -Online | "
        "Select-Object FeatureName, State | "
        "ConvertTo-Json -Compress"
    )
    output = _run_powershell(ps_cmd)
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Не удалось распарсить JSON от PowerShell: {exc}")
    # PowerShell может вернуть объект или массив
    if isinstance(data, dict):
        data = [data]
    return data


def enable_windows_feature(name: str, all: bool = True) -> Dict[str, str]:
    """Включает указанный optional feature.

    Args:
        name: Точное имя компонента (FeatureName).
        all: Если True, также включаются зависимости (``-All``).
    Returns:
        Словарь с полями ``FeatureName`` и ``State`` после попытки включения.
    """
    all_flag = " -All" if all else ""
    ps_cmd = (
        f"Enable-WindowsOptionalFeature -Online -FeatureName '{name}'{all_flag} "
        "| Select-Object FeatureName, State | ConvertTo-Json -Compress"
    )
    output = _run_powershell(ps_cmd)
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Не удалось распарсить JSON от PowerShell: {exc}")
    return result


def disable_windows_feature(name: str) -> Dict[str, str]:
    """Отключает указанный optional feature.

    Args:
        name: Точное имя компонента.
    Returns:
        Словарь с полями ``FeatureName`` и ``State`` после попытки отключения.
    """
    ps_cmd = (
        f"Disable-WindowsOptionalFeature -Online -FeatureName '{name}' "
        "| Select-Object FeatureName, State | ConvertTo-Json -Compress"
    )
    output = _run_powershell(ps_cmd)
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Не удалось распарсить JSON от PowerShell: {exc}")
    return result

__all__ = ["get_windows_features", "enable_windows_feature", "disable_windows_feature"]
