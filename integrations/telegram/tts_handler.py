# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Integrations Telegram - Tts Handler
# =============================================================================
# Description:
#   Module for integrating adaptive TTS pipeline into Telegram bot.
#
# Usage Examples:
#   Python API:
#     import integrations.telegram.tts_handler as tts_handler
#
# File: tts_handler.py
# Project: ai-breadboard
# Package: integrations.telegram
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:29:29
# =============================================================================

"""Module for integrating adaptive TTS pipeline into Telegram bot.
Uses python-telegram-bot or any compatible framework.
Implements streaming audio generation and instant delivery to users."""

import io
import httpx
import asyncio
from typing import AsyncGenerator
from logger import logger
from src.ai.voice import generate_voiceover_chunks
API_BASE_URL = 'http://127.0.0.1:8000'

async def handle_telegram_voiceover_request(update, context, media_id: int, field: str='plot'):
    """
    Handler for voice narration request in Telegram.
    Implements pipeline:
    1. Generate adapted text chunks using Gemini.
    2. Send status message "Preparing voice narration...".
    3. For each ready chunk: request TTS, download mp3, instantly send as voice message.
    """
    query = update.callback_query if update.callback_query else None
    chat_id = update.effective_chat.id
    status_message = await context.bot.send_message(chat_id=chat_id, text='🎙 *Starting voice narration preparation...* Text is being adapted for narrator.', parse_mode='Markdown')
    raw_text = 'Example text from database. 1. Plug in the device. 2. Press start button.'
    try:
        idx = 1
        async for chunk in generate_voiceover_chunks(raw_text):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_message.message_id, text=f'⏳ *Synthesizing part {idx}...*\n\n_{chunk}_', parse_mode='Markdown')
            async with httpx.AsyncClient() as client:
                response = await client.get(f'{API_BASE_URL}/api/tts/synthesize', params={'text': chunk}, timeout=30.0)
                if response.status_code == 200:
                    audio_data = io.BytesIO(response.content)
                    audio_data.name = f'voiceover_part_{idx}.ogg'
                    await context.bot.send_voice(chat_id=chat_id, voice=audio_data, caption=f'Part {idx}', title='Narrator')
                else:
                    logger.error(f'TTS API returned error code {response.status_code}')
                    await context.bot.send_message(chat_id=chat_id, text=f'❌ Error synthesizing part {idx}')
            idx += 1
            await asyncio.sleep(0.5)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_message.message_id, text='✅ *All voice narration ready and sent!*', parse_mode='Markdown')
    except Exception as e:
        logger.error(f'Error in TG voiceover handler: {e}')
        await context.bot.send_message(chat_id=chat_id, text=f'❌ Error occurred during voice narration: {str(e)}')