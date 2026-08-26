# -*- coding: utf-8 -*-
"""
Unified interface for all TTS systems (Microsoft Edge, Google, Silero).
"""
from __future__ import annotations

from pathlib import Path
from core.logger import logger

async def synthesize_speech(text: str, file_path: Path, tts_system: str = "edge-tts", voice: str = "ru-RU-DmitryNeural"):
    """Synthesizes speech to a file using the selected TTS system and voice."""
    logger.info(f"Synthesizing using system: {tts_system}, voice/speaker: {voice}")
    
    if tts_system == "gtts":
        from core.tts import gtts
        await gtts.synthesize(text, file_path, voice)
    elif tts_system == "silero":
        try:
            from core.tts import silero
            await silero.synthesize(text, file_path, voice)
        except ImportError as e:
            logger.warning(f"Could not load Silero TTS (missing dependencies like torch/soundfile): {e}. Falling back to edge-tts.")
            from core.tts import edge
            await edge.synthesize(text, file_path, voice)
    else:
        # Fallback to edge-tts
        from core.tts import edge
        await edge.synthesize(text, file_path, voice)

