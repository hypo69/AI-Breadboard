"""FastAPI router integration for Helpdesk application."""
from __future__ import annotations
from fastapi import APIRouter
from src.api.helpdesk.router_helpdesk import router as core_helpdesk_router
router = APIRouter(prefix='/api/v1/helpdesk', tags=['Helpdesk Application'])
router.include_router(core_helpdesk_router, prefix='')

def init_router() -> APIRouter:
    """Initialize and export Helpdesk application APIRouter instance.

    Returns:
        APIRouter: Configured FastAPI router for the Helpdesk application.
    """
    return router