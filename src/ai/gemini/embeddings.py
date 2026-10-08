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
# Updated: 2026-10-08 10:48:20
# =============================================================================

"""Mixin class for embedding generation in GoogleGenerativeAI."""

import asyncio
import json
import numpy as np
from logger import logger
from .core import GoogleGenerativeAICore
from .errors import format_error_as_json

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
        if hasattr(self, '_log_request_details'):
            self._log_request_details(method='embed', model=model_name, q=text)
        try:
            response = self._client.models.embed_content(model=model_name, contents=text)
            if response and response.embeddings:
                arr = np.array(response.embeddings[0].values)
                if hasattr(self, '_log_response_details'):
                    self._log_response_details(method='embed', model=model_name, response_text=f'Vector generated successfully (shape: {arr.shape})')
                return arr
            err_empty = {
                'error': {
                    'code': 204,
                    'status': 'EMPTY_EMBEDDING',
                    'message': 'Empty embeddings response from model',
                    'model': model_name,
                }
            }
            logger.warning(f'GoogleGenerativeAI: Empty embeddings:\n{json.dumps(err_empty, ensure_ascii=False, indent=2)}')
            return False
        except Exception as ex:
            err_json = format_error_as_json(ex, model=model_name)
            logger.error(f'GoogleGenerativeAI: Error генерации эмбеддинга:\n{err_json}')
            return False