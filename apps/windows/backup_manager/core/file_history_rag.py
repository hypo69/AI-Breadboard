# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows File History RAG Indexer and Search Engine
# =============================================================================
# Description:
#   Движок инкрементальной индексации и семантического поиска по архивам
#   службы Истории файлов Windows (fhsvc). Поддерживает однократное создание
#   индекса и последующее инкрементальное дополнение новыми версиями файлов.
#
# Examples:
#   >>> from apps.windows.backup_manager.core.file_history_rag import WindowsFileHistoryRAG
#   >>> rag = WindowsFileHistoryRAG()
#   >>> sync_report = rag.sync()
#   >>> results = rag.search("договор аренды", top_k=5)
#
# File: file_history_rag.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок RAG-индексации и поиска по архивам Истории файлов Windows."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from header import __root__
from logger import logger
from apps.windows.backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows.backup_manager.core.models import (
    FileHistoryRAGSearchResult,
    FileHistoryRAGStatus,
    FileVersionRecord,
    FileHistoryVersionSummary,
)
from apps.windows.backup_manager.core.storage_auditor import BackupStorageAuditor

_DEFAULT_INDEX_DIR: Path = __root__ / "data" / "rag_index" / "windows_file_history"

SUPPORTED_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".markdown", ".rst", ".log",
    ".json", ".csv", ".tsv", ".xml", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".htm", ".css", ".ps1", ".sh", ".sql", ".bat", ".cmd",
    ".pdf", ".docx",
}


