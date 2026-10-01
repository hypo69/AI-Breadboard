# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Embeddings Module
# =============================================================================
# Description:
#   Mixin class for embedding generation in GoogleGenerativeAI.
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.embeddings import GoogleGenerativeAIEmbeddingsMixin
#
#     service = GoogleGenerativeAIEmbeddingsMixin()
#
# File: embeddings.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Mixin class for embedding generation in GoogleGenerativeAI."""

import asyncio
import numpy as np
from logger import logger
from .core import GoogleGenerativeAICore

class GoogleGenerativeAIEmbeddingsMixin:
    """Mixin class for embedding generation in GoogleGenerativeAI.

    Provides methods for generating vector representations of text.
    """

    async def embed(self, text: str, model_name: str='text-embedding-004') -> np.ndarray | bool:
        """Generation of vector representation (embedding) for provided text.

        Args:
            text (str): Source text for vectorization.
            model_name (str): Name of the embedding model.

        Returns:
            np.ndarray | bool: One-dimensional embedding array or False on failure.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> vec = await ai.embed("Тестовый текст")
        """
        if not text:
            return False
        try:
            response = self._client.models.embed_content(model=model_name, contents=text)
            if response and response.embeddings:
                return np.array(response.embeddings[0].values)
            return False
        except Exception as ex:
            logger.error('GoogleGenerativeAI: Error генерации эмбеддинга', ex)
            return False