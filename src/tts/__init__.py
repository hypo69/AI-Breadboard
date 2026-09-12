# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Synthesizes speech to a file using the selected TT
# =============================================================================
# Description:
#   Synthesizes speech to a file using the selected TTS system and voice."""
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Unified interface for all TTS systems (Microsoft Edge, Google, Silero).
"""
from __future__ import annotations

from pathlib import Path
from src.logger import logger

async def synthesize_speech(text: str, file_path: Path, tts_system: str = "edge-tts", voice: str = "ru-RU-DmitryNeural"):
    """Synthesizes speech to a file using the selected TTS system and voice."""
    logger.info(f"Synthesizing using system: {tts_system}, voice/speaker: {voice}")
    
    if tts_system == "gtts":
        from src.tts import gtts
        await gtts.synthesize(text, file_path, voice)
    elif tts_system == "silero":
        try:
            from src.tts import silero
            await silero.synthesize(text, file_path, voice)
        except ImportError as e:
            logger.warning(f"Could not load Silero TTS (missing dependencies like torch/soundfile): {e}. Falling back to edge-tts.")
            from src.tts import edge
            await edge.synthesize(text, file_path, voice)
    else:
        # Fallback to edge-tts
        from src.tts import edge
        await edge.synthesize(text, file_path, voice)

