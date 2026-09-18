# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer Application Init
# =============================================================================
# Description:
#   Экспорт основных компонентов приложения Windows Registry Viewer.
#
# Examples:
#   >>> from apps.registry_viewer import RegistryViewer, init_router
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение Windows Registry Viewer."""

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
from apps.registry_viewer.viewer import RegistryViewer, COMMON_BOOKMARKS
from apps.registry_viewer.tui import RegistryViewerTUI
from apps.registry_viewer.router import init_router

__all__ = [
    "RegistryViewer",
    "RegistryBackupManager",
    "RegistryViewerTUI",
    "init_router",
    "COMMON_BOOKMARKS",
    "BookmarkItem",
    "RegistryKeyDetailsDTO",
    "RegistryValueDTO",
    "SearchMatchItem",
    "SearchResponseDTO",
    "BackupMetadataDTO",
    "RestoreBackupResponseDTO",
    "SetValueRequestDTO",
    "DeleteValueRequestDTO",
    "CreateKeyRequestDTO",
    "DeleteKeyRequestDTO",
    "EditOperationResultDTO",
]

