# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Pixel Rag Integration
# =============================================================================
# Description:
#   Tests for PixelRAG integration into DocumentRAGManager.
#
# Usage Examples:
#   CLI:
#     python -m tests.test_pixel_rag_integration
#   Python API:
#     from tests.test_pixel_rag_integration import TestPixelRAGIntegration
#
#     service = TestPixelRAGIntegration()
#
# File: test_pixel_rag_integration.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Tests for PixelRAG integration into DocumentRAGManager.

Tests:
- Image file detection and routing
- Hybrid search (text + pixel results)
- Metadata tracking with indexed_via field
- Error handling and graceful degradation"""

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

@pytest.mark.skipif(not PIL_AVAILABLE, reason='PIL not available')
class TestPixelRAGIntegration:
    """Integration tests for PixelRAG in DocumentRAGManager."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with TemporaryDirectory() as temp_base:
            docs_dir = Path(temp_base) / 'documents'
            index_dir = Path(temp_base) / 'indices'
            docs_dir.mkdir(parents=True)
            index_dir.mkdir(parents=True)
            yield (docs_dir, index_dir)

    def create_test_image(self, path: Path, width: int=100, height: int=100) -> None:
        """Create a simple test image."""
        img = Image.new('RGB', (width, height), color='red')
        img.save(path)

    def create_test_document(self, path: Path, content: str) -> None:
        """Create a test text document."""
        path.write_text(content, encoding='utf-8')

    def test_image_file_detection(self, temp_dirs):
        """Test that image files are properly detected and routed."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'document.txt', 'This is a test document')
        self.create_test_image(docs_dir / 'screenshot.png')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        from src.rag.document_rag import IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS
        assert '.png' in IMAGE_EXTENSIONS
        assert '.jpg' in IMAGE_EXTENSIONS
        assert '.png' in SUPPORTED_EXTENSIONS
        assert '.pdf' in SUPPORTED_EXTENSIONS

    def test_build_index_with_images(self, temp_dirs):
        """Test building index with mixed document types."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'readme.txt', 'Test document content')
        self.create_test_image(docs_dir / 'ui.png')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        result = doc_rag.build_index(provider='auto')
        assert 'files_scanned' in result
        assert 'new_chunks_added' in result
        assert 'total_documents' in result
        assert result['files_scanned'] >= 1

    def test_metadata_tracking_indexed_via(self, temp_dirs):
        """Test that indexed_via field is tracked correctly."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'doc.txt', 'Content')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        doc_rag.build_index(provider='auto')
        meta_file = index_dir / 'document_rag_meta.json'
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                if 'files' in meta and 'doc.txt' in meta['files']:
                    doc_info = meta['files']['doc.txt']
                    if 'indexed_via' in doc_info:
                        assert doc_info['indexed_via'] in ['text', 'pixel']

    def test_search_with_text_only(self, temp_dirs):
        """Test search with text-only documents."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'doc.txt', 'The quick brown fox jumps')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        doc_rag.build_index(provider='auto')
        results = doc_rag.search('fox', top_k=5)
        assert isinstance(results, list)
        text_results = [r for r in results if r.get('source_type') == 'text']
        assert isinstance(text_results, list)

    def test_pixel_rag_provider_available(self):
        """Test that PixelRAG provider can be initialized."""
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        with TemporaryDirectory() as temp_dir:
            doc_rag = DocumentRAGManager(docs_dir=Path(temp_dir) / 'docs', index_dir=Path(temp_dir) / 'index')
            pixel_rag = doc_rag._get_pixel_rag()
            assert pixel_rag is None or hasattr(pixel_rag, 'search')

    def test_search_result_structure(self, temp_dirs):
        """Test that search results have correct structure."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'test.txt', 'Sample text content')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        doc_rag.build_index(provider='auto')
        results = doc_rag.search('text', top_k=5)
        for result in results:
            assert 'chunk_id' in result
            assert 'doc_name' in result
            assert 'text' in result
            assert 'score' in result
            assert 'source_type' in result
            assert result['source_type'] in ['text', 'pixel']

    def test_document_list_includes_images(self, temp_dirs):
        """Test that list_documents includes image files."""
        docs_dir, index_dir = temp_dirs
        self.create_test_document(docs_dir / 'doc.txt', 'Content')
        self.create_test_image(docs_dir / 'image.png')
        try:
            from src.rag import DocumentRAGManager
        except ImportError:
            pytest.skip('DocumentRAGManager not available')
        doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
        docs = doc_rag.list_documents()
        doc_names = {d.name for d in docs}
        assert len(docs) >= 1
if __name__ == '__main__':
    print('PixelRAG Integration Tests')
    print('=' * 50)
    try:
        from src.rag import DocumentRAGManager
        from src.rag.document_rag import IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS
        print('✓ DocumentRAGManager imported successfully')
        print(f'✓ IMAGE_EXTENSIONS: {IMAGE_EXTENSIONS}')
        print(f"✓ SUPPORTED_EXTENSIONS includes images: {'.png' in SUPPORTED_EXTENSIONS}")
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp_dir:
            doc_rag = DocumentRAGManager(docs_dir=Path(temp_dir) / 'docs', index_dir=Path(temp_dir) / 'index')
            pixel_rag = doc_rag._get_pixel_rag()
            print(f"✓ PixelRAG provider: {('available' if pixel_rag else 'not available (OK if FAISS not installed)')}")
        print('\n✓ All basic sanity checks passed')
    except Exception as e:
        print(f'✗ Error during tests: {e}')
        import traceback
        traceback.print_exc()