# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Document RAG Ingestion and Versioned Search Manager
# =============================================================================
# Description:
#   Multi-format document parser, text chunker with overlap, incremental version
#   tracking with SHA-256 hashing, and vector index manager for knowledge base.
#
# File: document_rag.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from header import __root__
from logger import logger

_DATA_DIR: Path = __root__ / "data"
_DOCUMENTS_DIR: Path = _DATA_DIR / "rag_documents"
_INDEX_DIR: Path = _DATA_DIR / "rag_index"
_META_FILE: Path = _INDEX_DIR / "document_rag_meta.json"
_CHUNKS_FILE: Path = _INDEX_DIR / "document_rag_chunks.json"

SUPPORTED_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".markdown", ".rst", ".log",
    ".json", ".csv", ".tsv",
    ".py", ".js", ".ts", ".html", ".htm", ".css", ".sh", ".ps1", ".sql", ".yaml", ".yml", ".xml",
    ".pdf",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
}

IMAGE_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
}

PDF_EXTENSION: str = ".pdf"


def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hash of binary content.

    Args:
        content (bytes): Raw file bytes.

    Returns:
        str: Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(content).hexdigest()


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file on disk.

    Args:
        file_path (Path): Path to the target file.

    Returns:
        str: Hex-encoded SHA-256 digest or empty string on read error.
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"[DocumentRAG] Failed to compute hash for {file_path}: {e}")
        return ""


