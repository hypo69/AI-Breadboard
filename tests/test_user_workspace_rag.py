# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing User Workspace Multi-RAG & Cleaner Ingestion Pipeline
# =============================================================================
# Description:
#   Comprehensive unit and API integration tests for user multi-RAG management,
#   file ingestion via rag_cleaner plugin, indexing, and semantic search.
#
# File: test_user_workspace_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import io
import json
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main import app
from src.user_manager import user_manager
from src.rag.user_workspace_rag import user_workspace_rag_manager

client = TestClient(app)


class TestUserWorkspaceRAGManager:
    """Unit tests for UserWorkspaceRAGManager."""

    def test_collection_lifecycle(self):
        """Test creating, listing, getting, and deleting a user RAG collection."""
        test_user_id = 9999
        col_name = "test_project_alpha"
        
        # Create
        manifest = user_workspace_rag_manager.create_collection(
            user_id=test_user_id,
            name=col_name,
            description="Alpha test knowledge base"
        )
        assert manifest["id"] == col_name
        assert manifest["status"] == "created"

        # List
        collections = user_workspace_rag_manager.list_collections(test_user_id)
        assert any(c["id"] == col_name for c in collections)

        # Get
        retrieved = user_workspace_rag_manager.get_collection(test_user_id, col_name)
        assert retrieved is not None
        assert retrieved["name"] == col_name

        # Delete
        deleted = user_workspace_rag_manager.delete_collection(test_user_id, col_name)
        assert deleted is True

        # Verify gone
        assert user_workspace_rag_manager.get_collection(test_user_id, col_name) is None

    def test_ingestion_and_search_with_cleaner(self):
        """Test end-to-end cleaning, chunking, and search on multi-format files."""
        test_user_id = 9998
        col_name = "docs_collection"

        # Prepare user storage files
        user_files_dir = user_manager.get_user_directory(test_user_id, subfolder="files", create=True)
        
        # 1. Text file
        txt_file = user_files_dir / "guide.md"
        txt_file.write_text(
            "# System Architecture\n\nAI-Breadboard is an interactive platform for routing and testing AI models.\n\n"
            "# Capabilities\n\nIt supports Chat, Vision, OCR, and Multi-RAG document retrieval.",
            encoding="utf-8"
        )

        # 2. JSON file
        json_file = user_files_dir / "settings.json"
        json_file.write_text(json.dumps({"engine": "fastapi", "features": ["rag", "tts", "skills"]}), encoding="utf-8")

        # 3. Create collection
        user_workspace_rag_manager.create_collection(
            user_id=test_user_id,
            name=col_name,
            description="Knowledge base containing system docs"
        )

        # 4. Build collection
        build_res = user_workspace_rag_manager.build_collection(
            user_id=test_user_id,
            rag_id=col_name
        )
        assert build_res["status"] == "ok"
        assert build_res["chunks_count"] > 0
        assert "guide.md" in build_res["processed_files"]

        # 5. Search
        search_res = user_workspace_rag_manager.search_collection(
            user_id=test_user_id,
            rag_id=col_name,
            query="Architecture routing testing models",
            top_k=3
        )
        assert len(search_res) > 0
        assert "AI-Breadboard" in search_res[0]["text"]
        assert search_res[0]["score"] > 0.0

        # Clean up
        user_workspace_rag_manager.delete_collection(test_user_id, col_name)


class TestUserWorkspaceRAGAPI:
    """Integration tests for /api/user/rags REST API."""

    def test_api_crud_and_search_flow(self):
        """Test full REST API workflow: upload file, create collection, build, search, delete."""
        rag_name = "api_rag_test"

        # 1. Upload a file to personal files
        file_content = b"# Python Guidelines\n\nAlways follow explicit dependency injection and fail-fast principles in Python code."
        upload_resp = client.post(
            "/api/user/files/upload",
            files={"file": ("python_guide.md", io.BytesIO(file_content), "text/markdown")},
            data={"subfolder": "files"}
        )
        assert upload_resp.status_code == 200

        # 2. Create RAG collection
        create_resp = client.post(
            "/api/user/rags",
            json={"name": rag_name, "description": "Guidelines collection"}
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["collection"]["id"] == rag_name

        # 3. List RAG collections
        list_resp = client.get("/api/user/rags")
        assert list_resp.status_code == 200
        assert any(c["id"] == rag_name for c in list_resp.json()["collections"])

        # 4. Build index
        build_resp = client.post(
            f"/api/user/rags/{rag_name}/build",
            json={"files": ["python_guide.md"]}
        )
        assert build_resp.status_code == 200
        assert build_resp.json()["status"] == "ok"
        assert build_resp.json()["chunks_count"] > 0

        # 5. Search in RAG collection
        search_resp = client.post(
            f"/api/user/rags/{rag_name}/search",
            json={"query": "dependency injection fail-fast", "top_k": 2}
        )
        assert search_resp.status_code == 200
        results = search_resp.json()["results"]
        assert len(results) > 0
        assert "dependency injection" in results[0]["text"]

        # 6. Delete collection
        del_resp = client.delete(f"/api/user/rags/{rag_name}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

        # 7. Clean up uploaded file
        client.delete("/api/user/files?filename=python_guide.md&subfolder=files")
