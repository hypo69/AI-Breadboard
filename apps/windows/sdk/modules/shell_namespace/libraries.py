# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Modules Shell - Libraries Manager
# =============================================================================
# Description:
#   Модуль управления библиотеками Windows (.library-ms).
#   Обеспечивает сканирование, чтение XML-конфигураций библиотек, добавление и
#   создание пользовательских библиотек без затрагивания исходных файлов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.shell_namespace.libraries import ShellLibrariesManager
#
#     manager = ShellLibrariesManager()
#     libs = manager.list_libraries()
#
# File: libraries.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.shell_namespace
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:15:00
# =============================================================================

from __future__ import annotations
"""Модуль управления библиотеками Windows (.library-ms)."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

LIBRARIES_DIR = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Libraries')


def list_libraries() -> List[Dict[str, Any]]:
    """Получить список всех установленных библиотек Windows.

    Returns:
        list[dict]: Список найденных файлов .library-ms и их параметров.
    """
    lib_dir = Path(LIBRARIES_DIR)
    if not lib_dir.exists():
        return []

    libraries: List[Dict[str, Any]] = []

    for file_path in lib_dir.glob("*.library-ms"):
        info = parse_library_file(str(file_path))
        libraries.append(info)

    return libraries


def parse_library_file(file_path: str) -> Dict[str, Any]:
    """Распарсить файл библиотеки .library-ms.

    Args:
        file_path: Путь к файлу .library-ms.

    Returns:
        dict: Метаданные библиотеки (имя, папки-источники, GUID типа).
    """
    path = Path(file_path)
    result = {
        'name': path.stem,
        'file_path': str(path.resolve()),
        'exists': path.exists(),
        'folders': [],
        'folder_type': None,
    }

    if not path.exists():
        return result

    try:
        tree = ET.parse(str(path))
        root = tree.getroot()

        # Поиск пространств имен
        ns = {'s': 'http://schemas.microsoft.com/windows/2009/libraryDescription'}

        folder_type_elem = root.find('.//s:folderType', ns)
        if folder_type_elem is not None:
            result['folder_type'] = folder_type_elem.text

        for search_location in root.findall('.//s:searchLocationDescription', ns):
            url_elem = search_location.find('./s:url', ns)
            if url_elem is not None and url_elem.text:
                url_text = url_elem.text
                if url_text.lower().startswith('knownfolder:'):
                    kf_guid = url_text.split(':')[1]
                    result['folders'].append({'type': 'knownfolder', 'target': kf_guid})
                else:
                    result['folders'].append({'type': 'path', 'target': url_text})
    except Exception as err:
        logger.warning("Ошибка разбора файла библиотеки %s: %s", file_path, err)

    return result


def create_user_library(library_name: str, folder_paths: List[str]) -> Dict[str, Any]:
    """Создать новую пользовательскую библиотеку Windows.

    Args:
        library_name: Название библиотеки (например 'Projects').
        folder_paths: Список включенных каталогов.

    Returns:
        dict: Статус создания библиотеки.
    """
    clean_name = library_name.strip()
    if not clean_name:
        raise ValueError("Имя библиотеки не должно быть пустым")

    lib_path = Path(LIBRARIES_DIR) / f"{clean_name}.library-ms"
    lib_path.parent.mkdir(parents=True, exist_ok=True)

    # Формирование базового XML шаблона .library-ms
    root = ET.Element('libraryDescription', {
        'xmlns': 'http://schemas.microsoft.com/windows/2009/libraryDescription'
    })
    ET.SubElement(root, 'ownerSID').text = 'S-1-5-21-0-0-0-1000'

    loc_list = ET.SubElement(root, 'searchLocationDescriptionList')

    for p in folder_paths:
        loc = ET.SubElement(loc_list, 'searchLocationDescription')
        ET.SubElement(loc, 'url').text = p

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(lib_path), encoding='utf-8', xml_declaration=True)

    logger.info("Библиотека %s успешно создана по пути %s", clean_name, lib_path)
    return {
        'status': 'ok',
        'library_name': clean_name,
        'path': str(lib_path),
        'folders_count': len(folder_paths),
    }


class ShellLibrariesManager:
    """Менеджер библиотек Windows."""

    def list_libraries(self) -> List[Dict[str, Any]]:
        return list_libraries()

    def parse_library(self, file_path: str) -> Dict[str, Any]:
        return parse_library_file(file_path)

    def create_library(self, library_name: str, folder_paths: List[str]) -> Dict[str, Any]:
        return create_user_library(library_name, folder_paths)


__all__ = [
    'ShellLibrariesManager',
    'list_libraries',
    'parse_library_file',
    'create_user_library',
    'LIBRARIES_DIR',
]
