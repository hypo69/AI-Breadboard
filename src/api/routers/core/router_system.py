"""
Минимальная реализация роутера router_system.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_system/ping', tags=['router_system'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router(*args, **kwargs) -> APIRouter:
    """Инициализация и возврат роутера."""
    return router