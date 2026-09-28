"""
Минимальная реализация роутера router_diagnostics.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_diagnostics/ping', tags=['router_diagnostics'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router