"""
Минимальная реализация роутера router_ifttt.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_ifttt/ping', tags=['router_ifttt'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router