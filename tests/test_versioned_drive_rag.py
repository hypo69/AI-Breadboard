# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit & Integration tests for Directory and Drive Versioned RAG
# =============================================================================
# Description:
#   Tests incremental directory scanning, hash comparison, multi-version
#   preservation, and retrieval on simulated external and Google Drive folders.
#
# File: test_versioned_drive_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from src.rag.document_rag import DocumentRAGManager, compute_file_hash


@pytest.fixture
def temp_drive_environment():
    """Create isolated mock Drive folder and RAG index directories."""
    temp_dir = Path(tempfile.mkdtemp())
    drive_dir = temp_dir / "mock_drive"
    index_dir = temp_dir / "rag_index"
    docs_dir = temp_dir / "rag_docs"

    drive_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    yield drive_dir, docs_dir, index_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestVersionedDriveRAG:
    """Test suite for versioned directory scanning and temporal retrieval."""

    def test_scan_directory_incremental_lifecycle(self, temp_drive_environment):
        drive_dir, docs_dir, index_dir = temp_drive_environment
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        # 1. Populate mock drive with initial documents
        file1 = drive_dir / "finance_report.md"
        file1.write_text("# Q1 Finance Report\nTotal revenue was 1.2 million USD.", encoding="utf-8")

        sub_folder = drive_dir / "legal"
        sub_folder.mkdir(parents=True, exist_ok=True)
        file2 = sub_folder / "nda_template.txt"
        file2.write_text("Standard mutual non-disclosure agreement terms 2026.", encoding="utf-8")

        # Initial scan
        res1 = manager.scan_and_index_directory(drive_dir, provider="local_tfidf")
        assert res1["files_scanned"] == 2
        assert res1["files_added"] == 2
        assert res1["files_updated"] == 0
        assert res1["files_skipped"] == 0
        assert res1["new_chunks_added"] >= 2

        # Verify search works
        search_res = manager.search("revenue million", top_k=2)
        assert len(search_res) > 0
        assert search_res[0]["doc_name"] == "finance_report.md"
        assert search_res[0]["version"] == 1
        assert search_res[0]["is_latest"] is True

        # 2. Second scan without any changes (should skip)
        res2 = manager.scan_and_index_directory(drive_dir, provider="local_tfidf")
        assert res2["files_scanned"] == 2
        assert res2["files_added"] == 0
        assert res2["files_updated"] == 0
        assert res2["files_skipped"] == 2
        assert res2["new_chunks_added"] == 0

        # 3. Modify finance_report.md -> creates Version 2
        time.sleep(0.01)
        file1.write_text("# Q2 Finance Report\nTotal revenue increased to 2.5 million USD with strong profit.", encoding="utf-8")

        res3 = manager.scan_and_index_directory(drive_dir, provider="local_tfidf")
        assert res3["files_scanned"] == 2
        assert res3["files_added"] == 0
        assert res3["files_updated"] == 1
        assert res3["files_skipped"] == 1
        assert res3["new_chunks_added"] >= 1

        # Check history of finance_report.md
        history = manager.get_document_history("finance_report.md")
        assert history["found"] is True
        assert history["current_version"] == 2
        assert len(history["versions"]) == 2

        # Check search with version filters
        latest_results = manager.search("revenue", top_k=5, version_filter="latest")
        assert len(latest_results) > 0
        for r in latest_results:
            if r["doc_name"] == "finance_report.md":
                assert r["version"] == 2
                assert r["is_latest"] is True

        all_results = manager.search("revenue", top_k=10, version_filter="all")
        finance_versions = [r["version"] for r in all_results if r["doc_name"] == "finance_report.md"]
        assert 1 in finance_versions
        assert 2 in finance_versions

    def test_live_g_drive_detection_if_available(self, temp_drive_environment):
        """Test scanning real G:\\My Drive if present on system without crashing."""
        _, docs_dir, index_dir = temp_drive_environment
        g_drive_path = Path("G:/My Drive")
        if not g_drive_path.exists():
            pytest.skip("G:\\My Drive is not mounted on this environment.")

        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        # Scan only root or specific text files to keep test fast
        res = manager.scan_and_index_directory(
            g_drive_path,
            provider="local_tfidf",
            recursive=False,
            extensions=[".txt", ".md"],
        )
        assert "scanned_directory" in res
        assert res["files_scanned"] >= 0
