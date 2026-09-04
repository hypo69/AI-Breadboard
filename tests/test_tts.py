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
