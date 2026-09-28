"""
Минимальная реализация роутера router_menu.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_menu/ping', tags=['router_menu'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router