"""
Минимальная реализация роутера router_tts.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_tts/ping', tags=['router_tts'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router