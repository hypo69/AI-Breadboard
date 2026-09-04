# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API key management and quota tracking router
# =============================================================================
# Description:
#   Provides FastAPI endpoints for managing Gemini API keys, tracking quota status,
#   handling key rotation, and performing CRUD key operations.
#
# File: router_keys.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.logger import logger

router = APIRouter(prefix='/api/keys', tags=['keys'])

_SECRETS_FILE = Path(__file__).parent.parent / 'ai' / 'gemini' / 'secrets.json'
_KEYS_FILE = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
_DAY_SECONDS = 86400

# ============================================================================
# Pydantic Models
# ============================================================================

class KeyEntry(BaseModel):
    api_key: str
    status: str = 'active'
    last_run: Optional[str] = None
    exhausted_at: Optional[str] = None

class KeyCreateRequest(BaseModel):
    name: str
    api_key: str
    status: str = 'active'

class KeyUpdateRequest(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None

class KeyListResponse(BaseModel):
    keys: List[Dict]
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

def _load_secrets() -> Dict[str, str]:
    """Load all keys from secrets.json (email -> api_key)."""
    if _SECRETS_FILE.exists():
        try:
            return json.loads(_SECRETS_FILE.read_text(encoding='utf-8'))
        except Exception as ex:
            logger.error('Failed to load secrets.json', ex)
            raise HTTPException(status_code=500, detail='Failed to load secrets.json')
    return {}

def _save_secrets(data: Dict[str, str]) -> None:
    """Save keys to secrets.json."""
    try:
        _SECRETS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
    except Exception as ex:
        logger.error('Failed to save secrets.json', ex)
        raise HTTPException(status_code=500, detail='Failed to save secrets.json')

def _load_keys_data() -> Dict:
    """Load status data from gemini_keys.json."""
    if _KEYS_FILE.exists():
        try:
            return json.loads(_KEYS_FILE.read_text(encoding='utf-8'))
        except Exception as ex:
            logger.error('Failed to load keys data', ex)
            raise HTTPException(status_code=500, detail='Failed to load keys data')
    return {}

def _save_keys_data(data: Dict) -> None:
    """Save status data to gemini_keys.json."""
    try:
        _KEYS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as ex:
        logger.error('Failed to save keys data', ex)
        raise HTTPException(status_code=500, detail='Failed to save keys data')

def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def _iso_to_ts(iso: str) -> float:
    """Convert ISO string to timestamp."""
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0

def _check_exhaustion(name: str) -> tuple[bool, Optional[int]]:
    """Check if key is exhausted and return seconds until reset."""
    keys_data = _load_keys_data()
    entry = keys_data.get(name, {})
    
    exhausted_at = entry.get('exhausted_at')
    if not exhausted_at:
        return False, None
    
    elapsed = _now_ts() - _iso_to_ts(exhausted_at)
    remaining = _DAY_SECONDS - elapsed
    
    if remaining > 0:
        return True, int(remaining)
    return False, None

def _now_ts() -> float:
    """Return current Unix timestamp."""
    return datetime.now(timezone.utc).timestamp()

def _mask_key(api_key: str) -> str:
    """Mask API key for display: keep first 8 and last 4 chars."""
    if len(api_key) < 12:
        return '*' * len(api_key)
    return f"{api_key[:8]}...{api_key[-4:]}"

# ============================================================================
# API Endpoints
# ============================================================================

@router.get('', response_model=KeyListResponse)
async def list_keys() -> KeyListResponse:
    """List all API keys from secrets.json with masked values and status."""
    secrets = _load_secrets()
    keys_data = _load_keys_data()
    keys = []
    
    for name, api_key in secrets.items():
        exhausted, reset_in = _check_exhaustion(name)
        
        # Get status from keys_data or default to 'active'
        entry = keys_data.get(name, {})
        status = entry.get('status', 'active')
        
        keys.append({
            'name': name,
            'api_key_masked': _mask_key(api_key),
            'status': status,
            'last_run': entry.get('last_run'),
            'exhausted_at': entry.get('exhausted_at'),
            'exhausted': exhausted,
            'reset_in_seconds': reset_in
        })
    
    return KeyListResponse(keys=keys, total=len(keys))

@router.get('/{key_name}', response_model=KeyStatusResponse)
async def get_key_status(key_name: str) -> KeyStatusResponse:
    """Get detailed status for a specific key from secrets.json."""
    secrets = _load_secrets()
    keys_data = _load_keys_data()
    
    if key_name not in secrets:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found in secrets.json')
    
    entry = keys_data.get(key_name, {})
    exhausted, reset_in = _check_exhaustion(key_name)
    
    return KeyStatusResponse(
        name=key_name,
        status=entry.get('status', 'active'),
        last_run=entry.get('last_run'),
        exhausted_at=entry.get('exhausted_at'),
        exhausted=exhausted,
        reset_in_seconds=reset_in
    )

@router.post('', status_code=201)
async def create_key(request: KeyCreateRequest) -> Dict[str, str]:
    """Add a new API key to secrets.json."""
    if not request.name or not request.api_key:
        raise HTTPException(status_code=400, detail='Name and API key are required')
    
    secrets = _load_secrets()
    keys_data = _load_keys_data()
    
    if request.name in secrets:
        raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists in secrets.json')
    
    # Add to secrets.json
    secrets[request.name] = request.api_key
    _save_secrets(secrets)
    
    # Initialize status in keys_data
    keys_data[request.name] = {
        'status': request.status,
        'last_run': None,
        'exhausted_at': None
    }
    _save_keys_data(keys_data)
    
    logger.info(f'Added new key: {request.name}')
    
    return {'message': f'Key "{request.name}" added successfully'}

@router.delete('/{key_name}')
async def delete_key(key_name: str) -> Dict[str, str]:
    """Delete an API key from secrets.json."""
    secrets = _load_secrets()
    keys_data = _load_keys_data()
    
    if key_name not in secrets:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found in secrets.json')
    
    # Delete from secrets.json
    del secrets[key_name]
    _save_secrets(secrets)
    
    # Delete from keys_data
    if key_name in keys_data:
        del keys_data[key_name]
        _save_keys_data(keys_data)
    
    logger.info(f'Deleted key: {key_name}')
    
    return {'message': f'Key "{key_name}" deleted successfully'}

@router.patch('/{key_name}')
async def update_key(key_name: str, request: KeyUpdateRequest) -> Dict[str, str]:
    """Update key status or name in secrets.json and keys_data."""
    secrets = _load_secrets()
    keys_data = _load_keys_data()
    
    if key_name not in secrets:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found in secrets.json')
    
    # Update status
    if request.status:
        if request.status not in ('active', 'disabled'):
            raise HTTPException(status_code=400, detail='Status must be "active" or "disabled"')
        keys_data[key_name]['status'] = request.status
    
    # Rename key
    if request.name and request.name != key_name:
        if request.name in secrets:
            raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists')
        
        # Rename in secrets.json
        secrets[request.name] = secrets[key_name]
        del secrets[key_name]
        _save_secrets(secrets)
        
        # Rename in keys_data
        keys_data[request.name] = keys_data[key_name]
        del keys_data[key_name]
    
    _save_keys_data(keys_data)
    logger.info(f'Updated key: {key_name}')
    
    return {'message': f'Key "{key_name}" updated successfully'}

@router.post('/reset-all')
async def reset_all_quotas() -> Dict[str, str]:
    """Reset daily quota exhaustion for all API keys."""
    keys_data = _load_keys_data()
    reset_count = 0
    
    for name, info in keys_data.items():
        if 'exhausted_at' in info:
            del info['exhausted_at']
            reset_count += 1
            
    if reset_count > 0:
        _save_keys_data(keys_data)
        logger.info(f'Reset quota for {reset_count} keys')
        return {'message': f'Successfully сброшены квоты для {reset_count} ключей'}
        
    return {'message': 'Нет заблокированных ключей для сброса'}

@router.post('/{key_name}/reset-quota')
async def reset_quota(key_name: str) -> Dict[str, str]:
    """Reset daily quota exhaustion for a key."""
    keys_data = _load_keys_data()
    
    if key_name not in keys_data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')
    
    if 'exhausted_at' in keys_data[key_name]:
        del keys_data[key_name]['exhausted_at']
        _save_keys_data(keys_data)
        logger.info(f'Reset quota for key: {key_name}')
        return {'message': f'Quota reset for key "{key_name}"'}
    
    return {'message': f'Key "{key_name}" is not exhausted'}

# ============================================================================
# Initialization Function
# ============================================================================

def init_router() -> APIRouter:
    """Initialize the keys router."""
    return router
