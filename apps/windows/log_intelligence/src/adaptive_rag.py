# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Log_Intelligence Src - Adaptive Rag
# =============================================================================
# Description:
#   Получить стандартный путь к локальному хранилищу в %APPDATA%.
#
# Usage Examples:
#   Python API:
#     from apps.windows.log_intelligence.src.adaptive_rag import AdaptiveLogRAG
#
#     service = AdaptiveLogRAG()
#
# File: adaptive_rag.py
# Project: ai-breadboard
# Package: apps.windows.log_intelligence.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 05:03:00
# =============================================================================

from __future__ import annotations
"""Адаптивный движок создания и поиска RAG-документов с интеграцией в базу знаний WikiLLM."""

import collections
import datetime
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from .models import DataProfileReport, IngestionDecision, IngestionStrategy

from apps.windows.wikillm.models import (
    ArtifactType,
    Claim,
    DiagnosticKnowledge,
    KnowledgeEntity,
    KnowledgeSource,
    ResolutionAction,
)
from apps.windows.wikillm.storage import WikiStorage


def get_default_storage_dir() -> Path:
    """Получить стандартный путь к локальному хранилищу в %APPDATA%."""
    appdata_env = os.environ.get('APPDATA')
    if appdata_env:
        base_dir = Path(appdata_env) / 'AI-Breadboard' / 'apps' / 'windows' / 'log_intelligence'
    else:
        user_profile = os.environ.get('USERPROFILE') or os.environ.get('HOME')
        if user_profile:
            base_dir = Path(user_profile) / 'AppData' / 'Roaming' / 'AI-Breadboard' / 'apps' / 'windows' / 'log_intelligence'
        else:
            base_dir = Path('.').resolve() / 'data' / 'system_logs_rag'
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


