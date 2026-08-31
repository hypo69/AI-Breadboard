# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ответ при проверке версии.
# =============================================================================
# Description:
#   API-эндпоинты для проверки обновлений, выполнения обновлений приложения,
#
# File: router_version.py
# Project: ai-breadboard
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from header import __root__
from core.logger import logger
from core.version_manager import get_version_manager, UpdateStatus

class VersionCheckResponse(BaseModel):
    """Ответ при проверке версии."""
    status: str
    current_version: Optional[str] = None
    remote_version: Optional[str] = None
    is_update_available: bool = False
    message: Optional[str] = None

class UpdateRequest(BaseModel):
    """Запрос на update."""
    branch: str = "main"
    auto_backup: bool = True

class UpdateResponse(BaseModel):
    """Ответ при выполнении обновления."""
    success: bool
    status: str
    message: Optional[str] = None
    version: Optional[str] = None
    backup_path: Optional[str] = None

class BackupInfo(BaseModel):
    """Info о резервной копии."""
    path: str
    timestamp: str
    version: Optional[str] = None
    files_count: int

def init_router() -> APIRouter:
    """Инициализирует FastAPI роутер для управления версиями."""
    router = APIRouter(prefix='/api/version', tags=['version'])
    
    @router.get('/check', response_model=VersionCheckResponse)
    async def check_version() -> VersionCheckResponse:
        """
        Checks наличие обновлений.
        
        Returns:
            VersionCheckResponse с информацией о версиях
        """
        try:
            vm = get_version_manager(__root__)
            check_result = vm.check_updates()
            
            return VersionCheckResponse(
                status=check_result.get('status'),
                current_version=check_result.get('current_version'),
                remote_version=check_result.get('remote_version'),
                is_update_available=check_result.get('is_update_available', False),
                message=check_result.get('message')
            )
        except Exception as ex:
            logger.error(f"Error checking version: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))
    
    @router.post('/update', response_model=UpdateResponse)
    async def perform_update(request: UpdateRequest, background_tasks: BackgroundTasks) -> UpdateResponse:
        """
        Performs update приложения с автоматическим резервным копированием.
        
        Args:
            request: UpdateRequest с параметрами обновления
            background_tasks: BackgroundTasks для асинхронных операций
            
        Returns:
            UpdateResponse с результатом обновления
        """
        try:
            vm = get_version_manager(__root__)
            
            # Выполняем update в фоне
            update_result = await vm.update_application(
                branch=request.branch,
                auto_backup=request.auto_backup
            )
            
            return UpdateResponse(
                success=update_result.get('success', False),
                status=update_result.get('status'),
                message=update_result.get('message'),
                version=update_result.get('version'),
                backup_path=update_result.get('backup_path')
            )
        except Exception as ex:
            logger.error(f"Error performing update: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))
    
    @router.get('/backups', response_model=List[BackupInfo])
    async def list_backups() -> List[BackupInfo]:
        """
        Receives list всех резервных копий.
        
        Returns:
            List информации о резервных копиях
        """
        try:
            vm = get_version_manager(__root__)
            
            if not vm.temp_backup_dir.exists():
                return []
            
            backups = []
            for backup_dir in sorted(vm.temp_backup_dir.iterdir(), reverse=True):
                if not backup_dir.is_dir():
                    continue
                
                # Пытаемся прочитать информацию о резервной копии
                info_file = backup_dir / ".backup_info.json"
                version = None
                if info_file.exists():
                    try:
                        import json
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            version = info.get('version')
                    except Exception:
                        pass
                
                # Считаем количество файлов
                files_count = sum(1 for _ in backup_dir.rglob('*') if _.is_file())
                
                backups.append(BackupInfo(
                    path=str(backup_dir),
                    timestamp=backup_dir.stat().st_mtime,
                    version=version,
                    files_count=files_count
                ))
            
            return backups
        except Exception as ex:
            logger.error(f"Error listing backups: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))
    
    @router.post('/restore/{backup_name}')
    async def restore_backup(backup_name: str) -> Dict[str, Any]:
        """
        Восстанавливает приложение из резервной копии.
        
        Args:
            backup_name: Имя директории с резервной копией
            
        Returns:
            Dictionary с результатом восстановления
        """
        try:
            vm = get_version_manager(__root__)
            backup_path = vm.temp_backup_dir / backup_name
            
            if not backup_path.exists():
                raise HTTPException(status_code=404, detail="Backup not found")
            
            if not backup_path.is_dir():
                raise HTTPException(status_code=400, detail="Invalid backup path")
            
            success = vm.restore_from_backup(backup_path)
            
            if success:
                logger.info(f"Successfully restored from backup: {backup_name}")
                return {
                    "success": True,
                    "message": f"Successfully restored from backup: {backup_name}"
                }
            else:
                logger.error(f"Failed to restore from backup: {backup_name}")
                raise HTTPException(status_code=500, detail="Restoration failed")
        except HTTPException:
            raise
        except Exception as ex:
            logger.error(f"Error restoring backup: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))
    
    @router.post('/cleanup-backups')
    async def cleanup_backups(keep_count: int = 5) -> Dict[str, Any]:
        """
        Deletes старые резервные копии, оставляя последние N.
        
        Args:
            keep_count: Количество резервных копий для сохранения
            
        Returns:
            Dictionary с результатом очистки
        """
        try:
            vm = get_version_manager(__root__)
            deleted_count = vm.cleanup_old_backups(keep_count=keep_count)
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return {
                "success": True,
                "message": f"Deleted {deleted_count} old backups",
                "deleted_count": deleted_count
            }
        except Exception as ex:
            logger.error(f"Error cleaning up backups: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))
    
    @router.get('/status')
    async def get_version_status() -> Dict[str, Any]:
        """
        Receives полный status версии и обновлений.
        
        Returns:
            Dictionary с полной информацией о версиях и статусе
        """
        try:
            vm = get_version_manager(__root__)
            check_result = vm.check_updates()
            
            # Подсчитываем количество резервных копий
            backup_count = 0
            if vm.temp_backup_dir.exists():
                backup_count = sum(1 for d in vm.temp_backup_dir.iterdir() if d.is_dir())
            
            return {
                "status": check_result.get('status'),
                "current_version": check_result.get('current_version'),
                "remote_version": check_result.get('remote_version'),
                "is_update_available": check_result.get('is_update_available', False),
                "current_commit": check_result.get('current_commit'),
                "remote_commit": check_result.get('remote_commit'),
                "timestamp": check_result.get('timestamp'),
                "backup_count": backup_count,
                "backup_dir": str(vm.temp_backup_dir),
                "update_log_dir": str(vm.update_log_dir)
            }
        except Exception as ex:
            logger.error(f"Error getting version status: {ex}")
            raise HTTPException(status_code=500, detail=str(ex))

__all__ = ['init_router']
