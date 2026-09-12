# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Document RAG API endpoints
# =============================================================================
# Description:
#   Integration and unit tests for /api/rag router endpoints (upload, list,
#   delete, build, search, and status).
#
# File: test_router_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import io
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.rag.document_rag import DocumentRAGManager, get_document_rag_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_rag_manager(monkeypatch):
    """Provide an isolated DocumentRAGManager instance for each test."""
    temp_dir = Path(tempfile.mkdtemp())
    docs_dir = temp_dir / "rag_docs"
    index_dir = temp_dir / "rag_index"
    docs_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    isolated_mgr = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
    monkeypatch.setattr("src.fastapi.router_rag.get_document_rag_manager", lambda: isolated_mgr)
    monkeypatch.setattr("src.rag.document_rag._doc_rag_manager", isolated_mgr)

    yield isolated_mgr

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRouterRAG:
    """Test suite for /api/rag router."""

    def test_upload_and_list_documents(self, isolated_rag_manager):
        # 1. Upload two files
        file1 = ("guide.md", io.BytesIO(b"# User Guide\nHow to configure AI Breadboard."), "text/markdown")
        file2 = ("notes.txt", io.BytesIO(b"Notes about machine learning algorithms."), "text/plain")

        response = client.post(
            "/api/rag/upload",
            files=[
                ("files", (file1[0], file1[1], file1[2])),
                ("files", (file2[0], file2[1], file2[2])),
            ]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["uploaded"]) == 2

        # 2. Get list of documents
        list_res = client.get("/api/rag/documents")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["count"] == 2
        names = [d["name"] for d in list_data["documents"]]
        assert "guide.md" in names
        assert "notes.txt" in names

    def test_build_and_search(self, isolated_rag_manager):
        # 1. Upload a file
        content = b"FastAPI is a modern, fast web framework for building APIs with Python 3.8+."
        client.post(
            "/api/rag/upload",
            files=[("files", ("fastapi_intro.txt", io.BytesIO(content), "text/plain"))]
        )

        # 2. Build index
        build_res = client.post(
            "/api/rag/build",
            json={
                "provider": "local_tfidf",
                "chunk_size": 300,
                "chunk_overlap": 30,
            }
        )
        assert build_res.status_code == 200
        build_data = build_res.json()
        assert build_data["status"] == "success"
        assert build_data["result"]["total_chunks"] >= 1

        # 3. Check status endpoint
        status_res = client.get("/api/rag/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["data"]["total_documents"] == 1
        assert status_data["data"]["provider"] == "local_tfidf"

        # 4. Search endpoint
        search_res = client.post(
            "/api/rag/search",
            json={
                "query": "web framework for building APIs",
                "top_k": 3,
                "min_score": 0.0,
            }
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["status"] == "success"
        assert search_data["count"] >= 1
        assert search_data["results"][0]["doc_name"] == "fastapi_intro.txt"

        # 5. Search with novel words
        novel_res = client.post(
            "/api/rag/search",
            json={
                "query": "framework with unknown_word_12345",
                "top_k": 3,
                "min_score": 0.0,
            }
        )
        assert novel_res.status_code == 200
        assert novel_res.json()["status"] == "success"
        assert novel_res.json()["count"] >= 1

    def test_delete_document(self, isolated_rag_manager):
        # Upload a file
        client.post(
            "/api/rag/upload",
            files=[("files", ("temp_doc.txt", io.BytesIO(b"Ephemeral content"), "text/plain"))]
        )

        # Delete it
        del_res = client.delete("/api/rag/documents/temp_doc.txt")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

        # Check deletion
        docs_res = client.get("/api/rag/documents")
        assert docs_res.json()["count"] == 0

        # Delete again -> 404
        del_again = client.delete("/api/rag/documents/temp_doc.txt")
        assert del_again.status_code == 404
