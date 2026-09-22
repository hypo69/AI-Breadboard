# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Router for PixelRAG API
# =============================================================================
# Description:
#   REST API endpoints for PixelRAG hybrid search system:
#   - Document indexing (text and images)
#   - Semantic search with smart routing
#   - Query analysis
#   - Metadata management
#   - Statistics and monitoring
#
# File: pixel_rag_router.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from logger import logger
from src.rag import get_document_rag_manager
from src.rag.engine import get_rag_engine
from src.rag.query_router import get_query_router, RoutingType
from src.rag.pixel.image_metadata import get_image_metadata_manager

# ============================================================================
# Request/Response Models
# ============================================================================


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum score threshold")
    use_routing: bool = Field(True, description="Use smart query routing")
    version_filter: str = Field("latest", description="Version filter")


class QueryAnalysisResponse(BaseModel):
    """Query analysis response."""
    query: str
    routing_type: str
    language: str
    confidence: float
    visual_keywords: List[str]
    reason: str


class SearchResult(BaseModel):
    """Single search result."""
    chunk_id: str
    doc_name: str
    text: str
    score: float
    source_type: str
    source_path: Optional[str] = None
    version: int = 1
    tags: List[str] = []


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    routing_type: str
    results: List[SearchResult]
    total_results: int
    query_confidence: float
    status: str


class IndexStatusResponse(BaseModel):
    """Index status response."""
    total_documents: int
    total_chunks: int
    total_images: int
    total_size_mb: float
    last_built_at: float
    provider: str
    sources: Dict[str, int]


class DocumentInfo(BaseModel):
    """Document information."""
    filename: str
    size_bytes: int
    format: str
    indexed_via: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    components: Dict[str, str]
    version: str = "1.0.0"


# ============================================================================
# FastAPI Router
# ============================================================================

