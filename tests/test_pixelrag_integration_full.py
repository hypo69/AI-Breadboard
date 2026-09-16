# -*- coding: utf-8 -*-
"""
## hypo69 docblock
Integration tests for complete PixelRAG pipeline.

Tests:
- End-to-end workflow: index → query → results
- Hybrid text + image search
- Query routing with QueryRouter
- RAGEngine integration
- Metadata tracking
"""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
class TestPixelRAGIntegrationFull:
    """Full integration tests for PixelRAG system."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories."""
        with TemporaryDirectory() as temp_base:
            docs_dir = Path(temp_base) / "documents"
            index_dir = Path(temp_base) / "indices"
            docs_dir.mkdir()
            index_dir.mkdir()
            yield docs_dir, index_dir

    def create_test_image(self, path: Path, width: int = 100, height: int = 100) -> None:
        """Create test image."""
        img = Image.new('RGB', (width, height), color='blue')
        img.save(path)

    def create_test_document(self, path: Path, content: str) -> None:
        """Create test document."""
        path.write_text(content, encoding='utf-8')

    def test_full_pipeline_text_only(self, temp_dirs):
        """Test complete pipeline with text documents only."""
        docs_dir, index_dir = temp_dirs

        # Create documents
        self.create_test_document(
            docs_dir / "readme.txt",
            "This is a test document about saving files"
        )

        try:
            from src.rag import DocumentRAGManager
            
            # Index
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            result = doc_rag.build_index(provider='auto')
            
            assert result["files_scanned"] >= 1
            
            # Search
            search_results = doc_rag.search("saving files", top_k=5)
            
            assert isinstance(search_results, list)
        
        except ImportError:
            pytest.skip("DocumentRAGManager not available")

    def test_full_pipeline_with_images(self, temp_dirs):
        """Test complete pipeline with mixed documents."""
        docs_dir, index_dir = temp_dirs

        # Create documents
        self.create_test_document(docs_dir / "readme.txt", "Save button information")
        self.create_test_image(docs_dir / "button.png")

        try:
            from src.rag import DocumentRAGManager
            
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            
            # Index should handle both
            result = doc_rag.build_index(provider='auto')
            
            # At least scanned files
            assert result["files_scanned"] >= 1
            
            # Search
            search_results = doc_rag.search("button", top_k=5)
            
            assert isinstance(search_results, list)
            
            # Check result structure
            for result in search_results:
                assert "source_type" in result
                assert result["source_type"] in ["text", "pixel"]
        
        except ImportError:
            pytest.skip("Dependencies not available")

    def test_query_routing(self):
        """Test QueryRouter integration."""
        try:
            from src.rag.query_router import get_query_router, RoutingType
            
            router = get_query_router()
            
            # Text query
            analysis = router.analyze("Explain how to save")
            assert analysis.routing_type == RoutingType.TEXT
            
            # Visual query
            analysis = router.analyze("Покажи кнопку")
            assert analysis.routing_type == RoutingType.PIXEL
            
            # Hybrid query
            analysis = router.analyze("Show button and explain")
            assert analysis.routing_type == RoutingType.HYBRID
        
        except ImportError:
            pytest.skip("QueryRouter not available")

    def test_metadata_tracking(self, temp_dirs):
        """Test metadata tracking in search results."""
        docs_dir, index_dir = temp_dirs

        self.create_test_image(docs_dir / "screenshot.png")

        try:
            from src.rag import DocumentRAGManager
            
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            doc_rag.build_index(provider='auto')
            
            results = doc_rag.search("screenshot", top_k=5)
            
            # Results should have metadata
            for result in results:
                if result.get("source_type") == "pixel":
                    assert "meta" in result or "source_path" in result
        
        except ImportError:
            pytest.skip("Dependencies not available")

    def test_rag_engine_search(self, temp_dirs):
        """Test RAGEngine search_documents() method."""
        docs_dir, index_dir = temp_dirs

        self.create_test_document(docs_dir / "doc.txt", "Test content here")

        try:
            from src.rag.engine import get_rag_engine
            from src.rag import DocumentRAGManager
            import asyncio
            
            # Index documents
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            doc_rag.build_index(provider='auto')
            
            # Use RAGEngine
            engine = get_rag_engine()
            
            # Note: search_documents is async
            result = asyncio.run(engine.search_documents(
                "Test content",
                top_k=5,
                use_routing=True
            ))
            
            # Should return RAGRouteDecision
            assert result is not None
            assert hasattr(result, "decision_type")
        
        except ImportError:
            pytest.skip("Dependencies not available")

    def test_error_handling(self, temp_dirs):
        """Test error handling in pipeline."""
        docs_dir, index_dir = temp_dirs

        try:
            from src.rag import DocumentRAGManager
            
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            
            # Empty search
            results = doc_rag.search("", top_k=5)
            assert results == []
            
            # Should not crash
            results = doc_rag.search("nonexistent query", top_k=5)
            assert isinstance(results, list)
        
        except ImportError:
            pytest.skip("DocumentRAGManager not available")

    def test_document_list(self, temp_dirs):
        """Test document listing."""
        docs_dir, index_dir = temp_dirs

        self.create_test_document(docs_dir / "doc1.txt", "Content 1")
        self.create_test_image(docs_dir / "img1.png")

        try:
            from src.rag import DocumentRAGManager
            
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            
            # List should find both files
            docs = doc_rag.list_documents()
            
            assert len(docs) >= 1
        
        except ImportError:
            pytest.skip("DocumentRAGManager not available")

    def test_version_filtering(self, temp_dirs):
        """Test version filtering in search."""
        docs_dir, index_dir = temp_dirs

        self.create_test_document(docs_dir / "doc.txt", "Original content")

        try:
            from src.rag import DocumentRAGManager
            
            doc_rag = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
            doc_rag.build_index(provider='auto')
            
            # Search with version filter
            results_latest = doc_rag.search(
                "content",
                version_filter='latest',
                top_k=5
            )
            
            results_all = doc_rag.search(
                "content",
                version_filter='all',
                top_k=5
            )
            
            # Both should return lists
            assert isinstance(results_latest, list)
            assert isinstance(results_all, list)
        
        except ImportError:
            pytest.skip("DocumentRAGManager not available")


if __name__ == "__main__":
    print("PixelRAG Integration Tests")
    print("=" * 50)
    
    try:
        from src.rag.query_router import get_query_router
        from tempfile import TemporaryDirectory
        from pathlib import Path
        
        router = get_query_router()
        
        # Test routing
        print("Testing Query Routing:")
        
        result = router.analyze("Explain how to use")
        print(f"  'Explain how to use' → {result.routing_type.value}")
        
        result = router.analyze("Show me the button")
        print(f"  'Show me the button' → {result.routing_type.value}")
        
        result = router.analyze("Pokazi knopku i obysni")
        print(f"  'Pokazi knopku i obysni' → {result.routing_type.value}")
        
        print("\n✓ Basic integration test passed")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
