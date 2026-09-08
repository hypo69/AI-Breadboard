# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI router for Document & Codebase RAG management and search
# =============================================================================
# Description:
#   REST API endpoints for uploading documents, listing files, building vector
#   indexes, AST codebase indexing, and performing semantic / symbol searches.
#
# File: router_rag.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field

from src.logger import logger
from src.rag.document_rag import DocumentRAGManager, get_document_rag_manager
from plugins.generate_rag_from_codebase.plugin import GenerateRagCodebasePlugin


class BuildIndexRequest(BaseModel):
    """Payload for building document RAG index."""
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


class BuildCodebaseIndexRequest(BaseModel):
    """Payload for building AST codebase RAG index."""
    project_root: str = Field(default=".", description="Project directory path (absolute or relative)")
    index_name: str = Field(default="codebase", description="Unique name/identifier for the index")
    include_dirs: Optional[List[str]] = Field(default=None, description="Subdirectories to index")
    include_files: Optional[List[str]] = Field(default=None, description="Files in root to index")


class SearchCodebaseRequest(BaseModel):
    """Payload for searching codebase RAG index."""
    query: str = Field(..., min_length=1, description="Search query")
    index_name: str = Field(default="codebase", description="Target index name")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    type_filter: Optional[str] = Field(default=None, description="Optional chunk type filter")
    module_filter: Optional[str] = Field(default=None, description="Optional module filter")


class SymbolLookupRequest(BaseModel):
    """Payload for looking up symbols in AST codebase index."""
    symbol: str = Field(..., min_length=1, description="Class, function, or method name")
    index_name: str = Field(default="codebase", description="Target index name")
    exact: bool = Field(default=False, description="Require exact name match")
    limit: int = Field(default=10, ge=1, le=50, description="Max symbol matches")


def _get_current_user_id(request: Request) -> int:
    """Retrieve current authenticated user ID or fallback to local user. Raises 401 if unauthenticated."""
    from src.fastapi.router_auth import get_current_user_data
    user_data = get_current_user_data(request)
    if user_data.id:
        return user_data.id
    from src.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if db_user and 'id' in db_user:
        return db_user['id']
    return 1


def init_router() -> APIRouter:
    """Initialize and configure Document & Codebase RAG FastAPI router.

    Returns:
        APIRouter: Configured APIRouter instance.
    """
    router = APIRouter(prefix="/api/rag", tags=["Document & Codebase RAG"])
    codebase_plugin = GenerateRagCodebasePlugin()

    # --- Document RAG Endpoints ---

    @router.post("/upload", summary="Upload documents to knowledge base")
    async def upload_documents(
        request: Request,
        files: List[UploadFile] = File(...),
    ) -> Dict[str, Any]:
        """Upload one or more documents to knowledge base directory."""
        _get_current_user_id(request)
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
    async def list_documents(request: Request) -> Dict[str, Any]:
        """Get list of all documents currently stored in knowledge base."""
        _get_current_user_id(request)
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
    async def delete_document(filename: str, request: Request) -> Dict[str, Any]:
        """Delete specific document and remove its chunks from index."""
        _get_current_user_id(request)
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
    async def build_index(req: BuildIndexRequest, request: Request) -> Dict[str, Any]:
        """Chunk all uploaded documents and construct vector search index."""
        _get_current_user_id(request)
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
    async def get_rag_status(request: Request) -> Dict[str, Any]:
        """Get current index statistics and status."""
        _get_current_user_id(request)
        manager = get_document_rag_manager()
        return {
            "status": "success",
            "data": manager.get_status(),
        }

    @router.post("/search", summary="Search documents semantically")
    async def search_rag(req: SearchRequest, request: Request) -> Dict[str, Any]:
        """Perform semantic similarity search over indexed chunks."""
        _get_current_user_id(request)
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

    # --- Codebase RAG Endpoints (Admin & User) ---

    @router.post("/codebase/build", summary="Build or rebuild Codebase RAG index")
    async def build_codebase_index_endpoint(
        req: BuildCodebaseIndexRequest,
        request: Request
    ) -> Dict[str, Any]:
        """Build AST symbol and vector index for a project directory."""
        user_id = _get_current_user_id(request)
        result = codebase_plugin.build_codebase_index(
            project_root=req.project_root,
            index_name=req.index_name,
            user_id=user_id,
            include_dirs=req.include_dirs,
            include_files=req.include_files
        )
        return {"status": "success", "result": result}

    @router.get("/codebase/indexes", summary="List available Codebase RAG indexes")
    async def list_codebase_indexes_endpoint(request: Request) -> Dict[str, Any]:
        """List all codebase indexes for current user and system."""
        user_id = _get_current_user_id(request)
        indexes = codebase_plugin.list_available_indexes(user_id=user_id)
        # If user is present, also include system indexes
        if user_id is not None:
            sys_indexes = codebase_plugin.list_available_indexes(user_id=None)
            for s in sys_indexes:
                s["scope"] = "system"
            for u in indexes:
                u["scope"] = "user"
            indexes = indexes + [s for s in sys_indexes if s["name"] not in {u["name"] for u in indexes}]

        return {"status": "success", "count": len(indexes), "indexes": indexes}

    @router.post("/codebase/search", summary="Search Codebase RAG index semantically")
    async def search_codebase_endpoint(
        req: SearchCodebaseRequest,
        request: Request
    ) -> Dict[str, Any]:
        """Semantic search over code, docstrings, and docs."""
        user_id = _get_current_user_id(request)
        res = await codebase_plugin.execute_action("search_code", {
            "query": req.query,
            "index_name": req.index_name,
            "user_id": user_id,
            "top_k": req.top_k,
            "type_filter": req.type_filter,
            "module_filter": req.module_filter
        })
        return res

    @router.post("/codebase/symbols", summary="Lookup symbols in Codebase RAG AST index")
    async def lookup_symbols_endpoint(
        req: SymbolLookupRequest,
        request: Request
    ) -> Dict[str, Any]:
        """Lookup class, function, or method names in AST index."""
        user_id = _get_current_user_id(request)
        res = await codebase_plugin.execute_action("search_symbols", {
            "query": req.symbol,
            "index_name": req.index_name,
            "user_id": user_id,
            "exact": req.exact,
            "limit": req.limit
        })
        return res

    @router.delete("/codebase/indexes/{index_name}", summary="Delete Codebase RAG index")
    async def delete_codebase_index_endpoint(
        index_name: str,
        request: Request
    ) -> Dict[str, Any]:
        """Delete a named codebase RAG index."""
        user_id = _get_current_user_id(request)
        res = await codebase_plugin.execute_action("delete_index", {
            "index_name": index_name,
            "user_id": user_id
        })
        return res

    return router
