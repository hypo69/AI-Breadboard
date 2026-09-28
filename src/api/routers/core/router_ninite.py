"""
Минимальная реализация роутера router_ninite.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_ninite/ping', tags=['router_ninite'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router