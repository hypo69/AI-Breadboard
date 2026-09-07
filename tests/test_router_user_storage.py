# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing user storage endpoints
# =============================================================================
# Description:
#   Integration tests for /api/user/files endpoints: listing, uploading,
#   downloading, deleting user files, and inspecting personal storage statistics.
#
# File: test_router_user_storage.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import io
import pytest
from fastapi.testclient import TestClient
from main import app
from src.user_manager import user_manager

client = TestClient(app)

class TestUserStorageAPI:
    """Test user personal storage endpoints."""

    def test_list_empty_or_existing_files(self):
        """Test listing files for authenticated user."""
        response = client.get("/api/user/files?subfolder=files")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_upload_and_download_file(self):
        """Test uploading a file and then downloading it."""
        file_content = b"Content of user test document"
        file_name = "test_note.txt"

        # Upload
        response = client.post(
            "/api/user/files/upload",
            files={"file": (file_name, io.BytesIO(file_content), "text/plain")},
            data={"subfolder": "files"}
        )
        assert response.status_code == 200
        upload_data = response.json()
        assert upload_data["status"] == "ok"
        assert upload_data["filename"] == file_name

        # Verify listed
        list_resp = client.get("/api/user/files?subfolder=files")
        assert list_resp.status_code == 200
        file_names = [f["name"] for f in list_resp.json()["files"]]
        assert file_name in file_names

        # Download
        dl_resp = client.get(f"/api/user/files/download?filename={file_name}&subfolder=files")
        assert dl_resp.status_code == 200
        assert dl_resp.content == file_content

        # Delete
        del_resp = client.delete(f"/api/user/files?filename={file_name}&subfolder=files")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

        # Verify deleted
        dl_after_del = client.get(f"/api/user/files/download?filename={file_name}&subfolder=files")
        assert dl_after_del.status_code == 404

    def test_user_storage_stats(self):
        """Test retrieving current user storage statistics."""
        response = client.get("/api/user/files/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "stats" in data
        assert "total_size_bytes" in data["stats"]
        assert "total_files" in data["stats"]
