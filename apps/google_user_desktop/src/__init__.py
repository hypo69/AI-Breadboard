# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop Src -   Init  
# =============================================================================
# Description:
#   Исходный код приложения Google User Desktop.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.google_user_desktop.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Исходный код приложения Google User Desktop."""

from .google_drive_sync import GoogleDriveSync, sync_to_google_drive
from .state import (
    CalendarEventSummary,
    DocumentItemSummary,
    DriveFileSummary,
    GoogleAccountSummary,
    GoogleUserDesktopState,
    MailItemSummary,
)
from .sync_scheduler import (
    ManualSyncHandler,
    SyncScheduler,
    get_scheduler,
    manual_sync,
    start_sync_scheduler,
    stop_sync_scheduler,
)

__all__ = [
    'GoogleUserDesktopState',
    'GoogleAccountSummary',
    'MailItemSummary',
    'CalendarEventSummary',
    'DocumentItemSummary',
    'DriveFileSummary',
    'GoogleDriveSync',
    'sync_to_google_drive',
    'SyncScheduler',
    'ManualSyncHandler',
    'get_scheduler',
    'start_sync_scheduler',
    'stop_sync_scheduler',
    'manual_sync',
]
