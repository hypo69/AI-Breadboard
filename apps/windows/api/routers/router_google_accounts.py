# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Router Google Accounts
# =============================================================================
# Description:
#   Роутер управления учетными записями Google (OAuth2 / Service Account) для Windows API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_google_accounts import init_router
#
#     router = init_router()
#
# File: router_google_accounts.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""Роутер управления учетными записями Google (OAuth2 / Service Account) для Windows API."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
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
from apps.windows.api.auth import require_admin_user
from logger import logger

router = APIRouter(
    prefix="/api/admin/google-accounts",
    tags=["google-accounts"],
    dependencies=[Depends(require_admin_user)],
)


class GoogleAccountCreateRequest(BaseModel):
    """Модель запроса добавления Google аккаунта."""
    account_name: str
    account_type: str = "oauth2"
    email: Optional[str] = None
    credentials_json: Optional[str] = None
    credentials_dict: Optional[Dict[str, Any]] = None
    set_as_default: bool = False


class GoogleAccountResponse(BaseModel):
    """Модель ответа информации об аккаунте."""
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
    """Модель ответа списка Google аккаунтов."""
    accounts: List[GoogleAccountResponse]
    total: int


class GoogleSheetValuesRequest(BaseModel):
    """Запрос чтения значений из Google Sheets."""
    spreadsheet_id: str
    range_name: str
    account_name: Optional[str] = None


@router.get("", response_model=GoogleAccountsListResponse)
async def get_all_google_accounts() -> GoogleAccountsListResponse:
    """Список всех настроенных Google аккаунтов."""
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

            result.append(GoogleAccountResponse(
                name=name,
                type=acc_type,
                email=acc.get("email", ""),
                is_default=bool(acc.get("is_default", False)),
                status=acc.get("status", "active"),
                exhausted_at=acc.get("exhausted_at"),
                last_run=acc.get("last_run"),
                has_token=has_token,
                credentials_configured=creds_configured,
            ))
        return GoogleAccountsListResponse(accounts=result, total=len(result))
    except Exception as exc:
        logger.error(f"[router_google_accounts] Ошибка получения списка аккаунтов: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", response_model=Dict[str, Any])
async def create_google_account_endpoint(req: GoogleAccountCreateRequest) -> Dict[str, Any]:
    """Регистрация нового Google аккаунта."""
    try:
        creds_raw = req.credentials_json or (json.dumps(req.credentials_dict) if req.credentials_dict else None)
        save_google_account(
            name=req.account_name,
            account_type=req.account_type,
            email=req.email or "",
            credentials_raw=creds_raw,
            is_default=req.set_as_default,
        )
        return {"status": "success", "message": f"Аккаунт '{req.account_name}' успешно зарегистрирован"}
    except Exception as exc:
        logger.error(f"[router_google_accounts] Ошибка создания аккаунта: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{account_name}", response_model=Dict[str, Any])
async def delete_google_account_endpoint(account_name: str) -> Dict[str, Any]:
    """Удаление Google аккаунта."""
    try:
        deleted = delete_google_account(account_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Аккаунт '{account_name}' не найден")
        return {"status": "success", "message": f"Аккаунт '{account_name}' успешно удален"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[router_google_accounts] Ошибка удаления аккаунта: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{account_name}/set-default", response_model=Dict[str, Any])
async def set_default_google_account_endpoint(account_name: str) -> Dict[str, Any]:
    """Назначение Google аккаунта по умолчанию."""
    try:
        ok = set_default_account(account_name)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Аккаунт '{account_name}' не найден")
        return {"status": "success", "message": f"Аккаунт '{account_name}' установлен по умолчанию"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[router_google_accounts] Ошибка назначения аккаунта по умолчанию: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


def init_router() -> APIRouter:
    """Инициализация роутера Google Accounts."""
    return router


__all__ = [
    "router",
    "init_router",
    "GoogleAccountCreateRequest",
    "GoogleAccountResponse",
    "GoogleAccountsListResponse",
    "GoogleSheetValuesRequest",
]
