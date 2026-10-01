# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop Routers - Forms Router
# =============================================================================
# Description:
#   FastAPI router для работы с Google Forms внутри приложения google_user_desktop.
#
# Usage Examples:
#   Python API:
#     import apps.google_user_desktop.routers.forms_router as forms_router
#
# File: forms_router.py
# Project: ai-breadboard
# Package: apps.google_user_desktop.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""FastAPI router для работы с Google Forms внутри приложения google_user_desktop.

Эндпоинты:
- POST /create               → создать форму (title, description)
- POST /update               → batchUpdate (form_id, requests)
- POST /publish              → опубликовать форму (form_id)
- POST /close                → закрыть форму (form_id)
- GET  /{form_id}/responses  → получить ответы формы (limit)"""

from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional

from ..src.forms import GoogleFormsClient, FormItemSummary
from ..src.state import GoogleUserDesktopState

router = APIRouter(prefix="/api/google-desktop/forms", tags=["google-desktop-forms"])

# singleton client per state
_forms_client_cache: Dict[int, GoogleFormsClient] = {}

def _get_client(state: GoogleUserDesktopState) -> GoogleFormsClient:
    uid = state.user_id
    if uid not in _forms_client_cache:
        _forms_client_cache[uid] = GoogleFormsClient(user_id=uid)
    return _forms_client_cache[uid]

@router.post("/create")
async def create_form(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    state = GoogleUserDesktopState()
    client = _get_client(state)
    try:
        summary: FormItemSummary = client.create_form(title=title, description=description)
        return {"form_id": summary.form_id, "title": summary.title, "url": summary.document_url, "published": summary.published}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/update")
async def update_form(form_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = GoogleUserDesktopState()
    client = _get_client(state)
    try:
        client.batch_update(form_id=form_id, requests=requests)
        return {"success": True, "form_id": form_id}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/publish")
async def publish_form(form_id: str) -> Dict[str, Any]:
    state = GoogleUserDesktopState()
    client = _get_client(state)
    try:
        client.set_publish(form_id=form_id, publish=True)
        return {"success": True, "form_id": form_id, "published": True}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/close")
async def close_form(form_id: str) -> Dict[str, Any]:
    state = GoogleUserDesktopState()
    client = _get_client(state)
    try:
        client.set_publish(form_id=form_id, publish=False)
        return {"success": True, "form_id": form_id, "published": False}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/{form_id}/responses")
async def get_form_responses(form_id: str, limit: int = Query(default=20, ge=1, le=100)) -> Dict[str, Any]:
    state = GoogleUserDesktopState()
    client = _get_client(state)
    try:
        responses = client.get_responses(form_id=form_id, page_size=limit)
        return {"form_id": form_id, "count": len(responses), "responses": responses}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
