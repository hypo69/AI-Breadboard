# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Synthesizes text to a file using Microsoft Edge TT
# =============================================================================
# Description:
#   Synthesizes text to a file using Microsoft Edge TTS."""
#
# File: edge.py
# Project: ai-breadboard
# Package: core.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Module for Microsoft Edge TTS system.
"""
from __future__ import annotations

from pathlib import Path
import edge_tts

async def synthesize(text: str, file_path: Path, voice: str = "ru-RU-DmitryNeural"):
    """Synthesizes text to a file using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(file_path))
