# -*- coding: utf-8 -*-
# =============================================================================
# FastAPI application entry point for AI-Breadboard
# =============================================================================

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from src.app import (
    create_app,
    register_routers,
    register_pages,
    register_config_api,
    AppState,
    create_metrics,
    WSHub,
)
from src.app.server_config import run_server
from src.app.versioning import check_updates, prompt_and_perform_update
from src.logger import logger

# Create FastAPI app
app = create_app()

# Initialize application state
state = AppState()

# Initialize services
state.metrics = create_metrics(started_at=state.started_at)
state.ws_hub = WSHub()

# Store state in app for access from routes
app.state.app_state = state
app.state.metrics = state.metrics
app.state.ws_hub = state.ws_hub

# Initialize AI models (will be set during startup)
try:
    from src.ai.unified_chat_model import UnifiedChatModel
    state.chat_model = UnifiedChatModel()
    state.narrator_model = UnifiedChatModel()
    app.state.chat_model = state.chat_model
    app.state.narrator_model = state.narrator_model
except Exception as e:
    logger.warning(f"Failed to initialize AI models: {e}")
    state.chat_model = None
    state.narrator_model = None

# Register routers with state
register_routers(app, state)

# Register pages and configuration endpoints
register_pages(app)
register_config_api(app)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    from src.utils.scheduler import scheduler
    await scheduler.start()
    
    # Start WebSocket heartbeat
    if state.ws_hub:
        await state.ws_hub.start_heartbeat()
    
    try:
        result = check_updates()
        if result.get("is_update_available"):
            logger.warning(f"Update available: {result.get('remote_version')}")
        else:
            logger.info(f"Application is up to date: version {result.get('current_version')}")
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    # Stop WebSocket hub
    if state.ws_hub:
        await state.ws_hub.stop()
    
    from src.utils.scheduler import scheduler
    await scheduler.stop()


if __name__ == '__main__':
    import sys
    
    branch = str(os.getenv('GIT_BRANCH', 'main'))
    
    if '--check-update' in sys.argv[1:]:
        prompt_and_perform_update(branch=branch)
        sys.exit(0)
    
    if '--check-update-and-run' in sys.argv[1:]:
        prompt_and_perform_update(branch=branch)
    
    # Default startup: perform version check
    try:
        prompt_and_perform_update(branch=branch)
    except Exception:
        pass
    
    # Start server
    run_server(app)
