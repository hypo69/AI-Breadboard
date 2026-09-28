"""Helpdesk support management application and live operator desk."""
from apps.helpdesk.routers.router import init_router, router
__all__ = ['router', 'init_router']