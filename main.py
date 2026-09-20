# -*- coding: utf-8 -*-
# =============================================================================
# FastAPI application entry point for AI-Breadboard
# =============================================================================

import os
import sys
from pathlib import Path

# =============================================================================
# Патч для подавления WinError 10054 в asyncio на Windows (Proactor Event Loop)
# =============================================================================
# Причина: Когда браузер/клиент принудительно разрывает TCP-соединение (RST-пакет
# при смене страницы, закрытии вкладки или перезагрузке WebSocket), ProactorEventLoop
# в Windows пытается выполнить shutdown() на уже сброшенном сокете.
# Это вызывает исключение ConnectionResetError: [WinError 10054] внутри системного
# коллбэка _ProactorBasePipeTransport._call_connection_lost(), засоряя логи консоли.
# Патч безопасно перехватывает и подавляет именно WinError 10054, не влияя на другие ошибки.
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _patched_call_connection_lost(self, exc=None):
            try:
                _orig_call_connection_lost(self, exc)
            except ConnectionResetError:
                pass
            except OSError as err:
                # 10054 = WSAECONNRESET (Удаленный хост принудительно разорвал существующее подключение)
                if getattr(err, "winerror", None) != 10054:
                    raise

        _ProactorBasePipeTransport._call_connection_lost = _patched_call_connection_lost
    except Exception:
        pass

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
    from src.ai import UnifiedChatModel
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

    # Load system and user plugins
    try:
        from plugins import load_plugins
        state.plugins = load_plugins(ai_model=state.chat_model)
        app.state.plugins = state.plugins
        logger.info(f"Loaded {len(state.plugins)} plugins during startup.")
    except Exception as exc:
        logger.error(f"Failed to load plugins during startup: {exc}")
        state.plugins = {}
        app.state.plugins = {}

    # Initialize and start Telegram Bot if enabled
    enable_tg_env = os.getenv("ENABLE_TELEGRAM_BOT", "").lower() in ("true", "1", "yes")
    tg_plugin = state.plugins.get("telegram_bot")
    if tg_plugin and enable_tg_env:
        try:
            tg_plugin.set_plugins(state.plugins)
            await tg_plugin.start()
            logger.info("Telegram Bot plugin started successfully inside FastAPI lifecycle.")
        except Exception as exc:
            logger.error(f"Failed to start Telegram Bot plugin: {exc}")

    # Start Applications CSV Auto-Logging Engine
    try:
        from apps.common.autolog_engine import autolog_engine
        await autolog_engine.start()
    except Exception as exc:
        logger.warning(f"Не удалось запустить движок автологгирования приложений: {exc}")

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
    # Stop Applications Auto-Logging Engine
    try:
        from apps.common.autolog_engine import autolog_engine
        await autolog_engine.stop()
    except Exception as exc:
        logger.error(f"Ошибка при остановке автологгера приложений: {exc}")

    # Stop Telegram Bot if running
    tg_plugin = getattr(state, "plugins", {}).get("telegram_bot")
    if tg_plugin:
        try:
            await tg_plugin.stop()
            logger.info("Telegram Bot plugin stopped cleanly.")
        except Exception as exc:
            logger.error(f"Error while stopping Telegram Bot plugin: {exc}")

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
