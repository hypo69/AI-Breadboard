# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Modules Shell - Shell URI Resolver
# =============================================================================
# Description:
#   Каталог символических Shell URI и разрешение физических путей.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.shell_namespace.shell_uri import ShellUriResolver
#
#     resolver = ShellUriResolver()
#     info = resolver.resolve_uri('shell:Downloads')
#
# File: shell_uri.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.shell_namespace
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:15:00
# =============================================================================

from __future__ import annotations
"""Каталог символических Shell URI и разрешение физических путей."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from apps.windows.sdk.modules.shell_namespace.known_folders import list_known_folders

logger = logging.getLogger(__name__)

STANDARD_SHELL_URIS: Dict[str, Dict[str, str]] = {
    'shell:Desktop': {'description': 'Рабочий стол пользователя', 'known_folder': 'Desktop'},
    'shell:Downloads': {'description': 'Папка загрузок', 'known_folder': 'Downloads'},
    'shell:Personal': {'description': 'Мои документы', 'known_folder': 'Documents'},
    'shell:Recent': {'description': 'Недавние документы (%APPDATA%\\Microsoft\\Windows\\Recent)', 'path_env': r'%APPDATA%\Microsoft\Windows\Recent'},
    'shell:SendTo': {'description': 'Папка контекстного меню Отправить', 'path_env': r'%APPDATA%\Microsoft\Windows\SendTo'},
    'shell:Startup': {'description': 'Автозагрузка пользователя', 'path_env': r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'},
    'shell:Libraries': {'description': 'Библиотеки Windows', 'path_env': r'%APPDATA%\Microsoft\Windows\Libraries'},
    'shell:RecycleBinFolder': {'description': 'Корзина', 'clsid': '{645FF040-5081-101B-9F08-00AA002F954E}'},
    'shell:ControlPanelFolder': {'description': 'Панель управления', 'clsid': '{21EC2020-3AEA-1069-A2DD-08002B30309D}'},
}


def resolve_shell_uri(uri: str) -> Dict[str, Any]:
    """Разрешить символический Shell URI в объект пространства имен.

    Args:
        uri: Строка вида 'shell:Downloads' или 'shell:::{CLSID}'.

    Returns:
        dict: Разрешенный путь, тип и доступность.
    """
    clean_uri = uri.strip()
    meta = STANDARD_SHELL_URIS.get(clean_uri, {})

    resolved_path: Optional[str] = None
    target_type = 'virtual'

    if meta.get('path_env'):
        expanded = os.path.expandvars(meta['path_env'])
        if Path(expanded).exists():
            resolved_path = expanded
            target_type = 'filesystem'
    elif meta.get('known_folder'):
        kf_list = list_known_folders()
        kf_match = next((kf for kf in kf_list if kf['canonical_name'] == meta['known_folder']), None)
        if kf_match and kf_match.get('path'):
            resolved_path = kf_match['path']
            target_type = 'filesystem'

    return {
        'uri': clean_uri,
        'description': meta.get('description', 'Пользовательский или виртуальный Shell URI'),
        'resolved_path': resolved_path,
        'target_type': target_type,
        'exists': bool(resolved_path and Path(resolved_path).exists()),
    }


def list_shell_uris() -> List[Dict[str, Any]]:
    """Получить список всех стандартных Shell URIs с текущими статусами.

    Returns:
        list[dict]: Список каталога Shell URI.
    """
    return [resolve_shell_uri(uri) for uri in STANDARD_SHELL_URIS]


class ShellUriResolver:
    """Резолвер символических Shell URI."""

    def resolve_uri(self, uri: str) -> Dict[str, Any]:
        return resolve_shell_uri(uri)

    def list_uris(self) -> List[Dict[str, Any]]:
        return list_shell_uris()


__all__ = [
    'ShellUriResolver',
    'resolve_shell_uri',
    'list_shell_uris',
    'STANDARD_SHELL_URIS',
]
