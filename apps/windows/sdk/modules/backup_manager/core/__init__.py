# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager Core -   Init  
# =============================================================================
# Description:
#   Пакет ядра Windows Backup, Libraries & File History.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет ядра Windows Backup, Libraries & File History."""

from apps.windows.sdk.modules.backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows.sdk.modules.backup_manager.core.file_history_rag import WindowsFileHistoryRAG, get_file_history_rag
from apps.windows.sdk.modules.backup_manager.core.health_checker import BackupHealthChecker
from apps.windows.sdk.modules.backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows.sdk.modules.backup_manager.core.models import AddFolderToLibraryRequest, BackupHealthReport, CreateLibraryRequest, FileHistoryConfigInfo, FileHistoryRAGSearchRequest, FileHistoryRAGSearchResult, FileHistoryRAGStatus, FileHistoryRAGSyncRequest, FileHistoryStatus, FileHistoryVersionSummary, FileVersionRecord, LibraryFolder, ServiceState, StorageBackupAudit, TargetDriveInfo, UserFolderInfo, UserFoldersOverviewResponse, RelocateFolderRequest, RelocateFolderResponse, VssSnapshot, WindowsLibrary
from apps.windows.sdk.modules.backup_manager.core.storage_auditor import BackupStorageAuditor
from apps.windows.sdk.modules.backup_manager.core.user_folders_manager import UserFoldersManager
from apps.windows.sdk.modules.backup_manager.core.vss_manager import VssManager
__all__ = ['AddFolderToLibraryRequest', 'BackupHealthChecker', 'BackupHealthReport', 'BackupStorageAuditor', 'CreateLibraryRequest', 'FileHistoryConfigInfo', 'FileHistoryManager', 'FileHistoryRAGSearchRequest', 'FileHistoryRAGSearchResult', 'FileHistoryRAGStatus', 'FileHistoryRAGSyncRequest', 'FileHistoryStatus', 'FileHistoryVersionSummary', 'FileVersionRecord', 'LibraryFolder', 'RelocateFolderRequest', 'RelocateFolderResponse', 'ServiceState', 'StorageBackupAudit', 'TargetDriveInfo', 'UserFolderInfo', 'UserFoldersManager', 'UserFoldersOverviewResponse', 'VssManager', 'VssSnapshot', 'WindowsFileHistoryRAG', 'WindowsLibrariesManager', 'WindowsLibrary', 'get_file_history_rag']