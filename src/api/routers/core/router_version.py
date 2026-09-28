"""
Минимальная реализация роутера router_version.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_version/ping', tags=['router_version'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router