# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Backup and Restore Engine
# =============================================================================
# Description:
#   Модуль для создания автоматических резервных копий (снимков) разделов
#   реестра Windows перед модификацией, сохранения истории и отката изменений.
#
# File: backup.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок резервного копирования и отката снимков реестра Windows."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.registry_viewer.models import (
    BackupMetadataDTO,
    RegistryKeyDetailsDTO,
    RestoreBackupResponseDTO,
)
from src.logger import logger

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore


class RegistryBackupManager:
    """Менеджер создания снимков реестра и управления точками восстановления."""

    def __init__(self, backup_dir: Optional[Path] = None) -> None:
        """Инициализировать менеджер бэкапов с указанием рабочей директории.

        Args:
            backup_dir: Пользовательский путь для хранения бэкапов.
        """
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path("data") / "registry_backups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / "backups_index.json"
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Проверить наличие индексного файла истории бэкапов."""
        if not self.metadata_file.exists():
            try:
                self.metadata_file.write_text(json.dumps([], indent=2), encoding="utf-8")
            except Exception as e:
                logger.error(f"Не удалось инициализировать индекс бэкапов: {e}")

    def _load_index(self) -> List[Dict[str, Any]]:
        """Загрузить список метаданных всех бэкапов."""
        if not self.metadata_file.exists():
            return []
        try:
            return json.loads(self.metadata_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Ошибка чтения индекса бэкапов: {e}")
            return []

    def _save_index(self, index_data: List[Dict[str, Any]]) -> None:
        """Сохранить обновленный индекс метаданных бэкапов."""
        try:
            self.metadata_file.write_text(
                json.dumps(index_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса бэкапов: {e}")

    def list_backups(self) -> List[BackupMetadataDTO]:
        """Получить список всех зарегистрированных резервных копий."""
        data = self._load_index()
        # Сортировка от самых свежих к старым
        data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return [BackupMetadataDTO(**item) for item in data]

    def create_snapshot(
        self,
        hive: str,
        path: str,
        operation: str,
        key_details: Optional[RegistryKeyDetailsDTO] = None,
    ) -> BackupMetadataDTO:
        """Создать резервную копию ветки реестра перед операцией.

        Args:
            hive: Корневая ветка (HKLM, HKCU и т.д.).
            path: Относительный путь ключа.
            operation: Название выполняемой операции (set_value, delete_value, delete_key).
            key_details: Снимок данных ключа в виде DTO, если доступен.

        Returns:
            Метаданные созданного бэкапа.
        """
        now = datetime.now()
        timestamp_str = now.isoformat()
        safe_path = re.sub(r'[\\/:*?"<>| ]', "_", f"{hive}_{path}").strip("_")
        if not safe_path:
            safe_path = "root"
        backup_id = f"backup_{now.strftime('%Y%m%d_%H%M%S')}_{safe_path}"

        json_filename = f"{backup_id}.json"
        reg_filename = f"{backup_id}.reg"
        json_file_path = self.backup_dir / json_filename
        reg_file_path = self.backup_dir / reg_filename

        full_key_str = f"{hive}\\{path}".rstrip("\\")

        # 1. Сохранение структуры данных в JSON
        if key_details:
            json_file_path.write_text(
                json.dumps(key_details.model_dump(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        # 2. Создание нативного .reg файла через reg export (на Windows)
        reg_export_success = False
        if os.name == "nt":
            try:
                cmd = f'reg export "{full_key_str}" "{reg_file_path.resolve()}" /y'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    reg_export_success = True
                else:
                    logger.warning(f"Команда reg export вернула код {res.returncode}: {res.stderr}")
            except Exception as e:
                logger.warning(f"Не удалось выполнить нативный reg export: {e}")

        # Если reg export не удался (или ключ новый/пустой), формируем .reg файл вручную
        if not reg_export_success:
            reg_content = self._generate_reg_file_content(hive, path, key_details)
            reg_file_path.write_text(reg_content, encoding="utf-8")

        meta = BackupMetadataDTO(
            backup_id=backup_id,
            timestamp=timestamp_str,
            hive=hive,
            path=path,
            operation=operation,
            file_path=str(json_file_path.resolve()),
            reg_file_path=str(reg_file_path.resolve()),
            values_count=key_details.values_count if key_details else 0,
        )

        index = self._load_index()
        index.append(meta.model_dump())
        self._save_index(index)

        logger.info(f"Создан бэкап реестра {backup_id} для {full_key_str} (операция: {operation})")
        return meta

    def _generate_reg_file_content(
        self,
        hive: str,
        path: str,
        key_details: Optional[RegistryKeyDetailsDTO],
    ) -> str:
        """Сгенерировать текстовое представление файла .reg."""
        lines = ["Windows Registry Editor Version 5.00", "", f"[{hive}\\{path}".rstrip("\\") + "]"]
        if key_details:
            for val in key_details.values:
                val_name_str = f'"{val.name}"' if val.name and val.name != "(Default / По умолчанию)" else "@"
                if val.type_code == 1:  # REG_SZ
                    escaped_data = str(val.data).replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{val_name_str}="{escaped_data}"')
                elif val.type_code == 4:  # REG_DWORD
                    try:
                        int_val = int(val.data)
                        lines.append(f'{val_name_str}=dword:{int_val:08x}')
                    except (ValueError, TypeError):
                        lines.append(f'{val_name_str}="{val.data}"')
                else:
                    lines.append(f'; {val_name_str} (Type: {val.type_name}) = {val.data}')
        lines.append("")
        return "\n".join(lines)

    def restore_backup(self, backup_id: str) -> RestoreBackupResponseDTO:
        """Восстановить состояние реестра из указанного бэкапа.

        Args:
            backup_id: Идентификатор резервной копии.

        Returns:
            RestoreBackupResponseDTO с результатом восстановления.
        """
        index = self._load_index()
        target_meta = next((item for item in index if item["backup_id"] == backup_id), None)
        if not target_meta:
            raise KeyError(f"Резервная копия с ID '{backup_id}' не найдена в индексе")

        reg_path = Path(target_meta.get("reg_file_path", ""))
        json_path = Path(target_meta.get("file_path", ""))

        # Попытка восстановления через reg import на Windows
        if os.name == "nt" and reg_path.exists():
            try:
                cmd = f'reg import "{reg_path.resolve()}"'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    logger.info(f"Реестр успешно восстановлен из .reg файла {reg_path}")
                    return RestoreBackupResponseDTO(
                        status="ok",
                        backup_id=backup_id,
                        message=f"Реестр успешно восстановлен из нативного файла {reg_path.name}",
                        hive=target_meta["hive"],
                        path=target_meta["path"],
                    )
            except Exception as e:
                logger.warning(f"Ошибка выполнения reg import: {e}. Попытка восстановления из JSON.")

        # Fallback: ручное восстановление значений из JSON через winreg
        if json_path.exists():
            try:
                content = json.loads(json_path.read_text(encoding="utf-8"))
                hive = content.get("hive", target_meta["hive"])
                path = content.get("path", target_meta["path"])
                values = content.get("values", [])

                if winreg:
                    hive_map = {
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
                    root_hive = hive_map.get(hive.upper())
                    if root_hive:
                        with winreg.CreateKey(root_hive, path) as key:
                            for val in values:
                                v_name = val.get("name")
                                if v_name == "(Default / По умолчанию)" or v_name == "(Default)":
                                    v_name = ""
                                v_type = val.get("type_code", 1)
                                v_data = val.get("data")
                                winreg.SetValueEx(key, v_name, 0, v_type, v_data)

                logger.info(f"Реестр успешно восстановлен из JSON снимка {json_path}")
                return RestoreBackupResponseDTO(
                    status="ok",
                    backup_id=backup_id,
                    message=f"Параметры ключа '{hive}\\{path}' восстановлены из JSON снимка ({len(values)} параметров)",
                    hive=hive,
                    path=path,
                )
            except Exception as e:
                logger.error(f"Не удалось восстановить бэкап из JSON: {e}")
                raise RuntimeError(f"Ошибка восстановления из JSON: {e}")

        raise FileNotFoundError(f"Файлы резервной копии для ID '{backup_id}' не найдены на диске")
