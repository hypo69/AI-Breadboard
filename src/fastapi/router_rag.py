# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI router for Document RAG management and search
# =============================================================================
# Description:
#   REST API endpoints for uploading documents, listing files, building vector
#   indexes, and performing semantic searches over the knowledge base.
#
# File: router_rag.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from src.logger import logger
from src.rag.document_rag import DocumentRAGManager, get_document_rag_manager


class BuildIndexRequest(BaseModel):
    """Payload for building RAG index."""
    provider: str = Field(default="auto", description="Vector provider: 'auto', 'gemini', or 'local_tfidf'")
    api_key: Optional[str] = Field(default="", description="Gemini API Key if using Gemini embedding provider")
    chunk_size: int = Field(default=500, ge=100, le=4000, description="Max character length per chunk")
    chunk_overlap: int = Field(default=50, ge=0, le=1000, description="Overlap characters between chunks")


class SearchRequest(BaseModel):
    """Payload for semantic similarity search."""
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    api_key: Optional[str] = Field(default="", description="Gemini API Key if using Gemini search")


def init_router() -> APIRouter:
    """Initialize and configure Document RAG FastAPI router.

    Returns:
        APIRouter: Configured APIRouter instance.
    """
    router = APIRouter(prefix="/api/rag", tags=["Document RAG"])

    @router.post("/upload", summary="Upload documents to knowledge base")
    async def upload_documents(
        files: List[UploadFile] = File(...),
    ) -> Dict[str, Any]:
        """Upload one or more documents to knowledge base directory."""
        if not files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

        manager = get_document_rag_manager()
        uploaded: List[Dict[str, Any]] = []
        for file in files:
            try:
                content = await file.read()
                filename = file.filename or "untitled.txt"
                info = manager.save_document(filename, content)
                uploaded.append({
                    "name": info.name,
                    "size_bytes": info.size_bytes,
                    "status": info.status,
                })
            except Exception as e:
                logger.error(f"[router_rag] Failed to save {file.filename}: {e}")
                uploaded.append({
                    "name": file.filename or "unknown",
                    "error": str(e),
                })

        return {
            "status": "success",
            "uploaded": uploaded,
            "total_documents": len(manager.list_documents()),
        }

    @router.get("/documents", summary="List all knowledge base documents")
    async def list_documents() -> Dict[str, Any]:
        """Get list of all documents currently stored in knowledge base."""
        manager = get_document_rag_manager()
        docs = manager.list_documents()
        return {
            "status": "success",
            "count": len(docs),
            "documents": [
                {
                    "name": d.name,
                    "size_bytes": d.size_bytes,
                    "modified_at": d.modified_at,
                    "status": d.status,
                    "chunks_count": d.chunks_count,
                    "error_message": d.error_message,
                }
                for d in docs
            ],
        }

    @router.delete("/documents/{filename}", summary="Delete document from knowledge base")
    async def delete_document(filename: str) -> Dict[str, Any]:
        """Delete specific document and remove its chunks from index."""
        manager = get_document_rag_manager()
        success = manager.delete_document(filename)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{filename}' not found")

        return {
            "status": "success",
            "message": f"Document '{filename}' deleted successfully",
            "total_documents": len(manager.list_documents()),
        }

    @router.post("/build", summary="Build or rebuild document RAG index")
    async def build_index(req: BuildIndexRequest) -> Dict[str, Any]:
        """Chunk all uploaded documents and construct vector search index."""
        manager = get_document_rag_manager()
        api_key = req.api_key or ""
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY_1", "") or os.getenv("GEMINI_API_KEY", "")

        status_res = manager.build_index(
            provider=req.provider,
            api_key=api_key,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
        return {
            "status": "success",
            "result": status_res,
        }

    @router.get("/status", summary="Get RAG index status")
    async def get_rag_status() -> Dict[str, Any]:
        """Get current index statistics and status."""
        manager = get_document_rag_manager()
        return {
            "status": "success",
            "data": manager.get_status(),
        }

    @router.post("/search", summary="Search documents semantically")
    async def search_rag(req: SearchRequest) -> Dict[str, Any]:
        """Perform semantic similarity search over indexed chunks."""
        manager = get_document_rag_manager()
        api_key = req.api_key or ""
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY_1", "") or os.getenv("GEMINI_API_KEY", "")

        results = manager.search(
            query=req.query,
            top_k=req.top_k,
            min_score=req.min_score,
            api_key=api_key,
        )
        return {
            "status": "success",
            "query": req.query,
            "count": len(results),
            "results": results,
        }

    return router
