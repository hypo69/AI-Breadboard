"""
Минимальная реализация роутера router_admin.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_admin/ping', tags=['router_admin'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router

def init_skills_router() -> APIRouter:
    """Инициализация под‑роутера init_skills_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_skills_router/ping')
    async def sub_ping() -> dict:
        return {'status': 'ok'}
    return sub_router

def init_plugins_router() -> APIRouter:
    """Инициализация под‑роутера init_plugins_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_plugins_router/ping')
    async def sub_ping() -> dict:
        return {'status': 'ok'}
    return sub_router

def init_apps_router() -> APIRouter:
    """Инициализация под‑роутера init_apps_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_apps_router/ping')
    async def sub_ping() -> dict:
        return {'status': 'ok'}
    return sub_router

def init_user_storage_router() -> APIRouter:
    """Инициализация под‑роутера init_user_storage_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_user_storage_router/ping')
    async def sub_ping() -> dict:
        return {'status': 'ok'}
    return sub_router

def init_sync_router() -> APIRouter:
    """Инициализация под‑роутера init_sync_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_sync_router/ping')
    async def sub_ping() -> dict:
        return {'status': 'ok'}
    return sub_router