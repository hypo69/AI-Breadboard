# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup, Libraries & File History FastAPI Router
# =============================================================================
# Description:
#   REST API эндпоинты для аудита библиотек Windows, службы File History,
#   создания библиотек, принудительного запуска резервного копирования
#   и проверки теневых копий VSS.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.backup_manager.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для Windows Backup Manager."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from logger import logger
from apps.common.csv_logger import AppCsvLogger
from apps.windows.backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows.backup_manager.core.file_history_rag import WindowsFileHistoryRAG, get_file_history_rag
from apps.windows.backup_manager.core.health_checker import BackupHealthChecker
from apps.windows.backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows.backup_manager.core.models import (
    AddFolderToLibraryRequest,
    BackupHealthReport,
    CreateLibraryRequest,
    FileHistoryConfigInfo,
    FileHistoryRAGSearchRequest,
    FileHistoryRAGSearchResult,
    FileHistoryRAGStatus,
    FileHistoryRAGSyncRequest,
    FileHistoryStatus,
    FileHistoryVersionSummary,
    RelocateFolderRequest,
    RelocateFolderResponse,
    StorageBackupAudit,
    UserFoldersOverviewResponse,
    VssSnapshot,
    WindowsLibrary,
)
from apps.windows.backup_manager.core.storage_auditor import BackupStorageAuditor
from apps.windows.backup_manager.core.user_folders_manager import UserFoldersManager
from apps.windows.backup_manager.core.vss_manager import VssManager

_csv_logger = AppCsvLogger("windows_backup_manager")


