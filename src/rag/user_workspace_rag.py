# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Workspace RAG Collection & Pipeline Manager
# =============================================================================
# Description:
#   Manages isolated multi-RAG collections for users. Integrates with
#   plugins.rag_cleaner to sanitize, extract, and chunk documents from user storage,
#   constructing searchable vector/TF-IDF indexes per collection.
#
# File: user_workspace_rag.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from header import __root__
from src.logger import logger
from src.user_manager import user_manager
from plugins.rag_cleaner.cleaner import RAGDocumentCleanerCore


@dataclass
class UserRAGChunk:
    """Represents a sanitized document chunk within a user RAG collection."""
    chunk_id: str
    source_file: str
    doc_type: str
    chunk_index: int
    content: str
    length: int
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserRAGManifest:
    """Metadata manifest describing a user RAG collection."""
    id: str
    name: str
    description: str
    created_at: float
    updated_at: float
    status: str  # 'created', 'cleaning', 'indexed', 'error'
    files: List[str] = field(default_factory=list)
    total_chunks: int = 0
    provider: str = "local_tfidf"
    min_chunk_len: int = 20
    max_chunk_len: int = 1500
    error_message: str = ""


class UserWorkspaceRAGManager:
    """Manager for user personal multi-RAG workspaces and cleaning pipelines."""

    def __init__(self) -> None:
        """Initialize User Workspace RAG Manager."""
        pass

    def _get_user_rags_dir(self, user_id: int) -> Path:
        """Get or create the root directory for user RAG collections.

        Args:
            user_id (int): User unique identifier.

        Returns:
            Path: Path to user's rags directory.
        """
        user_root = user_manager.get_user_directory(user_id, create=True)
        rags_dir = user_root / "rags"
        rags_dir.mkdir(parents=True, exist_ok=True)
        return rags_dir

    def _get_collection_dir(self, user_id: int, rag_id: str) -> Path:
        """Get directory path for a specific user RAG collection.

        Args:
            user_id (int): User unique identifier.
            rag_id (str): Sanitized collection identifier.

        Returns:
            Path: Collection directory path.
        """
        clean_id = self._sanitize_id(rag_id)
        return self._get_user_rags_dir(user_id) / clean_id

    def _sanitize_id(self, raw_id: str) -> str:
        """Sanitize collection identifier for safe filesystem path.

        Args:
            raw_id (str): Raw input identifier or name.

        Returns:
            str: Clean identifier string.
        """
        clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_id.strip().lower())
        return clean if clean else "default_rag"

    def list_collections(self, user_id: int) -> List[Dict[str, Any]]:
        """List all RAG collections belonging to the specified user.

        Args:
            user_id (int): User unique identifier.

        Returns:
            List[Dict[str, Any]]: List of collection manifests.
        """
        rags_dir = self._get_user_rags_dir(user_id)
        collections: List[Dict[str, Any]] = []

        for item in rags_dir.iterdir():
            if item.is_dir():
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            collections.append(data)
                    except Exception as ex:
                        logger.error(f"[UserWorkspaceRAG] Error reading manifest from {item}: {ex}")

        # Sort by updated_at descending
        collections.sort(key=lambda c: c.get("updated_at", 0.0), reverse=True)
        return collections

    def get_collection(self, user_id: int, rag_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve manifest and details for a specific user RAG collection.

        Args:
            user_id (int): User unique identifier.
            rag_id (str): Collection identifier.

        Returns:
            Optional[Dict[str, Any]]: Collection manifest if found, None otherwise.
        """
        col_dir = self._get_collection_dir(user_id, rag_id)
        manifest_path = col_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as ex:
            logger.error(f"[UserWorkspaceRAG] Error reading manifest for {rag_id}: {ex}")
            return None

    def create_collection(
        self,
        user_id: int,
        name: str,
        description: str = "",
        files: Optional[List[str]] = None,
        min_chunk_len: int = 20,
        max_chunk_len: int = 1500
    ) -> Dict[str, Any]:
        """Create a new user RAG collection.

        Args:
            user_id (int): User unique identifier.
            name (str): Human-readable collection name.
            description (str): Collection description.
            files (Optional[List[str]]): List of filenames from user storage to attach.
            min_chunk_len (int): Minimum chunk length.
            max_chunk_len (int): Maximum chunk length.

        Returns:
            Dict[str, Any]: Created collection manifest.
        """
        rag_id = self._sanitize_id(name)
        col_dir = self._get_collection_dir(user_id, rag_id)
        col_dir.mkdir(parents=True, exist_ok=True)

        now = time.time()
        manifest = UserRAGManifest(
            id=rag_id,
            name=name.strip() or rag_id,
            description=description.strip(),
            created_at=now,
            updated_at=now,
            status="created",
            files=files or [],
            total_chunks=0,
            provider="local_tfidf",
            min_chunk_len=min_chunk_len,
            max_chunk_len=max_chunk_len,
            error_message=""
        )

        manifest_path = col_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(asdict(manifest), f, ensure_ascii=False, indent=2)

        logger.info(f"[UserWorkspaceRAG] Created collection '{rag_id}' for user {user_id}")
        return asdict(manifest)

    def delete_collection(self, user_id: int, rag_id: str) -> bool:
        """Delete an entire user RAG collection and its indices.

        Args:
            user_id (int): User unique identifier.
            rag_id (str): Collection identifier.

        Returns:
            bool: True if deleted successfully, False if not found.
        """
        col_dir = self._get_collection_dir(user_id, rag_id)
        if not col_dir.exists():
            return False

        try:
            shutil.rmtree(col_dir)
            logger.info(f"[UserWorkspaceRAG] Deleted collection '{rag_id}' for user {user_id}")
            return True
        except Exception as ex:
            logger.error(f"[UserWorkspaceRAG] Failed to delete collection '{rag_id}': {ex}")
            return False

    def build_collection(
        self,
        user_id: int,
        rag_id: str,
        files: Optional[List[str]] = None,
        min_chunk_len: Optional[int] = None,
        max_chunk_len: Optional[int] = None,
        provider: str = "local_tfidf",
        api_key: str = ""
    ) -> Dict[str, Any]:
        """Execute cleaning pipeline and build index for the user RAG collection.

        Args:
            user_id (int): User unique identifier.
            rag_id (str): Collection identifier.
            files (Optional[List[str]]): Specific files to include (or default to attached).
            min_chunk_len (Optional[int]): Minimum chunk length override.
            max_chunk_len (Optional[int]): Maximum chunk length override.
            provider (str): Embedding provider ('local_tfidf' or 'gemini').
            api_key (str): Optional API key for external embedding providers.

        Returns:
            Dict[str, Any]: Build summary and updated manifest.
        """
        col_dir = self._get_collection_dir(user_id, rag_id)
        manifest_path = col_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Collection '{rag_id}' not found for user {user_id}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_dict = json.load(f)

        min_len = min_chunk_len if min_chunk_len is not None else manifest_dict.get("min_chunk_len", 20)
        max_len = max_chunk_len if max_chunk_len is not None else manifest_dict.get("max_chunk_len", 1500)
        selected_files = files if files is not None else manifest_dict.get("files", [])

        # Update status to cleaning
        manifest_dict["status"] = "cleaning"
        manifest_dict["updated_at"] = time.time()
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_dict, f, ensure_ascii=False, indent=2)

        user_files_dir = user_manager.get_user_directory(user_id, subfolder="files", create=True)
        cleaner = RAGDocumentCleanerCore(min_chunk_len=min_len, max_chunk_len=max_len)

        all_chunks: List[UserRAGChunk] = []
        processed_files: List[str] = []

        try:
            # Determine files to process
            target_file_paths: List[Path] = []
            if selected_files:
                for fname in selected_files:
                    fpath = user_files_dir / fname
                    if fpath.exists() and fpath.is_file():
                        target_file_paths.append(fpath)
            else:
                # Process all files in user's files folder
                for fpath in user_files_dir.rglob("*"):
                    if fpath.is_file() and not fpath.name.startswith("."):
                        target_file_paths.append(fpath)

            for fpath in target_file_paths:
                rel_name = str(fpath.relative_to(user_files_dir)).replace("\\", "/")
                processed_files.append(rel_name)
                chunk_seq = 0
                for raw_chunk in cleaner.process_file(fpath):
                    chunk_id = f"{rel_name}#c{chunk_seq}"
                    chunk_obj = UserRAGChunk(
                        chunk_id=chunk_id,
                        source_file=rel_name,
                        doc_type=raw_chunk.get("doc_type", fpath.suffix.replace(".", "")),
                        chunk_index=chunk_seq,
                        content=raw_chunk.get("content", ""),
                        length=raw_chunk.get("length", len(raw_chunk.get("content", ""))),
                        meta={"source": rel_name, "chunk_index": chunk_seq}
                    )
                    all_chunks.append(chunk_obj)
                    chunk_seq += 1

            # Save cleaned chunks to cleaned_chunks.jsonl
            chunks_jsonl_path = col_dir / "cleaned_chunks.jsonl"
            with open(chunks_jsonl_path, "w", encoding="utf-8") as f:
                for c in all_chunks:
                    f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

            # Build TF-IDF / vector representations
            self._build_collection_tfidf_index(col_dir, [c.content for c in all_chunks])

            manifest_dict["status"] = "indexed"
            manifest_dict["total_chunks"] = len(all_chunks)
            manifest_dict["files"] = processed_files
            manifest_dict["provider"] = provider
            manifest_dict["min_chunk_len"] = min_len
            manifest_dict["max_chunk_len"] = max_len
            manifest_dict["updated_at"] = time.time()
            manifest_dict["error_message"] = ""

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"[UserWorkspaceRAG] Indexed collection '{rag_id}': {len(all_chunks)} chunks from {len(processed_files)} files")
            return {
                "status": "ok",
                "collection": manifest_dict,
                "chunks_count": len(all_chunks),
                "processed_files": processed_files
            }

        except Exception as ex:
            logger.error(f"[UserWorkspaceRAG] Error building collection '{rag_id}': {ex}")
            manifest_dict["status"] = "error"
            manifest_dict["error_message"] = str(ex)
            manifest_dict["updated_at"] = time.time()
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_dict, f, ensure_ascii=False, indent=2)
            raise

    def _build_collection_tfidf_index(self, col_dir: Path, texts: List[str]) -> None:
        """Construct and save local TF-IDF vocabulary, IDF, and vector matrices.

        Args:
            col_dir (Path): Collection root directory.
            texts (List[str]): Extracted chunk texts.
        """
        tokenized_docs = []
        vocab: Dict[str, int] = {}

        for t in texts:
            words = re.findall(r'\b\w+\b', t.lower())
            tokenized_docs.append(words)
            for w in words:
                if len(w) > 2 and w not in vocab:
                    vocab[w] = len(vocab)

        vocab_path = col_dir / "index_vocab.json"
        idf_path = col_dir / "index_idf.npy"
        vec_path = col_dir / "index_vectors.npy"

        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(vocab, f, ensure_ascii=False, indent=2)

        if not vocab or not texts:
            np.save(str(idf_path), np.zeros(0, dtype=np.float32))
            np.save(str(vec_path), np.zeros((len(texts), 0), dtype=np.float32))
            return

        doc_count = len(tokenized_docs)
        df = np.zeros(len(vocab), dtype=np.float32)
        for words in tokenized_docs:
            unique_words = set(words)
            for w in unique_words:
                if w in vocab:
                    df[vocab[w]] += 1

        idf = np.log((doc_count + 1.0) / (df + 1.0)) + 1.0
        np.save(str(idf_path), idf)

        matrix = np.zeros((len(texts), len(vocab)), dtype=np.float32)
        for i, words in enumerate(tokenized_docs):
            if not words:
                continue
            tf: Dict[int, int] = {}
            for w in words:
                if w in vocab:
                    idx = vocab[w]
                    tf[idx] = tf.get(idx, 0) + 1
            total_w = len(words)
            for idx, count in tf.items():
                matrix[i, idx] = (count / total_w) * idf[idx]

        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        normalized = matrix / norms
        np.save(str(vec_path), normalized)

    def search_collection(
        self,
        user_id: int,
        rag_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Perform semantic / lexical similarity search across the user RAG collection.

        Args:
            user_id (int): User unique identifier.
            rag_id (str): Collection identifier.
            query (str): Search query.
            top_k (int): Number of top results to return.
            min_score (float): Minimum score threshold (0.0 to 1.0).

        Returns:
            List[Dict[str, Any]]: Matched chunk items with similarity scores.
        """
        col_dir = self._get_collection_dir(user_id, rag_id)
        chunks_jsonl_path = col_dir / "cleaned_chunks.jsonl"
        vocab_path = col_dir / "index_vocab.json"
        idf_path = col_dir / "index_idf.npy"
        vec_path = col_dir / "index_vectors.npy"

        if not (chunks_jsonl_path.exists() and vocab_path.exists() and idf_path.exists() and vec_path.exists()):
            return []

        # Load chunks
        chunks: List[Dict[str, Any]] = []
        with open(chunks_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))

        if not chunks:
            return []

        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab: Dict[str, int] = json.load(f)

        if not vocab:
            return []

        idf = np.load(str(idf_path))
        vectors = np.load(str(vec_path))

        # Vectorize query
        words = re.findall(r'\b\w+\b', query.lower())
        q_vec = np.zeros(len(vocab), dtype=np.float32)
        if not words:
            return []

        tf: Dict[int, int] = {}
        for w in words:
            if w in vocab:
                idx = vocab[w]
                tf[idx] = tf.get(idx, 0) + 1

        total_w = len(words)
        for idx, count in tf.items():
            q_vec[idx] = (count / total_w) * idf[idx]

        norm = np.linalg.norm(q_vec)
        if norm > 1e-10:
            q_vec = q_vec / norm
        else:
            return []

        scores = np.dot(vectors, q_vec)
        top_indices = np.argsort(scores)[::-1]

        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score:
                continue
            chunk_data = chunks[idx]
            results.append({
                "chunk_id": chunk_data.get("chunk_id", ""),
                "source_file": chunk_data.get("source_file", ""),
                "doc_type": chunk_data.get("doc_type", ""),
                "chunk_index": chunk_data.get("chunk_index", 0),
                "text": chunk_data.get("content", ""),
                "score": round(score, 4)
            })
            if len(results) >= top_k:
                break

        return results


# Global singleton instance
user_workspace_rag_manager = UserWorkspaceRAGManager()