@dataclass
class DocumentChunk:
    """Document text chunk representation with temporal and version tracking."""
    chunk_id: str
    doc_name: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    version: int = 1
    version_timestamp: float = 0.0
    is_latest: bool = True
    content_hash: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentInfo:
    """Document metadata information with complete version history."""
    name: str
    size_bytes: int
    modified_at: float
    status: str  # 'indexed', 'pending', 'error', 'archived'
    chunks_count: int = 0
    error_message: str = ""
    version: int = 1
    is_latest: bool = True
    content_hash: str = ""
    versions: List[Dict[str, Any]] = field(default_factory=list)


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
        
        # Initialize PixelRAG provider for image indexing
        self._pixel_rag: Optional[Any] = None
        self._init_pixel_rag()
        
        self._load_state()

    def _load_state(self) -> None:
        """Load stored metadata and chunks from disk with backward compatibility."""
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
                    loaded_chunks: List[DocumentChunk] = []
                    for item in data:
                        # Ensure backward compatibility for legacy chunks without version fields
                        if "version" not in item:
                            item["version"] = 1
                        if "version_timestamp" not in item:
                            item["version_timestamp"] = 0.0
                        if "is_latest" not in item:
                            item["is_latest"] = True
                        if "content_hash" not in item:
                            item["content_hash"] = ""
                        loaded_chunks.append(DocumentChunk(**item))
                    self.chunks = loaded_chunks
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

    def _init_pixel_rag(self) -> None:
        """Initialize PixelRAG provider for image indexing."""
        try:
            from src.rag.pixel import PixelRAG
            pixel_index_dir = self.index_dir / "pixel_rag"
            self._pixel_rag = PixelRAG(index_dir=pixel_index_dir)
            logger.info("[DocumentRAG] PixelRAG provider initialized")
        except ImportError:
            logger.warning("[DocumentRAG] PixelRAG not available (missing dependencies)")
            self._pixel_rag = None
        except Exception as e:
            logger.warning(f"[DocumentRAG] Failed to initialize PixelRAG: {e}")
            self._pixel_rag = None

    def _get_pixel_rag(self) -> Optional[Any]:
        """Get PixelRAG provider, initializing if needed."""
        if self._pixel_rag is None:
            self._init_pixel_rag()
        return self._pixel_rag

    def save_document(self, filename: str, content: bytes) -> DocumentInfo:
        """Save or update an uploaded document file with incremental versioning.

        If a document with the same name exists:
        - If content hash matches, returns existing info.
        - If content has changed, increments version, marks older chunks as not latest,
          and appends new chunks without deleting historical ones.

        Args:
            filename (str): Name or relative path of the file.
            content (bytes): Raw binary content.

        Returns:
            DocumentInfo: Stored document info metadata.
        """
        norm_parts = [
            re.sub(r'[^a-zA-Z0-9_\-\.\u0400-\u04FF]', '_', p)
            for p in Path(filename).parts
            if p not in ("..", ".", "")
        ]
        safe_rel_path = "/".join(norm_parts) if norm_parts else "untitled.txt"
        file_path = self.docs_dir.joinpath(*norm_parts) if norm_parts else self.docs_dir / "untitled.txt"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        new_hash = compute_content_hash(content)
        current_time = time.time()
        files = self.meta.get("files", {})
        existing = files.get(safe_rel_path)

        if existing and existing.get("content_hash") == new_hash:
            # Content is identical, no new version needed
            return DocumentInfo(**existing)

        version = 1
        history: List[Dict[str, Any]] = []
        if existing:
            version = existing.get("version", 1) + 1
            history = existing.get("versions", [])
            if not history:
                history.append({
                    "version": existing.get("version", 1),
                    "modified_at": existing.get("modified_at", current_time),
                    "size_bytes": existing.get("size_bytes", len(content)),
                    "content_hash": existing.get("content_hash", ""),
                    "chunks_count": existing.get("chunks_count", 0),
                })
            # Mark previous chunks as superseded
            for c in self.chunks:
                if c.doc_name == safe_rel_path:
                    c.is_latest = False

        history.append({
            "version": version,
            "modified_at": current_time,
            "size_bytes": len(content),
            "content_hash": new_hash,
            "chunks_count": 0,
        })

        info = DocumentInfo(
            name=safe_rel_path,
            size_bytes=len(content),
            modified_at=current_time,
            status="pending",
            chunks_count=0,
            version=version,
            is_latest=True,
            content_hash=new_hash,
            versions=history,
        )

        files[safe_rel_path] = asdict(info)
        self.meta["files"] = files
        self._save_state()
        logger.info(f"[DocumentRAG] Saved document {safe_rel_path} v{version} ({len(content)} bytes, hash={new_hash[:8]})")
        return info

    def delete_document(self, filename: str, purge_history: bool = True) -> bool:
        """Delete document file and remove or archive its chunks from index.

        Args:
            filename (str): Document file name or relative path.
            purge_history (bool): If True, removes all versions and chunks completely.
                If False (soft delete), keeps historical chunks marked is_latest=False.

        Returns:
            bool: True if file was found and updated/removed.
        """
        parts = [p for p in Path(filename).parts if p not in ("..", ".")]
        file_path = self.docs_dir.joinpath(*parts) if parts else self.docs_dir / filename
        found = False
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            found = True

        files = self.meta.get("files", {})
        if filename in files:
            found = True
            if purge_history:
                del files[filename]
                prev_count = len(self.chunks)
                self.chunks = [c for c in self.chunks if c.doc_name != filename]
                if len(self.chunks) != prev_count:
                    self.vectors = None
                    self.vocab = {}
                    self.idf = None
            else:
                files[filename]["status"] = "archived"
                files[filename]["is_latest"] = False
                for c in self.chunks:
                    if c.doc_name == filename:
                        c.is_latest = False

            self.meta["files"] = files
            self.meta["total_chunks"] = len(self.chunks)
            self.meta["total_documents"] = len(self.meta.get("files", {}))
            self._save_state()

        logger.info(f"[DocumentRAG] Deleted document {filename} (purge={purge_history})")
        return found

    def list_documents(self, include_archived: bool = False) -> List[DocumentInfo]:
        """List all documents in metadata registry with current version status.

        Args:
            include_archived (bool): Whether to include archived/soft-deleted documents.

        Returns:
            List[DocumentInfo]: List of known documents.
        """
        files_meta = self.meta.get("files", {})
        results: List[DocumentInfo] = []

        # Include registered metadata files
        for name, m in files_meta.items():
            if not include_archived and m.get("status") == "archived":
                continue
            results.append(DocumentInfo(
                name=name,
                size_bytes=m.get("size_bytes", 0),
                modified_at=m.get("modified_at", 0.0),
                status=m.get("status", "pending"),
                chunks_count=m.get("chunks_count", 0),
                error_message=m.get("error_message", ""),
                version=m.get("version", 1),
                is_latest=m.get("is_latest", True),
                content_hash=m.get("content_hash", ""),
                versions=m.get("versions", []),
            ))

        # Check for unindexed physical files in docs_dir
        if self.docs_dir.exists():
            for p in self.docs_dir.rglob("*"):
                if p.is_file() and not p.name.startswith("."):
                    rel_name = p.relative_to(self.docs_dir).as_posix()
                    if rel_name not in files_meta:
                        stat = p.stat()
                        results.append(DocumentInfo(
                            name=rel_name,
                            size_bytes=stat.st_size,
                            modified_at=stat.st_mtime,
                            status="pending",
                            chunks_count=0,
                            version=1,
                            is_latest=True,
                            content_hash=compute_file_hash(p),
                            versions=[],
                        ))
        return results

    def get_document_history(self, filename: str) -> Dict[str, Any]:
        """Retrieve complete version history and chunks statistics for a document.

        Args:
            filename (str): Name or relative path of the document.

        Returns:
            Dict[str, Any]: Detailed version history and current state.
        """
        files = self.meta.get("files", {})
        info = files.get(filename)
        if not info:
            return {"found": False, "filename": filename, "versions": []}

        doc_chunks = [c for c in self.chunks if c.doc_name == filename]
        version_chunks_count: Dict[int, int] = {}
        for c in doc_chunks:
            version_chunks_count[c.version] = version_chunks_count.get(c.version, 0) + 1

        history_versions = info.get("versions", [])
        enriched_versions = []
        for v in history_versions:
            v_num = v.get("version", 1)
            enriched_versions.append({
                **v,
                "chunks_count": version_chunks_count.get(v_num, v.get("chunks_count", 0)),
            })

        return {
            "found": True,
            "filename": filename,
            "current_version": info.get("version", 1),
            "is_latest": info.get("is_latest", True),
            "total_chunks_stored": len(doc_chunks),
            "versions": enriched_versions,
        }

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
        version: int = 1,
        version_timestamp: float = 0.0,
        is_latest: bool = True,
        content_hash: str = "",
    ) -> List[DocumentChunk]:
        """Split text into overlapping semantic chunks with version metadata.

        Args:
            text (str): Source text.
            doc_name (str): Document file name.
            chunk_size (int): Target chunk length in characters.
            chunk_overlap (int): Overlap length in characters.
            version (int): Document version number.
            version_timestamp (float): Timestamp of document version.
            is_latest (bool): Whether this chunk belongs to the latest version.
            content_hash (str): SHA-256 hash of document content.

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
                chunk_id = f"{doc_name}#chunk_{chunk_idx}#v{version}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_name=doc_name,
                    chunk_index=chunk_idx,
                    text=chunk_content,
                    start_char=pos,
                    end_char=end_pos,
                    version=version,
                    version_timestamp=version_timestamp,
                    is_latest=is_latest,
                    content_hash=content_hash,
                    meta={
                        "doc_name": doc_name,
                        "chunk_index": chunk_idx,
                        "version": version,
                        "version_timestamp": version_timestamp,
                        "is_latest": is_latest,
                        "content_hash": content_hash,
                    },
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
        """Incrementally index documents in docs_dir, preserving existing historical chunks.

        Args:
            provider (str): 'gemini', 'local_tfidf', or 'auto'.
            api_key (str): Optional Gemini API key.
            chunk_size (int): Chunk character limit.
            chunk_overlap (int): Overlap characters.

        Returns:
            Dict[str, Any]: Status summary of build process.
        """
        return self.scan_and_index_directory(
            dir_path=self.docs_dir,
            provider=provider,
            api_key=api_key,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            recursive=True,
        )

    def scan_and_index_directory(
        self,
        dir_path: Path,
        provider: str = "auto",
        api_key: str = "",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Scan any local or external directory incrementally, detecting changed/new files.

        Tracks versions, marks older versions as is_latest=False, and indexes new chunks
        without discarding historical document states.

        Args:
            dir_path (Path): Path to directory to scan (e.g. docs_dir or 'G:/My Drive').
            provider (str): Vector provider ('auto', 'gemini', 'local_tfidf').
            api_key (str): Optional Gemini API key.
            chunk_size (int): Chunk size in characters.
            chunk_overlap (int): Overlap size in characters.
            recursive (bool): Whether to scan subdirectories.
            extensions (Optional[List[str]]): Specific file extensions to filter.

        Returns:
            Dict[str, Any]: Summary of scan and indexing results.
        """
        dir_path = Path(dir_path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(f"Directory '{dir_path}' does not exist or is not a directory.")

        allowed_exts = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        files_meta = self.meta.setdefault("files", {})
        new_chunks: List[DocumentChunk] = []
        files_scanned = 0
        files_added = 0
        files_updated = 0
        files_skipped = 0

        pattern = "**/*" if recursive else "*"
        for p in dir_path.glob(pattern):
            if not p.is_file() or p.name.startswith("."):
                continue
            if p.suffix.lower() not in allowed_exts:
                continue

            files_scanned += 1
            rel_name = p.relative_to(dir_path).as_posix()
            file_stat = p.stat()
            file_hash = compute_file_hash(p)
            file_mtime = file_stat.st_mtime
            file_size = file_stat.st_size

            existing = files_meta.get(rel_name)
            has_existing_chunks = any(c.doc_name == rel_name for c in self.chunks)
            if existing and existing.get("status") == "indexed" and existing.get("content_hash") == file_hash and has_existing_chunks:
                # File has not changed and is already indexed, skip re-chunking
                files_skipped += 1
                continue

            version = 1
            history: List[Dict[str, Any]] = []
            if existing and existing.get("status") == "indexed" and has_existing_chunks:
                files_updated += 1
                version = existing.get("version", 1) + 1
                history = existing.get("versions", [])
                if not history:
                    history.append({
                        "version": existing.get("version", 1),
                        "modified_at": existing.get("modified_at", file_mtime),
                        "size_bytes": existing.get("size_bytes", file_size),
                        "content_hash": existing.get("content_hash", ""),
                        "chunks_count": existing.get("chunks_count", 0),
                    })
                # Mark previous chunks as superseded
                for c in self.chunks:
                    if c.doc_name == rel_name:
                        c.is_latest = False
            else:
                files_added += 1
                version = existing.get("version", 1) if existing else 1
                history = existing.get("versions", []) if existing else []

            try:
                # Check if this is an image file
                is_image = p.suffix.lower() in IMAGE_EXTENSIONS
                
                if is_image:
                    # Route to PixelRAG for image indexing
                    pixel_rag = self._get_pixel_rag()
                    if pixel_rag is None:
                        raise RuntimeError("PixelRAG provider not available")
                    
                    # Create image document for PixelRAG
                    doc_for_pixel = {
                        "id": rel_name,
                        "text": str(p),  # Full path to image
                        "path": str(p),
                        "meta": {
                            "image_path": str(p),
                            "doc_name": rel_name,
                            "version": version,
                            "version_timestamp": file_mtime,
                            "content_hash": file_hash,
                            "source_type": "image",
                        }
                    }
                    
                    # Index in PixelRAG (synchronous wrapper)
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    indexed_count = loop.run_until_complete(
                        pixel_rag.add_documents([doc_for_pixel])
                    )
                    
                    doc_chunks = []  # No text chunks for images
                    indexed_via = "pixel"
                else:
                    # Text extraction for non-image files
                    text = self.extract_text(p)
                    doc_chunks = self.chunk_text(
                        text=text,
                        doc_name=rel_name,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        version=version,
                        version_timestamp=file_mtime,
                        is_latest=True,
                        content_hash=file_hash,
                    )
                    indexed_via = "text"
                
                new_chunks.extend(doc_chunks)

                existing_entry = next((item for item in history if item.get("version") == version), None)
                if existing_entry:
                    existing_entry["chunks_count"] = len(doc_chunks)
                    existing_entry["modified_at"] = file_mtime
                    existing_entry["size_bytes"] = file_size
                    existing_entry["content_hash"] = file_hash
                else:
                    history.append({
                        "version": version,
                        "modified_at": file_mtime,
                        "size_bytes": file_size,
                        "content_hash": file_hash,
                        "chunks_count": len(doc_chunks),
                    })

                files_meta[rel_name] = asdict(DocumentInfo(
                    name=rel_name,
                    size_bytes=file_size,
                    modified_at=file_mtime,
                    status="indexed",
                    chunks_count=len(doc_chunks),
                    error_message="",
                    version=version,
                    is_latest=True,
                    content_hash=file_hash,
                    versions=history,
                ))
                
                # Store indexing provider info in metadata
                if rel_name not in files_meta:
                    files_meta[rel_name] = {}
                files_meta[rel_name]["indexed_via"] = indexed_via
            except Exception as e:
                logger.error(f"[DocumentRAG] Failed to scan/index {rel_name}: {e}")
                files_meta[rel_name] = asdict(DocumentInfo(
                    name=rel_name,
                    size_bytes=file_size,
                    modified_at=file_mtime,
                    status="error",
                    chunks_count=0,
                    error_message=str(e),
                    version=version,
                    is_latest=False,
                    content_hash=file_hash,
                    versions=history,
                ))

        if new_chunks:
            self.chunks.extend(new_chunks)

        used_provider = self.meta.get("provider", "local_tfidf")
        if (provider == "gemini" or (provider == "auto" and api_key)) and api_key and self.chunks:
            try:
                from src.ai.gemini.rag import GeminiRAG
                gemini_rag = GeminiRAG(api_key=api_key, db_path=self.index_dir / "gemini_doc_rag")
                docs_payload = [
                    {
                        "id": c.chunk_id,
                        "text": c.text,
                        "meta": {
                            "doc_name": c.doc_name,
                            "chunk_index": c.chunk_index,
                            "version": c.version,
                            "version_timestamp": c.version_timestamp,
                            "is_latest": c.is_latest,
                            "content_hash": c.content_hash,
                        },
                    }
                    for c in (new_chunks if new_chunks else self.chunks)
                ]
                gemini_rag.add_documents(docs_payload)
                used_provider = "gemini"
                self.vectors = None
            except Exception as e:
                logger.warning(f"[DocumentRAG] Gemini embedding failed, updating local TF-IDF: {e}")
                self.vectors = self._compute_local_embeddings([c.text for c in self.chunks])
                used_provider = "local_tfidf"
        elif self.chunks:
            self.vectors = self._compute_local_embeddings([c.text for c in self.chunks])
            used_provider = "local_tfidf"
        else:
            self.vectors = None

        self.meta.update({
            "total_documents": len(files_meta),
            "total_chunks": len(self.chunks),
            "last_built_at": time.time(),
            "provider": used_provider,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "dimension": int(self.vectors.shape[1]) if self.vectors is not None else 0,
            "files": files_meta,
        })
        self._save_state()

        logger.info(
            f"[DocumentRAG] Scanned '{dir_path}': {files_scanned} files, added={files_added}, "
            f"updated={files_updated}, skipped={files_skipped}, new_chunks={len(new_chunks)}"
        )
        return {
            "scanned_directory": str(dir_path),
            "files_scanned": files_scanned,
            "files_added": files_added,
            "files_updated": files_updated,
            "files_skipped": files_skipped,
            "new_chunks_added": len(new_chunks),
            "total_documents": len(files_meta),
            "total_chunks": len(self.chunks),
            "provider": used_provider,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        api_key: str = "",
        version_filter: str = "latest",
    ) -> List[Dict[str, Any]]:
        """Semantic search query across indexed document chunks with version filtering.

        Automatically routes text queries to PixelRAG if images are indexed,
        alongside text results.

        Args:
            query (str): Search query string.
            top_k (int): Maximum number of results.
            min_score (float): Minimum similarity threshold (0.0 to 1.0).
            api_key (str): Optional Gemini API key if gemini provider is active.
            version_filter (str): Version filter mode:
                - 'latest' (default): Only return latest active version chunks.
                - 'all': Return matches across all historical versions.
                - 'v1', 'v2', '1', '2': Return matches from specific version.
                - '<float_timestamp>': Return matching version as of target timestamp.

        Returns:
            List[Dict[str, Any]]: Ranked results list with chunk text, score, version metadata.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        results: List[Dict[str, Any]] = []

        # Try text search if text chunks exist
        if self.chunks:
            results.extend(self._search_text(
                clean_query, top_k, min_score, api_key, version_filter
            ))

        # Try pixel search if PixelRAG has indexed images
        pixel_rag = self._get_pixel_rag()
        if pixel_rag is not None:
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                pixel_results = loop.run_until_complete(
                    pixel_rag.search(clean_query, top_k=top_k, threshold=min_score)
                )
                
                # Convert PixelRAG results to standard format
                for pr in pixel_results:
                    results.append({
                        "chunk_id": pr.get("id", ""),
                        "doc_name": pr.get("meta", {}).get("doc_name", ""),
                        "text": pr.get("text", ""),  # Image path
                        "score": pr.get("score", 0.0),
                        "source_type": "pixel",
                        "source_path": pr.get("text", ""),
                        "meta": pr.get("meta", {}),
                    })
            except Exception as e:
                logger.warning(f"[DocumentRAG] PixelRAG search failed: {e}")

        # Sort by score and limit to top_k
        results = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]
        return results

    def _search_text(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        api_key: str = "",
        version_filter: str = "latest",
    ) -> List[Dict[str, Any]]:
        """Search text chunks using configured provider (Gemini or local TF-IDF)."""
        if not self.chunks:
            return []

        # 1. Gemini provider search
        if self.meta.get("provider") == "gemini" and api_key:
            try:
                from src.ai.gemini.rag import GeminiRAG
                gemini_rag = GeminiRAG(api_key=api_key, db_path=self.index_dir / "gemini_doc_rag")
                raw_results = gemini_rag.search(query, top_k=top_k * 3, threshold=min_score)
                formatted = []
                for r in raw_results:
                    meta = r.get("meta", {})
                    is_latest = meta.get("is_latest", True)
                    version = meta.get("version", 1)
                    ts = meta.get("version_timestamp", 0.0)

                    if not self._matches_version_filter(version, is_latest, ts, version_filter):
                        continue

                    formatted.append({
                        "chunk_id": r.get("id", ""),
                        "doc_name": meta.get("doc_name", ""),
                        "chunk_index": meta.get("chunk_index", 0),
                        "score": round(float(r.get("score", 0.0)), 4),
                        "text": r.get("text", ""),
                        "version": version,
                        "version_timestamp": ts,
                        "is_latest": is_latest,
                        "content_hash": meta.get("content_hash", ""),
                        "source_type": "text",
                    })
                    if len(formatted) >= top_k:
                        break
                return formatted
            except Exception as e:
                logger.warning(f"[DocumentRAG] Gemini search failed, falling back to local TF-IDF: {e}")

        # 2. Local TF-IDF search
        all_texts = [c.text for c in self.chunks]
        if (
            self.vectors is None
            or self.vectors.shape[0] != len(all_texts)
            or not self.vocab
            or self.idf is None
            or self.vectors.shape[1] != len(self.vocab)
        ):
            self.vectors = self._compute_local_embeddings(all_texts)

        query_vec = self._transform_query(query)
        if query_vec.shape[1] == 0 or np.linalg.norm(query_vec) < 1e-10:
            return []

        similarities = np.dot(self.vectors, query_vec.T).flatten()
        sorted_indices = np.argsort(similarities)[::-1]

        results: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            score = float(similarities[idx])
            if score < min_score or score <= 0.0:
                continue

            c = self.chunks[idx]
            if not self._matches_version_filter(c.version, c.is_latest, c.version_timestamp, version_filter):
                continue

            results.append({
                "chunk_id": c.chunk_id,
                "doc_name": c.doc_name,
                "chunk_index": c.chunk_index,
                "score": round(score, 4),
                "text": c.text,
                "version": c.version,
                "version_timestamp": c.version_timestamp,
                "is_latest": c.is_latest,
                "content_hash": c.content_hash,
                "source_type": "text",
            })
            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _matches_version_filter(
        version: int,
        is_latest: bool,
        version_timestamp: float,
        version_filter: str,
    ) -> bool:
        """Check whether a chunk satisfies the specified version filter.

        Args:
            version (int): Chunk version number.
            is_latest (bool): Whether chunk is the latest version.
            version_timestamp (float): Timestamp when version was created.
            version_filter (str): Filter rule ('latest', 'all', 'vX', or timestamp).

        Returns:
            bool: True if chunk matches filter.
        """
        rule = version_filter.strip().lower()
        if rule == "all":
            return True
        if rule == "latest":
            return is_latest
        if rule.startswith("v") and rule[1:].isdigit():
            return version == int(rule[1:])
        if rule.isdigit():
            return version == int(rule)
        try:
            target_ts = float(rule)
            return version_timestamp <= target_ts
        except ValueError:
            return is_latest

    def get_status(self) -> Dict[str, Any]:
        """Return status dictionary of the document RAG subsystem.

        Returns:
            Dict[str, Any]: Subsystem health, index status, and version metrics.
        """
        docs = self.list_documents()
        total_versions = sum(len(d.versions) if d.versions else 1 for d in docs)
        return {
            "total_documents": len(docs),
            "total_versions": total_versions,
            "total_chunks": len(self.chunks),
            "last_built_at": self.meta.get("last_built_at", 0.0),
            "provider": self.meta.get("provider", "local_tfidf"),
            "chunk_size": self.meta.get("chunk_size", 500),
            "chunk_overlap": self.meta.get("chunk_overlap", 50),
            "dimension": self.meta.get("dimension", 0),
            "documents": [asdict(d) for d in docs],
        }


_doc_rag_manager: Optional[DocumentRAGManager] = None


def get_document_rag_manager() -> DocumentRAGManager:
    """Get or create singleton DocumentRAGManager instance."""
    global _doc_rag_manager
    if _doc_rag_manager is None:
        _doc_rag_manager = DocumentRAGManager()
    return _doc_rag_manager
