# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RAG-индекс на базе Gemini Embedding API и FAISS.
# =============================================================================
# Description:
#   Векторизация документов через Gemini text-embedding-004 / gemini-embedding-2,
#
# File: rag.py
# Project: ai-breadboard
# Package: core.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from typing import List, Dict
import numpy as np

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False
    faiss = False

from google import genai
from google.genai import types

from core.logger import logger

_EMBED_MODEL = 'models/gemini-embedding-2'
_EMBED_DIM = 3072

class GeminiRAG:
    """RAG-индекс на базе Gemini Embedding API и FAISS.

    Векторизация произвольных текстовых документов, хранение в FAISS,
    семантический поиск ближайших соседей.

    Attributes:
        db_path (Path): Путь к файлу (мы заменяем .db на .faiss/.json).
        client: Клиент google.genai.
    """

    def __init__(self, api_key: str = '', db_path: Path = Path('.')) -> None:
        """Initialization RAG-индекса."""
        self.db_path = db_path
        self.index_file = db_path.with_suffix('.faiss')
        self.meta_file = db_path.with_suffix('.json')
        self.dimension = _EMBED_DIM
        self.api_key = api_key
        self.client = False
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.error(f"[GeminiRAG] Error инициализации genai.Client: {e}")
        
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadatas: List[Dict] = []
        self._load()

    def _load(self) -> None:
        """Loading индекса и метаданных."""
        if self.meta_file.exists():
            try:
                with open(self.meta_file, 'r', encoding='utf-8') as f:
                    self.metadatas = json.load(f)
            except Exception as e:
                logger.error("Error чтения метаданных пользователя", e)
                self.metadatas = []
        else:
            self.metadatas = []

        if not _FAISS_AVAILABLE:
            self.index = False
            return

        if self.index_file.exists() and self.metadatas:
            try:
                self.index = faiss.read_index(str(self.index_file))
            except Exception as e:
                logger.error("Error чтения FAISS индекса, пересоздаем", e)
                self._rebuild_index()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def _rebuild_index(self) -> None:
        """Перестроение индекса из metadatas с валидацией векторов."""
        if not _FAISS_AVAILABLE:
            self.index = False
            return

        self.index = faiss.IndexFlatL2(self.dimension)
        if not self.metadatas:
            return

        valid_items = [
            m for m in self.metadatas
            if isinstance(m, dict) and 'vector' in m and isinstance(m['vector'], (list, np.ndarray)) and len(m['vector']) == self.dimension
        ]

        if len(valid_items) != len(self.metadatas):
            logger.warning(f"[GeminiRAG] Отфильтровано {len(self.metadatas) - len(valid_items)} записей без корректного поля 'vector'")
            self.metadatas = valid_items
            self._save()

        if self.metadatas:
            try:
                vectors = np.array([m['vector'] for m in self.metadatas], dtype=np.float32)
                self.index.add(vectors)
            except Exception as e:
                logger.error("Error при добавлении векторов в FAISS индекс", e)

    def _save(self) -> None:
        """Сохранение индекса и метаданных."""
        try:
            if _FAISS_AVAILABLE and self.index:
                faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadatas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error сохранения FAISS индекса/метаданных", e)

    def _embed(self, texts: List[str], task_type: str = 'RETRIEVAL_DOCUMENT') -> List[List[float]]:
        """Получение эмбеддингов для списка текстов через Gemini API с обработкой 429 и ротацией ключей."""
        import time
        from google.genai.errors import APIError
        from core.secrets.api_key_state import load_api_keys, mark_exhausted
        import random
        
        start_idx = random.randint(0, 100)
        max_retries = 10
        
        for attempt in range(max_retries):
            api_keys, key_names, _ = load_api_keys(skip_exhausted=False)
            if not api_keys:
                raise RuntimeError("Нет доступных ключей API Gemini")
            
            key_idx = (start_idx + attempt) % len(api_keys)
            current_key = api_keys[key_idx]
            current_name = key_names[key_idx]
            
            client = genai.Client(api_key=current_key)
            try:
                response = client.models.embed_content(
                    model=_EMBED_MODEL,
                    contents=[types.Content(parts=[types.Part.from_text(text=t)]) for t in texts],
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [e.values for e in response.embeddings]
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    delay = 5.0 + attempt * 2
                    logger.warning(f"Превышен лимит (429) для ключа {current_name}. Переключаемся и ждем {delay} сек...")
                    time.sleep(delay)
                    continue
                elif "400" in err_str or "INVALID_ARGUMENT" in err_str or "API_KEY_INVALID" in err_str:
                    logger.warning(f"Неверный ключ API (400) для {current_name}. Пропускаем...")
                    mark_exhausted(current_name)
                    continue
                raise e
                
        raise RuntimeError("Превышено количество попыток запроса эмбеддингов из-за ограничений скорости (429)")

    def add_documents(self, docs: List[dict], batch_size: int = 50) -> int:
        """Векторизация и сохранение документов в индекс."""
        if not docs:
            return 0
        
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            texts = [d['text'] for d in batch]
            try:
                vectors = self._embed(texts, task_type='RETRIEVAL_DOCUMENT')
            except Exception as e:
                logger.error(f"Error получения эмбеддингов для батча: {e}")
                raise e
            
            # Заменяем старые документы с совпадающими ID
            existing_ids = {doc['id'] for doc in batch}
            self.metadatas = [m for m in self.metadatas if m['id'] not in existing_ids]
            
            for doc, vec in zip(batch, vectors):
                self.metadatas.append({
                    'id': doc['id'],
                    'text': doc['text'],
                    'meta': doc.get('meta', {}),
                    'vector': vec
                })
                
            self._rebuild_index()
            self._save()
            import time
            time.sleep(1.0)
        return len(docs)

    def delete_document(self, doc_id: str) -> None:
        """Удаление документа из индекса по id."""
        self.metadatas = [m for m in self.metadatas if m['id'] != doc_id]
        self._rebuild_index()
        self._save()

    def clear(self) -> None:
        """Полная очистка индекса."""
        self.metadatas = []
        self.index = faiss.IndexFlatL2(self.dimension) if _FAISS_AVAILABLE else False
        self._save()

    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[dict]:
        """Семантический поиск ближайших документов по cosine similarity."""
        valid_metadatas = [
            m for m in self.metadatas
            if isinstance(m, dict) and 'vector' in m and isinstance(m['vector'], (list, np.ndarray)) and len(m['vector']) == self.dimension
        ]
        if not valid_metadatas:
            return []

        try:
            query_vec = np.array(self._embed([query], task_type='RETRIEVAL_QUERY')[0], dtype=np.float32)
        except Exception as e:
            logger.error("Error векторизации поискового запроса", e)
            return []

        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)

        doc_vectors = np.array([m['vector'] for m in valid_metadatas], dtype=np.float32)
        doc_norms = np.linalg.norm(doc_vectors, axis=1, keepdims=True) + 1e-10
        doc_vectors_normalized = doc_vectors / doc_norms
        actual_k = min(top_k, len(valid_metadatas))

        if not _FAISS_AVAILABLE:
            similarities = np.dot(doc_vectors_normalized, query_norm)
            top_indices = np.argsort(similarities)[::-1][:actual_k]
            results: List[dict] = []
            for idx in top_indices:
                sim = float(similarities[idx])
                if sim >= threshold:
                    meta = valid_metadatas[idx]
                    results.append({
                        'id': meta['id'],
                        'text': meta['text'],
                        'meta': meta.get('meta', {}),
                        'score': round(sim, 4)
                    })
            return results

        temp_index = faiss.IndexFlatL2(self.dimension)
        temp_index.add(doc_vectors_normalized)

        distances, indices = temp_index.search(query_norm.reshape(1, -1), actual_k)

        results: List[dict] = []
        for i in range(actual_k):
            idx = int(indices[0][i])
            if idx >= 0 and idx < len(valid_metadatas):
                l2_dist = float(distances[0][i])
                cosine_sim = 1.0 - (l2_dist / 2.0)

                if cosine_sim >= threshold:
                    meta = valid_metadatas[idx]
                    results.append({
                        'id': meta['id'],
                        'text': meta['text'],
                        'meta': meta.get('meta', {}),
                        'score': round(cosine_sim, 4)
                    })
        return results

    def count(self) -> int:
        """Количество документов в индексе."""
        return len(self.metadatas)
