# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Synthesizes text to a file using Google TTS (gTTS)
# =============================================================================
# Description:
#   Synthesizes text to a file using Google TTS (gTTS)."""
#
# File: gtts.py
# Project: ai-breadboard
# Package: src.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Module for Google Translator TTS system (gTTS).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from gtts import gTTS

async def synthesize(text: str, file_path: Path, voice: str = "ru"):
    """Synthesizes text to a file using Google TTS (gTTS)."""
    lang = "ru"
    if "-" in voice:
        lang = voice.split("-")[0]
        
    loop = asyncio.get_event_loop()
    tts = gTTS(text=text, lang=lang)
    await loop.run_in_executor(None, tts.save, str(file_path))
