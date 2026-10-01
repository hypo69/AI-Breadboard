# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard TTS - Edge Module
# =============================================================================
# Description:
#   Module for Microsoft Edge TTS system.
#
# Usage Examples:
#   Python API:
#     import src.tts.edge as edge
#
# File: edge.py
# Project: ai-breadboard
# Package: src.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Module for Microsoft Edge TTS system."""

from pathlib import Path
import edge_tts

async def synthesize(text: str, file_path: Path, voice: str='ru-RU-DmitryNeural'):
    """Synthesizes text to a file using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(file_path))