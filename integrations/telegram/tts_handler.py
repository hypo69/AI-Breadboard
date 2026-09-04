# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Adaptive TTS pipeline integration module for Telegram bot
# =============================================================================
# Description:
#   Module for integrating adaptive TTS (text-to-speech) pipeline into Telegram bot.
#   Generates voice messages from text with adaptive chunking and streaming delivery.
#   Uses python-telegram-bot or compatible framework.
#
# File: tg_tts_handler.py
# Project: ai-breadboard
# Package: integrations.telegram
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Module for integrating adaptive TTS pipeline into Telegram bot.
Uses python-telegram-bot or any compatible framework.
Implements streaming audio generation and instant delivery to users.
"""
import io
import httpx
import asyncio
from typing import AsyncGenerator
from src.logger import logger
from src.ai.voice import generate_voiceover_chunks

# URL of local FastAPI instance
API_BASE_URL = "http://127.0.0.1:8000"

async def handle_telegram_voiceover_request(update, context, media_id: int, field: str = "plot"):
    """
    Handler for voice narration request in Telegram.
    Implements pipeline:
    1. Generate adapted text chunks using Gemini.
    2. Send status message "Preparing voice narration...".
    3. For each ready chunk: request TTS, download mp3, instantly send as voice message.
    """
    query = update.callback_query if update.callback_query else None
    chat_id = update.effective_chat.id
    
    # 1. Send greeting message
    status_message = await context.bot.send_message(
        chat_id=chat_id,
        text="🎙 *Starting voice narration preparation...* Text is being adapted for narrator.",
        parse_mode="Markdown"
    )
    
    # Get original text from database
    # In real bot code you can import MediaDatabase directly:
    # from plugins.media_organizer.core.database import MediaDatabase
    # db = MediaDatabase(DB_FILE)
    # raw_text = db.get_media_field(media_id, field)
    # For example we'll use a stub simulating text retrieval:
    raw_text = "Example text from database. 1. Plug in the device. 2. Press start button."
    
    try:
        idx = 1
        async for chunk in generate_voiceover_chunks(raw_text):
            # Notify user about current part preparation
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message.message_id,
                text=f"⏳ *Synthesizing part {idx}...*\n\n_{chunk}_",
                parse_mode="Markdown"
            )
            
            # Send request to synthesis API (or call edge-tts directly)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/api/tts/synthesize",
                    params={"text": chunk},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    # Send audio file as voice message in Telegram
                    audio_data = io.BytesIO(response.content)
                    audio_data.name = f"voiceover_part_{idx}.ogg"  # Telegram accepts ogg/mp3
                    
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=audio_data,
                        caption=f"Part {idx}",
                        title="Narrator"
                    )
                else:
                    logger.error(f"TTS API returned error code {response.status_code}")
                    await context.bot.send_message(chat_id=chat_id, text=f"❌ Error synthesizing part {idx}")
            
            idx += 1
            await asyncio.sleep(0.5)  # Small pause between sending parts
            
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text="✅ *All voice narration ready and sent!*",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in TG voiceover handler: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error occurred during voice narration: {str(e)}"
        )
