# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API key management and quota tracking router
# =============================================================================
# Description:
#   Provides FastAPI endpoints for managing Gemini API keys, tracking quota status,
#   handling key rotation, and performing CRUD key operations using
#   src/secrets/gemini_keys.json storage.
#
# File: router_keys.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.logger import logger
from src.fastapi.router_auth import require_admin_user
from src.ai.gemini.gemini_api_key_state import (
    _DAY_SECONDS,
    _iso_to_ts,
    _load_keys_file,
    _now_iso,
    _now_ts,
    _save_keys_file,
    delete_api_key,
    get_status,
    reset_all_quotas as state_reset_all_quotas,
    reset_quota as state_reset_quota,
    save_api_key,
)

router = APIRouter(prefix='/api/keys', tags=['keys'], dependencies=[Depends(require_admin_user)])

# ============================================================================
# Pydantic Models
# ============================================================================

class KeyEntry(BaseModel):
    value: str
    status: str = 'active'
    last_run: Optional[str] = None
    exhausted_at: Optional[str] = None

class KeyCreateRequest(BaseModel):
    name: str
    value: Optional[str] = None
    api_key: Optional[str] = None
    status: str = 'active'

class KeyUpdateRequest(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None

class KeyListResponse(BaseModel):
    keys: List[Dict[str, Any]]
    total: int

class KeyStatusResponse(BaseModel):
    name: str
    status: str
    last_run: Optional[str]
    exhausted_at: Optional[str]
    exhausted: bool
    reset_in_seconds: Optional[int]

# ============================================================================
# Internal Helper Functions
# ============================================================================

def _check_exhaustion(name: str) -> tuple[bool, Optional[int]]:
    """Check if key is exhausted and return seconds until reset."""
    keys_data = _load_keys_file()
    entry = keys_data.get(name, {})

    status = entry.get('status', 'active')
    exhausted_at = entry.get('exhausted_at') or entry.get('last_run')

    if status != 'exhausted' and not entry.get('exhausted_at'):
        return False, None

    if not exhausted_at:
        return False, None

    ref_ts = _iso_to_ts(exhausted_at)
    if ref_ts <= 0:
        return False, None

    elapsed = _now_ts() - ref_ts
    remaining = _DAY_SECONDS - elapsed

    if remaining > 0:
        return True, int(remaining)
    return False, None

def _mask_key(key_val: str) -> str:
    """Mask API key for display: keep first 8 and last 4 chars."""
    if len(key_val) < 12:
        return '*' * len(key_val)
    return f"{key_val[:8]}...{key_val[-4:]}"

# ============================================================================
# API Endpoints
# ============================================================================

@router.get('', response_model=KeyListResponse)
async def list_keys() -> KeyListResponse:
    """List all API keys with masked values and runtime status."""
    keys_data = _load_keys_file()
    keys: List[Dict[str, Any]] = []

    for name, data in keys_data.items():
        exhausted, reset_in = _check_exhaustion(name)
        val = data.get('value') or data.get('api_key') or ''
        keys.append({
            'name': name,
            'api_key_masked': _mask_key(val),
            'value_masked': _mask_key(val),
            'status': data.get('status', 'active'),
            'last_run': data.get('last_run') or None,
            'exhausted_at': data.get('exhausted_at') or None,
            'exhausted': exhausted,
            'reset_in_seconds': reset_in,
        })

    return KeyListResponse(keys=keys, total=len(keys))

@router.get('/{key_name}', response_model=KeyStatusResponse)
async def get_key_status(key_name: str) -> KeyStatusResponse:
    """Get detailed status for a specific key."""
    keys_data = _load_keys_file()

    if key_name not in keys_data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')

    entry = keys_data[key_name]
    exhausted, reset_in = _check_exhaustion(key_name)

    return KeyStatusResponse(
        name=key_name,
        status=entry.get('status', 'active'),
        last_run=entry.get('last_run') or None,
        exhausted_at=entry.get('exhausted_at') or None,
        exhausted=exhausted,
        reset_in_seconds=reset_in,
    )

@router.post('', status_code=201)
async def create_key(request: KeyCreateRequest) -> Dict[str, str]:
    """Add a new API key to gemini_keys.json."""
    raw_key = request.value or request.api_key
    if not request.name or not raw_key:
        raise HTTPException(status_code=400, detail='Name and key value are required')

    keys_data = _load_keys_file()
    if request.name in keys_data:
        raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists')

    success = save_api_key(request.name, raw_key, status=request.status)
    if not success:
        raise HTTPException(status_code=500, detail=f'Failed to save key "{request.name}"')

    logger.info(f'Added new key: {request.name}')
    return {'message': f'Key "{request.name}" added successfully'}

@router.delete('/{key_name}')
async def delete_key_endpoint(key_name: str) -> Dict[str, str]:
    """Delete an API key from gemini_keys.json."""
    keys_data = _load_keys_file()
    if key_name not in keys_data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')

    delete_api_key(key_name)
    logger.info(f'Deleted key: {key_name}')
    return {'message': f'Key "{key_name}" deleted successfully'}

@router.patch('/{key_name}')
async def update_key(key_name: str, request: KeyUpdateRequest) -> Dict[str, str]:
    """Update key status, value, or rename key."""
    keys_data = _load_keys_file()
    if key_name not in keys_data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')

    entry = keys_data[key_name]
    target_val = request.value or entry.get('value', '')
    target_status = request.status or entry.get('status', 'active')

    if request.status and request.status not in ('active', 'exhausted', 'disabled'):
        raise HTTPException(status_code=400, detail='Status must be "active", "exhausted", or "disabled"')

    # Rename key if name changed
    if request.name and request.name != key_name:
        if request.name in keys_data:
            raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists')
        delete_api_key(key_name)
        save_api_key(request.name, target_val, status=target_status)
    else:
        save_api_key(key_name, target_val, status=target_status)

    logger.info(f'Updated key: {key_name}')
    return {'message': f'Key "{key_name}" updated successfully'}

@router.post('/reset-all')
async def reset_all_quotas() -> Dict[str, str]:
    """Reset daily quota exhaustion for all API keys."""
    reset_count = state_reset_all_quotas()
    if reset_count > 0:
        logger.info(f'Reset quota for {reset_count} keys')
        return {'message': f'Successfully reset quota for {reset_count} keys'}
    return {'message': 'No exhausted keys to reset'}

@router.post('/{key_name}/reset-quota')
async def reset_quota(key_name: str) -> Dict[str, str]:
    """Reset daily quota exhaustion for a key."""
    keys_data = _load_keys_file()
    if key_name not in keys_data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')

    success = state_reset_quota(key_name)
    if success:
        logger.info(f'Reset quota for key: {key_name}')
        return {'message': f'Quota reset for key "{key_name}"'}
    return {'message': f'Key "{key_name}" is not exhausted'}

# ============================================================================
# Initialization Function
# ============================================================================

def init_router() -> APIRouter:
    """Initialize the keys router."""
    return router
