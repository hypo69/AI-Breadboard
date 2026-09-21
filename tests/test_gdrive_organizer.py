# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Google Drive Organizer skill
# =============================================================================
# Description:
#   Validates Google Drive scanning hierarchy, audit rule engine,
#   reorganization proposal generation, and execution logic.
#
# File: test_gdrive_organizer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Ensure skill scripts directory is on sys.path
_SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "gdrive-organizer" / "scripts"
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from gdrive_scanner import GDriveScanner, FOLDER_MIME_TYPE
from audit_engine import GDriveAuditEngine
from proposal_generator import GDriveProposalGenerator
from reorganize_executor import GDriveReorganizeExecutor


@pytest.fixture
def sample_drive_items():
    """Create a sample fixture of drive items with various disorganization patterns."""
    return [
        # Folders
        {
            "id": "f_root_finance",
            "name": "Finance",
            "mimeType": FOLDER_MIME_TYPE,
            "parents": ["root"],
        },
        {
            "id": "f_empty",
            "name": "New folder (1)",
            "mimeType": FOLDER_MIME_TYPE,
            "parents": ["root"],
        },
        # Loose root files
        {
            "id": "file_invoice_1",
            "name": "Invoice_ClientA_2026.pdf",
            "mimeType": "application/pdf",
            "size": "10240",
            "md5Checksum": "abc123md5",
            "parents": ["root"],
            "modifiedTime": "2026-03-01T12:00:00Z",
        },
        {
            "id": "file_random_pic",
            "name": "screenshot_error.png",
            "mimeType": "image/png",
            "size": "20480",
            "md5Checksum": "img123md5",
            "parents": ["root"],
            "modifiedTime": "2026-03-02T12:00:00Z",
        },
        # Duplicate files
        {
            "id": "file_invoice_dup",
            "name": "Copy of Invoice_ClientA_2026.pdf",
            "mimeType": "application/pdf",
            "size": "10240",
            "md5Checksum": "abc123md5",
            "parents": ["f_root_finance"],
            "modifiedTime": "2026-03-05T12:00:00Z",
        },
        # Version clutter
        {
            "id": "file_contract_draft",
            "name": "NDA_Partner_v2_final.docx",
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "size": "5000",
            "parents": ["f_root_finance"],
            "modifiedTime": "2026-03-04T12:00:00Z",
        },
    ]


class TestGDriveScanner:
    """Test GDriveScanner hierarchy and traversal logic."""

    def test_build_hierarchy(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)

        assert "items_by_id" in hierarchy
        assert "folders" in hierarchy
        assert "files" in hierarchy

        assert len(hierarchy["folders"]) == 2
        assert len(hierarchy["files"]) == 4

        # Check path calculation
        items_by_id = hierarchy["items_by_id"]
        assert items_by_id["f_root_finance"]["full_path"] == "/[Root]/Finance"
        assert items_by_id["file_invoice_dup"]["full_path"] == "/[Root]/Finance/Copy of Invoice_ClientA_2026.pdf"


class TestGDriveAuditEngine:
    """Test GDriveAuditEngine issue detection and scoring."""

    def test_detect_root_files(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)

        root_files = engine.detect_root_files()
        assert len(root_files) == 2
        names = {f["name"] for f in root_files}
        assert "Invoice_ClientA_2026.pdf" in names
        assert "screenshot_error.png" in names

    def test_detect_duplicates(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)

        duplicates = engine.detect_duplicates()
        assert len(duplicates) == 1
        assert duplicates[0]["type"] == "exact_md5"
        assert duplicates[0]["count"] == 2

    def test_detect_version_clutter(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)

        clutter = engine.detect_version_clutter()
        assert len(clutter) >= 2
        names = {c["file"]["name"] for c in clutter}
        assert "Copy of Invoice_ClientA_2026.pdf" in names
        assert "NDA_Partner_v2_final.docx" in names

    def test_detect_empty_and_generic_folders(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)

        empty = engine.detect_empty_folders()
        assert len(empty) == 1
        assert empty[0]["id"] == "f_empty"

        generic = engine.detect_generic_folders()
        assert len(generic) == 1
        assert generic[0]["id"] == "f_empty"

    def test_full_audit_health_score(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)

        audit = engine.run_full_audit()
        assert "health_score" in audit
        assert 0.0 <= audit["health_score"] <= 100.0
        assert audit["total_files"] == 4
        assert audit["total_folders"] == 2


class TestGDriveProposalGenerator:
    """Test restructuring proposal and report generation."""

    def test_generate_plan_and_report(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)
        audit = engine.run_full_audit()

        generator = GDriveProposalGenerator(audit, hierarchy)
        plan = generator.generate_plan()

        assert "actions" in plan
        assert plan["total_actions"] > 0

        # Verify duplicate invoice copy is suggested for archival
        dup_actions = [a for a in plan["actions"] if a.get("file_id") == "file_invoice_1"]
        assert len(dup_actions) == 1
        assert dup_actions[0]["action"] == "ARCHIVE_DUPLICATE"
        assert dup_actions[0]["target_folder"] == "/Archives/Duplicates"

        # Verify screenshot is categorized and moved to Media/Images
        pic_moves = [a for a in plan["actions"] if a.get("file_id") == "file_random_pic"]
        assert len(pic_moves) == 1
        assert pic_moves[0]["action"] == "MOVE"
        assert pic_moves[0]["target_folder"] == "/Media/Images"

        # Verify markdown report generation
        report_md = generator.generate_markdown_report(plan)
        assert "# 📊 Google Drive Organization & Cleanup Report" in report_md
        assert "Organization Health Score" in report_md
        assert "Invoice_ClientA_2026.pdf" in report_md


class TestGDriveReorganizeExecutor:
    """Test plan executor and dry-run simulation."""

    def test_dry_run_execution(self, sample_drive_items):
        scanner = GDriveScanner(service=None)
        hierarchy = scanner.build_hierarchy(sample_drive_items)
        engine = GDriveAuditEngine(hierarchy)
        audit = engine.run_full_audit()
        generator = GDriveProposalGenerator(audit, hierarchy)
        plan = generator.generate_plan()

        executor = GDriveReorganizeExecutor(service=None)
        result = executor.execute_plan(plan, dry_run=True)

        assert result["dry_run"] is True
        assert result["successful"] > 0
        assert result["failed"] == 0