router = APIRouter(prefix="/api/rag/pixel", tags=["PixelRAG"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    ## hypo69 docblock
    Check PixelRAG system health.

    Returns:
        HealthResponse with system status
    """
    try:
        doc_rag = get_document_rag_manager()
        router_check = get_query_router()
        engine_check = get_rag_engine()

        components = {
            "document_rag": "✓ OK" if doc_rag else "✗ ERROR",
            "query_router": "✓ OK" if router_check else "✗ ERROR",
            "rag_engine": "✓ OK" if engine_check else "✗ ERROR",
        }

        return HealthResponse(
            status="✓ healthy",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PixelRAG system unavailable"
        )


@router.post("/search", response_model=SearchResponse, summary="Search documents")
async def search(request: SearchRequest) -> SearchResponse:
    """
    ## hypo69 docblock
    Search documents with smart routing.

    Uses QueryRouter to determine optimal search strategy
    (text-only, image-only, or hybrid).

    Args:
        request: Search request

    Returns:
        SearchResponse with results
    """
    try:
        doc_rag = get_document_rag_manager()
        router = get_query_router()

        # Analyze query
        analysis = router.analyze(request.query)

        # Search documents
        search_results = doc_rag.search(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score,
            version_filter=request.version_filter
        )

        # Filter by routing if not using routing
        if request.use_routing and analysis.routing_type != RoutingType.HYBRID:
            source_type = "text" if analysis.routing_type == RoutingType.TEXT else "pixel"
            search_results = [
                r for r in search_results
                if r.get("source_type") == source_type
            ]

        # Convert to response format
        results = [
            SearchResult(
                chunk_id=r.get("chunk_id", ""),
                doc_name=r.get("doc_name", ""),
                text=r.get("text", "")[:200],  # Truncate
                score=r.get("score", 0.0),
                source_type=r.get("source_type", "unknown"),
                source_path=r.get("source_path", r.get("text", "")),
                version=r.get("version", 1),
            )
            for r in search_results
        ]

        return SearchResponse(
            query=request.query,
            routing_type=analysis.routing_type.value,
            results=results,
            total_results=len(results),
            query_confidence=analysis.confidence,
            status="success"
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/analyze-query", response_model=QueryAnalysisResponse, summary="Analyze query")
async def analyze_query(query: str = Query(..., min_length=1)) -> QueryAnalysisResponse:
    """
    ## hypo69 docblock
    Analyze query and determine routing strategy.

    Args:
        query: Query string

    Returns:
        QueryAnalysisResponse with analysis
    """
    try:
        router = get_query_router()
        analysis = router.analyze(query)

        return QueryAnalysisResponse(
            query=query,
            routing_type=analysis.routing_type.value,
            language=analysis.language.value,
            confidence=analysis.confidence,
            visual_keywords=analysis.visual_keywords,
            reason=analysis.reason
        )

    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query analysis failed: {str(e)}"
        )


@router.get("/status", response_model=IndexStatusResponse, summary="Get index status")
async def get_status() -> IndexStatusResponse:
    """
    ## hypo69 docblock
    Get current index status and statistics.

    Returns:
        IndexStatusResponse with status info
    """
    try:
        doc_rag = get_document_rag_manager()
        status_dict = doc_rag.get_status()

        # Calculate totals
        total_images = 0
        total_size_bytes = 0

        try:
            metadata_mgr = get_image_metadata_manager()
            image_stats = metadata_mgr.get_statistics()
            total_images = image_stats.get("total_images", 0)
            total_size_bytes = image_stats.get("total_size_bytes", 0)
        except:
            pass

        return IndexStatusResponse(
            total_documents=status_dict.get("total_documents", 0),
            total_chunks=status_dict.get("total_chunks", 0),
            total_images=total_images,
            total_size_mb=total_size_bytes / (1024 * 1024),
            last_built_at=status_dict.get("last_built_at", 0.0),
            provider=status_dict.get("provider", "unknown"),
            sources={
                "text_chunks": status_dict.get("total_chunks", 0),
                "images": total_images
            }
        )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@router.post("/index", summary="Index documents")
async def index_documents(
    files: List[UploadFile] = File(..., description="Files to index")
) -> Dict[str, Any]:
    """
    ## hypo69 docblock
    Index uploaded documents (text and images).

    Args:
        files: List of files to index

    Returns:
        Indexing result
    """
    try:
        import tempfile
        from pathlib import Path

        doc_rag = get_document_rag_manager()
        indexed_count = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save uploaded files
            for file in files:
                file_path = temp_path / file.filename
                contents = await file.read()
                file_path.write_bytes(contents)
                indexed_count += 1

            # Index documents
            result = doc_rag.build_index(provider='auto')

        return {
            "status": "success",
            "files_indexed": indexed_count,
            "total_documents": result.get("total_documents", 0),
            "new_chunks": result.get("new_chunks_added", 0),
            "message": f"Indexed {indexed_count} files"
        }

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@router.get("/documents", summary="List indexed documents")
async def list_documents() -> Dict[str, Any]:
    """
    ## hypo69 docblock
    List all indexed documents.

    Returns:
        List of documents with metadata
    """
    try:
        doc_rag = get_document_rag_manager()
        documents = doc_rag.list_documents()

        return {
            "status": "success",
            "total_documents": len(documents),
            "documents": [
                {
                    "name": d.name,
                    "size_bytes": d.size_bytes,
                    "status": d.status,
                    "version": d.version,
                    "is_latest": d.is_latest
                }
                for d in documents
            ]
        }

    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/search-history", summary="Get search statistics")
async def get_search_stats() -> Dict[str, Any]:
    """
    ## hypo69 docblock
    Get search statistics and patterns.

    Returns:
        Search statistics
    """
    return {
        "status": "success",
        "total_searches": 0,  # Future: track in database
        "popular_queries": [],  # Future: analytics
        "routing_distribution": {
            "text": 0,
            "pixel": 0,
            "hybrid": 0
        },
        "average_query_time_ms": 0  # Future: track metrics
    }


@router.delete("/documents/{doc_name}", summary="Delete document")
async def delete_document(doc_name: str) -> Dict[str, Any]:
    """
    ## hypo69 docblock
    Delete a document from the index.

    Args:
        doc_name: Document name

    Returns:
        Deletion result
    """
    try:
        doc_rag = get_document_rag_manager()
        found = doc_rag.delete_document(doc_name, purge_history=False)

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_name} not found"
            )

        return {
            "status": "success",
            "message": f"Deleted {doc_name}",
            "purged": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


# ============================================================================
# Utility Functions
# ============================================================================

def get_pixel_rag_router() -> APIRouter:
    """
    ## hypo69 docblock
    Get configured PixelRAG API router.

    Returns:
        FastAPI Router instance
    """
    return router
