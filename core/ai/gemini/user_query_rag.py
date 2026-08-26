# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Пользовательский RAG на основе истории чата
# =============================================================================
# Описание:
#   Каждый запрос пользователя (вопрос + ответ модели) индексируется
#   в персональную SQLite-базу с Gemini-эмбеддингами.
#   Позволяет модели «помнить» предпочтения и прошлые запросы пользователя.
#
# File: user_query_rag.py
# Project: ai-mediteka
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hashlib
import time
import re
from pathlib import Path
from typing import Optional

from core.ai.gemini.rag import GeminiRAG
from core.logger import logger

# Директория для хранения пользовательских RAG-баз
_USER_RAGS_DIR = Path(__file__).parent / "user_rags"
_USER_RAGS_DIR.mkdir(exist_ok=True)

# Максимальное количество документов в одной базе (старые вытесняются)
_MAX_DOCS_PER_USER = 500

# Минимальная длина запроса для индексации (исключаем "да", "нет" и т.п.)
_MIN_QUERY_LEN = 10


def _get_user_rag_path(user_id) -> Path:
    """Возвращает путь к RAG-базе конкретного пользователя."""
    safe_id = str(user_id).replace(".", "_").replace("/", "_").replace("\\", "_")
    return _USER_RAGS_DIR / f"user_rag_{safe_id}.db"


def _make_doc_id(user_id, query: str) -> str:
    """Генерирует стабильный уникальный ID документа (дедупликация по запросу)."""
    key = f"{user_id}_{query.strip().lower()}"
    return f"{user_id}_{hashlib.md5(key.encode('utf-8')).hexdigest()}"


def get_user_rag(user_id, api_key: str) -> GeminiRAG:
    """Возвращает RAG-индекс для конкретного пользователя.

    Создаёт базу если её нет. Не перестраивает существующую.

    Args:
        user_id: ID пользователя (int из БД или строка "anon_<IP>").
        api_key: Ключ Gemini API для эмбеддингов.

    Returns:
        GeminiRAG: Экземпляр пользовательского RAG-индекса.
    """
    db_path = _get_user_rag_path(user_id)
    return GeminiRAG(api_key=api_key, db_path=db_path)


def is_garbage_query(query: str) -> bool:
    """Определяет, является ли запрос мусорным (не несущим полезной смысловой нагрузки)."""
    q = query.strip().lower()
    
    # 1. Слишком короткие запросы
    if len(q) < _MIN_QUERY_LEN:
        return True
        
    # 2. Повторяющиеся символы (например, "aaaaaa" или "ыыыыы")
    if re.search(r'(.)\1{4,}', q):
        return True
        
    # 3. Чистый шум (только знаки препинания, спецсимволы или пробелы)
    if not re.search(r'[a-zA-Zа-яА-Я0-9]', q):
        return True
        
    # 4. Простые разговорные фразы / приветствия / благодарности / слова-заполнители
    garbage_words = {
        'привет', 'здравствуй', 'здравствуйте', 'добрый', 'день', 'вечер', 'утро',
        'пока', 'свидания', 'встречи', 'прощай', 'спасибо', 'благодарю', 'пожалуйста',
        'дела', 'жизнь', 'делаешь', 'ты', 'тут', 'эй', 'ау', 'тест', 'test', 'hello',
        'hi', 'hey', 'good', 'morning', 'afternoon', 'evening', 'thank', 'you', 'thanks',
        'please', 'bye', 'goodbye', 'how', 'are', 'whats', 'up', 'ok', 'ок', 'ладно', 'как',
        'большое', 'не', 'за', 'что', 'да', 'нет', 'угу'
    }
    # Убираем знаки препинания для анализа слов
    clean_q = re.sub(r'[^\w\s]', '', q).strip()
    words = clean_q.split()
    if words and all(w in garbage_words for w in words):
        return True
        
    # 5. Keyboard mash (бессмысленный набор букв)
    # Если в слове длиной более 6 символов нет ни одной гласной (для русского и английского)
    for w in words:
        if len(w) > 6:
            # Для русского языка гласные: аеёиоуыэюя
            # Для английского: aeiouy
            if not re.search(r'[aeiouyаеёиоуыэюя]', w):
                return True

    return False


def _format_compact_summary(text: str, max_chars: int = 150) -> str:
    """Формирует ультра-компактное резюме текста для минимизации расхода токенов."""
    import re
    clean = re.sub(r'<film>(.*?)</film>', r'«\1»', text, flags=re.IGNORECASE)
    clean = re.sub(r'#+\s*', '', clean)
    clean = re.sub(r'[*_`]+', '', clean)
    clean = re.sub(r'[🎬📂👤📝💡✨💬📱❌🔍🌐🤖🛠️🎡📡⏳⬆️⬇️💾📥▶️⚡—–]+', ' ', clean)
    clean = re.sub(r'(?:Жанр|Режиссёр|В главных ролях|В ролях|Сюжет|Почему стоит посмотреть|Основные сведения):\s*', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) > max_chars:
        clean = clean[:max_chars].rsplit(' ', 1)[0] + '...'
    return clean


