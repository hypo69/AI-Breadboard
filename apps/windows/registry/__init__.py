# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer Application Init
# =============================================================================
# Description:
#   Экспорт основных компонентов приложения Windows Registry Viewer.
#
# Examples:
#   >>> from apps.windows.registry import RegistryViewer, init_router
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.registry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение Windows Registry Viewer."""

from apps.windows.registry.backup import RegistryBackupManager
from apps.windows.registry.models import (
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
from apps.windows.registry.viewer import RegistryViewer, COMMON_BOOKMARKS
from apps.windows.registry.tui import RegistryViewerTUI
from apps.windows.registry.router import init_router

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

