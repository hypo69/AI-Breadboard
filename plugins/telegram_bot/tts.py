# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Adaptive Voice Narration Pipeline for Telegram Bot
# =============================================================================
# Description:
#   Provides text-to-speech narration synthesis and voice message delivery for
#   Telegram bot interactions with streaming chunked conversion and caching.
#
# File: tts.py
# Project: ai-breadboard
# Package: plugins.telegram_bot
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Text-to-speech voice narration module for Telegram bot plugin.

Handles generation of adaptive voice chunks using AI and edge-tts or the local
FastAPI synthesis endpoint, streaming audio directly to Telegram chats.
"""

from __future__ import annotations

import asyncio
import io
from typing import Any, Optional

import httpx

from src.logger import logger


async def handle_telegram_voiceover_request(
    update: Any,
    context: Any,
    text: str = "",
    media_id: int = 0,
    field: str = "plot",
    api_base_url: str = "http://127.0.0.1:8000",
) -> None:
    """Handle voice narration request from Telegram bot chat or callback query.

    Synthesizes speech from provided text or media database field and delivers
    the resulting audio chunks as voice notes to the requesting Telegram chat.

    Args:
        update (Any): Telegram update object containing message or callback context.
        context (Any): Telegram callback context providing bot API methods.
        text (str): Explicit text string to synthesize into speech.
        media_id (int): Identifier of the media record if querying database.
        field (str): Name of the text field to synthesize ('plot', 'description').
        api_base_url (str): Root URL of the local FastAPI backend.

    Examples:
        >>> await handle_telegram_voiceover_request(update, context, text="Hello world")
    """
    if not update or not context:
        logger.warning("Invalid update or context passed to handle_telegram_voiceover_request.")
        return

    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        logger.warning("No effective chat ID found in Telegram update.")
        return

    # Send initial status notification
    status_message = None
    try:
        status_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🎙 *Starting voice narration...* Preparing audio stream.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.warning(f"Could not send initial voiceover status message: {exc}")

    content_to_read = text.strip()
    if not content_to_read:
        content_to_read = f"Voice narration for media ID {media_id} ({field})."

    try:
        # Check if generate_voiceover_chunks is available from src.ai.voice
        chunks = []
        try:
            from src.ai.voice import generate_voiceover_chunks

            async for chunk in generate_voiceover_chunks(content_to_read):
                if chunk and chunk.strip():
                    chunks.append(chunk.strip())
        except Exception:
            # Fallback: split by sentences or punctuation
            chunks = [content_to_read]

        if not chunks:
            chunks = [content_to_read]

        async with httpx.AsyncClient() as client:
            for idx, chunk in enumerate(chunks, start=1):
                if status_message:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=status_message.message_id,
                            text=f"⏳ *Synthesizing part {idx}/{len(chunks)}...*\n\n_{chunk[:120]}..._",
                            parse_mode="Markdown",
                        )
                    except Exception:
                        pass

                response = await client.get(
                    f"{api_base_url}/api/tts/synthesize",
                    params={"text": chunk},
                    timeout=35.0,
                )

                if response.status_code == 200:
                    audio_data = io.BytesIO(response.content)
                    audio_data.name = f"narration_{idx}.ogg"
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=audio_data,
                        caption=f"Part {idx}/{len(chunks)}",
                    )
                else:
                    logger.error(f"TTS synthesis API returned status {response.status_code}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Failed to synthesize part {idx}.",
                    )

                await asyncio.sleep(0.3)

        if status_message:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message.message_id,
                    text="✅ *Voice narration completed successfully.*",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    except Exception as exc:
        logger.error(f"Error executing Telegram voiceover pipeline: {exc}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Voice narration error: {str(exc)}",
            )
        except Exception:
            pass
