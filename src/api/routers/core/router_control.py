"""router_control

Минимальная реализация роутера control.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_control/ping', tags=['router_control'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера control."""
    return router