class AdaptiveLogRAG:
    """Адаптивный движок создания и поиска RAG-документов с поддержкой хранилища WikiLLM."""

    def __init__(self, storage_dir: Optional[Path] = None, max_chunks: int = 1000) -> None:
        """Инициализировать адаптивный RAG-индекс в локальном хранилище.

        Args:
            storage_dir: Путь к директории хранения.
            max_chunks: Максимальное количество чанков в оперативной памяти.
        """
        self.storage_dir = Path(storage_dir).resolve() if storage_dir else get_default_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_chunks = max_chunks
        self.chunks: List[Dict[str, Any]] = []

        # Интеграция с движком WikiStorage SQLite
        wiki_db_path = self.storage_dir / 'wikillm.db'
        self.wiki_storage = WikiStorage(db_path=wiki_db_path)

        self._load()

    def _get_chunks_file(self) -> Path:
        return self.storage_dir / 'adaptive_log_rag_chunks.json'

    def _get_history_file(self) -> Path:
        return self.storage_dir / 'profiling_history.json'

    def _load(self) -> None:
        c_file = self._get_chunks_file()
        if c_file.exists():
            try:
                with open(c_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
            except Exception as e:
                logger.error(f'[AdaptiveLogRAG] Ошибка загрузки чанков: {e}')
                self.chunks = []

    def save(self) -> None:
        c_file = self._get_chunks_file()
        try:
            with open(c_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'[AdaptiveLogRAG] Ошибка сохранения чанков: {e}')

    def ingest(self, profile: DataProfileReport, decision: IngestionDecision) -> int:
        """Сгенерировать целевые RAG-документы и сохранить их в базу знаний WikiLLM.

        Args:
            profile (DataProfileReport): Аналитический срез данных.
            decision (IngestionDecision): Решение и стратегия шлюза.

        Returns:
            int: Количество добавленных / обновленных чанков.
        """
        now_str = profile.generated_at or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        generated_chunks: List[Dict[str, Any]] = []

        snap_id = f'snapshot_{profile.channel}_{now_str[:13]}'
        snap_text = (
            f'Аналитический снимок здоровья канала {profile.channel}.\n'
            f'Метка времени: {now_str}\n'
            f'Индекс здоровья (Health Score): {profile.health_score} / 100\n'
            f'Всего событий: {profile.total_events}, Уникальных шаблонов: {profile.unique_templates_count}\n'
            f'Избыточность/дублирование: {profile.redundancy_ratio_pct}%\n'
            f'Ошибок: {profile.error_count + profile.critical_count}, Предупреждений: {profile.warning_count}\n'
            f'Выбранная стратегия: {decision.strategy.value}\n'
            f'Обоснование: {decision.rationale}'
        )
        generated_chunks.append({
            'id': snap_id,
            'type': 'health_snapshot',
            'channel': profile.channel,
            'title': f'Снимок здоровья {profile.channel} ({profile.health_score}%)',
            'text': snap_text,
            'timestamp': now_str,
            'meta': {'strategy': decision.strategy.value, 'health_score': profile.health_score},
        })

        # Регистрация сущности снимка в WikiStorage
        snap_entity = KnowledgeEntity(
            canonical_key=f"snapshot:{profile.channel}:{now_str[:13]}",
            entity_type=ArtifactType.INCIDENT,
            name=f"Снимок здоровья {profile.channel} ({profile.health_score}%)",
            summary=snap_text,
            severity="info" if profile.health_score >= 80 else ("warning" if profile.health_score >= 50 else "error"),
            confidence=1.0,
            tags=[profile.channel.lower(), "health_snapshot", f"score_{int(profile.health_score)}"],
        )
        self.wiki_storage.save_entity(snap_entity)
        self.wiki_storage.record_observation(snap_entity.canonical_key)

        if decision.strategy == IngestionStrategy.INCIDENT_FOCUSED:
            for idx, b in enumerate(profile.bursts):
                b_id = f"burst_{profile.channel}_{b.time_window.replace(':', '_')}_{idx}"
                b_text = (
                    f'Инцидентный каскад событий в канале {profile.channel}.\n'
                    f'Окно всплеска: {b.time_window}\n'
                    f'Событий в пике: {b.event_count}\n'
                    f'Доминирующий уровень: {b.dominant_level}\n'
                    f'Ключевой источник: {b.dominant_provider}\n'
                    f'Сводка: {b.summary}'
                )
                generated_chunks.append({
                    'id': b_id,
                    'type': 'incident_burst',
                    'channel': profile.channel,
                    'title': f'Инцидентный всплеск [{b.dominant_provider} ({b.dominant_level})]',
                    'text': b_text,
                    'timestamp': now_str,
                    'meta': {'window': b.time_window, 'provider': b.dominant_provider},
                })

                burst_entity = KnowledgeEntity(
                    canonical_key=f"burst:{profile.channel}:{b.dominant_provider}:{idx}",
                    entity_type=ArtifactType.INCIDENT,
                    name=f"Инцидентный всплеск [{b.dominant_provider} ({b.dominant_level})]",
                    summary=b_text,
                    severity="error" if b.dominant_level in ("Error", "Critical") else "warning",
                    confidence=0.95,
                    diagnostic_info=DiagnosticKnowledge(
                        symptoms=[b.summary],
                        possible_causes=[f"Всплеск активности провайдера {b.dominant_provider} в окне {b.time_window}"],
                    ),
                    tags=[profile.channel.lower(), b.dominant_provider.lower(), "incident_burst"],
                )
                self.wiki_storage.save_entity(burst_entity)
                self.wiki_storage.record_observation(burst_entity.canonical_key)

        if decision.strategy in (IngestionStrategy.NOVELTY_SIGNATURE, IngestionStrategy.INCIDENT_FOCUSED):
            for sig in profile.novel_signatures:
                sig_id = f"sig_{profile.channel}_{sig['provider']}_{sig['event_id']}"
                sig_text = (
                    f"Новая сигнатура журнала {profile.channel}.\n"
                    f"Поставщик: {sig['provider']}, Event ID: {sig['event_id']}\n"
                    f"Уровень: {sig['level']}, Встретилось раз: {sig['count']}\n"
                    f"Образец: {sig['sample']}"
                )
                generated_chunks.append({
                    'id': sig_id,
                    'type': 'novel_signature',
                    'channel': profile.channel,
                    'title': f"Сигнатура {sig['provider']} (ID {sig['event_id']})",
                    'text': sig_text,
                    'timestamp': now_str,
                    'meta': {'provider': sig['provider'], 'event_id': sig['event_id']},
                })

                sig_entity = KnowledgeEntity(
                    canonical_key=f"windows_event:{sig['provider']}:{sig['event_id']}",
                    entity_type=ArtifactType.WINDOWS_EVENT,
                    name=f"Сигнатура {sig['provider']} (ID {sig['event_id']})",
                    summary=sig_text,
                    fingerprint_pattern=sig.get('sample', ''),
                    severity="error" if sig['level'] in ("Error", "Critical") else "warning",
                    confidence=0.9,
                    tags=[profile.channel.lower(), str(sig['provider']).lower(), f"event_{sig['event_id']}"],
                )
                self.wiki_storage.save_entity(sig_entity)
                self.wiki_storage.record_observation(sig_entity.canonical_key)

        if decision.strategy == IngestionStrategy.NOISE_MASKED:
            for p in profile.top_patterns[:3]:
                p_id = f"pattern_{profile.channel}_{p['provider']}_{p['event_id']}_{hashlib.md5(p['template'].encode('utf-8')).hexdigest()[:6]}"
                p_text = (
                    f"Сжатый дайджест фонового сервиса {p['provider']}.\n"
                    f"Event ID: {p['event_id']}, Уровень: {p['level']}\n"
                    f"Количество повторений: {p['count']} шт.\n"
                    f"Шаблон сообщения: {p['template']}"
                )
                generated_chunks.append({
                    'id': p_id,
                    'type': 'noise_digest',
                    'channel': profile.channel,
                    'title': f"Фоновый шаблон [{p['provider']} x{p['count']}]",
                    'text': p_text,
                    'timestamp': now_str,
                    'meta': {'provider': p['provider'], 'count': p['count']},
                })

                pat_entity = KnowledgeEntity(
                    canonical_key=f"pattern:{profile.channel}:{p['provider']}:{p['event_id']}",
                    entity_type=ArtifactType.SYMPTOM,
                    name=f"Фоновый шаблон [{p['provider']} x{p['count']}]",
                    summary=p_text,
                    fingerprint_pattern=p.get('template', ''),
                    severity="info",
                    confidence=1.0,
                    tags=[profile.channel.lower(), str(p['provider']).lower(), "noise_digest"],
                )
                self.wiki_storage.save_entity(pat_entity)
                self.wiki_storage.record_observation(pat_entity.canonical_key)

        doc_dict: Dict[str, Dict[str, Any]] = {c['id']: c for c in self.chunks}
        for chunk in generated_chunks:
            doc_dict[chunk['id']] = chunk
        updated = list(doc_dict.values())
        updated.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        self.chunks = updated[:self.max_chunks]
        self.save()
        return len(generated_chunks)

    def search(self, query: str, top_k: int = 5, channel: str = '') -> List[Dict[str, Any]]:
        """Быстрый гибридный поиск по адаптивным чанкам RAG и SQLite FTS5 базе WikiLLM."""
        if not query.strip():
            return []

        results_by_id: Dict[str, Dict[str, Any]] = {}

        # 1. Полнотекстовый поиск FTS5 через WikiStorage
        try:
            fts_entities = self.wiki_storage.search_fts(query, limit=top_k)
            for entity in fts_entities:
                key = entity.canonical_key
                results_by_id[key] = {
                    'id': key,
                    'type': entity.entity_type.value,
                    'channel': channel or 'System',
                    'title': entity.name,
                    'text': entity.summary,
                    'timestamp': entity.updated_at,
                    'meta': {'severity': entity.severity, 'confidence': entity.confidence, 'source': 'wikillm_fts'},
                    'relevance_score': 2.0,
                }
        except Exception as fts_err:
            logger.debug(f"[AdaptiveLogRAG] Ошибка FTS поиска в WikiStorage: {fts_err}")

        # 2. Локальный поиск по ключевым словам и синонимам
        if self.chunks:
            candidates = [c for c in self.chunks if not channel or c.get('channel', '').lower() == channel.lower()]
            if not candidates:
                candidates = self.chunks

            cleaned = re.sub(r'[^\w\s-]', ' ', query.lower())
            tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
            if tokens:
                synonyms = {
                    'сеть': ['network', 'nic', 'realtek', 'vmswitch', 'disconnect', 'адаптер'],
                    'сбой': ['error', 'critical', 'crash', 'fault', 'инцидент', 'ошибка'],
                    'здоровье': ['health', 'snapshot', 'стабильность', 'score'],
                    'служба': ['service', 'scm', '7040', '7036'],
                }
                expanded = list(tokens)
                for t in tokens:
                    for k, syn_list in synonyms.items():
                        if t.startswith(k[:3]) or k.startswith(t[:3]):
                            expanded.extend(syn_list)

                for c in candidates:
                    c_id = c.get('id', '')
                    c_text = f"{c.get('title', '')} {c.get('text', '')}".lower()
                    score = 0.0
                    for tok in expanded:
                        if tok in c_text:
                            score += 1.0
                    if score > 0:
                        if c_id in results_by_id:
                            results_by_id[c_id]['relevance_score'] += score
                        else:
                            res = dict(c)
                            res['relevance_score'] = score
                            results_by_id[c_id] = res

        final_results = list(results_by_id.values())
        final_results.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        return final_results[:top_k]