# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows File History & Backup Storage Auditor
# =============================================================================
# Description:
#   Аудитор целевых хранилищ резервных копий Windows. Анализ структуры
#   каталогов FileHistory\<User>\<Host>\Data, учет версий файлов,
#   контроль свободного дискового пространства и выявление аномалий.
#
# Examples:
#   >>> from apps.windows.backup_manager.core.storage_auditor import BackupStorageAuditor
#   >>> auditor = BackupStorageAuditor()
#   >>> report = auditor.audit_storage("X:\\")
#
# File: storage_auditor.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль аудита и проверки целостности хранилища резервных копий Windows."""

from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from logger import logger
from apps.windows.backup_manager.core.models import (
    FileVersionRecord,
    StorageBackupAudit,
)


class BackupStorageAuditor:
    """Аудитор физических хранилищ резервных копий."""

    # Регулярка для извлечения даты версии из имени файла Windows:
    # Пример: document (2026_09_16 19_30_00 UTC).docx
    VERSION_REGEX = re.compile(r"^(.*?)(?: \((\d{4}_\d{2}_\d{2} \d{2}_\d{2}_\d{2} UTC)\))?(\.[^.]*)?$")

    def audit_storage(self, target_path_str: Optional[str] = None) -> StorageBackupAudit:
        """Проводит комплексный аудит хранилища резервных копий.

        Args:
            target_path_str: Путь к диску или каталогу бэкапа. Если не указан, пытается определить автоматически.

        Returns:
            StorageBackupAudit: Результат аудита с метриками объемов и версий.
        """
        if not target_path_str:
            # Попробуем найти на доступных подключенных дисках
            target_path_str = self._detect_backup_location()

        if not target_path_str:
            return StorageBackupAudit(
                target_path="Not configured / Not found",
                target_exists=False,
            )

        target_path = Path(target_path_str)
        if not target_path.exists():
            return StorageBackupAudit(
                target_path=str(target_path),
                target_exists=False,
            )

        free_gb = None
        total_gb = None
        try:
            usage = shutil.disk_usage(str(target_path))
            free_gb = round(usage.free / (1024 ** 3), 2)
            total_gb = round(usage.total / (1024 ** 3), 2)
        except Exception as ex:
            logger.debug(f"Не удалось получить disk_usage для {target_path}: {ex}")

        # Поиск папки Data
        data_roots = list(target_path.glob("FileHistory/*/*/Data"))
        if not data_roots:
            data_roots = list(target_path.glob("*/FileHistory/*/*/Data"))

        total_versions = 0
        total_bytes = 0
        drives_found = set()
        sample_versions: List[FileVersionRecord] = []

        if data_roots:
            for d_root in data_roots:
                for drive_dir in d_root.iterdir():
                    if drive_dir.is_dir():
                        drives_found.add(drive_dir.name)

                        # Сканируем файлы в директории
                        for root, _, files in os.walk(drive_dir):
                            for fname in files:
                                fpath = Path(root) / fname
                                try:
                                    fstat = fpath.stat()
                                    size = fstat.st_size
                                    total_bytes += size
                                    total_versions += 1

                                    if len(sample_versions) < 20:
                                        ts = None
                                        match = self.VERSION_REGEX.match(fname)
                                        if match and match.group(2):
                                            try:
                                                ts = datetime.strptime(match.group(2), "%Y_%m_%d %H_%M_%S UTC")
                                            except Exception:
                                                pass

                                        sample_versions.append(
                                            FileVersionRecord(
                                                original_relative_path=str(fpath.relative_to(d_root)),
                                                backup_file_path=str(fpath),
                                                version_timestamp=ts or datetime.fromtimestamp(fstat.st_mtime),
                                                size_bytes=size,
                                            )
                                        )
                                except Exception:
                                    continue

        total_mb = round(total_bytes / (1024 ** 2), 2)

        return StorageBackupAudit(
            target_path=str(target_path),
            target_exists=True,
            total_versions_found=total_versions,
            total_backup_size_bytes=total_bytes,
            total_backup_size_mb=total_mb,
            free_space_gb=free_gb,
            total_space_gb=total_gb,
            drives_in_backup=sorted(list(drives_found)),
            sample_versions=sample_versions,
        )

    def _detect_backup_location(self) -> Optional[str]:
        """Ищет типичные каталоги FileHistory на всех подключенных дисках Windows."""
        for drive_letter in ["D", "E", "F", "G", "H", "J", "R", "T", "X", "Z"]:
            candidate = Path(f"{drive_letter}:\\")
            if candidate.exists():
                fh_dir = candidate / "FileHistory"
                if fh_dir.exists():
                    return str(candidate)
        return None