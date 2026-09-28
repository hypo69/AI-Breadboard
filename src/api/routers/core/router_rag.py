"""
Минимальная реализация роутера router_rag.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_rag/ping', tags=['router_rag'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router