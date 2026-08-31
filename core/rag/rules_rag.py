# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Semantic search indexing for rules and prompts
# =============================================================================
# Description:
#   FAISS-based vector indexing and semantic search for module prompts
#   and rules from the prompts directory.
#
# File: rules_rag.py
# Project: ai-breadboard
# Package: core.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple

from core.logger import logger
from header import __root__

_AI_PROMPTS_ROOT: Path = __root__ / ".ai" / "prompts"
_PROMPTS_ROOT: Path = _AI_PROMPTS_ROOT if _AI_PROMPTS_ROOT.exists() else (__root__ / "prompts")
_TMP_RAG_DIR: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'rag'
_DEFAULT_INDEX_PATH: Path = _TMP_RAG_DIR / "rules.index"
_DEFAULT_DOCUMENTS_PATH: Path = _TMP_RAG_DIR / "documents.json"

_LEGACY_RAG_DIR: Path = __root__ / "rag"
_LEGACY_INDEX_PATH: Path = _LEGACY_RAG_DIR / "rules.index"
_LEGACY_DOCUMENTS_PATH: Path = _LEGACY_RAG_DIR / "documents.json"

_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
_TARGET_GLOBS: List[str] = ["**/*.md", "**/*.json"]
_EXCLUDE_NAMES: set[str] = {"README.md"}

@dataclass
class RulesSearchResult:
    """Search result from the rules index."""
    file: str
    path: str
    text: str
    score: float

def collect_prompt_documents(prompts_root: Path = _PROMPTS_ROOT) -> List[Dict[str, str]]:
    """
    ## hypo69 docblock
    Collects document corpus from the prompts directory.

    Args:
        prompts_root (Path): Root directory path of prompt files.

    Returns:
        List[Dict[str, str]]: List of documents in format {"file": str, "path": str, "text": str}.
    """
    documents: List[Dict[str, str]] = []
    if not prompts_root.exists():
        logger.warning(f"[RulesRAG] Prompts directory not found: {prompts_root}")
        return documents

    for glob_pat in _TARGET_GLOBS:
        for file_path in sorted(prompts_root.glob(glob_pat)):
            if not file_path.is_file() or file_path.name in _EXCLUDE_NAMES:
                continue

            rel_path: str = str(file_path.relative_to(prompts_root)).replace("\\", "/")
            raw_text: str = file_path.read_text(encoding="utf-8").strip()

            if file_path.suffix == ".json":
                text: str = f"[File: {file_path.name}]\n{raw_text}"
            else:
                text = raw_text

            documents.append({
                "file": file_path.name,
                "path": rel_path,
                "text": text,
            })
    return documents

def build_rules_index(
    prompts_root: Path = _PROMPTS_ROOT,
    output_dir: Path = _TMP_RAG_DIR,
) -> Tuple[Path, Path]:
    """
    ## hypo69 docblock
    Builds a FAISS index from prompt files and saves the documents and index.

    Args:
        prompts_root (Path): Path to the prompts directory.
        output_dir (Path): Directory for saving rules.index and documents.json.

    Returns:
        Tuple[Path, Path]: Paths to the saved index and documents file.
    """
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "rules.index"
    docs_path = output_dir / "documents.json"

    documents = collect_prompt_documents(prompts_root)
    if not documents:
        raise RuntimeError(f"Prompt documents not found in {prompts_root}")

    docs_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    texts = [doc["text"] for doc in documents]
    model = SentenceTransformer(_MODEL_NAME)
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors.astype(np.float32))

    faiss.write_index(index, str(index_path))
    logger.info(f"[RulesRAG] Index successfully built: {index_path} ({len(documents)} documents)")
    return index_path, docs_path

_ALWAYS_INCLUDE: List[str] = [
    "identity.md",
    "categories.md",
]

class RulesRAG:
    """
    ## hypo69 docblock
    Semantic search across module prompts using a vector FAISS index.
    """

    def __init__(self, index_path: Path = _DEFAULT_INDEX_PATH, docs_path: Path = _DEFAULT_DOCUMENTS_PATH) -> None:
        """
        ## hypo69 docblock
        Initializes and loads the rules index and document corpus.
        """
        # Search for index: first in tmp/rag, then in fallback paths
        resolved_index = index_path
        resolved_docs = docs_path
        if not resolved_index.exists() and _LEGACY_INDEX_PATH.exists():
            resolved_index = _LEGACY_INDEX_PATH
            resolved_docs = _LEGACY_DOCUMENTS_PATH

        if not resolved_index.exists() or not resolved_docs.exists():
            try:
                resolved_index, resolved_docs = build_rules_index(_PROMPTS_ROOT, _TMP_RAG_DIR)
            except Exception as e:
                raise FileNotFoundError(
                    f"Failed to find or rebuild FAISS rules index: {e}"
                )

        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer

        self._faiss = faiss
        self._np = np
        self._index = faiss.read_index(str(resolved_index))
        self._documents: List[Dict[str, Any]] = json.loads(
            resolved_docs.read_text(encoding="utf-8")
        )
        self._model: SentenceTransformer = SentenceTransformer(
            _MODEL_NAME,
            local_files_only=True,
        )

    def search(self, query: str, top_k: int = 4) -> List[RulesSearchResult]:
        """
        ## hypo69 docblock
        Performs semantic search across the rules corpus.

        Args:
            query (str): Query in natural language.
            top_k (int): Number of results to return.

        Returns:
            List[RulesSearchResult]: List of relevant module prompts.
        """
        if not query.strip():
            return []

        vector = self._model.encode([query], convert_to_numpy=True).astype(self._np.float32)
        distances, indices = self._index.search(vector, top_k)

        results: List[RulesSearchResult] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            results.append(RulesSearchResult(
                file=doc["file"],
                path=doc["path"],
                text=doc["text"],
                score=float(dist),
            ))
        return results

    def build_context(self, query: str, top_k: int = 4) -> str:
        """
        ## hypo69 docblock
        Builds text context from found documents for insertion into the system prompt.
        """
        always_docs: List[str] = []
        for doc in self._documents:
            if doc["file"] in _ALWAYS_INCLUDE:
                always_docs.append(doc["text"].strip())

        search_results = self.search(query, top_k=top_k)
        search_docs: List[str] = []
        for result in search_results:
            if result.file not in _ALWAYS_INCLUDE:
                search_docs.append(result.text.strip())

        all_parts = always_docs + search_docs
        return "\n\n---\n\n".join(all_parts)

