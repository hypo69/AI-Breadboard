# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager - Versions Router
# =============================================================================
# Description:
#   REST API версионирования файлов: /api/v1/versions/{save,list,restore}.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.backup_manager.versions_router import init_router
#
#     router = init_router()
#
# File: versions_router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 21:50:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер версионирования файлов (VSS + SQLite)."""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from apps.windows.sdk.modules.backup_manager.core.models import FileVersionEntry, RestoreVersionRequest, SaveVersionRequest
from apps.windows.sdk.modules.backup_manager.core.version_provider import WindowsVersionProvider


def init_router(provider: Optional[WindowsVersionProvider] = None) -> APIRouter:
    """Создает роутер; провайдер можно внедрить явно (тесты)."""
    router = APIRouter(prefix='/api/v1/versions', tags=['Windows File Versions'])
    state: Dict[str, Optional[WindowsVersionProvider]] = {'p': provider}

    def get_provider() -> WindowsVersionProvider:
        if state['p'] is None:
            state['p'] = WindowsVersionProvider()
        return state['p']

    @router.post('/save')
    async def save_version(req: SaveVersionRequest) -> Dict[str, Any]:
        """Создает мгновенную версию файла."""
        try:
            rec = await asyncio.to_thread(get_provider().save_version, req.file_path, req.description)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail='Файл не найден')
        return {
            'status': 'success',
            'version_id': rec.version_id,
            'storage_layer': rec.storage_layer,
            'snapshot_id': rec.snapshot_id,
            'created_at': rec.created_at,
            'sha256': rec.sha256_hash,
        }

    @router.get('/list', response_model=List[FileVersionEntry])
    async def list_versions(file_path: str) -> List[FileVersionEntry]:
        """Список версий файла."""
        return await asyncio.to_thread(get_provider().list_versions, file_path)

    @router.post('/restore')
    async def restore_version(req: RestoreVersionRequest) -> Dict[str, Any]:
        """Восстанавливает файл из версии."""
        try:
            rec = await asyncio.to_thread(get_provider().restore_version, req.version_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {'status': 'success', 'version_id': rec.version_id, 'file_path': rec.file_path}

    return router


__all__ = ['init_router']
