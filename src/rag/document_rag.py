# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Document RAG Ingestion and Search Manager
# =============================================================================
# Description:
#   Multi-format document parser, text chunker with overlap, and vector index
#   manager for uploaded knowledge base documents.
#
# File: document_rag.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from header import __root__
from src.logger import logger

_DATA_DIR: Path = __root__ / "data"
_DOCUMENTS_DIR: Path = _DATA_DIR / "rag_documents"
_INDEX_DIR: Path = _DATA_DIR / "rag_index"
_META_FILE: Path = _INDEX_DIR / "document_rag_meta.json"
_CHUNKS_FILE: Path = _INDEX_DIR / "document_rag_chunks.json"


@dataclass
class DocumentChunk:
    """Document text chunk representation."""
    chunk_id: str
    doc_name: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentInfo:
    """Document metadata information."""
    name: str
    size_bytes: int
    modified_at: float
    status: str  # 'indexed', 'pending', 'error'
    chunks_count: int = 0
    error_message: str = ""


class DocumentRAGManager:
    """
    ## hypo69 docblock
    Manager for document uploading, multi-format text extraction,
    chunking, vectorization, and similarity retrieval.
    """

    def __init__(
        self,
        docs_dir: Optional[Path] = None,
        index_dir: Optional[Path] = None,
    ) -> None:
        """Initialize Document RAG Manager.

        Args:
            docs_dir (Optional[Path]): Directory where uploaded documents are stored.
            index_dir (Optional[Path]): Directory where index and chunk metadata are saved.
        """
        self.docs_dir = docs_dir or _DOCUMENTS_DIR
        self.index_dir = index_dir or _INDEX_DIR
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.meta_file = self.index_dir / "document_rag_meta.json"
        self.chunks_file = self.index_dir / "document_rag_chunks.json"

        self.chunks: List[DocumentChunk] = []
        self.vectors: Optional[np.ndarray] = None
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None
        self.meta: Dict[str, Any] = {
            "total_documents": 0,
            "total_chunks": 0,
            "last_built_at": 0.0,
            "provider": "local_tfidf",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "dimension": 0,
            "files": {},
        }
        self._load_state()

    def _load_state(self) -> None:
        """Load stored metadata and chunks from disk."""
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to load metadata: {e}")

        if self.chunks_file.exists():
            try:
                with open(self.chunks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = [DocumentChunk(**item) for item in data]
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to load chunks: {e}")
                self.chunks = []

        vec_file = self.index_dir / "document_rag_vectors.npy"
        if vec_file.exists():
            try:
                self.vectors = np.load(str(vec_file))
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to load vectors: {e}")
                self.vectors = None

        vocab_file = self.index_dir / "document_rag_vocab.json"
        if vocab_file.exists():
            try:
                with open(vocab_file, "r", encoding="utf-8") as f:
                    self.vocab = json.load(f)
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to load vocab: {e}")
                self.vocab = {}

        idf_file = self.index_dir / "document_rag_idf.npy"
        if idf_file.exists():
            try:
                self.idf = np.load(str(idf_file))
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to load idf: {e}")
                self.idf = None

    def _save_state(self) -> None:
        """Persist metadata, chunks, and vectors to disk."""
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.meta, f, ensure_ascii=False, indent=2)

            with open(self.chunks_file, "w", encoding="utf-8") as f:
                json.dump([asdict(c) for c in self.chunks], f, ensure_ascii=False, indent=2)

            if self.vectors is not None:
                vec_file = self.index_dir / "document_rag_vectors.npy"
                np.save(str(vec_file), self.vectors)

            if self.vocab:
                vocab_file = self.index_dir / "document_rag_vocab.json"
                with open(vocab_file, "w", encoding="utf-8") as f:
                    json.dump(self.vocab, f, ensure_ascii=False, indent=2)

            if self.idf is not None:
                idf_file = self.index_dir / "document_rag_idf.npy"
                np.save(str(idf_file), self.idf)
        except Exception as e:
            logger.error(f"[DocumentRAG] Failed to save state: {e}")

    def save_document(self, filename: str, content: bytes) -> DocumentInfo:
        """Save an uploaded document file to docs directory.

        Supports relative paths and subdirectories for folder uploads.

        Args:
            filename (str): Name or relative path of the file.
            content (bytes): Raw binary content.

        Returns:
            DocumentInfo: Stored document info metadata.
        """
        # Clean relative path parts, preserve directory structure
        norm_parts = [
            re.sub(r'[^a-zA-Z0-9_\-\.\u0400-\u04FF]', '_', p)
            for p in Path(filename).parts
            if p not in ("..", ".", "")
        ]
        safe_rel_path = "/".join(norm_parts) if norm_parts else "untitled.txt"
        file_path = self.docs_dir.joinpath(*norm_parts) if norm_parts else self.docs_dir / "untitled.txt"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        info = DocumentInfo(
            name=safe_rel_path,
            size_bytes=len(content),
            modified_at=time.time(),
            status="pending",
            chunks_count=0,
        )

        files = self.meta.get("files", {})
        files[safe_rel_path] = asdict(info)
        self.meta["files"] = files
        self._save_state()
        logger.info(f"[DocumentRAG] Saved document {safe_rel_path} ({len(content)} bytes)")
        return info

    def delete_document(self, filename: str) -> bool:
        """Delete document file and remove its chunks from index.

        Args:
            filename (str): Document file name or relative path.

        Returns:
            bool: True if file was found and removed, False otherwise.
        """
        parts = [p for p in Path(filename).parts if p not in ("..", ".")]
        file_path = self.docs_dir.joinpath(*parts) if parts else self.docs_dir / filename
        found = False
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            found = True

        files = self.meta.get("files", {})
        if filename in files:
            del files[filename]
            self.meta["files"] = files
            found = True

        prev_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.doc_name != filename]
        if len(self.chunks) != prev_count:
            self.vectors = None
            self.vocab = {}
            self.idf = None

        self.meta["total_chunks"] = len(self.chunks)
        self.meta["total_documents"] = len(self.meta.get("files", {}))
        self._save_state()
        logger.info(f"[DocumentRAG] Deleted document {filename}")
        return found

    def list_documents(self) -> List[DocumentInfo]:
        """List all uploaded documents (including subdirectories) with current status.

        Returns:
            List[DocumentInfo]: List of all known documents.
        """
        files_meta = self.meta.get("files", {})
        results: List[DocumentInfo] = []

        for p in self.docs_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                rel_name = p.relative_to(self.docs_dir).as_posix()
                stat = p.stat()
                if rel_name in files_meta:
                    m = files_meta[rel_name]
                    results.append(DocumentInfo(
                        name=rel_name,
                        size_bytes=stat.st_size,
                        modified_at=stat.st_mtime,
                        status=m.get("status", "pending"),
                        chunks_count=m.get("chunks_count", 0),
                        error_message=m.get("error_message", ""),
                    ))
                else:
                    results.append(DocumentInfo(
                        name=rel_name,
                        size_bytes=stat.st_size,
                        modified_at=stat.st_mtime,
                        status="pending",
                        chunks_count=0,
                    ))
        return results

    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from various file formats.

        Args:
            file_path (Path): Path to document file.

        Returns:
            str: Extracted text content.
        """
        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md", ".markdown", ".rst", ".log"]:
            return file_path.read_text(encoding="utf-8", errors="replace")

        if suffix == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, (dict, list)):
                    return json.dumps(data, ensure_ascii=False, indent=2)
                return str(data)
            except Exception:
                return file_path.read_text(encoding="utf-8", errors="replace")

        if suffix in [".csv", ".tsv"]:
            try:
                delimiter = "\t" if suffix == ".tsv" else ","
                text_lines = []
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    for row in reader:
                        text_lines.append(" | ".join(row))
                return "\n".join(text_lines)
            except Exception:
                return file_path.read_text(encoding="utf-8", errors="replace")

        if suffix in [".py", ".js", ".ts", ".html", ".htm", ".css", ".sh", ".ps1", ".sql", ".yaml", ".yml", ".xml"]:
            return file_path.read_text(encoding="utf-8", errors="replace")

        if suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                text_parts = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"[Page {idx + 1}]\n{page_text}")
                return "\n\n".join(text_parts)
            except ImportError:
                logger.warning(f"[DocumentRAG] pypdf not installed for {file_path.name}, reading raw stream")
                return file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to parse PDF {file_path.name}: {e}")
                return ""

        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"[DocumentRAG] Unknown file format text extraction failed: {e}")
            return ""

    def chunk_text(
        self,
        text: str,
        doc_name: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[DocumentChunk]:
        """Split text into overlapping semantic chunks.

        Args:
            text (str): Source text.
            doc_name (str): Document file name.
            chunk_size (int): Target chunk length in characters.
            chunk_overlap (int): Overlap length in characters.

        Returns:
            List[DocumentChunk]: Generated chunks.
        """
        clean_text = text.strip()
        if not clean_text:
            return []

        chunks: List[DocumentChunk] = []
        step = max(1, chunk_size - chunk_overlap)
        pos = 0
        chunk_idx = 0

        while pos < len(clean_text):
            end_pos = min(pos + chunk_size, len(clean_text))
            
            if end_pos < len(clean_text):
                boundary = clean_text.rfind("\n\n", pos + (chunk_size // 2), end_pos)
                if boundary == -1:
                    boundary = clean_text.rfind("\n", pos + (chunk_size // 2), end_pos)
                if boundary == -1:
                    boundary = clean_text.rfind(". ", pos + (chunk_size // 2), end_pos)
                if boundary != -1:
                    end_pos = boundary + 1

            chunk_content = clean_text[pos:end_pos].strip()
            if chunk_content:
                chunk_id = f"{doc_name}#chunk_{chunk_idx}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_name=doc_name,
                    chunk_index=chunk_idx,
                    text=chunk_content,
                    start_char=pos,
                    end_char=end_pos,
                    meta={"doc_name": doc_name, "chunk_index": chunk_idx},
                ))
                chunk_idx += 1

            pos += step

        return chunks

    def _compute_local_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate TF-IDF vector embeddings locally without external API.

        Fits vocabulary and IDF weights on the provided texts, updating internal model state.

        Args:
            texts (List[str]): List of chunk strings.

        Returns:
            np.ndarray: Matrix of shape (N, dim) normalized embeddings.
        """
        tokenized_docs = []
        vocab: Dict[str, int] = {}
        for t in texts:
            words = re.findall(r'\b\w+\b', t.lower())
            tokenized_docs.append(words)
            for w in words:
                if len(w) > 2 and w not in vocab:
                    vocab[w] = len(vocab)

        self.vocab = vocab
        if not vocab:
            self.idf = None
            return np.zeros((len(texts), 0), dtype=np.float32)

        doc_count = len(tokenized_docs)
        df = np.zeros(len(vocab), dtype=np.float32)
        for words in tokenized_docs:
            unique_words = set(words)
            for w in unique_words:
                if w in vocab:
                    df[vocab[w]] += 1

        idf = np.log((doc_count + 1.0) / (df + 1.0)) + 1.0
        self.idf = idf

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
        return normalized

    def _transform_query(self, query: str) -> np.ndarray:
        """Transform query string into normalized vector using existing vocabulary and IDF.

        Args:
            query (str): Query text.

        Returns:
            np.ndarray: Vector of shape (1, dim).
        """
        if not self.vocab or self.idf is None:
            return np.zeros((1, 0), dtype=np.float32)

        words = re.findall(r'\b\w+\b', query.lower())
        vec = np.zeros((1, len(self.vocab)), dtype=np.float32)
        if not words:
            return vec

        tf: Dict[int, int] = {}
        for w in words:
            if w in self.vocab:
                idx = self.vocab[w]
                tf[idx] = tf.get(idx, 0) + 1

        total_w = len(words)
        for idx, count in tf.items():
            vec[0, idx] = (count / total_w) * self.idf[idx]

        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec = vec / norm
        return vec

    def build_index(
        self,
        provider: str = "auto",
        api_key: str = "",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> Dict[str, Any]:
        """Process all documents, chunk texts, and construct vector index.

        Args:
            provider (str): 'gemini', 'local_tfidf', or 'auto'.
            api_key (str): Optional Gemini API key.
            chunk_size (int): Chunk character limit.
            chunk_overlap (int): Overlap characters.

        Returns:
            Dict[str, Any]: Status summary of build process.
        """
        all_chunks: List[DocumentChunk] = []
        files_meta: Dict[str, Any] = {}

        for p in self.docs_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                doc_name = p.relative_to(self.docs_dir).as_posix()
                try:
                    text = self.extract_text(p)
                    doc_chunks = self.chunk_text(text, doc_name, chunk_size, chunk_overlap)
                    all_chunks.extend(doc_chunks)
                    files_meta[doc_name] = {
                        "name": doc_name,
                        "size_bytes": p.stat().st_size,
                        "modified_at": p.stat().st_mtime,
                        "status": "indexed",
                        "chunks_count": len(doc_chunks),
                        "error_message": "",
                    }
                except Exception as e:
                    logger.error(f"[DocumentRAG] Failed to index {doc_name}: {e}")
                    files_meta[doc_name] = {
                        "name": doc_name,
                        "size_bytes": p.stat().st_size,
                        "modified_at": p.stat().st_mtime,
                        "status": "error",
                        "chunks_count": 0,
                        "error_message": str(e),
                    }

        self.chunks = all_chunks
        used_provider = "local_tfidf"

        if (provider == "gemini" or (provider == "auto" and api_key)) and api_key and all_chunks:
            try:
                from src.ai.gemini.rag import GeminiRAG
                gemini_rag = GeminiRAG(api_key=api_key, db_path=self.index_dir / "gemini_doc_rag")
                gemini_rag.clear()
                docs_payload = [
                    {
                        "id": c.chunk_id,
                        "text": c.text,
                        "meta": {"doc_name": c.doc_name, "chunk_index": c.chunk_index},
                    }
                    for c in all_chunks
                ]
                gemini_rag.add_documents(docs_payload)
                used_provider = "gemini"
                self.vectors = None
            except Exception as e:
                logger.warning(f"[DocumentRAG] Gemini embedding failed, falling back to local: {e}")
                self.vectors = self._compute_local_embeddings([c.text for c in all_chunks])
                used_provider = "local_tfidf"
        elif all_chunks:
            self.vectors = self._compute_local_embeddings([c.text for c in all_chunks])
            used_provider = "local_tfidf"
        else:
            self.vectors = None

        self.meta = {
            "total_documents": len(files_meta),
            "total_chunks": len(all_chunks),
            "last_built_at": time.time(),
            "provider": used_provider,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "dimension": int(self.vectors.shape[1]) if self.vectors is not None else 0,
            "files": files_meta,
        }
        self._save_state()
        logger.info(f"[DocumentRAG] Built index: {len(files_meta)} docs, {len(all_chunks)} chunks, provider={used_provider}")
        return self.get_status()

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        api_key: str = "",
    ) -> List[Dict[str, Any]]:
        """Semantic search query across all indexed document chunks.

        Args:
            query (str): Search query string.
            top_k (int): Maximum number of results.
            min_score (float): Minimum similarity threshold (0.0 to 1.0).
            api_key (str): Optional Gemini API key if gemini provider is active.

        Returns:
            List[Dict[str, Any]]: Ranked results list with chunk text, score, and source doc.
        """
        clean_query = query.strip()
        if not clean_query or not self.chunks:
            return []

        if self.meta.get("provider") == "gemini" and api_key:
            try:
                from src.ai.gemini.rag import GeminiRAG
                gemini_rag = GeminiRAG(api_key=api_key, db_path=self.index_dir / "gemini_doc_rag")
                raw_results = gemini_rag.search(clean_query, top_k=top_k, threshold=min_score)
                formatted = []
                for r in raw_results:
                    meta = r.get("meta", {})
                    formatted.append({
                        "chunk_id": r.get("id", ""),
                        "doc_name": meta.get("doc_name", ""),
                        "chunk_index": meta.get("chunk_index", 0),
                        "score": round(float(r.get("score", 0.0)), 4),
                        "text": r.get("text", ""),
                    })
                return formatted
            except Exception as e:
                logger.warning(f"[DocumentRAG] Gemini search failed, falling back: {e}")

        all_texts = [c.text for c in self.chunks]
        if (
            self.vectors is None
            or self.vectors.shape[0] != len(all_texts)
            or not self.vocab
            or self.idf is None
            or self.vectors.shape[1] != len(self.vocab)
        ):
            self.vectors = self._compute_local_embeddings(all_texts)

        query_vec = self._transform_query(clean_query)
        if query_vec.shape[1] == 0 or np.linalg.norm(query_vec) < 1e-10:
            return []

        similarities = np.dot(self.vectors, query_vec.T).flatten()
        top_indices = np.argsort(similarities)[::-1][:min(top_k, len(self.chunks))]

        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_score and score > 0.0:
                c = self.chunks[idx]
                results.append({
                    "chunk_id": c.chunk_id,
                    "doc_name": c.doc_name,
                    "chunk_index": c.chunk_index,
                    "score": round(score, 4),
                    "text": c.text,
                })
        return results

    def get_status(self) -> Dict[str, Any]:
        """Return status dictionary of the document RAG subsystem.

        Returns:
            Dict[str, Any]: Subsystem health and index status.
        """
        return {
            "total_documents": len(self.list_documents()),
            "total_chunks": len(self.chunks),
            "last_built_at": self.meta.get("last_built_at", 0.0),
            "provider": self.meta.get("provider", "local_tfidf"),
            "chunk_size": self.meta.get("chunk_size", 500),
            "chunk_overlap": self.meta.get("chunk_overlap", 50),
            "dimension": self.meta.get("dimension", 0),
            "documents": [asdict(d) for d in self.list_documents()],
        }


_doc_rag_manager: Optional[DocumentRAGManager] = None


def get_document_rag_manager() -> DocumentRAGManager:
    """Get or create singleton DocumentRAGManager instance."""
    global _doc_rag_manager
    if _doc_rag_manager is None:
        _doc_rag_manager = DocumentRAGManager()
    return _doc_rag_manager
