"""
Tests for Google Drive Sync modules.

Verify that all modules can be imported and have required functionality.
"""

import sys
import os
import pytest
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestImports:
    """Test that all modules can be imported."""

    def test_google_drive_sync_import(self):
        """Test GoogleDriveSync can be imported."""
        from src.integrations.google_drive_sync import GoogleDriveSync

        assert GoogleDriveSync is not None
        assert hasattr(GoogleDriveSync, "ensure_sync_folder")
        assert hasattr(GoogleDriveSync, "upload_file")
        assert hasattr(GoogleDriveSync, "sync_directory")
        assert hasattr(GoogleDriveSync, "sync_all_data")

    def test_sync_scheduler_import(self):
        """Test SyncScheduler can be imported."""
        from src.integrations.sync_scheduler import SyncScheduler, ManualSyncHandler

        assert SyncScheduler is not None
        assert ManualSyncHandler is not None
        assert hasattr(SyncScheduler, "start")
        assert hasattr(SyncScheduler, "stop")
        assert hasattr(SyncScheduler, "sync_now")

    def test_integration_exports(self):
        """Test that integrations package exports all components."""
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
        assert callable(start_sync_scheduler)
        assert callable(stop_sync_scheduler)
        assert callable(manual_sync)


class TestModuleFunctionality:
    """Test basic functionality of modules."""

    def test_google_drive_sync_instantiation(self):
        """Test GoogleDriveSync can be instantiated (without credentials)."""
        from src.integrations.google_drive_sync import GoogleDriveSync

        # Should not raise even without valid credentials file
        sync = GoogleDriveSync(service_account_file="nonexistent.json")
        assert sync is not None
        assert hasattr(sync, "drive_service")

    def test_sync_scheduler_instantiation(self):
        """Test SyncScheduler can be instantiated."""
        from src.integrations.sync_scheduler import SyncScheduler

        scheduler = SyncScheduler(sync_interval_hours=6)
        assert scheduler is not None
        assert scheduler.sync_interval_hours == 6
        assert scheduler.is_running is False

    def test_manual_sync_handler_instantiation(self):
        """Test ManualSyncHandler can be instantiated."""
        from src.integrations.sync_scheduler import ManualSyncHandler

        handler = ManualSyncHandler()
        assert handler is not None
        assert hasattr(handler, "drive_sync")

    def test_get_scheduler_returns_singleton(self):
        """Test get_scheduler returns instance."""
        from src.integrations import get_scheduler

        scheduler1 = get_scheduler()

        assert scheduler1 is not None
        assert hasattr(scheduler1, "sync_now")


class TestConfiguration:
    """Test configuration files exist."""

    def test_sync_config_exists(self):
        """Test sync_config.json exists."""
        config_file = project_root / "sync_config.json"
        assert config_file.exists()
        assert config_file.is_file()

    def test_sync_config_valid_json(self):
        """Test sync_config.json contains valid JSON."""
        import json

        config_file = project_root / "sync_config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert config is not None
        assert "service_account_file" in config
        assert "sync_interval_hours" in config
        assert isinstance(config["sync_interval_hours"], int)

    def test_requirements_file_exists(self):
        """Test sync_requirements.txt exists."""
        req_file = project_root / "req" / "sync_requirements.txt"
        assert req_file.exists()
        assert req_file.is_file()
        assert req_file.read_text()  # File is not empty


class TestScripts:
    """Test that scripts exist and are valid."""

    def test_setup_script_exists(self):
        """Test setup_google_drive_sync.py exists."""
        script_file = project_root / "scripts" / "setup_google_drive_sync.py"
        assert script_file.exists()
        assert script_file.is_file()

    def test_powershell_script_exists(self):
        """Test sync.ps1 exists."""
        script_file = project_root / "sync.ps1"
        assert script_file.exists()
        assert script_file.is_file()

    def test_batch_script_exists(self):
        """Test sync.cmd exists."""
        script_file = project_root / "sync.cmd"
        assert script_file.exists()
        assert script_file.is_file()


class TestDocumentation:
    """Test that documentation files exist."""

    def test_readme_sync_exists(self):
        """Test README_SYNC.md exists."""
        doc_file = project_root / "README_SYNC.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100

    def test_setup_guide_exists(self):
        """Test GOOGLE_DRIVE_SYNC_SETUP.md exists."""
        doc_file = project_root / "GOOGLE_DRIVE_SYNC_SETUP.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100

    def test_google_setup_instructions_exists(self):
        """Test GOOGLE_SETUP_INSTRUCTIONS.md exists."""
        doc_file = project_root / "GOOGLE_SETUP_INSTRUCTIONS.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100

    def test_full_guide_exists(self):
        """Test GOOGLE_DRIVE_SYNC_GUIDE.md exists."""
        doc_file = project_root / "docs" / "GOOGLE_DRIVE_SYNC_GUIDE.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100

    def test_implementation_summary_exists(self):
        """Test SYNC_IMPLEMENTATION_SUMMARY.md exists."""
        doc_file = project_root / "SYNC_IMPLEMENTATION_SUMMARY.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100

    def test_next_steps_exists(self):
        """Test NEXT_STEPS.md exists."""
        doc_file = project_root / "NEXT_STEPS.md"
        assert doc_file.exists()
        assert doc_file.is_file()
        assert len(doc_file.read_text()) > 100


class TestHooks:
    """Test that hooks are configured."""

    def test_auto_sync_hook_exists(self):
        """Test auto-sync hook is configured."""
        hook_file = (
            project_root
            / ".kiro"
            / "hooks"
            / "auto-sync-on-config-save.json"
        )
        assert hook_file.exists()
        assert hook_file.is_file()

    def test_hook_configuration_valid(self):
        """Test hook configuration is valid JSON."""
        import json

        hook_file = (
            project_root
            / ".kiro"
            / "hooks"
            / "auto-sync-on-config-save.json"
        )
        with open(hook_file) as f:
            hook_config = json.load(f)

        assert hook_config is not None
        assert "hooks" in hook_config
        assert len(hook_config["hooks"]) > 0
        assert hook_config["hooks"][0]["trigger"] == "PostFileSave"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