def init_router() -> APIRouter:
    """Инициализация и сборка маршрутов FastAPI роутера.

    Returns:
        APIRouter: Сконфигурированный роутер.
    """
    router = APIRouter(prefix="/api/v1/windows-backup", tags=["Windows Backup & Libraries"])

    lib_mgr = WindowsLibrariesManager()
    fh_mgr = FileHistoryManager()
    storage_auditor = BackupStorageAuditor()
    vss_mgr = VssManager()
    user_folders_mgr = UserFoldersManager(lib_mgr=lib_mgr)
    checker = BackupHealthChecker(lib_mgr, fh_mgr, storage_auditor, vss_mgr)
    rag_engine = get_file_history_rag()


    @router.get("/health", response_model=BackupHealthReport)
    async def get_backup_health_report() -> BackupHealthReport:
        """Сводная оценка готовности системы резервного копирования Windows (Health Score)."""
        report = checker.generate_report()
        _csv_logger.log_poll(
            poll_type="backup_health",
            metric_name="health_score",
            value=report.health_score,
            unit="score",
            status="OK" if report.health_score >= 70 else "ATTENTION",
            details={"service_running": report.service_running, "libraries_count": report.libraries_count},
            filename="windows_backup_events.csv",
        )
        return report


    @router.get("/libraries", response_model=List[WindowsLibrary])
    async def list_libraries() -> List[WindowsLibrary]:
        """Получить список всех библиотек Windows и включенных в них папок."""
        return lib_mgr.get_all_libraries()

    @router.post("/libraries", response_model=WindowsLibrary, status_code=status.HTTP_201_CREATED)
    async def create_library(payload: CreateLibraryRequest) -> WindowsLibrary:
        """Создать новую системную библиотеку Windows (.library-ms)."""
        try:
            lib = lib_mgr.create_library(
                name=payload.name,
                folders=payload.folders,
                is_pinned=payload.is_pinned,
            )
            _csv_logger.log_event(
                event_type="create_library",
                status="SUCCESS",
                details={"name": payload.name, "folders": payload.folders},
                filename="windows_backup_events.csv",
            )
            return lib
        except Exception as ex:
            logger.error(f"Ошибка создания библиотеки {payload.name}: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post("/libraries/{library_name}/folders", response_model=WindowsLibrary)
    async def add_folder_to_library(library_name: str, payload: AddFolderToLibraryRequest) -> WindowsLibrary:
        """Добавить физическую папку в существующую библиотеку Windows."""
        res = lib_mgr.add_folder_to_library(
            library_name=library_name,
            folder_path=payload.folder_path,
            is_default_save=payload.is_default_save,
        )
        if not res:
            raise HTTPException(status_code=404, detail=f"Библиотека '{library_name}' не найдена.")
        _csv_logger.log_event(
            event_type="add_folder_to_library",
            status="SUCCESS",
            details={"library": library_name, "folder": payload.folder_path},
            filename="windows_backup_events.csv",
        )
        return res

    @router.get("/file-history/status", response_model=FileHistoryStatus)
    async def get_file_history_status() -> FileHistoryStatus:
        """Статус службы fhsvc и текущая конфигурация Истории файлов Windows."""
        return fh_mgr.get_status()

    @router.post("/file-history/trigger")
    async def trigger_file_history_backup() -> Dict[str, Any]:
        """Принудительно запустить цикл резервного копирования Истории файлов (fhexec -f)."""
        success, message = fh_mgr.trigger_backup_now()
        _csv_logger.log_event(
            event_type="file_history_trigger_backup",
            status="SUCCESS" if success else "FAILED",
            details=message,
            filename="windows_backup_events.csv",
        )
        if not success:
            raise HTTPException(status_code=500, detail=message)
        return {"success": True, "message": message}


    @router.get("/storage/audit", response_model=StorageBackupAudit)
    async def audit_backup_storage(target_path: Optional[str] = None) -> StorageBackupAudit:
        """Аудит файлов, версий и дискового пространства в целевом хранилище."""
        return storage_auditor.audit_storage(target_path)

    @router.get("/vss/snapshots", response_model=List[VssSnapshot])
    async def list_vss_snapshots() -> List[VssSnapshot]:
        """Список теневых копий томов Windows VSS (Volume Shadow Copies)."""
        return vss_mgr.list_snapshots()

    # --- File History RAG Endpoints ---

    @router.post("/file-history/rag/sync")
    async def sync_file_history_rag(payload: Optional[FileHistoryRAGSyncRequest] = None) -> Dict[str, Any]:
        """Запуск инкрементальной синхронизации и индексации архивов File History в RAG."""
        target_path = payload.target_path if payload else None
        chunk_size = payload.chunk_size if payload else 500
        chunk_overlap = payload.chunk_overlap if payload else 50
        force_rebuild = payload.force_rebuild if payload else False

        result = rag_engine.sync(
            target_path=target_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            force_rebuild=force_rebuild,
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Ошибка синхронизации"))
        return result

    @router.post("/file-history/rag/search", response_model=List[FileHistoryRAGSearchResult])
    async def search_file_history_rag(payload: FileHistoryRAGSearchRequest) -> List[FileHistoryRAGSearchResult]:
        """Семантический поиск по архивным версиям файлов Windows с фильтрами."""
        return rag_engine.search(
            query=payload.query,
            top_k=payload.top_k,
            min_score=payload.min_score,
            date_from=payload.date_from,
            date_to=payload.date_to,
            path_pattern=payload.path_pattern,
            drive_filter=payload.drive_filter,
        )

    @router.get("/file-history/rag/status", response_model=FileHistoryRAGStatus)
    async def get_file_history_rag_status() -> FileHistoryRAGStatus:
        """Текущее состояние и метрики RAG индекса Истории файлов."""
        return rag_engine.get_status()

    @router.get("/file-history/rag/versions", response_model=FileHistoryVersionSummary)
    async def get_file_versions_history(query: str) -> FileHistoryVersionSummary:
        """Получить список всех снимков конкретного документа в хранилище истории."""
        return rag_engine.get_file_versions(query)

    # --- User Folders & Storage Relocation Endpoints ---

    @router.get("/user-folders/overview", response_model=UserFoldersOverviewResponse)
    async def get_user_folders_overview() -> UserFoldersOverviewResponse:
        """Получить размеры пользовательских папок (Документы, Загрузки и т.д.) и список доступных дисков."""
        return user_folders_mgr.get_overview()

    @router.post("/user-folders/relocate", response_model=RelocateFolderResponse)
    async def relocate_user_folder(payload: RelocateFolderRequest) -> RelocateFolderResponse:
        """Перенести пользовательскую папку на другой физический диск с обновлением реестра и библиотек."""
        result = user_folders_mgr.relocate_folder(
            folder_id=payload.folder_id,
            target_drive_letter=payload.target_drive_letter,
            delete_source_after=payload.delete_source_after,
        )
        _csv_logger.log_event(
            event_type="user_folder_relocate",
            status="SUCCESS" if result.success else "FAILED",
            details={
                "folder_id": payload.folder_id,
                "target_drive": payload.target_drive_letter,
                "success": result.success,
                "message": result.message,
                "files_copied": result.files_copied,
            },
            filename="windows_backup_events.csv",
        )
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result

    return router