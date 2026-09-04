# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Embeddings
# =============================================================================
# Description:
#   Embedding generation for Google Generative AI.
#   Provides methods for generating vector representations of text.
#
# File: embeddings.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio

import numpy as np

from src.logger.logger import logger

from .core import GoogleGenerativeAICore


class GoogleGenerativeAIEmbeddingsMixin:
    """Mixin class for embedding generation in GoogleGenerativeAI.

    Provides methods for generating vector representations of text.
    """

    async def embed(self, text: str, model_name: str = 'text-embedding-004') -> np.ndarray | bool:
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
            response = self._client.models.embed_content(
                model=model_name,
                contents=text,
            )
            if response and response.embeddings:
                return np.array(response.embeddings[0].values)
            return False
        except Exception as ex:
            logger.error('GoogleGenerativeAI: Error генерации эмбеддинга', ex)
            return False
