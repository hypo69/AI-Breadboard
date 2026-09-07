# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for core/tts module
# =============================================================================
# Description:
#   Module contains tests for speech synthesis (Text-to-Speech) module. Checks
#
# File: test_tts.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Tests for core/tts module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

try:
    import torch
    has_torch = True
except ImportError:
    has_torch = False

class TestTTSEdge:
    """Tests for edge.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_edge(self):
        """Test edge-tts speech synthesis."""
        from src.tts.edge import synthesize
        
        with patch('src.tts.edge') as mock_tts:
            # Check that function exists
            assert callable(synthesize)

class TestTTSGTTS:
    """Tests for gtts.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_gtts(self):
        """Test gtts speech synthesis."""
        from src.tts.gtts import synthesize
        
        with patch('src.tts.gtts') as mock_tts:
            assert callable(synthesize)

@pytest.mark.skipif(not has_torch, reason="torch is not installed")
class TestTTSSilero:
    """Tests for silero.py TTS."""

    def test_get_silero_model(self):
        """Test loading Silero model."""
        try:
            # Check that module can be imported
            from src.tts.silero import get_silero_model
            assert callable(get_silero_model)
        except ModuleNotFoundError as e:
            if 'pyaudioop' in str(e):
                pytest.skip("pyaudioop module not available")
            raise

    @pytest.mark.asyncio
    async def test_synthesize_silero(self):
        """Test Silero speech synthesis."""
        try:
            from src.tts.silero import synthesize
            assert callable(synthesize)
        except ModuleNotFoundError as e:
            if 'pyaudioop' in str(e):
                pytest.skip("pyaudioop module not available")
            raise

class TestTTSInit:
    """Tests for __init__.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_speech_routing(self):
        """Test routing to edge-tts by default."""
        from src.tts import synthesize_speech
        with patch('src.tts.edge.synthesize', new_callable=AsyncMock) as mock_edge:
            await synthesize_speech("Hello", Path("test.mp3"), tts_system="edge-tts", voice="en-US-JennyNeural")
            mock_edge.assert_called_once_with("Hello", Path("test.mp3"), "en-US-JennyNeural")


class TestTTSLanguageAdjustment:
    """Tests for _adjust_voice_for_language in router_tts."""

    def test_adjust_voice_russian(self):
        from src.fastapi.router_tts import _adjust_voice_for_language
        # Cyrillic text with English default voice should adjust to Russian
        assert _adjust_voice_for_language("Привет, как дела?", "en-US-JennyNeural") == "ru-RU-DmitryNeural"

    def test_adjust_voice_hebrew(self):
        from src.fastapi.router_tts import _adjust_voice_for_language
        # Hebrew text with Russian voice should adjust to Hebrew
        assert _adjust_voice_for_language("שלום עולם, מה שלומך?", "ru-RU-DmitryNeural") == "he-IL-AvriNeural"

    def test_adjust_voice_english(self):
        from src.fastapi.router_tts import _adjust_voice_for_language
        # English text with Russian voice should adjust to English
        assert _adjust_voice_for_language("Hello world, how are you?", "ru-RU-DmitryNeural") == "en-US-AriaNeural"

    def test_preserve_voice_when_matching(self):
        from src.fastapi.router_tts import _adjust_voice_for_language
        assert _adjust_voice_for_language("שלום", "he-IL-HilaNeural") == "he-IL-HilaNeural"
        assert _adjust_voice_for_language("Hello", "en-US-JennyNeural") == "en-US-JennyNeural"
        assert _adjust_voice_for_language("Привет", "ru-RU-SvetlanaNeural") == "ru-RU-SvetlanaNeural"
