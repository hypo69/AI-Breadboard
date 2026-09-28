"""
Минимальная реализация роутера router_audio.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_audio/ping', tags=['router_audio'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router