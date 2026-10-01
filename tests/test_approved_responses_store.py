# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Approved Responses Store
# =============================================================================
# Description:
#   Проверка сохранения и чтения одобренных ответов с системным контекстом и тегами.
#
# Usage Examples:
#   Python API:
#     from tests.test_approved_responses_store import test_save_and_list_responses
#
#     res = test_save_and_list_responses()
#
# File: test_approved_responses_store.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Проверка сохранения и чтения одобренных ответов с системным контекстом и тегами."""

import json
from pathlib import Path
from unittest.mock import patch
import pytest
from src.ai.gemini import approved_responses_store

def test_save_and_list_responses(tmp_path: Path):
    """Проверка сохранения и чтения одобренных ответов с системным контекстом и тегами."""
    with patch.object(approved_responses_store, '_STORE_DIR', tmp_path):
        ok = approved_responses_store.save_approved_response(user_id='user_123', query='Как работает RAG?', chat_text='RAG использует векторный поиск и LLM.', voice_text='Кратко о RAG.', system_context={'os': 'Windows 11', 'gpu': 'RTX 4090'}, tags=['tc', 'diagnostics'])
        assert ok is True
        ok_2 = approved_responses_store.save_approved_response(user_id='user_456', query='Что такое Python?', chat_text='Python — язык программирования.', tags=['general'])
        assert ok_2 is True
        all_items = approved_responses_store.list_responses()
        assert len(all_items) == 2
        user_123_items = approved_responses_store.list_responses(user_id='user_123')
        assert len(user_123_items) == 1
        assert user_123_items[0]['query'] == 'Как работает RAG?'
        assert user_123_items[0]['system_context']['gpu'] == 'RTX 4090'
        tc_items = approved_responses_store.list_responses(tag='tc')
        assert len(tc_items) == 1

def test_update_and_delete_response(tmp_path: Path):
    """Проверка обновления и удаления сохраненного ответа."""
    with patch.object(approved_responses_store, '_STORE_DIR', tmp_path):
        approved_responses_store.save_approved_response(user_id='user_123', query='Старый запрос', chat_text='Старый ответ')
        items = approved_responses_store.list_responses()
        assert len(items) == 1
        doc_id = items[0]['id']
        upd_ok = approved_responses_store.update_response(doc_id=doc_id, query='Новый запрос', chat_text='Новый ответ', voice_text='Новая озвучка', tags=['updated'])
        assert upd_ok is True
        updated_items = approved_responses_store.list_responses()
        assert updated_items[0]['query'] == 'Новый запрос'
        assert updated_items[0]['chat_text'] == 'Новый ответ'
        assert updated_items[0]['voice_text'] == 'Новая озвучка'
        assert 'updated' in updated_items[0]['tags']
        del_ok = approved_responses_store.delete_response(doc_id=doc_id)
        assert del_ok is True
        remaining_items = approved_responses_store.list_responses()
        assert len(remaining_items) == 0

def test_export_tuning_dataset(tmp_path: Path):
    """Проверка экспорта датасета для тюнинга в различных форматах."""
    store_dir = tmp_path / 'store'
    export_dir = tmp_path / 'exports'
    store_dir.mkdir()
    export_dir.mkdir()
    with patch.object(approved_responses_store, '_STORE_DIR', store_dir):
        approved_responses_store.save_approved_response(user_id='tester', query='Почему греется процессор?', chat_text='Проверьте кулер и термопасту.', system_context={'cpu_temp': 92})
        alpaca_file = export_dir / 'alpaca.jsonl'
        count_alpaca = approved_responses_store.export_tuning_dataset(alpaca_file, fmt='alpaca')
        assert count_alpaca == 1
        with open(alpaca_file, encoding='utf-8') as f:
            data = json.loads(f.readline())
            assert data['instruction'] == 'Почему греется процессор?'
            assert 'cpu_temp' in data['input']
        sharegpt_file = export_dir / 'sharegpt.jsonl'
        count_sharegpt = approved_responses_store.export_tuning_dataset(sharegpt_file, fmt='sharegpt')
        assert count_sharegpt == 1
        gemini_file = export_dir / 'gemini.jsonl'
        count_gemini = approved_responses_store.export_tuning_dataset(gemini_file, fmt='gemini')
        assert count_gemini == 1