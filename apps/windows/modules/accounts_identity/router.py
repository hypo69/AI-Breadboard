# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Router
# =============================================================================
# Description:
#   FastAPI роутер для REST API каталога Accounts & Identity и Windows Identity Graph.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.router import router as identity_router
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 01:46:00
# =============================================================================

"""FastAPI роутер для Accounts & Identity."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from apps.windows.modules.accounts_identity.models import (
    AccountDetails,
    AuditEventItem,
    DomainInfo,
    GroupDetails,
    IdentityGraph,
    OperationCatalogItem,
    PasswordPolicy,
    Principal,
    ProfileDetails,
    SessionDetails,
    TokenDetails,
)
from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

router = APIRouter(prefix="/identity", tags=["Accounts & Identity"])
_service = get_accounts_identity_service()


class UserCreateRequest(BaseModel):
    """Модель создания пользователя."""
    username: str
    password: Optional[str] = None
    full_name: str = ""
    description: str = ""


class GroupMemberRequest(BaseModel):
    """Модель управления участниками группы."""
    username: str


@router.get("/catalog", response_model=List[OperationCatalogItem])
async def get_operations_catalog(query: Optional[str] = Query(None, description="Поисковый запрос")) -> List[OperationCatalogItem]:
    """Возвращает каталог всех ~180 операций Accounts & Identity."""
    return _service.get_catalog(query=query)


@router.get("/current", response_model=TokenDetails)
async def get_current_user_context() -> TokenDetails:
    """Возвращает контекст безопасности и маркер доступа текущего процесса."""
    return _service.get_current_identity()


@router.get("/users", response_model=List[AccountDetails])
async def get_all_users() -> List[AccountDetails]:
    """Перечисляет все локальные учетные записи пользователей SAM."""
    return _service.list_users()


@router.get("/users/{username_or_sid}", response_model=AccountDetails)
async def get_user_by_name_or_sid(username_or_sid: str) -> AccountDetails:
    """Получает детальные параметры пользователя по имени или SID."""
    user = _service.get_user(username_or_sid)
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь '{username_or_sid}' не найден")
    return user


@router.post("/users")
async def create_user(req: UserCreateRequest) -> Dict[str, Any]:
    """Создает нового локального пользователя."""
    success = _service.create_user(
        name=req.username,
        password=req.password,
        full_name=req.full_name,
        description=req.description,
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось создать пользователя '{req.username}'")
    return {"status": "ok", "message": f"Пользователь '{req.username}' успешно создан"}


@router.delete("/users/{username}")
async def delete_user(username: str) -> Dict[str, Any]:
    """Удаляет локального пользователя."""
    success = _service.delete_user(username)
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось удалить пользователя '{username}'")
    return {"status": "ok", "message": f"Пользователь '{username}' удален"}


@router.get("/groups", response_model=List[GroupDetails])
async def get_all_groups() -> List[GroupDetails]:
    """Перечисляет все локальные группы безопасности."""
    return _service.list_groups()


@router.get("/groups/{group_name}", response_model=GroupDetails)
async def get_group_details(group_name: str) -> GroupDetails:
    """Получает сведения о группе и ее участниках."""
    group = _service.get_group(group_name)
    if not group:
        raise HTTPException(status_code=404, detail=f"Группа '{group_name}' не найдена")
    return group


@router.post("/groups/{group_name}/members")
async def add_member_to_group(group_name: str, req: GroupMemberRequest) -> Dict[str, Any]:
    """Добавляет пользователя в группу."""
    success = _service.add_user_to_group(group_name, req.username)
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось добавить '{req.username}' в группу '{group_name}'")
    return {"status": "ok", "message": f"'{req.username}' добавлен в группу '{group_name}'"}


@router.delete("/groups/{group_name}/members/{username}")
async def remove_member_from_group(group_name: str, username: str) -> Dict[str, Any]:
    """Исключает пользователя из группы."""
    success = _service.remove_user_from_group(group_name, username)
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось удалить '{username}' из группы '{group_name}'")
    return {"status": "ok", "message": f"'{username}' удален из группы '{group_name}'"}


@router.get("/auth/policies", response_model=PasswordPolicy)
async def get_password_policy() -> PasswordPolicy:
    """Возвращает глобальную политику паролей и блокировок."""
    return _service.get_password_policy()


@router.get("/sessions", response_model=List[SessionDetails])
async def get_all_sessions() -> List[SessionDetails]:
    """Перечисляет активные консольные и терминальные сеансы."""
    return _service.list_sessions()


@router.get("/profiles", response_model=List[ProfileDetails])
async def get_all_profiles() -> List[ProfileDetails]:
    """Перечисляет зарегистрированные профили пользователей."""
    return _service.list_profiles()


@router.get("/domain-info", response_model=DomainInfo)
async def get_domain_info() -> DomainInfo:
    """Возвращает сведения о домене и Entra ID."""
    return _service.get_domain_info()


@router.get("/resolve/{identifier}")
async def resolve_identity(identifier: str) -> Dict[str, Any]:
    """Разрешает SID или имя в субъект безопасности."""
    return _service.resolve(identifier)


@router.get("/explain/{identifier}", response_model=Principal)
async def explain_identity(identifier: str) -> Principal:
    """Формирует полное досье Principal (пользователь, группы, LSA-права, сессии, процессы, профиль, аудит)."""
    return _service.explain(identifier)


@router.get("/who-is-admin")
async def who_is_admin() -> List[Dict[str, Any]]:
    """Находит всех администраторов системы (включая непрямое вложенное членство)."""
    return _service.who_is_admin()


@router.get("/who-can-logon-as-service")
async def who_can_logon_as_service() -> List[str]:
    """Возвращает учетные записи с правом SeServiceLogonRight."""
    return _service.who_can_logon_as_service()


@router.get("/who-can-rdp")
async def who_can_rdp() -> List[str]:
    """Возвращает учетные записи с доступом к RDP."""
    return _service.who_can_rdp()


@router.get("/orphaned-sids")
async def get_orphaned_sids() -> List[Dict[str, Any]]:
    """Находит осиротевшие SID в системе."""
    return _service.find_orphaned_sids()


@router.get("/orphaned-profiles")
async def get_orphaned_profiles() -> List[Dict[str, Any]]:
    """Находит осиротевшие профили без пользователей."""
    return _service.find_orphaned_profiles()


@router.get("/explain-pid/{pid}")
async def explain_pid(pid: int) -> Dict[str, Any]:
    """Исследует контекст безопасности процесса: PID -> Token -> SID -> Account -> Groups -> Privileges -> Integrity -> Elevation."""
    return _service.explain_pid(pid)


@router.get("/graph", response_model=IdentityGraph)
async def get_identity_graph() -> IdentityGraph:
    """Строит полный Windows Identity Graph."""
    return _service.get_identity_graph()


@router.get("/audit", response_model=List[AuditEventItem])
async def get_security_audit_events(
    limit: int = Query(50, ge=1, le=200, description="Лимит событий"),
    event_id: Optional[int] = Query(None, description="Фильтр по Event ID (например, 4720, 4624)"),
) -> List[AuditEventItem]:
    """Возвращает журнал событий безопасности Windows (Security Event Log)."""
    return _service.get_audit_events(limit=limit, event_id=event_id)


@router.get("/audit/user/{username}", response_model=List[AuditEventItem])
async def get_user_security_audit_events(
    username: str,
    limit: int = Query(20, ge=1, le=100, description="Лимит событий"),
) -> List[AuditEventItem]:
    """Возвращает историю событий безопасности для указанного пользователя."""
    return _service.get_user_audit_events(username=username, limit=limit)

