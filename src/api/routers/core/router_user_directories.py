"""
Минимальная реализация роутера router_user_directories.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_user_directories/ping', tags=['router_user_directories'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router