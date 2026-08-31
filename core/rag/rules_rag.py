# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Результат поиска по индексу правил.
# =============================================================================
# Description:
#   Индексация и семантический поиск по Moduleным промптам и правилам из prompts/.
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
    """Результат поиска по индексу правил."""
    file: str
    path: str
    text: str
    score: float

def collect_prompt_documents(prompts_root: Path = _PROMPTS_ROOT) -> List[Dict[str, str]]:
    """
    ## hypo69 docblock
    Собирает корпус документов из директории промптов.

    Args:
        prompts_root (Path): Корневой каталог файлов промптов.

    Returns:
        List[Dict[str, str]]: List документов формата {"file": str, "path": str, "text": str}.
    """
    documents: List[Dict[str, str]] = []
    if not prompts_root.exists():
        logger.warning(f"[RulesRAG] Каталог промптов не найден: {prompts_root}")
        return documents

    for glob_pat in _TARGET_GLOBS:
        for file_path in sorted(prompts_root.glob(glob_pat)):
            if not file_path.is_file() or file_path.name in _EXCLUDE_NAMES:
                continue

            rel_path: str = str(file_path.relative_to(prompts_root)).replace("\\", "/")
            raw_text: str = file_path.read_text(encoding="utf-8").strip()

            if file_path.suffix == ".json":
                text: str = f"[Файл: {file_path.name}]\n{raw_text}"
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
    Строит FAISS-индекс по файлам промптов и saves документы и индекс.

    Args:
        prompts_root (Path): Путь к каталогу prompts.
        output_dir (Path): Каталог для сохранения rules.index и documents.json.

    Returns:
        Tuple[Path, Path]: Пути к сохранённому индексу и файлу документов.
    """
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "rules.index"
    docs_path = output_dir / "documents.json"

    documents = collect_prompt_documents(prompts_root)
    if not documents:
        raise RuntimeError(f"Документы промптов не найдены в {prompts_root}")

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
    logger.info(f"[RulesRAG] Индекс successfully построен: {index_path} ({len(documents)} документов)")
    return index_path, docs_path

_ALWAYS_INCLUDE: List[str] = [
    "identity.md",
    "categories.md",
]

class RulesRAG:
    """
    ## hypo69 docblock
    Семантический поиск по модулям промптов через векторный FAISS-индекс.
    """

    def __init__(self, index_path: Path = _DEFAULT_INDEX_PATH, docs_path: Path = _DEFAULT_DOCUMENTS_PATH) -> None:
        """
        ## hypo69 docblock
        Инициализирует и loads индекс правил и корпус документов.
        """
        # Поиск индекса: сначала в tmp/rag, затем в fallback путях
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
                    f"Не удалось найти или пересобрать FAISS-индекс правил: {e}"
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
        Performs семантический поиск по корпусу правил.

        Args:
            query (str): Запрос на естественном языке.
            top_k (int): Число возвращаемых результатов.

        Returns:
            List[RulesSearchResult]: List релевантных модулей промптов.
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
        Собирает текстовый контекст из найденных документов для вставки в системный промпт.
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

