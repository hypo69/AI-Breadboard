# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Sync Modules
# =============================================================================
# Description:
#   Tests for Google Drive Sync modules integrated into apps.google_user_desktop.
#
# Usage Examples:
#   CLI:
#     python -m tests.test_sync_modules
#   Python API:
#     from tests.test_sync_modules import TestImports
#
#     service = TestImports()
#
# File: test_sync_modules.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Tests for Google Drive Sync modules integrated into apps.google_user_desktop.

Verify that all modules can be imported and have required functionality."""

import sys
import os
import pytest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestImports:
    """Test that all modules can be imported."""

    def test_google_drive_sync_import(self):
        """Test GoogleDriveSync can be imported."""
        from apps.google_user_desktop.src.google_drive_sync import GoogleDriveSync
        assert GoogleDriveSync is not None
        assert hasattr(GoogleDriveSync, 'ensure_sync_folder')
        assert hasattr(GoogleDriveSync, 'upload_file')
        assert hasattr(GoogleDriveSync, 'sync_directory')
        assert hasattr(GoogleDriveSync, 'sync_all_data')

    def test_sync_scheduler_import(self):
        """Test SyncScheduler can be imported."""
        from apps.google_user_desktop.src.sync_scheduler import SyncScheduler, ManualSyncHandler
        assert SyncScheduler is not None
        assert ManualSyncHandler is not None
        assert hasattr(SyncScheduler, 'start')
        assert hasattr(SyncScheduler, 'stop')
        assert hasattr(SyncScheduler, 'sync_now')

    def test_integration_exports(self):
        """Test that google_user_desktop package exports all components."""
        from apps.google_user_desktop import (
            GoogleDriveSync,
            SyncScheduler,
            ManualSyncHandler,
            get_scheduler,
            start_sync_scheduler,
            stop_sync_scheduler,
            manual_sync,
        )
        assert GoogleDriveSync is not None
        assert SyncScheduler is not None
        assert ManualSyncHandler is not None
        assert callable(get_scheduler)
        assert callable(start_sync_scheduler)
        assert callable(stop_sync_scheduler)
        assert callable(manual_sync)

    def test_legacy_integrations_export(self):
        """Test that src.integrations legacy package exports all components."""
        from src.integrations import (
            GoogleDriveSync,
            SyncScheduler,
            ManualSyncHandler,
            get_scheduler,
            start_sync_scheduler,
            stop_sync_scheduler,
            manual_sync,
        )
        assert GoogleDriveSync is not None
        assert SyncScheduler is not None
        assert ManualSyncHandler is not None
        assert callable(get_scheduler)

class TestModuleFunctionality:
    """Test basic functionality of modules."""

    def test_google_drive_sync_instantiation(self):
        """Test GoogleDriveSync can be instantiated (without credentials)."""
        from apps.google_user_desktop.src.google_drive_sync import GoogleDriveSync
        sync = GoogleDriveSync(service_account_file='nonexistent.json')
        assert sync is not None
        assert hasattr(sync, 'drive_service')

    def test_sync_scheduler_instantiation(self):
        """Test SyncScheduler can be instantiated."""
        from apps.google_user_desktop.src.sync_scheduler import SyncScheduler, ManualSyncHandler
        scheduler = SyncScheduler(sync_interval_hours=6)
        assert scheduler is not None
        assert scheduler.sync_interval_hours == 6
        assert scheduler.is_running is False

    def test_manual_sync_handler_instantiation(self):
        """Test ManualSyncHandler can be instantiated."""
        from apps.google_user_desktop.src.sync_scheduler import ManualSyncHandler
        handler = ManualSyncHandler()
        assert handler is not None
        assert hasattr(handler, 'drive_sync')

    def test_get_scheduler_returns_singleton(self):
        """Test get_scheduler returns instance."""
        from apps.google_user_desktop import get_scheduler
        scheduler1 = get_scheduler()
        assert scheduler1 is not None
        assert hasattr(scheduler1, 'sync_now')

class TestScripts:
    """Test that scripts exist and are valid."""

    def test_setup_script_exists(self):
        """Test setup_google_drive_sync.py exists."""
        script_file = project_root / 'scripts' / 'setup_google_drive_sync.py'
        assert script_file.exists()
        assert script_file.is_file()

class TestDocumentation:
    """Test that documentation files exist."""

    def test_readme_sync_exists(self):
        """Test README_SYNC.md exists."""
        doc_file = project_root / 'docs' / 'ru' / 'manual' / 'README_SYNC.md'
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text(encoding='utf-8')) > 100

    def test_setup_guide_exists(self):
        """Test GOOGLE_DRIVE_SYNC_SETUP.md exists."""
        doc_file = project_root / 'docs' / 'ru' / 'guides' / 'GOOGLE_DRIVE_SYNC_SETUP.md'
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text(encoding='utf-8')) > 100

    def test_google_setup_instructions_exists(self):
        """Test GOOGLE_SETUP_INSTRUCTIONS.md exists."""
        doc_file = project_root / 'docs' / 'ru' / 'guides' / 'GOOGLE_SETUP_INSTRUCTIONS.md'
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text(encoding='utf-8')) > 100

    def test_full_guide_exists(self):
        """Test GOOGLE_DRIVE_SYNC_GUIDE.md exists."""
        doc_file = project_root / 'docs' / 'GOOGLE_DRIVE_SYNC_GUIDE.md'
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text(encoding='utf-8')) > 100

if __name__ == '__main__':
    pytest.main([__file__, '-v'])