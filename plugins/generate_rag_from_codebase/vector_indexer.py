# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Codebase Vector Indexer and Search Engine
# =============================================================================
# Description:
#   Builds, persists, and performs semantic similarity search over codebase chunks
#   with TF-IDF vectorization and metadata filtering.
#
# File: vector_indexer.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Vector indexer and search retrieval for codebase RAG.

Calculates vector representations for structured code and markdown chunks,
supports cosine similarity search, and filters by document type or module.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


class CodebaseVectorIndexer:
    """TF-IDF and metadata-driven semantic vector search engine for codebase chunks.

    Attributes:
        index_dir (Path): Directory where index files are stored.
        chunks (List[Dict[str, Any]]): In-memory list of indexed chunks.
        vocab (Dict[str, int]): Term vocabulary mapping token to index.
        idf (Optional[np.ndarray]): Inverse document frequency weights.
        vectors (Optional[np.ndarray]): Normalized document chunk vectors.
    """

    def __init__(self, index_dir: Path) -> None:
        """Initialize the vector indexer.

        Args:
            index_dir (Path): Storage directory for index artifacts.
        """
        self.index_dir = Path(index_dir)
        self.chunks: List[Dict[str, Any]] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None
        self.vectors: Optional[np.ndarray] = None

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize code or text into normalized terms.

        Args:
            text (str): Input text string.

        Returns:
            List[str]: List of token strings.
        """
        # Split by non-alphanumeric characters while splitting camelCase and snake_case
        s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        words = re.findall(r"[A-Za-z0-9_\-\.]{2,}", s1.lower())
        return words

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Build vector index from parsed chunks.

        Args:
            chunks (List[Dict[str, Any]]): List of semantic code/doc chunks.
        """
        self.chunks = chunks
        if not chunks:
            self.vocab = {}
            self.idf = None
            self.vectors = None
            return

        # 1. Build Vocabulary & Document Frequencies
        df: Dict[str, int] = {}
        tokenized_docs: List[List[str]] = []

        for chunk in chunks:
            text = chunk.get("text", "")
            tokens = self._tokenize(text)
            tokenized_docs.append(tokens)
            unique_tokens: Set[str] = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        # Keep vocabulary with min occurrence >= 1
        self.vocab = {token: idx for idx, token in enumerate(df.keys())}
        num_docs = len(chunks)
        vocab_size = len(self.vocab)

        # 2. Compute IDF: log((N + 1) / (df + 1)) + 1
        self.idf = np.zeros(vocab_size, dtype=np.float32)
        for token, idx in self.vocab.items():
            self.idf[idx] = math.log((num_docs + 1.0) / (df[token] + 1.0)) + 1.0

        # 3. Compute TF-IDF matrix
        matrix = np.zeros((num_docs, vocab_size), dtype=np.float32)
        for doc_idx, tokens in enumerate(tokenized_docs):
            if not tokens:
                continue
            tf: Dict[int, int] = {}
            for token in tokens:
                if token in self.vocab:
                    t_idx = self.vocab[token]
                    tf[t_idx] = tf.get(t_idx, 0) + 1

            doc_len = len(tokens)
            for t_idx, count in tf.items():
                matrix[doc_idx, t_idx] = (count / doc_len) * self.idf[t_idx]

        # 4. L2 Normalize
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors = matrix / norms

    def search(
        self,
        query: str,
        top_k: int = 5,
        type_filter: Optional[str] = None,
        module_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using cosine similarity.

        Args:
            query (str): Search query string.
            top_k (int): Maximum number of results to return.
            type_filter (Optional[str]): Restrict to specific chunk type.
            module_filter (Optional[str]): Restrict to specific module prefix.

        Returns:
            List[Dict[str, Any]]: Ranked results with score and chunk metadata.
        """
        if not self.chunks or self.vectors is None or not self.vocab:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        # Vectorize query
        q_vec = np.zeros(len(self.vocab), dtype=np.float32)
        tf: Dict[int, int] = {}
        for token in q_tokens:
            if token in self.vocab:
                t_idx = self.vocab[token]
                tf[t_idx] = tf.get(t_idx, 0) + 1

        for t_idx, count in tf.items():
            if self.idf is not None:
                q_vec[t_idx] = (count / len(q_tokens)) * self.idf[t_idx]

        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        # Cosine similarity
        scores = np.dot(self.vectors, q_vec)
        ranked_indices = np.argsort(-scores)

        results: List[Dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                break

            chunk = self.chunks[idx]

            # Filters
            if type_filter and chunk.get("type") != type_filter:
                continue
            if module_filter:
                mod = chunk.get("module") or ""
                if not mod.startswith(module_filter):
                    continue

            result_item = dict(chunk)
            result_item["similarity_score"] = round(score, 4)
            results.append(result_item)

            if len(results) >= top_k:
                break

        return results

    def save(self) -> None:
        """Save chunk definitions, vocabulary, IDF and vectors to index directory."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        chunks_file = self.index_dir / "chunks.json"
        vocab_file = self.index_dir / "vocab.json"
        idf_file = self.index_dir / "idf.npy"
        vectors_file = self.index_dir / "vectors.npy"

        chunks_file.write_text(json.dumps(self.chunks, indent=2, ensure_ascii=False), encoding="utf-8")
        vocab_file.write_text(json.dumps(self.vocab, indent=2, ensure_ascii=False), encoding="utf-8")

        if self.idf is not None:
            np.save(str(idf_file), self.idf)
        if self.vectors is not None:
            np.save(str(vectors_file), self.vectors)

    def load(self) -> bool:
        """Load index from files in index directory.

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        chunks_file = self.index_dir / "chunks.json"
        vocab_file = self.index_dir / "vocab.json"
        idf_file = self.index_dir / "idf.npy"
        vectors_file = self.index_dir / "vectors.npy"

        if not (chunks_file.exists() and vocab_file.exists() and idf_file.exists() and vectors_file.exists()):
            return False

        try:
            self.chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
            self.vocab = json.loads(vocab_file.read_text(encoding="utf-8"))
            self.idf = np.load(str(idf_file))
            self.vectors = np.load(str(vectors_file))
            return True
        except Exception:
            return False
