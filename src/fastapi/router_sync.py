"""
FastAPI router for Google Drive Sync management.

Provides REST API endpoints for managing data synchronization with Google Drive.
Includes status monitoring, manual sync operations, and scheduler control.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from pydantic import BaseModel, Field

# Try to import sync modules
try:
    from src.integrations.google_drive_sync import GoogleDriveSync
    from src.integrations.sync_scheduler import (
        SyncScheduler,
        get_scheduler,
        ManualSyncHandler,
    )
except ImportError:
    GoogleDriveSync = None
    SyncScheduler = None
    get_scheduler = None
    ManualSyncHandler = None


# Pydantic models
class SyncStatus(BaseModel):
    """Sync status information."""

    is_running: bool = Field(description="Whether scheduler is running")
    last_sync_time: Optional[str] = Field(None, description="Last sync timestamp")
    next_sync_time: Optional[str] = Field(None, description="Next scheduled sync")
    sync_interval_hours: int = Field(6, description="Sync interval in hours")
    root_folder_id: Optional[str] = Field(None, description="Google Drive folder ID")
    total_files_synced: int = Field(0, description="Total files synchronized")
    last_sync_result: Optional[Dict] = Field(None, description="Last sync result")
    sync_enabled: bool = Field(True, description="Whether sync is enabled")


class SyncStartRequest(BaseModel):
    """Request to start sync scheduler."""

    sync_interval_hours: int = Field(6, ge=1, le=24, description="Sync interval")
    include_data: bool = Field(True, description="Include data folder")
    include_logs: bool = Field(True, description="Include logs folder")
    include_secrets: bool = Field(True, description="Include secrets folder")
    include_configs: bool = Field(True, description="Include configs folder")


class ManualSyncRequest(BaseModel):
    """Request to manually sync."""

    sync_type: str = Field("all", description="Type: all, data, logs, secrets, configs")
    target_path: Optional[str] = Field(None, description="Specific path to sync")


class SyncStats(BaseModel):
    """Synchronization statistics."""

    total_size_mb: float = Field(0, description="Total size in MB")
    files_count: int = Field(0, description="Total files count")
    folders_count: int = Field(0, description="Total folders count")
    last_24h_syncs: int = Field(0, description="Syncs in last 24 hours")
    sync_errors: int = Field(0, description="Number of sync errors")


class DriveInfo(BaseModel):
    """Google Drive folder information."""

    folder_id: str = Field(description="Google Drive folder ID")
    folder_name: str = Field(description="Folder name")
    folder_url: str = Field(description="Google Drive URL")
    is_accessible: bool = Field(True, description="Whether folder is accessible")


# Create router
router = APIRouter(prefix="/api/admin/sync", tags=["admin", "sync"])


def _get_sync_instance() -> Optional[GoogleDriveSync]:
    """Get GoogleDriveSync instance."""
    if GoogleDriveSync is None:
        return None
    try:
        return GoogleDriveSync()
    except Exception:
        return None


def _get_scheduler_instance() -> Optional[SyncScheduler]:
    """Get SyncScheduler instance."""
    if get_scheduler is None:
        return None
    try:
        return get_scheduler()
    except Exception:
        return None


def _load_sync_config() -> Dict:
    """Load sync configuration."""
    config_file = Path("sync_config.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _load_sync_state() -> Dict:
    """Load sync state."""
    state_file = Path("sync_state.json")
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# API Endpoints


@router.get("/status", response_model=SyncStatus, summary="Get sync status")
async def get_sync_status(request: Request) -> SyncStatus:
    """Get current synchronization status."""
    try:
        scheduler = _get_scheduler_instance()
        sync = _get_sync_instance()
        config = _load_sync_config()
        state = _load_sync_state()

        status = SyncStatus(
            is_running=scheduler.is_running if scheduler else False,
            last_sync_time=state.get("timestamp"),
            sync_interval_hours=config.get("sync_interval_hours", 6),
            root_folder_id=sync.root_folder_id if sync else None,
            sync_enabled=config.get("sync_enabled", True),
        )

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SyncStats, summary="Get sync statistics")
async def get_sync_stats(request: Request) -> SyncStats:
    """Get synchronization statistics."""
    try:
        stats = SyncStats()

        # Calculate directory sizes
        try:
            for folder in ["data", "logs", "src/secrets"]:
                if os.path.isdir(folder):
                    total_size = 0
                    files = 0
                    for root, dirs, fs in os.walk(folder):
                        files += len(fs)
                        for f in fs:
                            fpath = os.path.join(root, f)
                            try:
                                total_size += os.path.getsize(fpath)
                            except Exception:
                                pass

                    stats.total_size_mb += total_size / (1024 * 1024)
                    stats.files_count += files
                    stats.folders_count += len(dirs)
        except Exception:
            pass

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive-info", response_model=DriveInfo, summary="Get Google Drive info")
async def get_drive_info(request: Request) -> DriveInfo:
    """Get Google Drive folder information."""
    try:
        sync = _get_sync_instance()
        if not sync:
            raise HTTPException(status_code=503, detail="Google Drive not configured")

        folder_id = sync.ensure_sync_folder()
        if not folder_id:
            raise HTTPException(status_code=500, detail="Could not access Google Drive")

        return DriveInfo(
            folder_id=folder_id,
            folder_name="AI-Breadboard-Sync",
            folder_url=f"https://drive.google.com/drive/folders/{folder_id}",
            is_accessible=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", summary="Start sync scheduler")
async def start_sync(
    request: Request, sync_request: SyncStartRequest, background_tasks: BackgroundTasks
):
    """Start automatic synchronization scheduler."""
    try:
        scheduler = _get_scheduler_instance()
        if not scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")

        if scheduler.is_running:
            return {
                "status": "already_running",
                "message": "Scheduler is already running",
            }

        scheduler.sync_interval_hours = sync_request.sync_interval_hours
        scheduler.start()

        return {
            "status": "started",
            "message": f"Scheduler started with {sync_request.sync_interval_hours}h interval",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", summary="Stop sync scheduler")
async def stop_sync(request: Request):
    """Stop automatic synchronization scheduler."""
    try:
        scheduler = _get_scheduler_instance()
        if not scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")

        if not scheduler.is_running:
            return {"status": "not_running", "message": "Scheduler is not running"}

        scheduler.stop()

        return {"status": "stopped", "message": "Scheduler stopped"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-now", summary="Perform immediate sync")
async def sync_now(
    request: Request, sync_request: ManualSyncRequest, background_tasks: BackgroundTasks
):
    """Perform immediate synchronization."""
    try:
        sync = _get_sync_instance()
        if not sync:
            raise HTTPException(status_code=503, detail="Sync not configured")

        sync.ensure_sync_folder()

        def perform_sync():
            if sync_request.sync_type == "all":
                sync.sync_all_data()
            elif sync_request.sync_type == "data" and os.path.isdir("data"):
                sync.sync_directory("data", sync.root_folder_id)
            elif sync_request.sync_type == "logs" and os.path.isdir("logs"):
                sync.sync_directory("logs", sync.root_folder_id)
            elif sync_request.sync_type == "secrets" and os.path.isdir("src/secrets"):
                sync.sync_directory("src/secrets", sync.root_folder_id)

        background_tasks.add_task(perform_sync)

        return {
            "status": "syncing",
            "message": f"Synchronization of {sync_request.sync_type} started in background",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection", summary="Test Google Drive connection")
async def test_connection(request: Request):
    """Test connection to Google Drive."""
    try:
        sync = _get_sync_instance()
        if not sync:
            return {
                "status": "not_configured",
                "message": "Google Drive sync not configured",
                "connected": False,
            }

        if sync.drive_service is None:
            return {
                "status": "error",
                "message": "Google Drive service not initialized",
                "connected": False,
            }

        sync.ensure_sync_folder()

        return {
            "status": "connected",
            "message": "Successfully connected to Google Drive",
            "connected": True,
            "folder_id": sync.root_folder_id,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "connected": False,
        }


@router.get("/config", summary="Get sync configuration")
async def get_config(request: Request):
    """Get current sync configuration."""
    try:
        config = _load_sync_config()
        return config if config else {}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", summary="Update sync configuration")
async def update_config(request: Request, config: Dict):
    """Update sync configuration."""
    try:
        config_file = Path("sync_config.json")

        # Load current config
        current_config = _load_sync_config()

        # Update with new values
        current_config.update(config)

        # Save updated config
        with open(config_file, "w") as f:
            json.dump(current_config, f, indent=2)

        return {"status": "updated", "message": "Configuration updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def init_router() -> APIRouter:
    """Initialize sync router."""
    return router
