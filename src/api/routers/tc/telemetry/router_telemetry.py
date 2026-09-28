from fastapi import APIRouter

router = APIRouter()

def init_router() -> APIRouter:
    """Экспортировать роутер телеметрии."""
    return router

__all__ = ["init_router", "router"]
