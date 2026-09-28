"""
Минимальная реализация роутера router_news.
"""
from fastapi import APIRouter
router = APIRouter()

@router.get('/router_news/ping', tags=['router_news'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router(*args, **kwargs) -> APIRouter:
    """Инициализация и возврат роутера."""
    return router