"""
Минимальная реализация роутера router_keys.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_keys/ping', tags=['router_keys'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router