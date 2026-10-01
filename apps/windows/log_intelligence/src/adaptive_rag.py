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
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Получить стандартный путь к локальному хранилищу в %APPDATA%."""

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
    """Адаптивный движок создания и поиска RAG-документов на основе решений Data Researcher."""

    def __init__(self, storage_dir: Optional[Path]=None, max_chunks: int=1000) -> None:
        """Инициализировать адаптивный RAG-индекс в локальном хранилище."""
        self.storage_dir = Path(storage_dir).resolve() if storage_dir else get_default_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_chunks = max_chunks
        self.chunks: List[Dict[str, Any]] = []
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
        """Сгенерировать целевые RAG-документы строго по выбранной стратегии Decision Gate.

        Args:
            profile (DataProfileReport): Аналитический срез данных.
            decision (IngestionDecision): Решение и стратегия шлюза.

        Returns:
            int: Количество добавленных / обновленных чанков.
        """
        now_str = profile.generated_at or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        generated_chunks: List[Dict[str, Any]] = []
        snap_id = f'snapshot_{profile.channel}_{now_str[:13]}'
        snap_text = f'Аналитический снимок здоровья канала {profile.channel}.\nМетка времени: {now_str}\nИндекс здоровья (Health Score): {profile.health_score} / 100\nВсего событий: {profile.total_events}, Уникальных шаблонов: {profile.unique_templates_count}\nИзбыточность/дублирование: {profile.redundancy_ratio_pct}%\nОшибок: {profile.error_count + profile.critical_count}, Предупреждений: {profile.warning_count}\nВыбранная стратегия: {decision.strategy.value}\nОбоснование: {decision.rationale}'
        generated_chunks.append({'id': snap_id, 'type': 'health_snapshot', 'channel': profile.channel, 'title': f'Снимок здоровья {profile.channel} ({profile.health_score}%)', 'text': snap_text, 'timestamp': now_str, 'meta': {'strategy': decision.strategy.value, 'health_score': profile.health_score}})
        if decision.strategy == IngestionStrategy.INCIDENT_FOCUSED:
            for idx, b in enumerate(profile.bursts):
                b_id = f"burst_{profile.channel}_{b.time_window.replace(':', '_')}_{idx}"
                b_text = f'Инцидентный каскад событий в канале {profile.channel}.\nОкно всплеска: {b.time_window}\nСобытий в пике: {b.event_count}\nДоминирующий уровень: {b.dominant_level}\nКлючевой источник: {b.dominant_provider}\nСводка: {b.summary}'
                generated_chunks.append({'id': b_id, 'type': 'incident_burst', 'channel': profile.channel, 'title': f'Инцидентный всплеск [{b.dominant_provider} ({b.dominant_level})]', 'text': b_text, 'timestamp': now_str, 'meta': {'window': b.time_window, 'provider': b.dominant_provider}})
        if decision.strategy in (IngestionStrategy.NOVELTY_SIGNATURE, IngestionStrategy.INCIDENT_FOCUSED):
            for sig in profile.novel_signatures:
                sig_id = f"sig_{profile.channel}_{sig['provider']}_{sig['event_id']}"
                sig_text = f"Новая сигнатура журнала {profile.channel}.\nПоставщик: {sig['provider']}, Event ID: {sig['event_id']}\nУровень: {sig['level']}, Встретилось раз: {sig['count']}\nОбразец: {sig['sample']}"
                generated_chunks.append({'id': sig_id, 'type': 'novel_signature', 'channel': profile.channel, 'title': f"Сигнатура {sig['provider']} (ID {sig['event_id']})", 'text': sig_text, 'timestamp': now_str, 'meta': {'provider': sig['provider'], 'event_id': sig['event_id']}})
        if decision.strategy == IngestionStrategy.NOISE_MASKED:
            for p in profile.top_patterns[:3]:
                p_id = f"pattern_{profile.channel}_{p['provider']}_{p['event_id']}_{hashlib.md5(p['template'].encode('utf-8')).hexdigest()[:6]}"
                p_text = f"Сжатый дайджест фонового сервиса {p['provider']}.\nEvent ID: {p['event_id']}, Уровень: {p['level']}\nКоличество повторений: {p['count']} шт.\nШаблон сообщения: {p['template']}"
                generated_chunks.append({'id': p_id, 'type': 'noise_digest', 'channel': profile.channel, 'title': f"Фоновый шаблон [{p['provider']} x{p['count']}]", 'text': p_text, 'timestamp': now_str, 'meta': {'provider': p['provider'], 'count': p['count']}})
        doc_dict: Dict[str, Dict[str, Any]] = {c['id']: c for c in self.chunks}
        for chunk in generated_chunks:
            doc_dict[chunk['id']] = chunk
        updated = list(doc_dict.values())
        updated.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        self.chunks = updated[:self.max_chunks]
        self.save()
        return len(generated_chunks)

    def search(self, query: str, top_k: int=5, channel: str='') -> List[Dict[str, Any]]:
        """Быстрый гибридный поиск по адаптивным чанкам RAG."""
        if not query.strip() or not self.chunks:
            return []
        candidates = [c for c in self.chunks if not channel or c.get('channel', '').lower() == channel.lower()]
        if not candidates:
            candidates = self.chunks
        cleaned = re.sub('[^\\w\\s-]', ' ', query.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
        if not tokens:
            return []
        synonyms = {'сеть': ['network', 'nic', 'realtek', 'vmswitch', 'disconnect', 'адаптер'], 'сбой': ['error', 'critical', 'crash', 'fault', 'инцидент', 'ошибка'], 'здоровье': ['health', 'snapshot', 'стабильность', 'score'], 'служба': ['service', 'scm', '7040', '7036']}
        expanded = list(tokens)
        for t in tokens:
            for k, syn_list in synonyms.items():
                if t.startswith(k[:3]) or k.startswith(t[:3]):
                    expanded.extend(syn_list)
        scored = []
        for c in candidates:
            c_text = f"{c.get('title', '')} {c.get('text', '')}".lower()
            score = 0.0
            for tok in expanded:
                if tok in c_text:
                    score += 1.0
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, c in scored[:top_k]:
            res = dict(c)
            res['relevance_score'] = s
            results.append(res)
        return results