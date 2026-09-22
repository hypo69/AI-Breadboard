"""Automatically discovered API routers."""

from __future__ import annotations

from pathlib import Path

from logger import logger

__root__ = Path(__file__).parent.parent.parent


def auto_discover_routers(app):
    """Automatically discover and register all routers in src/api/.
    
    This function scans the src/api/ directory for files named router_*.py
    and automatically registers their router instances with the FastAPI app.
    
    Args:
        app: FastAPI application instance to register routers with.
    """
    import importlib
    import pkgutil
    
    api_dir = __root__ / 'src' / 'api'
    
    if not api_dir.exists():
        logger.warning(f"API directory not found: {api_dir}")
        return
    
    for module_info in pkgutil.iter_modules([str(api_dir)]):
        module_name = module_info.name
        if module_name.startswith('router_') and module_name not in ('router_version',):
            try:
                module = importlib.import_module(f'src.api.{module_name}')
                # Try to get router instance
                if hasattr(module, 'router'):
                    app.include_router(module.router)
                    logger.debug(f"Auto-registered router: {module_name}")
                # Try to get init function
                elif hasattr(module, 'init_router'):
                    router = module.init_router()
                    app.include_router(router)
                    logger.debug(f"Auto-registered router via init_router: {module_name}")
            except Exception as e:
                logger.warning(f"Failed to load router module {module_name}: {e}")
