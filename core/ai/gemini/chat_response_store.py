# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: JSON-хранилище одобренных ответов чата
# =============================================================================
# Описание:
#   Сохраняет явно одобренные пользователем ответы модели в JSON-файлы.
#   Каждый файл — один одобренный диалог. Из этих файлов отдельный процесс
#   rebuild_chat_rag.py строит FAISS-индекс.
#
# File: chat_response_store.py
# Project: ai-assistant
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import uuid
from datetime import datetime
from pathlib import Path

from core.logger import logger

# Директория для хранения одобренных ответов
_STORE_DIR = Path(__file__).parent.parent.parent / 'plugins' / 'media_organizer' / 'data' / 'chat_responses'
_STORE_DIR.mkdir(parents=True, exist_ok=True)


def save_approved_response(user_id: str, query: str, chat_text: str, voice_text: str = '') -> bool:
    """Сохраняет одобренный пользователем ответ в JSON-файл.

    Args:
        user_id: Идентификатор пользователя (id из БД или anon_<ip>).
        query: Исходный запрос пользователя.
        chat_text: Текст ответа модели для чата.
        voice_text: Текст ответа модели для диктора (опционально).

    Returns:
        True если сохранение прошло успешно, иначе False.
    """
    try:
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id),
            'query': query,
            'chat_text': chat_text,
            'voice_text': voice_text,
        }
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{entry['id'][:8]}.json"
        filepath = _STORE_DIR / filename
        filepath.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"[ChatResponseStore] Сохранён одобренный ответ: {filename}")
        return True
    except Exception as ex:
        logger.error('[ChatResponseStore] Ошибка сохранения ответа', ex)
        return False


def list_responses(user_id: str = '') -> list[dict]:
    """Возвращает список всех сохранённых одобренных ответов (опционально фильтр по user_id).

    Args:
        user_id: Если задан — возвращает только записи этого пользователя.

    Returns:
        Список словарей с данными ответов.
    """
    results = []
    for fp in sorted(_STORE_DIR.glob('*.json')):
        try:
            entry = json.loads(fp.read_text(encoding='utf-8'))
            if user_id and entry.get('user_id') != str(user_id):
                continue
            results.append(entry)
        except Exception as ex:
            logger.error(f'[ChatResponseStore] Ошибка чтения файла {fp.name}', ex)
    return results


def update_response(doc_id: str, query: str, chat_text: str, voice_text: str = '') -> bool:
    """Обновляет содержимое сохраненного диалога на диске по его ID.

    Args:
        doc_id: ID документа.
        query: Новый текст запроса.
        chat_text: Новый ответ модели.
        voice_text: Новый текст диктора.

    Returns:
        True при успехе, иначе False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    entry['query'] = query
                    entry['chat_text'] = chat_text
                    entry['voice_text'] = voice_text
                    fp.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
                    logger.info(f"[ChatResponseStore] Обновлен ответ RAG: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ChatResponseStore] Ошибка парсинга при обновлении {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ChatResponseStore] Ошибка обновления ответа', ex)
        return False


def delete_response(doc_id: str) -> bool:
    """Удаляет файл сохраненного диалога с диска по его ID.

    Args:
        doc_id: ID документа.

    Returns:
        True при успехе, иначе False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    fp.unlink()
                    logger.info(f"[ChatResponseStore] Удален ответ RAG: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ChatResponseStore] Ошибка парсинга при удалении {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ChatResponseStore] Ошибка удаления ответа', ex)
        return False

