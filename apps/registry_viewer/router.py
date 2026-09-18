# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer FastAPI Router
# =============================================================================
# Description:
#   FastAPI роутер эндпоинтов для приложения Windows Registry Viewer.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для приложения Windows Registry Viewer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from apps.registry_viewer.models import (
    BookmarkItem,
    CreateKeyRequestDTO,
    DeleteKeyRequestDTO,
    DeleteValueRequestDTO,
    EditOperationResultDTO,
    RegistryKeyDetailsDTO,
    RestoreBackupResponseDTO,
    SearchResponseDTO,
    SetValueRequestDTO,
)
from apps.registry_viewer.viewer import RegistryViewer



def init_router(viewer: Optional[RegistryViewer] = None) -> APIRouter:
    """Инициализировать и вернуть FastAPI роутер Registry Viewer."""
    registry_engine = viewer or RegistryViewer()
    router = APIRouter(prefix="/api/registry", tags=["registry-viewer"])

    @router.get("/bookmarks")
    async def get_bookmarks() -> Dict[str, Any]:
        """Получить список быстрых системных закладок реестра."""
        bookmarks = registry_engine.get_bookmarks()
        return {
            "status": "ok",
            "bookmarks": [bm.model_dump() for bm in bookmarks],
        }

    @router.get("/key", response_model=RegistryKeyDetailsDTO)
    async def get_key_details(
        hive: str = Query(default="HKEY_LOCAL_MACHINE", description="Корневая ветка реестра (HKLM, HKCU и др.)"),
        path: str = Query(default="", description="Относительный путь к разделу реестра"),
    ) -> RegistryKeyDetailsDTO:
        """Получить список подразделов и параметров указанного ключа реестра."""
        try:
            return registry_engine.read_key(hive=hive, path=path)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/search", response_model=SearchResponseDTO)
    async def search_registry(
        hive: str = Query(default="HKEY_LOCAL_MACHINE", description="Корневая ветка для поиска"),
        path: str = Query(default="SOFTWARE", description="Базовый путь поиска"),
        query: str = Query(..., min_length=2, description="Поисковая строка"),
        max_results: int = Query(default=50, ge=1, le=200, description="Максимум результатов"),
    ) -> SearchResponseDTO:
        """Поиск ключей, параметров и значений в системном реестре."""
        try:
            return registry_engine.search(
                query=query,
                hive=hive,
                path=path,
                max_results=max_results,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/export")
    async def export_key(
        hive: str = Query(default="HKEY_LOCAL_MACHINE", description="Корневая ветка"),
        path: str = Query(default="", description="Путь ключа"),
        format: str = Query(default="json", enum=["json", "csv"], description="Формат экспорта"),
    ) -> Response:
        """Экспорт параметров ключа реестра в JSON или CSV."""
        try:
            details = registry_engine.read_key(hive=hive, path=path)
            if format == "csv":
                csv_data = registry_engine.export_key_to_csv(details)
                return Response(
                    content=csv_data,
                    media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="registry_export.csv"'},
                )
            json_data = registry_engine.export_key_to_json(details)
            return Response(
                content=json_data,
                media_type="application/json",
                headers={"Content-Disposition": 'attachment; filename="registry_export.json"'},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # Редактирование, создание бэкапов и восстановление
    # =========================================================================

    @router.post("/value", response_model=EditOperationResultDTO)
    async def set_value(req: SetValueRequestDTO) -> EditOperationResultDTO:
        """Создать или изменить параметр реестра с созданием снимка резервной копии."""
        try:
            return registry_engine.set_value(req)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/value", response_model=EditOperationResultDTO)
    async def delete_value(req: DeleteValueRequestDTO) -> EditOperationResultDTO:
        """Удалить параметр реестра с созданием снимка резервной копии."""
        try:
            return registry_engine.delete_value(req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/key", response_model=EditOperationResultDTO)
    async def create_key(req: CreateKeyRequestDTO) -> EditOperationResultDTO:
        """Создать новый раздел в реестре."""
        try:
            return registry_engine.create_key(req)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/key", response_model=EditOperationResultDTO)
    async def delete_key(req: DeleteKeyRequestDTO) -> EditOperationResultDTO:
        """Удалить раздел реестра с созданием снимка резервной копии."""
        try:
            return registry_engine.delete_key(req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/backups")
    async def list_backups() -> Dict[str, Any]:
        """Получить список всех резервных копий реестра."""
        try:
            backups = registry_engine.list_backups()
            return {
                "status": "ok",
                "total": len(backups),
                "backups": [b.model_dump() for b in backups],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/restore", response_model=RestoreBackupResponseDTO)
    async def restore_backup(
        backup_id: str = Query(..., description="ID резервной копии для восстановления")
    ) -> RestoreBackupResponseDTO:
        """Восстановить раздел реестра из снимка бэкапа."""
        try:
            return registry_engine.restore_backup(backup_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
