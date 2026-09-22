# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer Core Engine
# =============================================================================
# Description:
#   Ядро для безопасного чтения, навигации, рекурсивного поиска и экспорта
#   данных системного реестра Windows (с поддержкой мок-режима).
#
# File: viewer.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Ядро чтения и исследования системного реестра Windows."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from apps.registry_viewer.backup import RegistryBackupManager
from apps.registry_viewer.models import (
    BackupMetadataDTO,
    BookmarkItem,
    CreateKeyRequestDTO,
    DeleteKeyRequestDTO,
    DeleteValueRequestDTO,
    EditOperationResultDTO,
    RegistryKeyDetailsDTO,
    RegistryValueDTO,
    RestoreBackupResponseDTO,
    SearchMatchItem,
    SearchResponseDTO,
    SetValueRequestDTO,
)

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

# Маппинг строковых типов на числовые коды winreg
TYPE_NAME_TO_CODE = {
    "REG_SZ": 1,
    "REG_EXPAND_SZ": 2,
    "REG_BINARY": 3,
    "REG_DWORD": 4,
    "REG_DWORD_BIG_ENDIAN": 5,
    "REG_LINK": 6,
    "REG_MULTI_SZ": 7,
    "REG_RESOURCE_LIST": 8,
    "REG_FULL_RESOURCE_DESCRIPTOR": 9,
    "REG_RESOURCE_REQUIREMENTS_LIST": 10,
    "REG_QWORD": 11,
}

# Маппинг корневых веток реестра
HIVE_MAP: Dict[str, Any] = {}
if winreg:
    HIVE_MAP = {
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKEY_USERS": winreg.HKEY_USERS,
        "HKU": winreg.HKEY_USERS,
        "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        "HKCC": winreg.HKEY_CURRENT_CONFIG,
    }

REG_TYPE_NAMES = {
    0: "REG_NONE",
    1: "REG_SZ",
    2: "REG_EXPAND_SZ",
    3: "REG_BINARY",
    4: "REG_DWORD",
    5: "REG_DWORD_BIG_ENDIAN",
    6: "REG_LINK",
    7: "REG_MULTI_SZ",
    8: "REG_RESOURCE_LIST",
    9: "REG_FULL_RESOURCE_DESCRIPTOR",
    10: "REG_RESOURCE_REQUIREMENTS_LIST",
    11: "REG_QWORD",
}

COMMON_BOOKMARKS: List[Dict[str, Any]] = [
    {
        "id": "startup_run",
        "title": "Автозагрузка пользователя (Run)",
        "hive": "HKEY_CURRENT_USER",
        "path": r"Software\Microsoft\Windows\CurrentVersion\Run",
        "description": "Программы, автоматически запускаемые при входе текущего пользователя",
        "icon": "🚀",
    },
    {
        "id": "startup_run_hklm",
        "title": "Общесистемная автозагрузка (Run HKLM)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "description": "Общесистемные программы автозапуска для всех пользователей",
        "icon": "⚙️",
    },
    {
        "id": "installed_apps_x64",
        "title": "Установленные программы (x64)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        "description": "Список 64-битных установленных программ и компонентов системы",
        "icon": "📦",
    },
    {
        "id": "installed_apps_x86",
        "title": "Установленные программы (x86)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        "description": "Список 32-битных установленных программ в 64-битной среде Windows",
        "icon": "📁",
    },
    {
        "id": "services",
        "title": "Системные службы (Services)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SYSTEM\CurrentControlSet\Services",
        "description": "Конфигурация всех установленных системных служб и драйверов Windows",
        "icon": "🛡️",
    },
    {
        "id": "environment",
        "title": "Переменные среды (Environment)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        "description": "Системные переменные окружения ОС (PATH, TEMP и др.)",
        "icon": "🌐",
    },
    {
        "id": "userassist",
        "title": "История UserAssist",
        "hive": "HKEY_CURRENT_USER",
        "path": r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist",
        "description": "Статистика и история запусков приложений текущего пользователя",
        "icon": "📊",
    },
    {
        "id": "policies",
        "title": "Групповые политики (Policies)",
        "hive": "HKEY_LOCAL_MACHINE",
        "path": r"SOFTWARE\Policies\Microsoft\Windows",
        "description": "Системные групповые политики безопасности и ограничений",
        "icon": "🔒",
    },
]


