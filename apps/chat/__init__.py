"""Пакет автономного приложения AI Chat для AI-Breadboard."""
from apps.chat.engine import ChatEngine
from apps.chat.router import init_router
__all__ = ['ChatEngine', 'init_router']