# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop -   Init  
# =============================================================================
# Description:
#   Приложение Google User Desktop — единый центр управления Google Workspace и синхронизации.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.google_user_desktop
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Приложение Google User Desktop — единый центр управления Google Workspace и синхронизации."""

from .routers.router import get_state, init_router, router
from .routers.sync_router import include_sync_routes
from .routers.sync_router import router as sync_router
from .src.google_drive_sync import GoogleDriveSync, sync_to_google_drive
from .src.state import (
    CalendarEventSummary,
    DocumentItemSummary,
    DriveFileSummary,
    GoogleAccountSummary,
    GoogleUserDesktopState,
    MailItemSummary,
)
from .src.sync_scheduler import (
    ManualSyncHandler,
    SyncScheduler,
    get_scheduler,
    manual_sync,
    start_sync_scheduler,
    stop_sync_scheduler,
)

__all__ = [
    'GoogleAccountSummary',
    'MailItemSummary',
    'CalendarEventSummary',
    'DocumentItemSummary',
    'DriveFileSummary',
    'GoogleUserDesktopState',
    'GoogleDriveSync',
    'sync_to_google_drive',
    'SyncScheduler',
    'ManualSyncHandler',
    'get_scheduler',
    'start_sync_scheduler',
    'stop_sync_scheduler',
    'manual_sync',
    'include_sync_routes',
    'sync_router',
    'get_state',
    'init_router',
    'router',
]
