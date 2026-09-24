# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Store and manage user-approved model responses for TC & RAG
# =============================================================================
# Description:
#   Stores model responses explicitly approved by user to JSON files in data/tc/approved_responses.
#   Manages persistence of chat, voice, and system context with metadata.
#   Supports export to fine-tuning datasets (Alpaca, ShareGPT, Gemini) and indexing into RAG.
#
# File: approved_responses_store.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from logger import logger

# Directory for storing approved responses in the TC data workspace
_STORE_DIR = __root__ / 'data' / 'tc' / 'approved_responses'
_STORE_DIR.mkdir(parents=True, exist_ok=True)


def get_store_dir() -> Path:
    """Возвращает текущую директорию хранения одобренных ответов.

    Returns:
        Path: Путь к директории хранения.
    """
    return _STORE_DIR


def save_approved_response(
    user_id: str,
    query: str,
    chat_text: str,
    voice_text: str = '',
    system_context: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Сохраняет одобренный пользователем ответ модели в JSON-файл.

    Args:
        user_id: Идентификатор пользователя (ID или 'anon_...').
        query: Исходный запрос пользователя.
        chat_text: Ответ модели для чата.
        voice_text: Опциональный текст для озвучивания.
        system_context: Опциональные метаданные системы (железо, ОС, приложение).
        tags: Опциональные теги категории (например, ['tc', 'hardware', 'gpu']).

    Returns:
        bool: True в случае успешного сохранения, иначе False.
    """
    try:
        now_utc = datetime.now(timezone.utc)
        entry: Dict[str, Any] = {
            'id': str(uuid.uuid4()),
            'timestamp': now_utc.isoformat(),
            'user_id': str(user_id),
            'query': query,
            'chat_text': chat_text,
            'voice_text': voice_text,
            'system_context': system_context or {},
            'tags': tags or ['tc'],
        }
        filename = f"{now_utc.strftime('%Y%m%d_%H%M%S')}_{entry['id'][:8]}.json"
        filepath = _STORE_DIR / filename
        filepath.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"[ApprovedResponsesStore] Approved response saved: {filename}")
        return True
    except Exception as ex:
        logger.error('[ApprovedResponsesStore] Error saving response', ex)
        return False


def list_responses(user_id: str = '', tag: str = '') -> List[Dict[str, Any]]:
    """Возвращает список всех сохраненных одобренных ответов.

    Args:
        user_id: Фильтр по идентификатору пользователя.
        tag: Опциональный фильтр по тегу.

    Returns:
        List[Dict[str, Any]]: Список словарей с данными ответов.
    """
    results: List[Dict[str, Any]] = []
    if not _STORE_DIR.exists():
        return results

    for fp in sorted(_STORE_DIR.glob('*.json')):
        try:
            entry = json.loads(fp.read_text(encoding='utf-8'))
            if user_id and entry.get('user_id') != str(user_id):
                continue
            if tag and tag not in entry.get('tags', []):
                continue
            results.append(entry)
        except Exception as ex:
            logger.error(f'[ApprovedResponsesStore] Error reading file {fp.name}', ex)
    return results


def update_response(
    doc_id: str,
    query: str,
    chat_text: str,
    voice_text: str = '',
    system_context: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Обновляет сохраненный диалог на диске по его уникальному ID.

    Args:
        doc_id: Уникальный ID записи.
        query: Обновленный текст запроса.
        chat_text: Обновленный ответ модели.
        voice_text: Обновленный текст озвучки.
        system_context: Обновленный системный контекст.
        tags: Обновленные теги.

    Returns:
        bool: True при успехе, иначе False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    entry['query'] = query
                    entry['chat_text'] = chat_text
                    entry['voice_text'] = voice_text
                    if system_context is not None:
                        entry['system_context'] = system_context
                    if tags is not None:
                        entry['tags'] = tags
                    fp.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
                    logger.info(f"[ApprovedResponsesStore] Response updated: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ApprovedResponsesStore] Error parsing {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ApprovedResponsesStore] Error updating response', ex)
        return False


def delete_response(doc_id: str) -> bool:
    """Удаляет файл сохраненного диалога по его ID.

    Args:
        doc_id: Уникальный ID записи.

    Returns:
        bool: True при успехе, иначе False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    fp.unlink()
                    logger.info(f"[ApprovedResponsesStore] Response deleted: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ApprovedResponsesStore] Error during delete {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ApprovedResponsesStore] Error deleting response', ex)
        return False


def export_tuning_dataset(
    output_path: Path | str,
    fmt: str = 'alpaca',
    system_instruction: str = 'Ты — AI-ассистент по диагностике и мониторингу ПК (Test Computer).'
) -> int:
    """Экспортирует сохраненные ответы в датасет для тюнинга модели (JSONL).

    Args:
        output_path: Путь к файлу назначения (.jsonl).
        fmt: Формат датасета ('alpaca', 'sharegpt', 'gemini').
        system_instruction: Системная инструкция для контекста.

    Returns:
        int: Количество экспортированных записей.
    """
    responses = list_responses()
    if not responses:
        return 0

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    for item in responses:
        q = item.get('query', '').strip()
        ans = item.get('chat_text', '').strip()
        ctx = item.get('system_context', {})
        ctx_str = f"Системный контекст: {json.dumps(ctx, ensure_ascii=False)}" if ctx else ""

        if not q or not ans:
            continue

        if fmt == 'alpaca':
            records.append({
                'instruction': q,
                'input': ctx_str,
                'output': ans,
            })
        elif fmt == 'sharegpt':
            conversations = []
            if system_instruction or ctx_str:
                full_sys = f"{system_instruction} {ctx_str}".strip()
                conversations.append({'from': 'system', 'value': full_sys})
            conversations.append({'from': 'human', 'value': q})
            conversations.append({'from': 'gpt', 'value': ans})
            records.append({'conversations': conversations})
        elif fmt == 'gemini':
            # Gemini Tuning format
            contents = [
                {'role': 'user', 'parts': [{'text': f"{ctx_str}\n\n{q}".strip() if ctx_str else q}]},
                {'role': 'model', 'parts': [{'text': ans}]}
            ]
            records.append({
                'systemInstruction': {'role': 'system', 'parts': [{'text': system_instruction}]},
                'contents': contents
            })

    with open(out_file, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    logger.info(f"[ApprovedResponsesStore] Exported {len(records)} records to {out_file} (format={fmt})")
    return len(records)
