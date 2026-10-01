# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Registry -   Init  
# =============================================================================
# Description:
#   Приложение Windows Registry Viewer.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.registry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Приложение Windows Registry Viewer."""

from apps.windows.registry.backup import RegistryBackupManager
from apps.windows.registry.models import BackupMetadataDTO, BookmarkItem, CreateKeyRequestDTO, DeleteKeyRequestDTO, DeleteValueRequestDTO, EditOperationResultDTO, RegistryKeyDetailsDTO, RegistryValueDTO, RestoreBackupResponseDTO, SearchMatchItem, SearchResponseDTO, SetValueRequestDTO
from apps.windows.registry.viewer import RegistryViewer, COMMON_BOOKMARKS
from apps.windows.registry.tui import RegistryViewerTUI
from apps.windows.registry.router import init_router
__all__ = ['RegistryViewer', 'RegistryBackupManager', 'RegistryViewerTUI', 'init_router', 'COMMON_BOOKMARKS', 'BookmarkItem', 'RegistryKeyDetailsDTO', 'RegistryValueDTO', 'SearchMatchItem', 'SearchResponseDTO', 'BackupMetadataDTO', 'RestoreBackupResponseDTO', 'SetValueRequestDTO', 'DeleteValueRequestDTO', 'CreateKeyRequestDTO', 'DeleteKeyRequestDTO', 'EditOperationResultDTO']