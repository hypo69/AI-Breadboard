"""
Минимальная реализация роутера router_mcp.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_mcp/ping', tags=['router_mcp'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router

def init_admin_mcp_router() -> APIRouter:
    """Инициализировать и вернуть админский MCP роутер."""
    return router

def init_user_mcp_router() -> APIRouter:
    """Инициализировать и вернуть пользовательский MCP роутер."""
    return router