def compute_file_sha256(file_path: Path) -> str:
    """Вычисляет хэш SHA-256 для файла.

    Args:
        file_path (Path): Путь к файлу.

    Returns:
        str: Hex-строка дайджеста SHA-256 или пустая строка при ошибке чтения.
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as ex:
        logger.error(f"[FileHistoryRAG] Ошибка вычисления хэша для {file_path}: {ex}")
        return ""


@dataclass
class FileHistoryChunk:
    """Текстовый фрагмент архивной версии файла с временными метаданными."""
    chunk_id: str
    original_path: str
    backup_file_path: str
    chunk_index: int
    text: str
    version_timestamp_iso: Optional[str] = None
    drive_letter: Optional[str] = None
    file_size_bytes: int = 0
    content_hash: str = ""


class WindowsFileHistoryRAG:
    """
    ## hypo69 docblock
    Движок инкрементальной RAG-индексации и поиска по архивам Windows File History.
    Создается один раз и дополняется только новыми версиями файлов.
    """

    VERSION_REGEX = re.compile(r"^(.*?)(?: \((\d{4}_\d{2}_\d{2} \d{2}_\d{2}_\d{2} UTC)\))?(\.[^.]*)?$")

    def __init__(
        self,
        index_dir: Optional[Path] = None,
        fh_manager: Optional[FileHistoryManager] = None,
        storage_auditor: Optional[BackupStorageAuditor] = None,
    ) -> None:
        """Инициализация движка RAG по Истории файлов.

        Args:
            index_dir (Optional[Path]): Каталог для сохранения индекса и метаданных.
            fh_manager (Optional[FileHistoryManager]): Менеджер службы File History.
            storage_auditor (Optional[BackupStorageAuditor]): Аудитор хранилища бэкапов.
        """
        self.index_dir = index_dir or _DEFAULT_INDEX_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.fh_manager = fh_manager or FileHistoryManager()
        self.storage_auditor = storage_auditor or BackupStorageAuditor()

        self.meta_file = self.index_dir / "meta.json"
        self.chunks_file = self.index_dir / "chunks.json"
        self.vectors_file = self.index_dir / "vectors.npy"
        self.vocab_file = self.index_dir / "vocab.json"
        self.idf_file = self.index_dir / "idf.npy"

        self.chunks: List[FileHistoryChunk] = []
        self.vectors: Optional[np.ndarray] = None
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None
        self.meta: Dict[str, Any] = {
            "total_files_indexed": 0,
            "total_chunks": 0,
            "last_sync_time": None,
            "indexed_files": {},
        }

        self._load_state()

    def _load_state(self) -> None:
        """Загружает сохраненный индекс и метаданные с диска."""
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception as ex:
                logger.error(f"[FileHistoryRAG] Ошибка загрузки meta.json: {ex}")

        if self.chunks_file.exists():
            try:
                with open(self.chunks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = [FileHistoryChunk(**item) for item in data]
            except Exception as ex:
                logger.error(f"[FileHistoryRAG] Ошибка загрузки chunks.json: {ex}")
                self.chunks = []

        if self.vectors_file.exists():
            try:
                self.vectors = np.load(str(self.vectors_file))
            except Exception as ex:
                logger.error(f"[FileHistoryRAG] Ошибка загрузки vectors.npy: {ex}")
                self.vectors = None

        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, "r", encoding="utf-8") as f:
                    self.vocab = json.load(f)
            except Exception as ex:
                logger.error(f"[FileHistoryRAG] Ошибка загрузки vocab.json: {ex}")
                self.vocab = {}

        if self.idf_file.exists():
            try:
                self.idf = np.load(str(self.idf_file))
            except Exception as ex:
                logger.error(f"[FileHistoryRAG] Ошибка загрузки idf.npy: {ex}")
                self.idf = None

    def _save_state(self) -> None:
        """Сохраняет метаданные, чанки и векторные индексы на диск."""
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.meta, f, ensure_ascii=False, indent=2)

            with open(self.chunks_file, "w", encoding="utf-8") as f:
                json.dump([asdict(c) for c in self.chunks], f, ensure_ascii=False, indent=2)

            if self.vectors is not None:
                np.save(str(self.vectors_file), self.vectors)

            if self.vocab:
                with open(self.vocab_file, "w", encoding="utf-8") as f:
                    json.dump(self.vocab, f, ensure_ascii=False, indent=2)

            if self.idf is not None:
                np.save(str(self.idf_file), self.idf)
        except Exception as ex:
            logger.error(f"[FileHistoryRAG] Ошибка сохранения состояния индекса: {ex}")

    def resolve_backup_target(self, explicit_target: Optional[str] = None) -> Optional[Path]:
        """Определяет базовую директорию хранилища Windows File History.

        Args:
            explicit_target (Optional[str]): Явно заданный пользователем путь.

        Returns:
            Optional[Path]: Путь к хранилищу или None, если не найдено.
        """
        if explicit_target:
            p = Path(explicit_target)
            if p.exists():
                return p

        # 1. Попытка извлечь из Config.xml
        cfg = self.fh_manager.parse_config()
        if cfg.is_configured:
            if cfg.target_url:
                p = Path(cfg.target_url)
                if p.exists():
                    return p
            if cfg.target_drive_letter:
                p = Path(f"{cfg.target_drive_letter}:\\")
                if p.exists():
                    return p

        # 2. Попытка автоматического обнаружения через аудитор
        detected = self.storage_auditor._detect_backup_location()
        if detected:
            p = Path(detected)
            if p.exists():
                return p

        return None

    def parse_version_filename(self, filename: str) -> Tuple[str, Optional[datetime], str]:
        """Парсит имя архивного файла Windows File History.

        Пример: 'Project Report (2026_09_16 19_30_00 UTC).docx'
        -> ('Project Report', datetime(2026, 9, 16, 19, 30, 0), '.docx')

        Args:
            filename (str): Имя файла.

        Returns:
            Tuple[str, Optional[datetime], str]: (базовое имя, временная метка, расширение).
        """
        match = self.VERSION_REGEX.match(filename)
        if not match:
            p = Path(filename)
            return p.stem, None, p.suffix.lower()

        base_name = match.group(1) or ""
        ts_str = match.group(2)
        ext = (match.group(3) or "").lower()

        dt: Optional[datetime] = None
        if ts_str:
            try:
                dt = datetime.strptime(ts_str, "%Y_%m_%d %H_%M_%S UTC")
            except Exception:
                dt = None

        return base_name, dt, ext

    def extract_text(self, file_path: Path) -> str:
        """Извлекает текстовое содержимое из архивного файла различных форматов.

        Args:
            file_path (Path): Путь к файлу.

        Returns:
            str: Извлеченный текст.
        """
        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return ""

        try:
            if ext in [".txt", ".md", ".markdown", ".rst", ".log", ".py", ".js", ".ts", ".html", ".htm", ".css", ".ps1", ".sh", ".sql", ".bat", ".cmd", ".xml", ".yaml", ".yml"]:
                return file_path.read_text(encoding="utf-8", errors="replace")

            if ext == ".json":
                data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
                return json.dumps(data, ensure_ascii=False, indent=2)

            if ext in [".csv", ".tsv"]:
                delim = "\t" if ext == ".tsv" else ","
                lines = []
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f, delimiter=delim)
                    for row in reader:
                        lines.append(" | ".join(row))
                return "\n".join(lines)

            if ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(file_path))
                    parts = [page.extract_text() or "" for page in reader.pages]
                    return "\n\n".join(p.strip() for p in parts if p.strip())
                except Exception as ex:
                    logger.warning(f"[FileHistoryRAG] Ошибка чтения PDF {file_path.name}: {ex}")
                    return ""

            if ext == ".docx":
                try:
                    import docx
                    doc = docx.Document(str(file_path))
                    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                except Exception as ex:
                    logger.warning(f"[FileHistoryRAG] Ошибка чтения DOCX {file_path.name}: {ex}")
                    return ""

        except Exception as ex:
            logger.error(f"[FileHistoryRAG] Ошибка извлечения текста из {file_path}: {ex}")

        return ""

    def chunk_text(
        self,
        text: str,
        original_path: str,
        backup_file_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        version_dt: Optional[datetime] = None,
        drive_letter: Optional[str] = None,
        file_size: int = 0,
        content_hash: str = "",
    ) -> List[FileHistoryChunk]:
        """Разбивает текст на перекрывающиеся семантические чанки.

        Args:
            text (str): Исходный текст.
            original_path (str): Оригинальный относительный путь к файлу.
            backup_file_path (str): Путь к файлу резервной копии.
            chunk_size (int): Размер чанка.
            chunk_overlap (int): Перекрытие.
            version_dt (Optional[datetime]): Время снимка версии.
            drive_letter (Optional[str]): Буква диска.
            file_size (int): Размер файла.
            content_hash (str): Хэш SHA-256.

        Returns:
            List[FileHistoryChunk]: Список чанков.
        """
        clean_text = text.strip()
        if not clean_text:
            return []

        chunks: List[FileHistoryChunk] = []
        step = max(1, chunk_size - chunk_overlap)
        pos = 0
        chunk_idx = 0
        ts_iso = version_dt.isoformat() if version_dt else None

        while pos < len(clean_text):
            end_pos = min(pos + chunk_size, len(clean_text))
            if end_pos < len(clean_text):
                boundary = clean_text.rfind("\n\n", pos + (chunk_size // 2), end_pos)
                if boundary == -1:
                    boundary = clean_text.rfind("\n", pos + (chunk_size // 2), end_pos)
                if boundary == -1:
                    boundary = clean_text.rfind(". ", pos + (chunk_size // 2), end_pos)
                if boundary != -1:
                    end_pos = boundary + 1

            chunk_str = clean_text[pos:end_pos].strip()
            if chunk_str:
                chunk_id = f"{original_path}#{ts_iso or 'current'}#chunk_{chunk_idx}"
                chunks.append(
                    FileHistoryChunk(
                        chunk_id=chunk_id,
                        original_path=original_path,
                        backup_file_path=backup_file_path,
                        chunk_index=chunk_idx,
                        text=chunk_str,
                        version_timestamp_iso=ts_iso,
                        drive_letter=drive_letter,
                        file_size_bytes=file_size,
                        content_hash=content_hash,
                    )
                )
                chunk_idx += 1

            pos += step

        return chunks

    def _compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """Вычисляет TF-IDF матрицу локально без внешних сетевых вызовов.

        Args:
            texts (List[str]): Список текстов чанков.

        Returns:
            np.ndarray: Нормализованная матрица эмбеддингов.
        """
        tokenized_docs = []
        vocab: Dict[str, int] = {}
        for t in texts:
            words = re.findall(r"\b\w+\b", t.lower())
            tokenized_docs.append(words)
            for w in words:
                if len(w) > 2 and w not in vocab:
                    vocab[w] = len(vocab)

        self.vocab = vocab
        if not vocab:
            self.idf = None
            return np.zeros((len(texts), 0), dtype=np.float32)

        doc_count = len(tokenized_docs)
        df = np.zeros(len(vocab), dtype=np.float32)
        for words in tokenized_docs:
            unique_words = set(words)
            for w in unique_words:
                if w in vocab:
                    df[vocab[w]] += 1

        idf = np.log((doc_count + 1.0) / (df + 1.0)) + 1.0
        self.idf = idf

        matrix = np.zeros((len(texts), len(vocab)), dtype=np.float32)
        for i, words in enumerate(tokenized_docs):
            if not words:
                continue
            tf: Dict[int, int] = {}
            for w in words:
                if w in vocab:
                    idx = vocab[w]
                    tf[idx] = tf.get(idx, 0) + 1
            total_w = len(words)
            for idx, count in tf.items():
                matrix[i, idx] = (count / total_w) * idf[idx]

        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        return matrix / norms

    def _transform_query(self, query: str) -> np.ndarray:
        """Преобразует поисковый запрос в вектор с использованием существующего словаря и IDF.

        Args:
            query (str): Текст запроса.

        Returns:
            np.ndarray: Нормализованный вектор запроса (1, dim).
        """
        if not self.vocab or self.idf is None:
            return np.zeros((1, 0), dtype=np.float32)

        words = re.findall(r"\b\w+\b", query.lower())
        vec = np.zeros((1, len(self.vocab)), dtype=np.float32)
        if not words:
            return vec

        tf: Dict[int, int] = {}
        for w in words:
            if w in self.vocab:
                idx = self.vocab[w]
                tf[idx] = tf.get(idx, 0) + 1

        total_w = len(words)
        for idx, count in tf.items():
            vec[0, idx] = (count / total_w) * self.idf[idx]

        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec = vec / norm
        return vec

    def sync(
        self,
        target_path: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """Выполняет инкрементальную синхронизацию и индексацию архива File History.

        При первом запуске строит индекс. При повторных запусках обрабатывает
        ТОЛЬКО новые появившиеся снимки файлов.

        Args:
            target_path (Optional[str]): Каталог бэкапа (если не задан, автоопределение).
            chunk_size (int): Размер чанка.
            chunk_overlap (int): Перекрытие чанков.
            force_rebuild (bool): Сбросить индекс и пересобрать всё заново.

        Returns:
            Dict[str, Any]: Отчет о синхронизации.
        """
        root_dir = self.resolve_backup_target(target_path)
        if not root_dir or not root_dir.exists():
            return {
                "success": False,
                "error": "Каталог хранилища File History не найден или не настроен.",
                "scanned_files": 0,
                "new_files_added": 0,
                "total_chunks": len(self.chunks),
            }

        if force_rebuild:
            self.chunks = []
            self.vectors = None
            self.vocab = {}
            self.idf = None
            self.meta["indexed_files"] = {}

        # Поиск папок Data
        data_roots = list(root_dir.glob("FileHistory/*/*/Data"))
        if not data_roots:
            data_roots = list(root_dir.glob("*/FileHistory/*/*/Data"))

        if not data_roots:
            if (root_dir / "Data").exists():
                data_roots = [root_dir / "Data"]
            elif (root_dir / "FileHistory").exists():
                data_roots = list(root_dir.glob("FileHistory/*/*/Data"))
            else:
                data_roots = [root_dir]

        indexed_files = self.meta.get("indexed_files", {})
        new_chunks: List[FileHistoryChunk] = []
        files_scanned = 0
        new_files_added = 0
        skipped_unchanged = 0

        for d_root in data_roots:
            if not d_root.exists():
                continue

            for root, _, files in os.walk(d_root):
                for fname in files:
                    fpath = Path(root) / fname
                    ext = fpath.suffix.lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue

                    files_scanned += 1
                    try:
                        fstat = fpath.stat()
                        mtime = fstat.st_mtime
                        fsize = fstat.st_size
                    except Exception:
                        continue

                    fpath_key = str(fpath.resolve())
                    existing_entry = indexed_files.get(fpath_key)

                    # Проверка инкрементальности: если mtime и размер совпадают, пропускаем
                    if existing_entry and existing_entry.get("mtime") == mtime and existing_entry.get("size") == fsize:
                        skipped_unchanged += 1
                        continue

                    fhash = compute_file_sha256(fpath)
                    if existing_entry and existing_entry.get("hash") == fhash:
                        existing_entry["mtime"] = mtime
                        skipped_unchanged += 1
                        continue

                    base_name, version_dt, _ = self.parse_version_filename(fname)
                    try:
                        rel_path = fpath.relative_to(d_root).as_posix()
                    except Exception:
                        rel_path = fpath.name

                    parts = rel_path.split("/")
                    drive_letter = parts[0] if parts and len(parts[0]) == 1 else None

                    text = self.extract_text(fpath)
                    if not text:
                        indexed_files[fpath_key] = {
                            "mtime": mtime,
                            "size": fsize,
                            "hash": fhash,
                            "original_path": rel_path,
                            "version_timestamp": version_dt.isoformat() if version_dt else datetime.fromtimestamp(mtime).isoformat(),
                            "chunks_count": 0,
                        }
                        continue

                    doc_chunks = self.chunk_text(
                        text=text,
                        original_path=rel_path,
                        backup_file_path=str(fpath),
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        version_dt=version_dt or datetime.fromtimestamp(mtime),
                        drive_letter=drive_letter,
                        file_size=fsize,
                        content_hash=fhash,
                    )

                    new_chunks.extend(doc_chunks)
                    new_files_added += 1

                    indexed_files[fpath_key] = {
                        "mtime": mtime,
                        "size": fsize,
                        "hash": fhash,
                        "original_path": rel_path,
                        "version_timestamp": version_dt.isoformat() if version_dt else datetime.fromtimestamp(mtime).isoformat(),
                        "chunks_count": len(doc_chunks),
                    }

        if new_chunks:
            self.chunks.extend(new_chunks)
            all_texts = [c.text for c in self.chunks]
            self.vectors = self._compute_embeddings(all_texts)

        self.meta.update({
            "total_files_indexed": len(indexed_files),
            "total_chunks": len(self.chunks),
            "last_sync_time": datetime.now().isoformat(),
            "dimension": int(self.vectors.shape[1]) if self.vectors is not None else 0,
            "indexed_files": indexed_files,
        })
        self._save_state()

        logger.info(
            f"[FileHistoryRAG] Синхронизация завершена: сканировано={files_scanned}, "
            f"добавлено={new_files_added}, пропущено={skipped_unchanged}, всего_чанков={len(self.chunks)}"
        )

        return {
            "success": True,
            "storage_path": str(root_dir),
            "files_scanned": files_scanned,
            "new_files_added": new_files_added,
            "skipped_unchanged": skipped_unchanged,
            "new_chunks_added": len(new_chunks),
            "total_chunks": len(self.chunks),
            "total_files_indexed": len(indexed_files),
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        path_pattern: Optional[str] = None,
        drive_filter: Optional[str] = None,
    ) -> List[FileHistoryRAGSearchResult]:
        """Выполняет семантический поиск по архивным версиям файлов Windows с фильтрами.

        Args:
            query (str): Поисковый запрос.
            top_k (int): Лимит результатов.
            min_score (float): Минимальный порог релевантности.
            date_from (Optional[datetime]): Минимальная дата создания снимка.
            date_to (Optional[datetime]): Максимальная дата создания снимка.
            path_pattern (Optional[str]): Фильтр по подстроке пути к файлу.
            drive_filter (Optional[str]): Фильтр по букве диска (например, 'C').

        Returns:
            List[FileHistoryRAGSearchResult]: Список найденных релевантных фрагментов.
        """
        clean_query = query.strip()
        if not clean_query or not self.chunks:
            return []

        all_texts = [c.text for c in self.chunks]
        if (
            self.vectors is None
            or self.vectors.shape[0] != len(all_texts)
            or not self.vocab
            or self.idf is None
            or self.vectors.shape[1] != len(self.vocab)
        ):
            self.vectors = self._compute_embeddings(all_texts)

        query_vec = self._transform_query(clean_query)
        if query_vec.shape[1] == 0 or np.linalg.norm(query_vec) < 1e-10:
            return []

        similarities = np.dot(self.vectors, query_vec.T).flatten()
        sorted_indices = np.argsort(similarities)[::-1]

        results: List[FileHistoryRAGSearchResult] = []
        path_pat_lower = path_pattern.lower() if path_pattern else None
        drive_flt_upper = drive_filter.upper() if drive_filter else None

        for idx in sorted_indices:
            score = float(similarities[idx])
            if score < min_score or score <= 0.0:
                continue

            chunk = self.chunks[idx]

            if path_pat_lower and path_pat_lower not in chunk.original_path.lower():
                continue

            if drive_flt_upper and chunk.drive_letter and chunk.drive_letter.upper() != drive_flt_upper:
                continue

            chunk_dt: Optional[datetime] = None
            if chunk.version_timestamp_iso:
                try:
                    chunk_dt = datetime.fromisoformat(chunk.version_timestamp_iso)
                except Exception:
                    pass

            if date_from and chunk_dt and chunk_dt < date_from:
                continue
            if date_to and chunk_dt and chunk_dt > date_to:
                continue

            results.append(
                FileHistoryRAGSearchResult(
                    chunk_id=chunk.chunk_id,
                    original_path=chunk.original_path,
                    backup_file_path=chunk.backup_file_path,
                    version_timestamp=chunk_dt,
                    score=round(score, 4),
                    text=chunk.text,
                    chunk_index=chunk.chunk_index,
                )
            )

            if len(results) >= top_k:
                break

        return results

    def get_file_versions(self, path_substring: str) -> FileHistoryVersionSummary:
        """Возвращает историю всех найденных версий документа по его имени или пути.

        Args:
            path_substring (str): Имя или часть пути к документу.

        Returns:
            FileHistoryVersionSummary: Список всех снимков данного файла.
        """
        indexed = self.meta.get("indexed_files", {})
        versions: List[FileVersionRecord] = []
        query_sub = path_substring.lower()

        for fpath, info in indexed.items():
            orig = info.get("original_path", "")
            if query_sub in orig.lower() or query_sub in Path(fpath).name.lower():
                ts_iso = info.get("version_timestamp")
                dt = datetime.fromisoformat(ts_iso) if ts_iso else None
                versions.append(
                    FileVersionRecord(
                        original_relative_path=orig,
                        backup_file_path=fpath,
                        version_timestamp=dt,
                        size_bytes=info.get("size", 0),
                    )
                )

        versions.sort(key=lambda v: v.version_timestamp or datetime.min, reverse=True)
        return FileHistoryVersionSummary(
            original_path=path_substring,
            total_versions=len(versions),
            versions=versions,
        )

    def get_status(self) -> FileHistoryRAGStatus:
        """Возвращает текущее состояние и метрики RAG-индекса.

        Returns:
            FileHistoryRAGStatus: Модель статуса.
        """
        last_sync = self.meta.get("last_sync_time")
        last_sync_dt = datetime.fromisoformat(last_sync) if last_sync else None

        return FileHistoryRAGStatus(
            index_dir=str(self.index_dir),
            total_files_indexed=len(self.meta.get("indexed_files", {})),
            total_chunks=len(self.chunks),
            dimension=self.meta.get("dimension", 0),
            last_sync_time=last_sync_dt,
            is_ready=len(self.chunks) > 0 and self.vectors is not None,
        )


_file_history_rag_instance: Optional[WindowsFileHistoryRAG] = None


def get_file_history_rag() -> WindowsFileHistoryRAG:
    """Возвращает синглтон-экземпляр WindowsFileHistoryRAG."""
    global _file_history_rag_instance
    if _file_history_rag_instance is None:
        _file_history_rag_instance = WindowsFileHistoryRAG()
    return _file_history_rag_instance
