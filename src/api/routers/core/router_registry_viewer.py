"""
Минимальная реализация роутера router_registry_viewer.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_registry_viewer/ping', tags=['router_registry_viewer'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router