def index_user_query(
    user_id,
    api_key: str,
    query: str,
    response: str,
) -> bool:
    """Индексирует пару (запрос пользователя + ответ модели) в персональный RAG.

    Пропускает слишком короткие/мусорные запросы и дубликаты (по хешу).
    При переполнении (> _MAX_DOCS_PER_USER) удаляет старейшие записи.

    Args:
        user_id: ID пользователя или строка "anon_<IP>".
        api_key: Ключ Gemini API.
        query: Текст запроса пользователя.
        response: Ответ модели.

    Returns:
        bool: True если документ был добавлен/обновлён, False если пропущен.
    """
    if not query or not response:
        return False

    # Фильтруем мусорные запросы
    if is_garbage_query(query):
        logger.info(f"UserRAG [{user_id}]: запрос отфильтрован как мусорный: '{query}'")
        return False

    # Фильтруем ответы, являющиеся сырым JSON, служебными логами или ошибками
    resp_stripped = response.strip()
    if resp_stripped.startswith('{') and ('"title"' in resp_stripped or '"error"' in resp_stripped or '"results"' in resp_stripped):
        logger.info(f"UserRAG [{user_id}]: ответ отфильтрован как сырой JSON: '{resp_stripped[:60]}...'")
        return False
    if any(resp_stripped.startswith(pfx) for pfx in ('❌', 'Ошибка', 'Error', 'DEBUG', 'Traceback', '[DIRECT PLAY', '[DIRECT RAG')):
        logger.info(f"UserRAG [{user_id}]: ответ отфильтрован как служебное/ошибочное сообщение")
        return False

    try:
        rag = get_user_rag(user_id, api_key)

        # Прореживание при переполнении — удаляем старейшие записи
        _prune_if_needed(rag, user_id)

        doc_id = _make_doc_id(user_id, query)
        # Храним ультра-компактное резюме (до 150 символов), чтобы при последующем поиске
        # в контекст модели вставлялось минимум токенов
        response_summary = _format_compact_summary(response, max_chars=150)
        doc_text = f"Пользователь спросил: {query.strip()}\nОтвет модели: {response_summary}"

        rag.add_documents([{
            "id": doc_id,
            "text": doc_text,
            "meta": {
                "user_id": str(user_id),
                "timestamp": time.time(),
                "q": query[:500],
                "response": response[:1000],  # полный текст в мета, не попадает в промпт
                "is_manual": False
            },
        }])
        return True

    except Exception as ex:
        logger.error(f"Ошибка индексации запроса пользователя {user_id}", ex, False)
        return False


def search_user_context(
    user_id,
    api_key: str,
    query: str,
    top_k: int = 3,
    threshold: float = 0.4,
) -> list:
    """Семантический поиск по истории запросов пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.
        query: Текущий запрос для поиска похожего контекста.
        top_k: Количество результатов.
        threshold: Минимальный порог схожести (0.0-1.0).

    Returns:
        list[dict]: Список {"id", "text", "meta", "score"} по убыванию score.
    """
    try:
        rag = get_user_rag(user_id, api_key)
        if rag.count() == 0:
            return []
        return rag.search(query, top_k=top_k, threshold=threshold)
    except Exception as ex:
        logger.error(f"Ошибка поиска по RAG пользователя {user_id}", ex, False)
        return []


def get_user_rag_stats(user_id, api_key: str) -> dict:
    """Возвращает статистику RAG-индекса пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.

    Returns:
        dict: Поля count, db_path, db_size_kb.
    """
    db_path = _get_user_rag_path(user_id)
    try:
        rag = get_user_rag(user_id, api_key)
        count = rag.count()
    except Exception:
        count = 0

    size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0
    return {
        "user_id": str(user_id),
        "count": count,
        "db_path": str(db_path),
        "db_size_kb": size_kb,
    }


def clear_user_rag(user_id, api_key: str) -> bool:
    """Полная очистка персонального RAG-индекса пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.

    Returns:
        bool: True при успехе.
    """
    try:
        rag = get_user_rag(user_id, api_key)
        rag.clear()
        return True
    except Exception as ex:
        logger.error(f"Ошибка очистки RAG пользователя {user_id}", ex, False)
        return False


def clean_invalid_user_rag_entries(user_id, api_key: str = '') -> int:
    """Удаляет из базы User RAG записи, содержащие сырой JSON или сообщения об ошибках."""
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
            if 'Ответ модели: {' in text and '"title"' in text:
                continue
            if any(check_str.startswith(pfx) for pfx in ('❌', 'Ошибка', 'Error', 'DEBUG', 'Traceback')):
                continue
            valid_metas.append(m)

        deleted_count = initial_count - len(valid_metas)
        if deleted_count > 0:
            rag.metadatas = valid_metas
            rag._rebuild_index()
            rag._save()
            logger.info(f"UserRAG [{user_id}]: очищено {deleted_count} поврежденных записей.")
        return deleted_count
    except Exception as ex:
        logger.error(f"Ошибка очистки поврежденных записей RAG пользователя {user_id}", ex, False)
        return 0


# =============================================================================
# Internal helpers
# =============================================================================

def _prune_if_needed(rag: GeminiRAG, user_id) -> None:
    """Удаляет старейшие документы если индекс превысил _MAX_DOCS_PER_USER.

    Стратегия: читаем meta.timestamp из всех документов, удаляем 10% старейших.
    """
    count = rag.count()
    if count < _MAX_DOCS_PER_USER:
        return

    try:
        parsed = []
        for m in rag.metadatas:
            doc_id = m.get('id')
            meta = m.get('meta', {})
            ts = float(meta.get("timestamp", 0))
            parsed.append((doc_id, ts))

        parsed.sort(key=lambda x: x[1])
        to_delete = parsed[:max(1, count // 10)]

        for doc_id, _ in to_delete:
            rag.delete_document(doc_id)

        logger.info(f"UserRAG [{user_id}]: удалено {len(to_delete)} старых записей (было {count})")

    except Exception as ex:
        logger.error(f"Ошибка прореживания RAG пользователя {user_id}", ex, False)
