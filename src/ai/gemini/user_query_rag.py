# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - User Query Rag Module
# =============================================================================
# Description:
#   Возвращает путь к базе данных RAG для конкретного пользователя и именованной базы знаний (роли).
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.user_query_rag import get_user_rag
#
#     res = get_user_rag()
#     print(res)
#
# File: user_query_rag.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Возвращает путь к базе данных RAG для конкретного пользователя и именованной базы знаний (роли)."""

import hashlib
import time
import re
from pathlib import Path
from typing import Optional
from src.ai.gemini.rag import GeminiRAG
from logger import logger
_USER_RAGS_DIR = Path(__file__).parent / 'user_rags'
_USER_RAGS_DIR.mkdir(exist_ok=True)
_MAX_DOCS_PER_USER = 500
_MIN_QUERY_LEN = 10

def _get_user_rag_path(user_id, rag_name: Optional[str]=None) -> Path:
    """Возвращает путь к базе данных RAG для конкретного пользователя и именованной базы знаний (роли)."""
    safe_id = str(user_id).replace('.', '_').replace('/', '_').replace('\\', '_')
    if rag_name and str(rag_name).strip() and (str(rag_name).strip().lower() not in ('default', 'main', 'user')):
        safe_rag = str(rag_name).strip().replace('.', '_').replace('/', '_').replace('\\', '_').lower()
        return _USER_RAGS_DIR / f'user_rag_{safe_id}_{safe_rag}.db'
    return _USER_RAGS_DIR / f'user_rag_{safe_id}.db'

def _make_doc_id(user_id, query: str) -> str:
    """Генерирует уникальный идентификатор документа (дедупликация по тексту запроса)."""
    key = f'{user_id}_{query.strip().lower()}'
    return f"{user_id}_{hashlib.md5(key.encode('utf-8')).hexdigest()}"

def get_user_rag(user_id, api_key: str, rag_name: Optional[str]=None) -> GeminiRAG:
    """Возвращает объект индекса RAG для конкретного пользователя и целевой RAG базы.

    Args:
        user_id: Идентификатор пользователя (int из БД или строка "anon_<IP>").
        api_key: API ключ Gemini для векторных эмбеддингов.
        rag_name: Опциональное имя целевой RAG базы данных (роли).

    Returns:
        GeminiRAG: Инстанс индекса RAG.
    """
    db_path = _get_user_rag_path(user_id, rag_name=rag_name)
    return GeminiRAG(api_key=api_key, db_path=db_path)

def is_garbage_query(query: str) -> bool:
    """Determine if query is garbage (contains no useful semantic content)."""
    q = query.strip().lower()
    if len(q) < _MIN_QUERY_LEN:
        return True
    if re.search('(.)\\1{4,}', q):
        return True
    if not re.search('[a-zA-Zа-яА-Я0-9]', q):
        return True
    garbage_words = {'привет', 'здравствуй', 'здравствуйте', 'добрый', 'день', 'вечер', 'утро', 'пока', 'свидания', 'встречи', 'прощай', 'спасибо', 'благодарю', 'пожалуйста', 'дела', 'жизнь', 'делаешь', 'ты', 'тут', 'эй', 'ау', 'тест', 'test', 'hello', 'hi', 'hey', 'good', 'morning', 'afternoon', 'evening', 'thank', 'you', 'thanks', 'please', 'bye', 'goodbye', 'how', 'are', 'whats', 'up', 'ok', 'ок', 'ладно', 'как', 'большое', 'не', 'за', 'что', 'да', 'нет', 'угу'}
    clean_q = re.sub('[^\\w\\s]', '', q).strip()
    words = clean_q.split()
    if words and all((w in garbage_words for w in words)):
        return True
    for w in words:
        if len(w) > 6:
            if not re.search('[aeiouyаеёиоуыэюя]', w):
                return True
    return False

def _format_compact_summary(text: str, max_chars: int=150) -> str:
    """Format ultra-compact text summary to minimize token usage."""
    import re
    clean = re.sub('<film>(.*?)</film>', '«\\1»', text, flags=re.IGNORECASE)
    clean = re.sub('#+\\s*', '', clean)
    clean = re.sub('[*_`]+', '', clean)
    clean = re.sub('[🎬📂👤📝💡✨💬📱❌🔍🌐🤖🛠️🎡📡⏳⬆️⬇️💾📥▶️⚡—–]+', ' ', clean)
    clean = re.sub('(?:Жанр|Режиссёр|В главных ролях|В ролях|Сюжет|Почему стоит посмотреть|Основные сведения):\\s*', '', clean)
    clean = re.sub('\\s+', ' ', clean).strip()
    if len(clean) > max_chars:
        clean = clean[:max_chars].rsplit(' ', 1)[0] + '...'
    return clean

