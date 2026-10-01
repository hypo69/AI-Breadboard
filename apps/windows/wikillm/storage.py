# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Storage
# =============================================================================
# Description:
#   Хранилище базы знаний WikiLLM на SQLite с поддержкой полнотекстового поиска FTS5,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.storage import WikiStorage
#
#     service = WikiStorage()
#
# File: storage.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Хранилище базы знаний WikiLLM на SQLite с поддержкой полнотекстового поиска FTS5,"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from logger import logger
from .models import (
    ArtifactType,
    Claim,
    CodeKnowledge,
    DiagnosticKnowledge,
    Evidence,
    KnowledgeEntity,
    KnowledgeSource,
    ObservationRecord,
    ResolutionAction,
    utc_now_iso,
)


class WikiStorage:
    """SQLite-хранилище сущностей, фактов, наблюдений и полнотекстового индекса."""

    def __init__(self, db_path: str | Path = "data/windows_wikillm/knowledge.db") -> None:
        """Инициализирует подключение к SQLite базе данных.

        Args:
            db_path: Путь к файлу базы данных или ':memory:'.
        """
        self.db_path = Path(db_path) if str(db_path) != ":memory:" else ":memory:"
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON")
        elif isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Контекстный менеджер соединения с базой данных SQLite."""
        if self._mem_conn is not None:
            try:
                yield self._mem_conn
                self._mem_conn.commit()
            except Exception:
                self._mem_conn.rollback()
                raise
        else:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _init_db(self) -> None:
        """Создает таблицы базы данных и виртуальную таблицу FTS5 при их отсутствии."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    canonical_key TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'system',
                    severity TEXT NOT NULL DEFAULT 'info',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    provenance_source TEXT NOT NULL DEFAULT 'observed',
                    provenance_model TEXT,
                    fingerprint TEXT,
                    diagnostic_json TEXT,
                    code_json TEXT,
                    tags_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS observations (
                    canonical_key TEXT PRIMARY KEY,
                    total_occurrences INTEGER NOT NULL DEFAULT 1,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    co_occurrences_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    canonical_key TEXT NOT NULL REFERENCES entities(canonical_key) ON DELETE CASCADE,
                    statement TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    source TEXT NOT NULL DEFAULT 'observed',
                    verified INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    canonical_key TEXT NOT NULL REFERENCES entities(canonical_key) ON DELETE CASCADE,
                    description TEXT NOT NULL,
                    telemetry_metric TEXT,
                    sample_value TEXT,
                    observed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS relationships (
                    source_key TEXT NOT NULL,
                    target_key TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    co_occurrences INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY(source_key, target_key, relationship_type)
                );

                CREATE TABLE IF NOT EXISTS resolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_key TEXT NOT NULL REFERENCES entities(canonical_key) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    command TEXT,
                    risk_level TEXT NOT NULL DEFAULT 'safe',
                    is_automated INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_entities_fingerprint ON entities(fingerprint);
                CREATE INDEX IF NOT EXISTS idx_entities_category ON entities(category);
                CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
                CREATE INDEX IF NOT EXISTS idx_claims_key ON claims(canonical_key);
                CREATE INDEX IF NOT EXISTS idx_evidence_key ON evidence(canonical_key);
                CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_key);

                CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(
                    canonical_key UNINDEXED,
                    name,
                    summary,
                    tags,
                    details
                );
                """
            )

    def save_entity(self, entity: KnowledgeEntity) -> None:
        """Сохраняет или обновляет сущность базы знаний со всеми связями и FTS-индексом.

        Args:
            entity: Экземпляр KnowledgeEntity для сохранения.
        """
        now = utc_now_iso()
        diag_json = entity.diagnostic_info.model_dump_json() if entity.diagnostic_info else None
        code_json = entity.code_info.model_dump_json() if entity.code_info else None
        tags_json = json.dumps(entity.tags, ensure_ascii=False)

        with self._connect() as conn:
            # 1. Вставка или обновление главной записи entities
            conn.execute(
                """
                INSERT INTO entities (
                    canonical_key, entity_type, name, summary, category, severity,
                    confidence, provenance_source, provenance_model, fingerprint,
                    diagnostic_json, code_json, tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_key) DO UPDATE SET
                    entity_type = excluded.entity_type,
                    name = excluded.name,
                    summary = excluded.summary,
                    category = excluded.category,
                    severity = excluded.severity,
                    confidence = excluded.confidence,
                    provenance_source = excluded.provenance_source,
                    provenance_model = excluded.provenance_model,
                    fingerprint = excluded.fingerprint,
                    diagnostic_json = excluded.diagnostic_json,
                    code_json = excluded.code_json,
                    tags_json = excluded.tags_json,
                    updated_at = excluded.updated_at
                """,
                (
                    entity.canonical_key,
                    entity.entity_type.value,
                    entity.name,
                    entity.summary,
                    entity.category,
                    entity.severity,
                    entity.confidence,
                    entity.provenance_source.value,
                    entity.provenance_model,
                    entity.fingerprint,
                    diag_json,
                    code_json,
                    tags_json,
                    entity.created_at or now,
                    now,
                ),
            )

            # 2. Обновление claims
            conn.execute("DELETE FROM claims WHERE canonical_key = ?", (entity.canonical_key,))
            for claim in entity.claims:
                cid = claim.claim_id or str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO claims (claim_id, canonical_key, statement, confidence, source, verified, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cid,
                        entity.canonical_key,
                        claim.statement,
                        claim.confidence,
                        claim.source.value,
                        1 if claim.verified else 0,
                        claim.created_at or now,
                    ),
                )

            # 3. Обновление evidence
            conn.execute("DELETE FROM evidence WHERE canonical_key = ?", (entity.canonical_key,))
            for ev in entity.evidence:
                eid = ev.evidence_id or str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO evidence (evidence_id, canonical_key, description, telemetry_metric, sample_value, observed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eid,
                        entity.canonical_key,
                        ev.description,
                        ev.telemetry_metric,
                        ev.sample_value,
                        ev.observed_at or now,
                    ),
                )

            # 4. Обновление resolutions
            conn.execute("DELETE FROM resolutions WHERE canonical_key = ?", (entity.canonical_key,))
            if entity.diagnostic_info:
                actions = entity.diagnostic_info.remediation_steps + entity.diagnostic_info.diagnostic_actions
                for act in actions:
                    conn.execute(
                        """
                        INSERT INTO resolutions (canonical_key, title, description, command, risk_level, is_automated)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            entity.canonical_key,
                            act.title,
                            act.description,
                            act.command,
                            act.risk_level,
                            1 if act.is_automated else 0,
                        ),
                    )

            # 5. Обновление FTS5 индекса
            conn.execute("DELETE FROM source_fts WHERE canonical_key = ?", (entity.canonical_key,))
            details_text = f"{diag_json or ''} {code_json or ''}"
            conn.execute(
                """
                INSERT INTO source_fts (canonical_key, name, summary, tags, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entity.canonical_key,
                    entity.name,
                    entity.summary,
                    " ".join(entity.tags),
                    details_text,
                ),
            )

    def get_entity(self, canonical_key: str) -> Optional[KnowledgeEntity]:
        """Загружает сущность по каноническому ключу со всеми сопутствующими данными.

        Args:
            canonical_key: Канонический ключ сущности.

        Returns:
            KnowledgeEntity или None, если сущность не найдена.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM entities WHERE canonical_key = ?", (canonical_key,)
            ).fetchone()
            if not row:
                return None

            claims_rows = conn.execute(
                "SELECT * FROM claims WHERE canonical_key = ?", (canonical_key,)
            ).fetchall()
            evidence_rows = conn.execute(
                "SELECT * FROM evidence WHERE canonical_key = ?", (canonical_key,)
            ).fetchall()

            claims = [
                Claim(
                    claim_id=r["claim_id"],
                    statement=r["statement"],
                    confidence=r["confidence"],
                    source=KnowledgeSource(r["source"]),
                    verified=bool(r["verified"]),
                    created_at=r["created_at"],
                )
                for r in claims_rows
            ]

            evidence = [
                Evidence(
                    evidence_id=r["evidence_id"],
                    description=r["description"],
                    telemetry_metric=r["telemetry_metric"],
                    sample_value=r["sample_value"],
                    observed_at=r["observed_at"],
                )
                for r in evidence_rows
            ]

            diag_info = None
            if row["diagnostic_json"]:
                try:
                    diag_info = DiagnosticKnowledge.model_validate_json(row["diagnostic_json"])
                except Exception:
                    pass

            code_info = None
            if row["code_json"]:
                try:
                    code_info = CodeKnowledge.model_validate_json(row["code_json"])
                except Exception:
                    pass

            tags = []
            if row["tags_json"]:
                try:
                    tags = json.loads(row["tags_json"])
                except Exception:
                    pass

            return KnowledgeEntity(
                canonical_key=row["canonical_key"],
                entity_type=ArtifactType(row["entity_type"]),
                name=row["name"],
                summary=row["summary"],
                category=row["category"],
                severity=row["severity"],
                confidence=row["confidence"],
                provenance_source=KnowledgeSource(row["provenance_source"]),
                provenance_model=row["provenance_model"],
                fingerprint=row["fingerprint"],
                diagnostic_info=diag_info,
                code_info=code_info,
                claims=claims,
                evidence=evidence,
                tags=tags,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def find_by_fingerprint(self, fingerprint: str) -> Optional[KnowledgeEntity]:
        """Ищет сущность по шаблону отпечатка (fingerprint).

        Args:
            fingerprint: Строка отпечатка.

        Returns:
            KnowledgeEntity или None.
        """
        if not fingerprint:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT canonical_key FROM entities WHERE fingerprint = ? LIMIT 1", (fingerprint,)
            ).fetchone()
            if row:
                return self.get_entity(row["canonical_key"])
        return None

    def search_fts(self, query: str, limit: int = 10) -> List[KnowledgeEntity]:
        """Выполняет полнотекстовый поиск по FTS5 индексу.

        Args:
            query: Поисковый запрос.
            limit: Максимальное количество результатов.

        Returns:
            Список найденных KnowledgeEntity.
        """
        cleaned_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
        if not cleaned_query:
            return []

        fts_query = " OR ".join(f'"{token}*"' for token in cleaned_query.split() if token)
        if not fts_query:
            return []

        results: List[KnowledgeEntity] = []
        with self._connect() as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT canonical_key, rank FROM source_fts
                    WHERE source_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                # В случае синтаксической ошибки FTS используем LIKE fallback
                rows = conn.execute(
                    """
                    SELECT canonical_key FROM entities
                    WHERE name LIKE ? OR summary LIKE ?
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()

            for r in rows:
                ent = self.get_entity(r["canonical_key"])
                if ent:
                    results.append(ent)

        return results

    def record_observation(
        self, canonical_key: str, co_occurring_keys: Optional[List[str]] = None
    ) -> ObservationRecord:
        """Фиксирует локальное наблюдение артефакта и обновляет счетчики совместных появлений.

        Args:
            canonical_key: Канонический ключ артефакта.
            co_occurring_keys: Список одновременно наблюдавшихся других артефактов.

        Returns:
            Обновленная запись ObservationRecord.
        """
        now = utc_now_iso()
        co_keys = [k for k in (co_occurring_keys or []) if k != canonical_key]

        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM observations WHERE canonical_key = ?", (canonical_key,)
            ).fetchone()

            if row:
                total = row["total_occurrences"] + 1
                co_map: Dict[str, int] = {}
                try:
                    co_map = json.loads(row["co_occurrences_json"])
                except Exception:
                    pass

                for k in co_keys:
                    co_map[k] = co_map.get(k, 0) + 1

                conn.execute(
                    """
                    UPDATE observations
                    SET total_occurrences = ?, last_seen = ?, co_occurrences_json = ?
                    WHERE canonical_key = ?
                    """,
                    (total, now, json.dumps(co_map, ensure_ascii=False), canonical_key),
                )
                rec = ObservationRecord(
                    canonical_key=canonical_key,
                    total_occurrences=total,
                    first_seen=row["first_seen"],
                    last_seen=now,
                    co_occurrences=co_map,
                )
            else:
                co_map = {k: 1 for k in co_keys}
                conn.execute(
                    """
                    INSERT INTO observations (canonical_key, total_occurrences, first_seen, last_seen, co_occurrences_json)
                    VALUES (?, 1, ?, ?, ?)
                    """,
                    (canonical_key, now, now, json.dumps(co_map, ensure_ascii=False)),
                )
                rec = ObservationRecord(
                    canonical_key=canonical_key,
                    total_occurrences=1,
                    first_seen=now,
                    last_seen=now,
                    co_occurrences=co_map,
                )

            # Обновление графа отношений
            for target_k, count in co_map.items():
                conn.execute(
                    """
                    INSERT INTO relationships (source_key, target_key, relationship_type, confidence, co_occurrences)
                    VALUES (?, ?, 'co_occurs_with', 0.8, ?)
                    ON CONFLICT(source_key, target_key, relationship_type) DO UPDATE SET
                        co_occurrences = excluded.co_occurrences,
                        confidence = MIN(1.0, 0.5 + (excluded.co_occurrences * 0.05))
                    """,
                    (canonical_key, target_k, count),
                )

        return rec

    def get_observation(self, canonical_key: str) -> Optional[ObservationRecord]:
        """Возвращает историю наблюдений сущности.

        Args:
            canonical_key: Канонический ключ.

        Returns:
            ObservationRecord или None.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM observations WHERE canonical_key = ?", (canonical_key,)
            ).fetchone()
            if not row:
                return None
            co_map = {}
            try:
                co_map = json.loads(row["co_occurrences_json"])
            except Exception:
                pass
            return ObservationRecord(
                canonical_key=row["canonical_key"],
                total_occurrences=row["total_occurrences"],
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
                co_occurrences=co_map,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику базы знаний WikiLLM.

        Returns:
            Словарь с метриками (число сущностей, наблюдений, категорий).
        """
        with self._connect() as conn:
            total_entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            total_obs = conn.execute("SELECT COUNT(*), SUM(total_occurrences) FROM observations").fetchone()
            total_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as c FROM entities GROUP BY category"
            ).fetchall()
            type_rows = conn.execute(
                "SELECT entity_type, COUNT(*) as c FROM entities GROUP BY entity_type"
            ).fetchall()

        return {
            "total_entities": total_entities,
            "unique_observed_artifacts": total_obs[0] if total_obs else 0,
            "total_observation_events": (total_obs[1] or 0) if total_obs else 0,
            "total_claims": total_claims,
            "categories": {r["category"]: r["c"] for r in cat_rows},
            "types": {r["entity_type"]: r["c"] for r in type_rows},
        }

    def list_entities(
        self, limit: int = 50, offset: int = 0, entity_type: Optional[str] = None
    ) -> List[KnowledgeEntity]:
        """Возвращает постраничный список сущностей базы знаний.

        Args:
            limit: Количество записей.
            offset: Смещение.
            entity_type: Фильтр по типу сущности (опционально).

        Returns:
            Список сущностей KnowledgeEntity.
        """
        results: List[KnowledgeEntity] = []
        with self._connect() as conn:
            if entity_type:
                rows = conn.execute(
                    "SELECT canonical_key FROM entities WHERE entity_type = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                    (entity_type, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT canonical_key FROM entities ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()

            for r in rows:
                ent = self.get_entity(r["canonical_key"])
                if ent:
                    results.append(ent)

        return results
