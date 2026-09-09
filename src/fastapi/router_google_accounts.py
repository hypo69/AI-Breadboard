# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Workspace Accounts Pool Management Router
# =============================================================================
# Description:
#   Provides FastAPI endpoints for managing the Google Workspace account pool,
#   OAuth 2.0 / Service Account credentials, setting defaults, quota reset,
#   and testing connectivity for Gmail, Google Drive, Sheets, and Docs.
#
# File: router_google_accounts.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.ai.google_accounts_state import (
    _TOKENS_DIR,
    delete_google_account,
    get_account_info,
    list_google_accounts,
    load_account_credentials,
    mark_account_exhausted,
    reset_account_status,
    save_google_account,
    set_default_account,
)
from src.fastapi.router_auth import require_admin_user
from src.logger import logger

router = APIRouter(
    prefix="/api/admin/google-accounts",
    tags=["google-accounts"],
    dependencies=[Depends(require_admin_user)],
)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class GoogleAccountCreateRequest(BaseModel):
    account_name: str
    account_type: str = "oauth2"  # "oauth2" or "service_account"
    email: Optional[str] = None
    credentials_json: Optional[str] = None
    credentials_dict: Optional[Dict[str, Any]] = None
    set_as_default: bool = False


class GoogleAccountResponse(BaseModel):
    name: str
    type: str
    email: str
    is_default: bool
    status: str
    exhausted_at: Optional[str]
    last_run: Optional[str]
    has_token: bool
    credentials_configured: bool


class GoogleAccountsListResponse(BaseModel):
    accounts: List[GoogleAccountResponse]
    total: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=GoogleAccountsListResponse)
async def get_all_google_accounts() -> GoogleAccountsListResponse:
    """List all configured Google Workspace accounts with their statuses."""
    try:
        raw_accounts = list_google_accounts(skip_exhausted=False)
        result: List[GoogleAccountResponse] = []
        for acc in raw_accounts:
            name = acc.get("name", "")
            acc_type = acc.get("type", "oauth2")
            token_path = _TOKENS_DIR / f"{name}_token.json"
            has_token = token_path.exists()
            creds_file = acc.get("credentials_file", "")
            creds_configured = bool(creds_file and Path(creds_file).exists()) or bool(acc.get("credentials_raw"))

            result.append(
                GoogleAccountResponse(
                    name=name,
                    type=acc_type,
                    email=acc.get("email", ""),
                    is_default=bool(acc.get("is_default", False)),
                    status=acc.get("status", "active"),
                    exhausted_at=acc.get("exhausted_at"),
                    last_run=acc.get("last_run"),
                    has_token=has_token,
                    credentials_configured=creds_configured,
                )
            )
        return GoogleAccountsListResponse(accounts=result, total=len(result))
    except Exception as ex:
        logger.error(f"Error listing Google Workspace accounts: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/{name}", response_model=Dict[str, Any])
async def get_google_account_details(name: str) -> Dict[str, Any]:
    """Retrieve metadata and status for a specific Google account."""
    info = get_account_info(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    
    token_path = _TOKENS_DIR / f"{name}_token.json"
    info["has_token"] = token_path.exists()
    return info


@router.post("", response_model=Dict[str, Any])
async def create_or_update_google_account(
    req: GoogleAccountCreateRequest,
) -> Dict[str, Any]:
    """Create or update a Google Workspace account in the pool."""
    account_name = req.account_name.strip()
    if not account_name:
        raise HTTPException(status_code=400, detail="account_name is required")

    creds_input: Any = None
    if req.credentials_dict:
        creds_input = req.credentials_dict
    elif req.credentials_json:
        try:
            creds_input = json.loads(req.credentials_json)
        except Exception as ex:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON in credentials_json: {ex}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either credentials_json or credentials_dict must be provided",
        )

    ok = save_google_account(
        account_name=account_name,
        credentials_path_or_dict=creds_input,
        account_type=req.account_type,
        email=req.email,
        set_as_default=req.set_as_default,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save Google account")

    logger.info(f"Google account '{account_name}' ({req.account_type}) saved to pool")
    return {"status": "success", "message": f"Account '{account_name}' saved", "name": account_name}


@router.post("/upload", response_model=Dict[str, Any])
async def upload_google_account_credentials(
    account_name: str = Form(...),
    account_type: str = Form("oauth2"),
    email: Optional[str] = Form(None),
    set_as_default: bool = Form(False),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload credentials JSON file (OAuth client secrets or Service Account key)."""
    clean_name = account_name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="account_name is required")

    try:
        content = await file.read()
        creds_dict = json.loads(content.decode("utf-8"))
    except Exception as ex:
        raise HTTPException(
            status_code=400, detail=f"Uploaded file is not a valid JSON file: {ex}"
        )

    # Auto-detect type if possible
    detected_type = account_type
    if creds_dict.get("type") == "service_account":
        detected_type = "service_account"
        if not email and "client_email" in creds_dict:
            email = creds_dict["client_email"]
    elif "installed" in creds_dict or "web" in creds_dict:
        detected_type = "oauth2"

    ok = save_google_account(
        account_name=clean_name,
        credentials_path_or_dict=creds_dict,
        account_type=detected_type,
        email=email,
        set_as_default=set_as_default,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save uploaded account credentials")

    logger.info(f"Uploaded Google account '{clean_name}' ({detected_type}) credentials")
    return {
        "status": "success",
        "message": f"Credentials for '{clean_name}' successfully uploaded",
        "name": clean_name,
        "type": detected_type,
    }


@router.post("/{name}/default", response_model=Dict[str, Any])
async def set_google_account_default(name: str) -> Dict[str, Any]:
    """Set the specified account as default for Google Workspace actions."""
    ok = set_default_account(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    return {"status": "success", "message": f"Account '{name}' set as default"}


@router.post("/{name}/reset-status", response_model=Dict[str, Any])
async def reset_google_account_status(name: str) -> Dict[str, Any]:
    """Reset the exhaustion/error status for the specified Google account."""
    ok = reset_account_status(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    return {"status": "success", "message": f"Account '{name}' status reset to active"}


@router.delete("/{name}", response_model=Dict[str, Any])
async def delete_google_account_endpoint(name: str) -> Dict[str, Any]:
    """Delete account configuration and cached tokens from the pool."""
    ok = delete_google_account(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    return {"status": "success", "message": f"Account '{name}' deleted"}


@router.post("/{name}/test", response_model=Dict[str, Any])
async def test_google_account_connection(name: str) -> Dict[str, Any]:
    """Test credential loading and validity for the specified account."""
    info = get_account_info(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")

    try:
        creds = load_account_credentials(account_name=name)
        if not creds:
            return {
                "status": "warning",
                "valid": False,
                "message": f"Account '{name}' is configured, but active credentials / token could not be loaded. OAuth authorization or valid service account key required.",
                "account": info,
            }

        valid = getattr(creds, "valid", True)
        expired = getattr(creds, "expired", False)
        scopes = getattr(creds, "scopes", []) or []

        return {
            "status": "success" if valid else "warning",
            "valid": bool(valid),
            "expired": bool(expired),
            "scopes": list(scopes),
            "message": f"Credentials loaded successfully for '{name}'. Valid: {valid}, Expired: {expired}",
            "account": info,
        }
    except Exception as ex:
        logger.error(f"Error testing Google account '{name}': {ex}")
        return {
            "status": "error",
            "valid": False,
            "message": f"Authentication test failed: {ex}",
            "account": info,
        }


def init_router() -> APIRouter:
    """Factory initializer for Google Accounts FastAPI router."""
    return router