def index_user_query(user_id, api_key: str, query: str, response: str, rag_name: Optional[str]=None) -> bool:
    """Индексирует пару (запрос пользователя + ответ модели) в RAG базу знаний.

    Args:
        user_id: Идентификатор пользователя или строка "anon_<IP>".
        api_key: API ключ Gemini.
        query: Текст запроса пользователя.
        response: Ответ модели.
        rag_name: Опциональное имя целевой RAG базы данных (роли).

    Returns:
        bool: True если документ был успешно добавлен/обновлен, иначе False.
    """
    if not query or not response:
        return False
    if is_garbage_query(query):
        logger.warning(f"UserRAG [{user_id}]: запрос отфильтрован как сервисный/мусорный: '{query}'")
        return False
    resp_stripped = response.strip()
    if resp_stripped.startswith('{') and ('"title"' in resp_stripped or '"error"' in resp_stripped or '"results"' in resp_stripped):
        logger.warning(f"UserRAG [{user_id}]: ответ отфильтрован как сырой JSON: '{resp_stripped[:60]}...'")
        return False
    if any((resp_stripped.startswith(pfx) for pfx in ('❌', 'Error', 'ERROR', 'DEBUG', 'Traceback', '[DIRECT PLAY', '[DIRECT RAG'))):
        logger.warning(f'UserRAG [{user_id}]: ответ отфильтрован как системное сообщение об ошибке')
        return False
    try:
        rag = get_user_rag(user_id, api_key, rag_name=rag_name)
        _prune_if_needed(rag, user_id)
        doc_id = _make_doc_id(user_id, query)
        response_summary = _format_compact_summary(response, max_chars=150)
        doc_text = f'User asked: {query.strip()}\nModel response: {response_summary}'
        rag.add_documents([{'id': doc_id, 'text': doc_text, 'meta': {'user_id': str(user_id), 'timestamp': time.time(), 'q': query[:500], 'response': response[:1000], 'rag_name': str(rag_name or 'default'), 'is_manual': False}}])
        return True
    except Exception as ex:
        logger.error(f'Ошибка индексации запроса пользователя {user_id}', ex, False)
        return False

def search_user_context(user_id, api_key: str, query: str, top_k: int=3, threshold: float=0.4, rag_name: Optional[str]=None) -> list:
    """Семантический поиск по истории RAG конкретной базы данных/роли.

    Args:
        user_id: Идентификатор пользователя.
        api_key: API ключ Gemini.
        query: Запрос для поиска похожего контекста.
        top_k: Количество результатов.
        threshold: Минимальный порог сходства (0.0-1.0).
        rag_name: Имя целевой RAG базы данных (роли).

    Returns:
        list[dict]: Список словарей {"id", "text", "meta", "score"}, отсортированных по релевантности.
    """
    try:
        rag = get_user_rag(user_id, api_key, rag_name=rag_name)
        if rag.count() == 0:
            return []
        return rag.search(query, top_k=top_k, threshold=threshold)
    except Exception as ex:
        logger.error(f'Ошибка поиска в RAG {user_id} (rag_name={rag_name})', ex, False)
        return []

def get_user_rag_stats(user_id, api_key: str) -> dict:
    """Return statistics of user's RAG index.

    Args:
        user_id: User ID.
        api_key: Gemini API key.

    Returns:
        dict: Fields count, db_path, db_size_kb.
    """
    db_path = _get_user_rag_path(user_id)
    try:
        rag = get_user_rag(user_id, api_key)
        count = rag.count()
    except Exception:
        count = 0
    size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0
    return {'user_id': str(user_id), 'count': count, 'db_path': str(db_path), 'db_size_kb': size_kb}

def clear_user_rag(user_id, api_key: str) -> bool:
    """Complete cleanup of user's personal RAG index.

    Args:
        user_id: User ID.
        api_key: Gemini API key.

    Returns:
        bool: True on success.
    """
    try:
        rag = get_user_rag(user_id, api_key)
        rag.clear()
        return True
    except Exception as ex:
        logger.error(f'Error clearing user RAG {user_id}', ex, False)
        return False

def clean_invalid_user_rag_entries(user_id, api_key: str='') -> int:
    """Delete from User RAG entries containing raw JSON or error messages."""
    try:
        rag = get_user_rag(user_id, api_key)
        initial_count = len(rag.metadatas)
        valid_metas = []
        for m in rag.metadatas:
            text = m.get('text', '')
            meta_resp = m.get('meta', {}).get('response', '')
            check_str = (meta_resp or text).strip()
            if check_str.startswith('{') and ('"title"' in check_str or '"error"' in check_str):
                continue
            if 'Model response: {' in text and '"title"' in text:
                continue
            if any((check_str.startswith(pfx) for pfx in ('❌', 'Error', 'ERROR', 'DEBUG', 'Traceback'))):
                continue
            valid_metas.append(m)
        deleted_count = initial_count - len(valid_metas)
        if deleted_count > 0:
            rag.metadatas = valid_metas
            rag._rebuild_index()
            rag._save()
            logger.info(f'UserRAG [{user_id}]: cleaned {deleted_count} corrupted records.')
        return deleted_count
    except Exception as ex:
        logger.error(f'Error cleaning corrupted RAG entries for user {user_id}', ex, False)
        return 0

def _prune_if_needed(rag: GeminiRAG, user_id) -> None:
    """Delete oldest documents if index exceeds _MAX_DOCS_PER_USER.

    Strategy: read meta.timestamp from all docs, delete 10% oldest.
    """
    count = rag.count()
    if count < _MAX_DOCS_PER_USER:
        return
    try:
        parsed = []
        for m in rag.metadatas:
            doc_id = m.get('id')
            meta = m.get('meta', {})
            ts = float(meta.get('timestamp', 0))
            parsed.append((doc_id, ts))
        parsed.sort(key=lambda x: x[1])
        to_delete = parsed[:max(1, count // 10)]
        for doc_id, _ in to_delete:
            rag.delete_document(doc_id)
        logger.info(f'UserRAG [{user_id}]: deleted {len(to_delete)} old records (was {count})')
    except Exception as ex:
        logger.error(f'Error pruning user RAG {user_id}', ex, False)