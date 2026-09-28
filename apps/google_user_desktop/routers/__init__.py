"""FastAPI роутер пакет приложения Google User Desktop."""
from .router import get_state, init_router, router

__all__ = ['router', 'init_router', 'get_state']
