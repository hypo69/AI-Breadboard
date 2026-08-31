# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Run Telegram bot with full plugin and AI model suite
# =============================================================================
# Description:
#   Runs Telegram bot in separate process, independent from uvicorn server.
#   Loads all plugins and initializes AI models for bot functionality.
#
# File: bot_runner.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram bot runner script.

Launches Telegram bot in separate process with full plugin suite and
AI model integration for chat functionality."""

from __future__ import annotations

import asyncio
import os
import sys
import signal
from pathlib import Path

from dotenv import load_dotenv

import header
from header import __root__

load_dotenv(__root__ / '.env')

from core.utils.jjson import j_loads_ns
from core.logger import logger

from core.config import server_cfg, ai_cfg, tts_cfg, logging_cfg

async def _run_bot() -> None:
    """Run Telegram bot with full plugin and AI model suite.
    
    Initializes bot with configured AI model (either Google Generative AI
    or Foundry model), loads plugins, and starts async event loop.
    """
    from core.ai import GoogleGenerativeAI
    from core.utils.file import read_text_file
    from plugins import load_plugins

    _system_instruction = read_text_file(__root__ / 'prompts' / 'chat' / 'system_instruction.md') or ''
    _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]

    use_foundry = getattr(ai_cfg, 'use_foundry', False) if ai_cfg else False
    foundry_model_id = getattr(ai_cfg, 'foundry_model_id', 'qwen2.5-1.5b') if ai_cfg else 'qwen2.5-1.5b'

    if use_foundry:
        from core.ai.foundry_chat import FoundryChatBase
        model = FoundryChatBase(model_id=foundry_model_id, system_prompt=_system_instruction)
    else:
        model = GoogleGenerativeAI(api_key_names=_api_key_names, system_instruction=_system_instruction)

    plugins = load_plugins(model)
    tg_plugin = plugins.get('telegram_bot')

    if not tg_plugin:
        logger.warning('Telegram bot plugin not found - bot_runner exiting.')
        return

    if hasattr(tg_plugin, 'set_plugins'):
        tg_plugin.set_plugins(plugins)

    loop = asyncio.get_event_loop()

    stop_event = asyncio.Event()

    def _handle_exit(*_):
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_exit)
        except (NotImplementedError, AttributeError):
            signal.signal(sig, _handle_exit)

    logger.info('Telegram bot started (separate process)')
    try:
        await tg_plugin.start()
        await stop_event.wait()
    finally:
        await tg_plugin.stop()
        logger.info('Telegram bot stopped')

if __name__ == '__main__':
    asyncio.run(_run_bot())
