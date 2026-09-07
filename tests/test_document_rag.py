# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for DocumentRAGManager
# =============================================================================
# Description:
#   Comprehensive unit tests for document parsing, chunking, TF-IDF vectorization,
#   file operations, and similarity search.
#
# File: test_document_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import numpy as np

from src.rag.document_rag import DocumentRAGManager, DocumentChunk, DocumentInfo


@pytest.fixture
def temp_rag_dirs():
    """Create isolated temporary directories for documents and index."""
    temp_dir = Path(tempfile.mkdtemp())
    docs_dir = temp_dir / "docs"
    index_dir = temp_dir / "index"
    docs_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    yield docs_dir, index_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDocumentRAGManager:
    """Test suite for DocumentRAGManager."""

    def test_save_and_list_documents(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        content = b"# Architecture Overview\nThis is a test document about AI Breadboard."
        info = manager.save_document("test_doc.md", content)

        assert info.name == "test_doc.md"
        assert info.size_bytes == len(content)
        assert info.status == "pending"

        docs = manager.list_documents()
        assert len(docs) == 1
        assert docs[0].name == "test_doc.md"

    def test_extract_text_formats(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        # Markdown / text
        md_file = docs_dir / "sample.md"
        md_file.write_text("Hello World\nLine 2", encoding="utf-8")
        assert "Hello World" in manager.extract_text(md_file)

        # JSON
        json_file = docs_dir / "sample.json"
        json_file.write_text(json.dumps({"key": "value", "items": [1, 2]}), encoding="utf-8")
        extracted_json = manager.extract_text(json_file)
        assert "key" in extracted_json and "value" in extracted_json

        # CSV
        csv_file = docs_dir / "sample.csv"
        csv_file.write_text("name,role\nAlice,Admin\nBob,User", encoding="utf-8")
        extracted_csv = manager.extract_text(csv_file)
        assert "Alice | Admin" in extracted_csv

    def test_chunk_text(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        sample_text = (
            "Paragraph 1 contains important information about algorithms.\n\n"
            "Paragraph 2 discusses database indexing and vector stores.\n\n"
            "Paragraph 3 covers user authentication and security rules."
        )

        chunks = manager.chunk_text(sample_text, "sample.md", chunk_size=80, chunk_overlap=15)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.doc_name == "sample.md"
            assert len(chunk.text) > 0
            assert chunk.chunk_id.startswith("sample.md#chunk_")

    def test_build_and_search_index_local(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        # Add two documents with distinct subjects
        doc1 = b"Quantum computing relies on qubits and quantum entanglement principles."
        doc2 = b"Culinary arts involve cooking techniques, french sauces, and baking pastries."
        manager.save_document("quantum.txt", doc1)
        manager.save_document("cooking.txt", doc2)

        # Build index
        status = manager.build_index(provider="local_tfidf", chunk_size=200, chunk_overlap=20)
        assert status["total_documents"] == 2
        assert status["total_chunks"] >= 2
        assert status["provider"] == "local_tfidf"

        # Search for quantum topic
        results = manager.search("qubits and entanglement", top_k=2)
        assert len(results) > 0
        assert results[0]["doc_name"] == "quantum.txt"
        assert results[0]["score"] > 0.0

        # Search with novel/unseen words (testing matrix shape alignment)
        results_novel = manager.search("qubits and completely novel unknown words xyz123", top_k=2)
        assert len(results_novel) > 0
        assert results_novel[0]["doc_name"] == "quantum.txt"

        # Search with completely out-of-vocabulary query
        results_oov = manager.search("supercalifragilisticexpialidocious foobar bazqux", top_k=2)
        assert results_oov == []

        # Search for culinary topic
        results_cooking = manager.search("baking and french sauces", top_k=2)
        assert len(results_cooking) > 0
        assert results_cooking[0]["doc_name"] == "cooking.txt"

    def test_delete_document(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        manager.save_document("delete_me.txt", b"Temporary data.")
        assert len(manager.list_documents()) == 1

        deleted = manager.delete_document("delete_me.txt")
        assert deleted is True
        assert len(manager.list_documents()) == 0

        # Deleting non-existent file
        assert manager.delete_document("non_existent.txt") is False

    def test_save_and_list_nested_folder_documents(self, temp_rag_dirs):
        docs_dir, index_dir = temp_rag_dirs
        manager = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)

        # Save files under subdirectories (e.g. from folder upload)
        manager.save_document("subfolder/deep/doc1.txt", b"Deep document content about space exploration.")
        manager.save_document("subfolder/doc2.txt", b"Subfolder doc about marine biology.")

        docs = manager.list_documents()
        doc_names = [d.name for d in docs]
        assert "subfolder/deep/doc1.txt" in doc_names
        assert "subfolder/doc2.txt" in doc_names

        # Build index over nested folders
        status = manager.build_index(provider="local_tfidf")
        assert status["total_documents"] == 2

        # Search query matching nested document
        results = manager.search("space exploration", top_k=1)
        assert len(results) > 0
        assert results[0]["doc_name"] == "subfolder/deep/doc1.txt"

        # Delete nested document
        deleted = manager.delete_document("subfolder/deep/doc1.txt")
        assert deleted is True
        remaining = manager.list_documents()
        assert len(remaining) == 1
        assert remaining[0].name == "subfolder/doc2.txt"

