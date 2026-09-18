# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Libraries Manager
# =============================================================================
# Description:
#   Движок управления системными библиотеками Windows Shell (.library-ms).
#   Чтение, валидация XML, добавление и удаление исходных директорий,
#   проверка существования и доступности физических путей.
#
# Examples:
#   >>> from apps.windows_backup_manager.core.libraries_manager import WindowsLibrariesManager
#   >>> mgr = WindowsLibrariesManager()
#   >>> libs = mgr.get_all_libraries()
#
# File: libraries_manager.py
# Project: ai-breadboard
# Package: apps.windows_backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления библиотеками Windows Shell (.library-ms)."""

from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from src.logger import logger
from apps.windows_backup_manager.core.models import LibraryFolder, WindowsLibrary


class WindowsLibrariesManager:
    """Менеджер библиотек Windows."""

    NS = {"lib": "http://schemas.microsoft.com/windows/2009/library"}

    def __init__(self, libraries_dir: Optional[Path] = None) -> None:
        """Инициализация менеджера библиотек.

        Args:
            libraries_dir: Путь к каталогу библиотек (по умолчанию %APPDATA%/Microsoft/Windows/Libraries).
        """
        if libraries_dir:
            self.libraries_dir = libraries_dir
        else:
            appdata = os.environ.get("APPDATA")
            if appdata:
                self.libraries_dir = Path(appdata) / "Microsoft" / "Windows" / "Libraries"
            else:
                self.libraries_dir = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Libraries"

        self.libraries_dir.mkdir(parents=True, exist_ok=True)

    def get_all_libraries(self) -> List[WindowsLibrary]:
        """Возвращает список всех зарегистрированных библиотек Windows.

        Returns:
            List[WindowsLibrary]: Список объектов библиотек с включенными папками.
        """
        libraries: List[WindowsLibrary] = []
        if not self.libraries_dir.exists():
            return libraries

        for lib_file in self.libraries_dir.glob("*.library-ms"):
            try:
                lib_obj = self.parse_library_file(lib_file)
                if lib_obj:
                    libraries.append(lib_obj)
            except Exception as ex:
                logger.error(f"Ошибка при разборе библиотеки {lib_file.name}: {ex}")

        return libraries

    def parse_library_file(self, file_path: Path) -> Optional[WindowsLibrary]:
        """Парсит XML-файл .library-ms и строит модель WindowsLibrary.

        Args:
            file_path: Путь к файлу .library-ms.

        Returns:
            Optional[WindowsLibrary]: Модель библиотеки или None при ошибке.
        """
        if not file_path.exists():
            return None

        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()

            # Имя без .library-ms
            lib_name = file_path.stem

            owner_sid_elem = root.find("lib:ownerSID", self.NS)
            owner_sid = owner_sid_elem.text if owner_sid_elem is not None else None

            is_pinned_elem = root.find("lib:isLibraryPinned", self.NS)
            is_pinned = is_pinned_elem.text.lower() == "true" if is_pinned_elem is not None and is_pinned_elem.text else True

            folders: List[LibraryFolder] = []
            all_exist = True

            connectors = root.findall(".//lib:searchConnectorDescription", self.NS)
            for connector in connectors:
                url_elem = connector.find(".//lib:simpleLocation/lib:url", self.NS)
                if url_elem is not None and url_elem.text:
                    folder_path_str = url_elem.text.strip()
                    path_obj = Path(folder_path_str)
                    exists = path_obj.exists()
                    if not exists:
                        all_exist = False

                    is_default_save = False
                    def_save_elem = connector.find("lib:isDefaultSaveLocation", self.NS)
                    if def_save_elem is not None and def_save_elem.text:
                        is_default_save = def_save_elem.text.lower() == "true"

                    drive_letter = None
                    free_gb = None
                    if exists and len(path_obj.parts) > 0:
                        drive_letter = path_obj.drive
                        try:
                            usage = shutil.disk_usage(str(path_obj))
                            free_gb = round(usage.free / (1024 ** 3), 2)
                        except Exception:
                            pass

                    folders.append(
                        LibraryFolder(
                            path=folder_path_str,
                            exists=exists,
                            is_default_save=is_default_save,
                            drive_letter=drive_letter,
                            free_space_gb=free_gb,
                        )
                    )

            return WindowsLibrary(
                name=lib_name,
                file_path=str(file_path),
                owner_sid=owner_sid,
                is_pinned=is_pinned,
                folder_count=len(folders),
                folders=folders,
                all_folders_exist=all_exist,
            )
        except Exception as ex:
            logger.error(f"Не удалось распарсить {file_path}: {ex}")
            return None

    def create_library(self, name: str, folders: List[str], is_pinned: bool = True) -> WindowsLibrary:
        """Создает новый XML-файл библиотеки Windows .library-ms.

        Args:
            name: Имя библиотеки.
            folders: Список путей к папкам.
            is_pinned: Закреплять ли в проводнике.

        Returns:
            WindowsLibrary: Созданный объект библиотеки.
        """
        clean_name = name.strip()
        target_file = self.libraries_dir / f"{clean_name}.library-ms"

        connectors_xml = []
        for i, folder in enumerate(folders):
            folder_clean = str(Path(folder).resolve())
            is_default = "true" if i == 0 else "false"
            connector = f"""    <searchConnectorDescription>
      <isDefaultSaveLocation>{is_default}</isDefaultSaveLocation>
      <isDefaultNonOwnerSaveLocation>{is_default}</isDefaultNonOwnerSaveLocation>
      <isSupported>true</isSupported>
      <simpleLocation>
        <url>{folder_clean}</url>
      </simpleLocation>
    </searchConnectorDescription>"""
            connectors_xml.append(connector)

        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
  <version>1</version>
  <isLibraryPinned>{"true" if is_pinned else "false"}</isLibraryPinned>
  <templateInfo>
    <folderType>{{00000000-0000-0000-0000-000000000000}}</folderType>
  </templateInfo>
  <searchConnectorDescriptionList>
{chr(10).join(connectors_xml)}
  </searchConnectorDescriptionList>
</libraryDescription>"""

        target_file.write_text(xml_data, encoding="utf-8")
        logger.info(f"Создана библиотека Windows: {clean_name} ({target_file})")

        parsed = self.parse_library_file(target_file)
        if parsed:
            return parsed

        return WindowsLibrary(
            name=clean_name,
            file_path=str(target_file),
            is_pinned=is_pinned,
            folder_count=len(folders),
            folders=[LibraryFolder(path=f, exists=Path(f).exists()) for f in folders],
        )

    def add_folder_to_library(self, library_name: str, folder_path: str, is_default_save: bool = False) -> Optional[WindowsLibrary]:
        """Добавляет директорию в существующую библиотеку Windows.

        Args:
            library_name: Имя библиотеки.
            folder_path: Путь к добавляемой папке.
            is_default_save: Сделать ли основной папкой для сохранения.

        Returns:
            Optional[WindowsLibrary]: Обновленная библиотека или None.
        """
        lib_file = self.libraries_dir / f"{library_name}.library-ms"
        if not lib_file.exists():
            return None

        current = self.parse_library_file(lib_file)
        if not current:
            return None

        existing_paths = [f.path.lower() for f in current.folders]
        folder_clean = str(Path(folder_path).resolve())

        if folder_clean.lower() in existing_paths:
            return current

        all_paths = [f.path for f in current.folders]
        if is_default_save:
            all_paths.insert(0, folder_clean)
        else:
            all_paths.append(folder_clean)

        return self.create_library(current.name, all_paths, is_pinned=current.is_pinned)