class RegistryViewer:
    """Основной движок взаимодействия, редактирования и бэкапа реестра Windows."""

    def __init__(self, config_path: Optional[str] = None, backup_dir: Optional[Path] = None) -> None:
        """Инициализация RegistryViewer с загрузкой конфигурации и менеджера бэкапов."""
        self.config: Dict[str, Any] = {}
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.warning(f"Не удалось загрузить конфиг из {config_path}: {e}")

        self.backup_manager = RegistryBackupManager(backup_dir=backup_dir)

    @staticmethod
    def _canonical_hive(hive: str) -> str:
        """Нормализовать имя корневой ветки реестра."""
        h = hive.strip().upper()
        return {
            "HKLM": "HKEY_LOCAL_MACHINE",
            "HKCU": "HKEY_CURRENT_USER",
            "HKCR": "HKEY_CLASSES_ROOT",
            "HKU": "HKEY_USERS",
            "HKCC": "HKEY_CURRENT_CONFIG",
        }.get(h, h)

    @staticmethod
    def format_value_data(raw_data: Any, type_code: int) -> Tuple[Any, int]:
        """Форматировать сырые данные реестра в безопасный сериализуемый формат."""
        if isinstance(raw_data, bytes):
            size = len(raw_data)
            hex_preview = raw_data[:64].hex().upper()
            formatted_hex = " ".join(hex_preview[i:i + 2] for i in range(0, len(hex_preview), 2))
            if size > 64:
                formatted_hex += f" ... ({size} bytes total)"
            return formatted_hex, size
        if isinstance(raw_data, list):
            return raw_data, sum(len(str(x)) for x in raw_data)
        if isinstance(raw_data, int):
            return raw_data, 4 if type_code == 4 else 8
        str_val = str(raw_data)
        return str_val, len(str_val.encode("utf-8", errors="ignore"))

    def get_bookmarks(self) -> List[BookmarkItem]:
        """Получить список предопределенных быстрых системных закладок."""
        return [BookmarkItem(**bm) for bm in COMMON_BOOKMARKS]

    def get_bookmark_by_id(self, bookmark_id: str) -> Optional[BookmarkItem]:
        """Получить закладку по её идентификатору."""
        for bm in COMMON_BOOKMARKS:
            if bm["id"] == bookmark_id:
                return BookmarkItem(**bm)
        return None

    def read_key(
        self,
        hive: str = "HKEY_LOCAL_MACHINE",
        path: str = "",
        max_subkeys: int = 1000,
        max_values: int = 500,
    ) -> RegistryKeyDetailsDTO:
        """Безопасно прочитать подразделы и параметры указанного ключа реестра."""
        hive_canonical = self._canonical_hive(hive)
        path_clean = path.strip().strip("\\/")

        if not winreg or hive_canonical not in HIVE_MAP:
            return self._get_mock_key_details(hive_canonical, path_clean)

        root_hive = HIVE_MAP[hive_canonical]
        subkeys: List[str] = []
        values: List[RegistryValueDTO] = []

        try:
            access_rights = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
            with winreg.OpenKey(root_hive, path_clean, 0, access_rights) as key:
                num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

                for i in range(min(num_subkeys, max_subkeys)):
                    try:
                        sk_name = winreg.EnumKey(key, i)
                        subkeys.append(sk_name)
                    except OSError:
                        continue

                for j in range(min(num_values, max_values)):
                    try:
                        val_name, raw_data, val_type = winreg.EnumValue(key, j)
                        display_name = val_name if val_name else "(Default / По умолчанию)"
                        formatted_data, size_b = self.format_value_data(raw_data, val_type)
                        type_str = REG_TYPE_NAMES.get(val_type, f"REG_TYPE_{val_type}")

                        values.append(
                            RegistryValueDTO(
                                name=display_name,
                                type_code=val_type,
                                type_name=type_str,
                                data=formatted_data,
                                size_bytes=size_b,
                            )
                        )
                    except OSError:
                        continue

        except FileNotFoundError:
            raise KeyError(f"Ключ реестра '{hive_canonical}\\{path_clean}' не найден")
        except PermissionError:
            raise PermissionError(f"Отказано в доступе к ветке '{hive_canonical}\\{path_clean}'")
        except Exception as e:
            logger.error(f"Ошибка чтения реестра {hive_canonical}\\{path_clean}: {e}")
            raise RuntimeError(f"Ошибка чтения реестра: {str(e)}")

        subkeys.sort(key=str.lower)
        full_path_str = f"{hive_canonical}\\{path_clean}".rstrip("\\")

        return RegistryKeyDetailsDTO(
            hive=hive_canonical,
            path=path_clean,
            full_path=full_path_str,
            subkeys=subkeys,
            values=values,
            subkeys_count=len(subkeys),
            values_count=len(values),
        )

    def search(
        self,
        query: str,
        hive: str = "HKEY_LOCAL_MACHINE",
        path: str = "SOFTWARE",
        max_results: int = 50,
        max_depth: int = 3,
    ) -> SearchResponseDTO:
        """Поиск ключей, параметров и значений по поддереву реестра."""
        hive_canonical = self._canonical_hive(hive)
        path_clean = path.strip().strip("\\/")
        query_lower = query.lower()
        results: List[SearchMatchItem] = []

        if not winreg or hive_canonical not in HIVE_MAP:
            return self._get_mock_search_results(hive_canonical, path_clean, query, max_results)

        root_hive = HIVE_MAP[hive_canonical]
        access_rights = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)

        def _traverse(current_path: str, depth: int) -> None:
            if len(results) >= max_results or depth > max_depth:
                return

            try:
                with winreg.OpenKey(root_hive, current_path, 0, access_rights) as key:
                    num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

                    # Проверка параметров
                    for j in range(min(num_values, 100)):
                        if len(results) >= max_results:
                            return
                        try:
                            val_name, raw_data, val_type = winreg.EnumValue(key, j)
                            display_val_name = val_name if val_name else "(Default)"
                            formatted_data, _ = self.format_value_data(raw_data, val_type)
                            type_str = REG_TYPE_NAMES.get(val_type, f"REG_TYPE_{val_type}")

                            # Совпадение в имени параметра
                            if query_lower in display_val_name.lower():
                                results.append(
                                    SearchMatchItem(
                                        hive=hive_canonical,
                                        key_path=current_path,
                                        match_type="value_name",
                                        matched_text=display_val_name,
                                        value_name=display_val_name,
                                        value_type=type_str,
                                        value_data=formatted_data,
                                    )
                                )

                            # Совпадение в значении параметра
                            str_data = str(formatted_data).lower()
                            if query_lower in str_data and len(results) < max_results:
                                results.append(
                                    SearchMatchItem(
                                        hive=hive_canonical,
                                        key_path=current_path,
                                        match_type="value_data",
                                        matched_text=str(formatted_data)[:200],
                                        value_name=display_val_name,
                                        value_type=type_str,
                                        value_data=formatted_data,
                                    )
                                )
                        except OSError:
                            continue

                    # Проверка и обход подразделов
                    for i in range(min(num_subkeys, 100)):
                        if len(results) >= max_results:
                            return
                        try:
                            sk_name = winreg.EnumKey(key, i)
                            child_path = f"{current_path}\\{sk_name}" if current_path else sk_name

                            if query_lower in sk_name.lower():
                                results.append(
                                    SearchMatchItem(
                                        hive=hive_canonical,
                                        key_path=child_path,
                                        match_type="key_name",
                                        matched_text=sk_name,
                                    )
                                )

                            _traverse(child_path, depth + 1)
                        except OSError:
                            continue
            except (FileNotFoundError, PermissionError, OSError):
                return

        _traverse(path_clean, 1)

        return SearchResponseDTO(
            status="ok",
            hive=hive_canonical,
            path=path_clean,
            query=query,
            total_found=len(results),
            results=results,
        )

    def export_key_to_json(self, key_details: RegistryKeyDetailsDTO, target_file: Optional[Path] = None) -> str:
        """Экспорт информации о ключе в формат JSON."""
        json_str = json.dumps(key_details.model_dump(), indent=2, ensure_ascii=False)
        if target_file:
            target_file.write_text(json_str, encoding="utf-8")
        return json_str

    def export_key_to_csv(self, key_details: RegistryKeyDetailsDTO, target_file: Optional[Path] = None) -> str:
        """Экспорт параметров ключа в формат CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["KeyPath", "ValueName", "Type", "Data", "SizeBytes"])

        for val in key_details.values:
            writer.writerow([key_details.full_path, val.name, val.type_name, str(val.data), val.size_bytes])

        csv_str = output.getvalue()
        if target_file:
            target_file.write_text(csv_str, encoding="utf-8")
        return csv_str

    # =========================================================================
    # Операции редактирования и резервного копирования реестра
    # =========================================================================

    def _prepare_value_for_write(self, type_name: str, raw_data: Any) -> Tuple[int, Any]:
        """Преобразовать входные данные в корректный тип для winreg."""
        type_code = TYPE_NAME_TO_CODE.get(type_name.upper(), 1)

        if type_code in (4, 5):  # REG_DWORD, REG_DWORD_BIG_ENDIAN
            try:
                return type_code, int(raw_data)
            except (ValueError, TypeError):
                raise ValueError(f"Значение '{raw_data}' не может быть приведено к числу DWORD")

        if type_code == 11:  # REG_QWORD
            try:
                return type_code, int(raw_data)
            except (ValueError, TypeError):
                raise ValueError(f"Значение '{raw_data}' не может быть приведено к 64-битному числу QWORD")

        if type_code == 7:  # REG_MULTI_SZ
            if isinstance(raw_data, list):
                return type_code, [str(x) for x in raw_data]
            if isinstance(raw_data, str):
                return type_code, [s.strip() for s in raw_data.split("\n") if s.strip()]
            return type_code, [str(raw_data)]

        if type_code == 3:  # REG_BINARY
            if isinstance(raw_data, bytes):
                return type_code, raw_data
            if isinstance(raw_data, str):
                cleaned_hex = raw_data.replace(" ", "").replace("0x", "")
                try:
                    return type_code, bytes.fromhex(cleaned_hex)
                except ValueError:
                    return type_code, raw_data.encode("utf-8")
            return type_code, bytes(raw_data)

        # По умолчанию строковые типы REG_SZ, REG_EXPAND_SZ и т.д.
        return type_code, str(raw_data)

    def set_value(self, req: SetValueRequestDTO) -> EditOperationResultDTO:
        """Создать или изменить параметр в реестре с обязательным автобэкапом.

        Args:
            req: DTO с параметрами запроса (hive, path, name, type_name, data, create_backup).

        Returns:
            Результат операции EditOperationResultDTO.
        """
        hive_canonical = self._canonical_hive(req.hive)
        path_clean = req.path.strip().strip("\\/")
        val_name = req.name.strip()
        if val_name == "(Default / По умолчанию)" or val_name == "(Default)":
            val_name = ""

        type_code, typed_data = self._prepare_value_for_write(req.type_name, req.data)

        backup_meta: Optional[BackupMetadataDTO] = None
        if req.create_backup:
            try:
                current_details = self.read_key(hive=hive_canonical, path=path_clean)
                backup_meta = self.backup_manager.create_snapshot(
                    hive=hive_canonical,
                    path=path_clean,
                    operation=f"set_value:{req.name or '@'}",
                    key_details=current_details,
                )
            except Exception as e:
                logger.warning(f"Не удалось создать снимок перед set_value: {e}")

        if not winreg or hive_canonical not in HIVE_MAP:
            logger.info(f"[MOCK] Запись в реестр {hive_canonical}\\{path_clean}: {val_name} = {typed_data}")
            return EditOperationResultDTO(
                status="ok",
                operation="set_value",
                hive=hive_canonical,
                path=path_clean,
                backup=backup_meta,
                message=f"[MOCK] Параметр '{req.name or '@'}' успешно сохранен",
            )

        root_hive = HIVE_MAP[hive_canonical]
        try:
            with winreg.CreateKey(root_hive, path_clean) as key:
                winreg.SetValueEx(key, val_name, 0, type_code, typed_data)
        except PermissionError:
            raise PermissionError(f"Отказано в доступе при записи в '{hive_canonical}\\{path_clean}'. Требуются права администратора.")
        except Exception as e:
            logger.error(f"Ошибка записи параметра реестра: {e}")
            raise RuntimeError(f"Ошибка сохранения параметра: {str(e)}")

        logger.info(f"Параметр '{req.name or '@'}' успешно сохранен в '{hive_canonical}\\{path_clean}'")
        return EditOperationResultDTO(
            status="ok",
            operation="set_value",
            hive=hive_canonical,
            path=path_clean,
            backup=backup_meta,
            message=f"Параметр '{req.name or '@'}' успешно сохранен",
        )

    def delete_value(self, req: DeleteValueRequestDTO) -> EditOperationResultDTO:
        """Удалить параметр из реестра с обязательным автобэкапом.

        Args:
            req: DTO с параметрами удаления (hive, path, name, create_backup).

        Returns:
            Результат операции EditOperationResultDTO.
        """
        hive_canonical = self._canonical_hive(req.hive)
        path_clean = req.path.strip().strip("\\/")
        val_name = req.name.strip()
        if val_name == "(Default / По умолчанию)" or val_name == "(Default)":
            val_name = ""

        backup_meta: Optional[BackupMetadataDTO] = None
        if req.create_backup:
            try:
                current_details = self.read_key(hive=hive_canonical, path=path_clean)
                backup_meta = self.backup_manager.create_snapshot(
                    hive=hive_canonical,
                    path=path_clean,
                    operation=f"delete_value:{req.name}",
                    key_details=current_details,
                )
            except Exception as e:
                logger.warning(f"Не удалось создать снимок перед delete_value: {e}")

        if not winreg or hive_canonical not in HIVE_MAP:
            logger.info(f"[MOCK] Удаление параметра {val_name} из {hive_canonical}\\{path_clean}")
            return EditOperationResultDTO(
                status="ok",
                operation="delete_value",
                hive=hive_canonical,
                path=path_clean,
                backup=backup_meta,
                message=f"[MOCK] Параметр '{req.name}' успешно удален",
            )

        root_hive = HIVE_MAP[hive_canonical]
        try:
            with winreg.OpenKey(root_hive, path_clean, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, val_name)
        except FileNotFoundError:
            raise KeyError(f"Параметр '{req.name}' не найден в ключе '{hive_canonical}\\{path_clean}'")
        except PermissionError:
            raise PermissionError(f"Отказано в доступе при удалении параметра из '{hive_canonical}\\{path_clean}'")
        except Exception as e:
            logger.error(f"Ошибка удаления параметра реестра: {e}")
            raise RuntimeError(f"Ошибка удаления параметра: {str(e)}")

        logger.info(f"Параметр '{req.name}' успешно удален из '{hive_canonical}\\{path_clean}'")
        return EditOperationResultDTO(
            status="ok",
            operation="delete_value",
            hive=hive_canonical,
            path=path_clean,
            backup=backup_meta,
            message=f"Параметр '{req.name}' успешно удален",
        )

    def create_key(self, req: CreateKeyRequestDTO) -> EditOperationResultDTO:
        """Создать новый подраздел в реестре.

        Args:
            req: DTO с параметрами создания ключа.

        Returns:
            Результат операции EditOperationResultDTO.
        """
        hive_canonical = self._canonical_hive(req.hive)
        path_clean = req.path.strip().strip("\\/")

        if not winreg or hive_canonical not in HIVE_MAP:
            logger.info(f"[MOCK] Создание ключа {hive_canonical}\\{path_clean}")
            return EditOperationResultDTO(
                status="ok",
                operation="create_key",
                hive=hive_canonical,
                path=path_clean,
                backup=None,
                message=f"[MOCK] Подраздел '{hive_canonical}\\{path_clean}' успешно создан",
            )

        root_hive = HIVE_MAP[hive_canonical]
        try:
            with winreg.CreateKey(root_hive, path_clean) as _:
                pass
        except PermissionError:
            raise PermissionError(f"Отказано в доступе при создании ключа '{hive_canonical}\\{path_clean}'")
        except Exception as e:
            logger.error(f"Ошибка создания ключа реестра: {e}")
            raise RuntimeError(f"Ошибка создания ключа: {str(e)}")

        logger.info(f"Подраздел '{hive_canonical}\\{path_clean}' успешно создан")
        return EditOperationResultDTO(
            status="ok",
            operation="create_key",
            hive=hive_canonical,
            path=path_clean,
            backup=None,
            message=f"Подраздел '{hive_canonical}\\{path_clean}' успешно создан",
        )

    def delete_key(self, req: DeleteKeyRequestDTO) -> EditOperationResultDTO:
        """Удалить подраздел реестра с предварительным автобэкапом.

        Args:
            req: DTO с параметрами удаления ключа (recursive, create_backup).

        Returns:
            Результат операции EditOperationResultDTO.
        """
        hive_canonical = self._canonical_hive(req.hive)
        path_clean = req.path.strip().strip("\\/")

        backup_meta: Optional[BackupMetadataDTO] = None
        if req.create_backup:
            try:
                current_details = self.read_key(hive=hive_canonical, path=path_clean)
                backup_meta = self.backup_manager.create_snapshot(
                    hive=hive_canonical,
                    path=path_clean,
                    operation="delete_key",
                    key_details=current_details,
                )
            except Exception as e:
                logger.warning(f"Не удалось создать снимок перед delete_key: {e}")

        if not winreg or hive_canonical not in HIVE_MAP:
            logger.info(f"[MOCK] Удаление ключа {hive_canonical}\\{path_clean}")
            return EditOperationResultDTO(
                status="ok",
                operation="delete_key",
                hive=hive_canonical,
                path=path_clean,
                backup=backup_meta,
                message=f"[MOCK] Раздел '{hive_canonical}\\{path_clean}' успешно удален",
            )

        root_hive = HIVE_MAP[hive_canonical]

        def _delete_tree(parent_hive: Any, sub_path: str) -> None:
            with winreg.OpenKey(parent_hive, sub_path, 0, winreg.KEY_ALL_ACCESS) as k:
                num_subkeys, _, _ = winreg.QueryInfoKey(k)
                for _ in range(num_subkeys):
                    child = winreg.EnumKey(k, 0)
                    _delete_tree(k, child)
            winreg.DeleteKey(parent_hive, sub_path)

        try:
            if req.recursive:
                _delete_tree(root_hive, path_clean)
            else:
                winreg.DeleteKey(root_hive, path_clean)
        except FileNotFoundError:
            raise KeyError(f"Ключ '{hive_canonical}\\{path_clean}' не найден")
        except PermissionError:
            raise PermissionError(f"Отказано в доступе при удалении ключа '{hive_canonical}\\{path_clean}'")
        except Exception as e:
            logger.error(f"Ошибка удаления ключа реестра: {e}")
            raise RuntimeError(f"Ошибка удаления ключа: {str(e)}")

        logger.info(f"Раздел '{hive_canonical}\\{path_clean}' успешно удален")
        return EditOperationResultDTO(
            status="ok",
            operation="delete_key",
            hive=hive_canonical,
            path=path_clean,
            backup=backup_meta,
            message=f"Раздел '{hive_canonical}\\{path_clean}' успешно удален",
        )

    def list_backups(self) -> List[BackupMetadataDTO]:
        """Получить список всех резервных копий."""
        return self.backup_manager.list_backups()

    def restore_backup(self, backup_id: str) -> RestoreBackupResponseDTO:
        """Восстановить раздел реестра из снимка бэкапа."""
        return self.backup_manager.restore_backup(backup_id)

    def _get_mock_key_details(self, hive: str, path: str) -> RegistryKeyDetailsDTO:
        """Сгенерировать мок-данные при отсутствии прямого доступа к winreg."""
        full = f"{hive}\\{path}".rstrip("\\")
        subkeys = ["Microsoft", "Classes", "Clients", "RegisteredApplications", "Windows"]
        values = [
            RegistryValueDTO(
                name="(Default / По умолчанию)",
                type_code=1,
                type_name="REG_SZ",
                data="Mock Windows Registry Entry",
                size_bytes=26,
            ),
            RegistryValueDTO(
                name="Version",
                type_code=1,
                type_name="REG_SZ",
                data="10.0.26100.1",
                size_bytes=12,
            ),
            RegistryValueDTO(
                name="SystemType",
                type_code=4,
                type_name="REG_DWORD",
                data=64,
                size_bytes=4,
            ),
            RegistryValueDTO(
                name="PathList",
                type_code=7,
                type_name="REG_MULTI_SZ",
                data=["C:\\Windows\\System32", "C:\\Windows"],
                size_bytes=30,
            ),
        ]
        return RegistryKeyDetailsDTO(
            hive=hive,
            path=path,
            full_path=full,
            subkeys=subkeys,
            values=values,
            subkeys_count=len(subkeys),
            values_count=len(values),
        )

    def _get_mock_search_results(
        self, hive: str, path: str, query: str, max_results: int
    ) -> SearchResponseDTO:
        """Сгенерировать мок-результаты поиска."""
        results = [
            SearchMatchItem(
                hive=hive,
                key_path=f"{path}\\Microsoft\\Windows\\CurrentVersion",
                match_type="key_name",
                matched_text=f"Windows ({query})",
            ),
            SearchMatchItem(
                hive=hive,
                key_path=f"{path}\\Microsoft\\Windows\\CurrentVersion\\Run",
                match_type="value_name",
                matched_text=f"SecurityHealth_{query}",
                value_name=f"SecurityHealth_{query}",
                value_type="REG_SZ",
                value_data="C:\\Windows\\system32\\SecurityHealthSystray.exe",
            ),
        ]
        return SearchResponseDTO(
            status="ok",
            hive=hive,
            path=path,
            query=query,
            total_found=len(results[:max_results]),
            results=results[:max_results],
        )

