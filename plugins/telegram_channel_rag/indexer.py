# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Channel RAG Vector Indexer & Search Retrieval
# =============================================================================
# Description:
#   Builds, persists, and performs semantic TF-IDF / vector searches across
#   indexed Telegram messages, providing relevance ranking and message URLs.
#
# File: indexer.py
# Project: ai-breadboard
# Package: plugins.telegram_channel_rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram RAG Vector Indexer module.

Handles chunking, term frequency-inverse document frequency (TF-IDF) vectorization,
matrix persistence, and cosine similarity ranking with message URL resolution.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from src.logger import logger


class TelegramChannelIndexer:
    """TF-IDF and semantic vector search engine for Telegram channel messages.

    Attributes:
        index_dir (Path): Directory where index files are stored.
        messages (List[Dict[str, Any]]): In-memory list of indexed messages.
        vocab (Dict[str, int]): Token to index mapping.
        idf (Optional[np.ndarray]): Term IDF weights array.
        vectors (Optional[np.ndarray]): Normalized document chunk vectors.
    """

    def __init__(self, index_dir: Path) -> None:
        """Initialize the Telegram indexer.

        Args:
            index_dir (Path): Storage directory for index artifacts.
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.messages: List[Dict[str, Any]] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None
        self.vectors: Optional[np.ndarray] = None

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize message text into normalized alphanumeric words.

        Args:
            text (str): Raw message text string.

        Returns:
            List[str]: List of token strings.
        """
        # Supports multilingual alphanumeric tokens (Russian, English, digits)
        words = re.findall(r"[a-zA-Zа-яА-Я0-9_.-]{2,}", text.lower())
        return words

    def build_index(self, messages: List[Dict[str, Any]]) -> None:
        """Build vector index from collected messages.

        Args:
            messages (List[Dict[str, Any]]): List of collected message records.
        """
        self.messages = messages
        if not messages:
            self.vocab = {}
            self.idf = None
            self.vectors = None
            return

        # 1. Build Vocabulary & Document Frequencies
        df: Dict[str, int] = {}
        tokenized_docs: List[List[str]] = []

        for msg in messages:
            # Combine text and author for search indexing
            content = f"{msg.get('author', '')} {msg.get('text', '')}"
            tokens = self._tokenize(content)
            tokenized_docs.append(tokens)
            unique_tokens: Set[str] = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        self.vocab = {token: idx for idx, token in enumerate(df.keys())}
        num_docs = len(messages)
        vocab_size = len(self.vocab)

        # 2. Compute IDF: log((N + 1) / (df + 1)) + 1
        idf_arr = np.zeros(vocab_size, dtype=np.float32)
        for token, idx in self.vocab.items():
            idf_arr[idx] = math.log((num_docs + 1) / (df[token] + 1)) + 1.0
        self.idf = idf_arr

        # 3. Compute TF-IDF Vectors
        vec_list = []
        for tokens in tokenized_docs:
            vec = np.zeros(vocab_size, dtype=np.float32)
            if tokens:
                for t in tokens:
                    if t in self.vocab:
                        vec[self.vocab[t]] += 1.0
                # Term Frequency normalization
                vec = vec / len(tokens)
                vec = vec * self.idf
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
            vec_list.append(vec)

        self.vectors = np.array(vec_list, dtype=np.float32) if vec_list else None
        logger.info(f"Built Telegram RAG index for {num_docs} messages with vocab size {vocab_size}")

    def save(self) -> None:
        """Persist index structures to disk."""
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            
            # Save messages
            msg_file = self.index_dir / "messages.json"
            msg_file.write_text(json.dumps(self.messages, ensure_ascii=False, indent=2), encoding="utf-8")

            # Save vocab
            vocab_file = self.index_dir / "vocab.json"
            vocab_file.write_text(json.dumps(self.vocab, ensure_ascii=False), encoding="utf-8")

            # Save IDF and Vectors
            if self.idf is not None:
                np.save(self.index_dir / "idf.npy", self.idf)
            if self.vectors is not None:
                np.save(self.index_dir / "vectors.npy", self.vectors)

            logger.info(f"Saved Telegram RAG index to {self.index_dir}")
        except Exception as exc:
            logger.error(f"Error saving Telegram RAG index: {exc}")

    def load(self) -> bool:
        """Load index structures from disk.

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        msg_file = self.index_dir / "messages.json"
        vocab_file = self.index_dir / "vocab.json"
        idf_file = self.index_dir / "idf.npy"
        vec_file = self.index_dir / "vectors.npy"

        if not (msg_file.exists() and vocab_file.exists() and idf_file.exists() and vec_file.exists()):
            return False

        try:
            self.messages = json.loads(msg_file.read_text(encoding="utf-8"))
            self.vocab = json.loads(vocab_file.read_text(encoding="utf-8"))
            self.idf = np.load(idf_file)
            self.vectors = np.load(vec_file)
            logger.info(f"Loaded Telegram RAG index from {self.index_dir} ({len(self.messages)} messages)")
            return True
        except Exception as exc:
            logger.error(f"Failed to load Telegram RAG index from {self.index_dir}: {exc}")
            return False

    def search(self, query: str, top_k: int = 5, min_score: float = 0.05) -> List[Dict[str, Any]]:
        """Perform semantic retrieval for a search query.

        Args:
            query (str): User query string.
            top_k (int): Number of top relevant messages to return.
            min_score (float): Minimum cosine similarity threshold.

        Returns:
            List[Dict[str, Any]]: Ranked results containing message details, score, and link.
        """
        if not query.strip() or self.vectors is None or len(self.messages) == 0:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens or not self.vocab:
            return []

        # Vectorize query
        vocab_size = len(self.vocab)
        q_vec = np.zeros(vocab_size, dtype=np.float32)
        for t in q_tokens:
            if t in self.vocab:
                q_vec[self.vocab[t]] += 1.0

        if np.all(q_vec == 0):
            return []

        q_vec = q_vec / len(q_tokens)
        if self.idf is not None:
            q_vec = q_vec * self.idf

        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # Compute cosine similarity
        scores = np.dot(self.vectors, q_vec)

        # Get top indices
        top_indices = np.argsort(scores)[::-1]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score:
                break
            msg = dict(self.messages[idx])
            msg["score"] = round(score, 4)
            results.append(msg)
            if len(results) >= top_k:
                break

        return results
