# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup Health & Diagnostics Engine
# =============================================================================
# Description:
#   Комплексный аудитор готовности резервного копирования Windows.
#   Собирает метрики по библиотекам, состоянию службы File History,
#   дисковому пространству и снимкам VSS, рассчитывает Health Score.
#
# Examples:
#   >>> from apps.windows.backup_manager.core.health_checker import BackupHealthChecker
#   >>> checker = BackupHealthChecker()
#   >>> report = checker.generate_report()
#
# File: health_checker.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок комплексного аудита готовности резервного копирования."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from apps.windows.backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows.backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows.backup_manager.core.models import (
    BackupHealthReport,
    ServiceState,
)
from apps.windows.backup_manager.core.storage_auditor import BackupStorageAuditor
from apps.windows.backup_manager.core.vss_manager import VssManager


class BackupHealthChecker:
    """Аудитор готовности и здоровья системы резервного копирования Windows."""

    def __init__(
        self,
        lib_mgr: Optional[WindowsLibrariesManager] = None,
        fh_mgr: Optional[FileHistoryManager] = None,
        storage_auditor: Optional[BackupStorageAuditor] = None,
        vss_mgr: Optional[VssManager] = None,
    ) -> None:
        self.lib_mgr = lib_mgr or WindowsLibrariesManager()
        self.fh_mgr = fh_mgr or FileHistoryManager()
        self.storage_auditor = storage_auditor or BackupStorageAuditor()
        self.vss_mgr = vss_mgr or VssManager()

    def generate_report(self) -> BackupHealthReport:
        """Формирует детальный сводный отчет о состоянии системы бэкапов.

        Returns:
            BackupHealthReport: Полный аналитический отчет с оценкой индекса здоровья.
        """
        libraries = self.lib_mgr.get_all_libraries()
        fh_status = self.fh_mgr.get_status()
        storage_audit = self.storage_auditor.audit_storage(
            fh_status.config.target_url or fh_status.config.target_drive_letter
        )
        vss_snapshots = self.vss_mgr.list_snapshots()

        # Расчет индекса здоровья (Health Score)
        score = 100
        recommendations: List[str] = []

        # 1. Проверка библиотек
        if not libraries:
            score -= 25
            recommendations.append("Не найдено настроенных библиотек Windows (.library-ms). Создайте библиотеки для важных папок.")
        else:
            missing_folders = [f.path for lib in libraries for f in lib.folders if not f.exists]
            if missing_folders:
                score -= 15
                recommendations.append(f"Некоторые папки в библиотеках недоступны или удалены ({len(missing_folders)} шт.).")

        # 2. Проверка службы File History
        if fh_status.service_status != ServiceState.RUNNING:
            score -= 20
            recommendations.append(f"Служба Истории файлов (fhsvc) не запущена (статус: {fh_status.service_status.value}). Рекомендуется перевести в Auto и запустить.")

        # 3. Проверка целевой конфигурации
        if not fh_status.config.is_configured:
            score -= 30
            recommendations.append("История файлов не настроена в Windows. Назначьте целевой диск для резервного копирования.")
        else:
            if not storage_audit.target_exists:
                score -= 25
                recommendations.append("Целевой накопитель резервных копий недоступен или отключен.")

        if storage_audit.free_space_gb is not None and storage_audit.free_space_gb < 10.0:
            score -= 15
            recommendations.append(f"На целевом диске бэкапов осталось мало свободного места ({storage_audit.free_space_gb} ГБ).")

        score = max(0, min(100, score))

        return BackupHealthReport(
            timestamp=datetime.now(),
            libraries_count=len(libraries),
            libraries=libraries,
            file_history=fh_status,
            storage_audit=storage_audit,
            vss_snapshots=vss_snapshots,
            health_score=score,
            recommendations=recommendations,
        )