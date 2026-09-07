# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User personal file storage router
# =============================================================================
# Description:
#   Provides FastAPI endpoints for managing isolated personal user file storage,
#   including uploading, listing, downloading, deleting files, and inspecting storage stats.
#
# File: router_user_storage.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse

from src.logger import logger
from src.user_manager import user_manager

router = APIRouter(prefix='/api/user/files', tags=['user-storage'])

def _get_current_user_id(request: Request) -> int:
    """Retrieve current authenticated user ID or fallback to local user."""
    from src.fastapi.router_auth import verify_jwt_token
    token = request.cookies.get('auth_token', '')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            if user_data.id:
                return user_data.id
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and 'id' in db_user:
                return db_user['id']

    # Local development fallback
    hostname = request.url.hostname or ''
    is_local = (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )
    if is_local:
        return 1

    raise HTTPException(status_code=401, detail='Authentication required')

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks."""
    basename = os.path.basename(filename).strip()
    clean = "".join(c for c in basename if c.isalnum() or c in (".", "_", "-", " ", "(", ")"))
    if not clean or clean.startswith('.'):
        clean = f"file_{clean}" if clean else "unnamed_file"
    return clean

@router.get('')
async def list_user_files(
    request: Request,
    subfolder: str = Query('files', description='Target subfolder: files, rag, profile, temp, or all')
) -> Dict[str, Any]:
    """List files in the user's personal directory.

    Args:
        request: FastAPI request object.
        subfolder: Subfolder to query.

    Returns:
        Dict[str, Any]: List of files with metadata.
    """
    user_id = _get_current_user_id(request)
    
    if subfolder == 'all':
        user_root = user_manager.get_user_directory(user_id, create=True)
        items = []
        for file_path in user_root.rglob('*'):
            if file_path.is_file():
                rel = file_path.relative_to(user_root)
                stat = file_path.stat()
                items.append({
                    'name': file_path.name,
                    'relative_path': str(rel).replace('\\', '/'),
                    'subfolder': rel.parts[0] if len(rel.parts) > 1 else 'root',
                    'size_bytes': stat.st_size,
                    'modified_at': stat.st_mtime
                })
        return {
            'status': 'ok',
            'user_id': user_id,
            'files': items,
            'total': len(items)
        }

    target_dir = user_manager.get_user_directory(user_id, subfolder=subfolder, create=True)
    items = []
    for file_path in target_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            items.append({
                'name': file_path.name,
                'subfolder': subfolder,
                'size_bytes': stat.st_size,
                'modified_at': stat.st_mtime
            })

    return {
        'status': 'ok',
        'user_id': user_id,
        'subfolder': subfolder,
        'files': items,
        'total': len(items)
    }

@router.post('/upload')
async def upload_user_file(
    request: Request,
    file: UploadFile = File(...),
    subfolder: str = Form('files')
) -> Dict[str, Any]:
    """Upload a file to the user's personal storage directory.

    Args:
        request: FastAPI request object.
        file: Uploaded file object.
        subfolder: Destination subfolder (default 'files').

    Returns:
        Dict[str, Any]: Upload confirmation and file details.
    """
    user_id = _get_current_user_id(request)
    clean_name = _sanitize_filename(file.filename or 'upload.dat')
    target_dir = user_manager.get_user_directory(user_id, subfolder=subfolder, create=True)
    dest_path = target_dir / clean_name

    try:
        with open(dest_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as ex:
        logger.error(f'Failed to save uploaded file for user {user_id}:', ex, False)
        raise HTTPException(status_code=500, detail='Failed to write file to disk')
    finally:
        file.file.close()

    stat = dest_path.stat()
    return {
        'status': 'ok',
        'user_id': user_id,
        'filename': clean_name,
        'subfolder': subfolder,
        'size_bytes': stat.st_size,
        'path': str(dest_path)
    }

@router.get('/download')
async def download_user_file(
    request: Request,
    filename: str = Query(..., description='Filename to download'),
    subfolder: str = Query('files', description='Subfolder where file is stored')
) -> FileResponse:
    """Download a file from user's personal storage directory.

    Args:
        request: FastAPI request object.
        filename: Name of the file.
        subfolder: Subfolder name.

    Returns:
        FileResponse: File stream response.
    """
    user_id = _get_current_user_id(request)
    clean_name = _sanitize_filename(filename)
    target_dir = user_manager.get_user_directory(user_id, subfolder=subfolder, create=False)
    file_path = target_dir / clean_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail='File not found in user storage')

    return FileResponse(path=file_path, filename=clean_name)

@router.delete('')
async def delete_user_file(
    request: Request,
    filename: str = Query(..., description='Filename to delete'),
    subfolder: str = Query('files', description='Subfolder where file is stored')
) -> Dict[str, Any]:
    """Delete a file from user's personal storage directory.

    Args:
        request: FastAPI request object.
        filename: Name of the file.
        subfolder: Subfolder name.

    Returns:
        Dict[str, Any]: Deletion result status.
    """
    user_id = _get_current_user_id(request)
    clean_name = _sanitize_filename(filename)
    target_dir = user_manager.get_user_directory(user_id, subfolder=subfolder, create=False)
    file_path = target_dir / clean_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail='File not found in user storage')

    try:
        file_path.unlink()
        return {'status': 'ok', 'deleted': clean_name, 'user_id': user_id}
    except Exception as ex:
        logger.error(f'Error deleting file {file_path}:', ex, False)
        raise HTTPException(status_code=500, detail='Failed to delete file')

@router.get('/stats')
async def get_user_storage_stats_endpoint(request: Request) -> Dict[str, Any]:
    """Retrieve storage usage statistics for the current user.

    Args:
        request: FastAPI request object.

    Returns:
        Dict[str, Any]: Storage statistics.
    """
    user_id = _get_current_user_id(request)
    stats = user_manager.get_user_storage_stats(user_id)
    return {'status': 'ok', 'stats': stats}


# =============================================================================
# User Multi-RAG Management & Ingestion Pipeline Routes
# =============================================================================

from pydantic import BaseModel, Field
from src.rag.user_workspace_rag import user_workspace_rag_manager


class CreateUserRAGRequest(BaseModel):
    """Payload for creating a new user RAG collection."""
    name: str = Field(..., min_length=1, max_length=100, description="Collection name")
    description: str = Field(default="", max_length=500, description="Collection description")
    files: Optional[List[str]] = Field(default_factory=list, description="Attached user filenames")
    min_chunk_len: int = Field(default=20, ge=5, le=500, description="Minimum chunk length")
    max_chunk_len: int = Field(default=1500, ge=100, le=5000, description="Maximum chunk length")


class BuildUserRAGRequest(BaseModel):
    """Payload for building a user RAG index with cleaner pipeline."""
    files: Optional[List[str]] = Field(default=None, description="Specific files to clean and index")
    min_chunk_len: Optional[int] = Field(default=None, ge=5, le=500, description="Min chunk length override")
    max_chunk_len: Optional[int] = Field(default=None, ge=100, le=5000, description="Max chunk length override")
    provider: str = Field(default="local_tfidf", description="Vector provider: local_tfidf or gemini")
    api_key: Optional[str] = Field(default="", description="Optional API key for external provider")


class SearchUserRAGRequest(BaseModel):
    """Payload for searching inside a user RAG collection."""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Max results")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Min score threshold")


user_rags_router = APIRouter(prefix='/api/user/rags', tags=['user-rags'])


@user_rags_router.get('')
async def list_user_rags_endpoint(request: Request) -> Dict[str, Any]:
    """List all RAG collections for the current user.

    Args:
        request: FastAPI request object.

    Returns:
        Dict[str, Any]: List of collections and user ID.
    """
    user_id = _get_current_user_id(request)
    collections = user_workspace_rag_manager.list_collections(user_id)
    return {
        'status': 'ok',
        'user_id': user_id,
        'collections': collections,
        'total': len(collections)
    }


@user_rags_router.post('')
async def create_user_rag_endpoint(
    request: Request,
    payload: CreateUserRAGRequest
) -> Dict[str, Any]:
    """Create a new user RAG collection.

    Args:
        request: FastAPI request object.
        payload: Collection metadata.

    Returns:
        Dict[str, Any]: Created collection manifest.
    """
    user_id = _get_current_user_id(request)
    created = user_workspace_rag_manager.create_collection(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        files=payload.files,
        min_chunk_len=payload.min_chunk_len,
        max_chunk_len=payload.max_chunk_len
    )
    return {'status': 'ok', 'user_id': user_id, 'collection': created}


@user_rags_router.get('/{rag_id}')
async def get_user_rag_endpoint(
    request: Request,
    rag_id: str
) -> Dict[str, Any]:
    """Get metadata for a specific user RAG collection.

    Args:
        request: FastAPI request object.
        rag_id: Collection identifier.

    Returns:
        Dict[str, Any]: Collection manifest.
    """
    user_id = _get_current_user_id(request)
    collection = user_workspace_rag_manager.get_collection(user_id, rag_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection '{rag_id}' not found")
    return {'status': 'ok', 'user_id': user_id, 'collection': collection}


@user_rags_router.delete('/{rag_id}')
async def delete_user_rag_endpoint(
    request: Request,
    rag_id: str
) -> Dict[str, Any]:
    """Delete a user RAG collection and its indices.

    Args:
        request: FastAPI request object.
        rag_id: Collection identifier.

    Returns:
        Dict[str, Any]: Deletion status.
    """
    user_id = _get_current_user_id(request)
    deleted = user_workspace_rag_manager.delete_collection(user_id, rag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Collection '{rag_id}' not found")
    return {'status': 'ok', 'user_id': user_id, 'deleted': rag_id}


@user_rags_router.post('/{rag_id}/build')
async def build_user_rag_endpoint(
    request: Request,
    rag_id: str,
    payload: BuildUserRAGRequest
) -> Dict[str, Any]:
    """Run rag_cleaner pipeline and build vector index for user RAG collection.

    Args:
        request: FastAPI request object.
        rag_id: Collection identifier.
        payload: Build options.

    Returns:
        Dict[str, Any]: Build summary and updated manifest.
    """
    user_id = _get_current_user_id(request)
    try:
        result = user_workspace_rag_manager.build_collection(
            user_id=user_id,
            rag_id=rag_id,
            files=payload.files,
            min_chunk_len=payload.min_chunk_len,
            max_chunk_len=payload.max_chunk_len,
            provider=payload.provider,
            api_key=payload.api_key or ""
        )
        return {'status': 'ok', 'user_id': user_id, **result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Collection '{rag_id}' not found")
    except Exception as ex:
        logger.error(f"Error building RAG collection {rag_id}:", ex, False)
        raise HTTPException(status_code=500, detail=f"Failed to build RAG index: {ex}")


@user_rags_router.post('/{rag_id}/search')
async def search_user_rag_endpoint(
    request: Request,
    rag_id: str,
    payload: SearchUserRAGRequest
) -> Dict[str, Any]:
    """Search within a specific user RAG collection.

    Args:
        request: FastAPI request object.
        rag_id: Collection identifier.
        payload: Search query parameters.

    Returns:
        Dict[str, Any]: List of matching chunks with similarity scores.
    """
    user_id = _get_current_user_id(request)
    results = user_workspace_rag_manager.search_collection(
        user_id=user_id,
        rag_id=rag_id,
        query=payload.query,
        top_k=payload.top_k,
        min_score=payload.min_score
    )
    return {
        'status': 'ok',
        'user_id': user_id,
        'rag_id': rag_id,
        'query': payload.query,
        'results': results,
        'total': len(results)
    }


def init_router() -> APIRouter:
    """Initialize and return the user storage router with RAG sub-router.

    Returns:
        APIRouter: Configured user storage router.
    """
    combined_router = APIRouter()
    combined_router.include_router(router)
    combined_router.include_router(user_rags_router)
    return combined_router

