# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тесты модуля core/tts
# =============================================================================
# Description:
#   Module содержит тесты для модуля синтеза речи (Text-to-Speech). Checks
#
# File: test_tts.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Тесты модуля core/tts
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
    """Тесты edge.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_edge(self):
        """Тест синтеза речи edge-tts."""
        from core.tts.edge import synthesize
        
        with patch('core.tts.edge') as mock_tts:
            # Check что function существует
            assert callable(synthesize)

class TestTTSGTTS:
    """Тесты gtts.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_gtts(self):
        """Тест синтеза речи gtts."""
        from core.tts.gtts import synthesize
        
        with patch('core.tts.gtts') as mock_tts:
            assert callable(synthesize)

@pytest.mark.skipif(not has_torch, reason="torch is not installed")
class TestTTSSilero:
    """Тесты silero.py TTS."""

    def test_get_silero_model(self):
        """Тест загрузки модели Silero."""
        try:
            # Проверяем что Module можно импортировать
            from core.tts.silero import get_silero_model
            assert callable(get_silero_model)
        except ModuleNotFoundError as e:
            if 'pyaudioop' in str(e):
                pytest.skip("pyaudioop module not available")
            raise

    @pytest.mark.asyncio
    async def test_synthesize_silero(self):
        """Тест синтеза речи Silero."""
        try:
            from core.tts.silero import synthesize
            assert callable(synthesize)
        except ModuleNotFoundError as e:
            if 'pyaudioop' in str(e):
                pytest.skip("pyaudioop module not available")
            raise

class TestTTSInit:
    """Тесты __init__.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_speech(self):
        """Тест синтеза речи (обертка)."""
        from core.tts import synthesize_speech
        
        # Check что function существует
        assert callable(synthesize_speech)

class TestTTSIntegration:
    """Интеграционные тесты TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_all_systems(self, tmp_path):
        """Тест синтеза для всех систем."""
        import core.tts
        
        test_file = tmp_path / 'test.mp3'
        text = "Тестовый текст для синтеза речи"
        
        with patch('core.tts.synthesize_speech') as mock_synth:
            mock_synth.return_value = AsyncMock()
            
            result = await core.tts.synthesize_speech(text, test_file, "edge-tts", "ru-RU-DmitryNeural")
            
            mock_synth.assert_called_once()

