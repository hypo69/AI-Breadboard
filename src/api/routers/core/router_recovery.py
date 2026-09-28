"""
Минимальная реализация роутера router_recovery.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_recovery/ping', tags=['router_recovery'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router