# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard TTS - Silero Module
# =============================================================================
# Description:
#   Module for Silero TTS system.
#
# Usage Examples:
#   Python API:
#     from src.tts.silero import get_silero_model
#
#     res = get_silero_model()
#     print(res)
#
# File: silero.py
# Project: ai-breadboard
# Package: src.tts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Module for Silero TTS system."""

import os
import asyncio
from pathlib import Path
import torch
import soundfile as sf
from pydub import AudioSegment
from logger import logger
_model = ''

def get_silero_model():
    """Loads and returns the Silero model, caching it in memory."""
    global _model
    if _model != '':
        return _model
    import sys
    saved_modules = {}
    for k in list(sys.modules.keys()):
        if k == 'src' or k.startswith('src.'):
            saved_modules[k] = sys.modules.pop(k)
    try:
        hub_src_dir = Path(torch.hub.get_dir()) / 'snakers4_silero-models_master' / 'src'
        hub_init = hub_src_dir / '__init__.py'
        if hub_src_dir.exists() and (not hub_init.exists()):
            try:
                hub_init.touch()
            except Exception:
                pass
        hub_dir = Path(torch.hub.get_dir()) / 'snakers4_silero-models_master'
        if str(hub_dir) not in sys.path:
            sys.path.insert(0, str(hub_dir))
        device = torch.device('cpu')
        model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru', speaker='v5_ru', trust_repo=True)
        model.to(device)
        _model = model
    except Exception as e:
        raise e
    finally:
        for k, v in saved_modules.items():
            sys.modules[k] = v
    return _model

async def synthesize(text: str, file_path: Path, voice: str='eugene'):
    """Synthesizes text to a file using Silero TTS."""
    valid_speakers = {'aidar', 'baya', 'eugene', 'kseniya', 'xenia', 'random'}
    speaker = voice if voice in valid_speakers else 'eugene'
    temp_wav_path = file_path.with_suffix('.wav')
    loop = asyncio.get_event_loop()

    def _run_synthesis():
        try:
            model = get_silero_model()
            audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=48000)
            sf.write(str(temp_wav_path), audio_tensor.numpy(), 48000)
        except Exception as e:
            logger.error(f'Error during Silero synthesis: {e}')
            raise e
    await loop.run_in_executor(None, _run_synthesis)
    if file_path.suffix.lower() == '.mp3':

        def _convert_to_mp3():
            try:
                audio = AudioSegment.from_wav(str(temp_wav_path))
                audio.export(str(file_path), format='mp3')
            finally:
                if temp_wav_path.exists():
                    temp_wav_path.unlink()
        await loop.run_in_executor(None, _convert_to_mp3)
    elif temp_wav_path != file_path:
        if file_path.exists():
            file_path.unlink()
        temp_wav_path.rename(file_path)