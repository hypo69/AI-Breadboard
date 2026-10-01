# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard TTS - Gtts Module
# =============================================================================
# Description:
#   Module for Google Translator TTS system (gTTS).
#
# Usage Examples:
#   Python API:
#     import src.tts.gtts as gtts
#
# File: gtts.py
# Project: ai-breadboard
# Package: src.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Module for Google Translator TTS system (gTTS)."""

import asyncio
from pathlib import Path
from gtts import gTTS

async def synthesize(text: str, file_path: Path, voice: str='ru'):
    """Synthesizes text to a file using Google TTS (gTTS)."""
    lang = 'ru'
    if '-' in voice:
        lang = voice.split('-')[0]
    loop = asyncio.get_event_loop()
    tts = gTTS(text=text, lang=lang)
    await loop.run_in_executor(None, tts.save, str(file_path))