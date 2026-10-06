# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Buffer
# =============================================================================
# Description:
#   Управление буферизацией и пакетной записью (batching) потока телеметрии в SQLite.
#
#   Зачем нужен этот модуль:
#     1. Снижение нагрузки на диск (I/O) и ускорение SQLite:
#        Объединяет одиночные события метрик в пачки, выполняя одну быструю
#        транзакцию вместо сотен мелких операций записи с частыми fsync/commit.
#     2. Предотвращение блокировок базы данных:
#        Минимизирует время удержания эксклюзивных транзакций SQLite, предотвращая
#        ошибки 'database is locked' при одновременном чтении данных агентами и UI.
#     3. Защита от потери данных (Fail-Safe / Disaster Recovery):
#        При сбоях записи или аварийном завершении удерживает данные во внешнем
#        журнале и автоматически восстанавливает/дописывает их при следующем старте.
#
#   Поддерживаемые режимы буферизации (buffer_mode):
#     - 'memory' (По умолчанию):
#         Накапливает записи в оперативной памяти (список в RAM).
#         Сброс в БД происходит по достижении buffer_size или по таймеру flush_interval_seconds.
#         Обеспечивает максимальную скорость работы.
#     - 'file':
#         Каждая входящая запись немедленно сериализуется и дописывается на диск
#         в аварийный JSONL-файл (telemetry_buffer.jsonl) с вызовом fsync.
#         По достижении buffer_size или по таймеру весь файл сбрасывается в SQLite
#         и усекается. Защищает от потери данных при внезапном падении процесса/питания.
#     - 'direct':
#         Отключает фоновый периодический таймер автосброса. Записи накапливаются в RAM
#         и сбрасываются только при заполнении buffer_size или явном вызове flush().
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.buffer import TelemetryBuffer
#     from apps.windows.telemetry.sqlite.connection import TelemetryConnectionManager
#     from apps.windows.telemetry.sqlite.writer import TelemetryWriter
#
#     cm = TelemetryConnectionManager("telemetry.db")
#     writer = TelemetryWriter(cm)
#     buf = TelemetryBuffer(
#         connection_manager=cm,
#         writer=writer,
#         buffer_mode='memory',  # 'memory' | 'file' | 'direct'
#         buffer_size=50,
#         flush_interval_seconds=30.0
#     )
#     buf.enqueue({"timestamp": "...", "cpu_percent": 12.5})
#
# File: buffer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 06:28:30
# =============================================================================

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .connection import TelemetryConnectionManager
from .writer import TelemetryWriter

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryBuffer:
    """Управляет буферизацией событий телеметрии в памяти и аварийном JSONL файле с контролем лимитов RAM."""

    def __init__(
        self,
        connection_manager: TelemetryConnectionManager,
        writer: TelemetryWriter,
        buffer_mode: str = 'memory',
        buffer_size: int = 50,
        flush_interval_seconds: float = 30.0,
        buffer_file_path: Optional[Union[str, Path]] = None,
        auto_flush: bool = True,
        max_buffer_bytes: int = 32 * 1024 * 1024,
    ) -> None:
        """Инициализирует буфер сброса телеметрии.

        Args:
            connection_manager: Менеджер подключений SQLite.
            writer: Писатель пакетов телеметрии.
            buffer_mode: Режим буферизации ('memory', 'file', 'direct').
            buffer_size: Максимальный размер пачки до сброса.
            flush_interval_seconds: Интервал таймера сброса в секундах.
            buffer_file_path: Путь к файлу аварийного буфера.
            auto_flush: Флаг автоматического запуска таймера сброса.
            max_buffer_bytes: Максимальный лимит памяти для записей буфера в байтах (по умолчанию 32 МБ).
        """
        self._cm = connection_manager
        self._writer = writer
        self._buffer_mode = buffer_mode.lower() if buffer_mode in ('memory', 'file', 'direct') else 'memory'
        self._buffer_size = max(1, int(buffer_size))
        self._max_buffer_bytes = max(1024 * 1024, int(max_buffer_bytes))
        self._current_buffer_bytes: int = 0
        self._flush_interval_seconds = max(0.5, float(flush_interval_seconds))
        self._auto_flush = bool(auto_flush) and not self._cm.read_only

        if buffer_file_path:
            self._buffer_file_path = Path(buffer_file_path)
        else:
            self._buffer_file_path = self._cm.db_path.parent / 'telemetry_buffer.jsonl'

        if not self._cm.read_only:
            self._buffer_file_path.parent.mkdir(parents=True, exist_ok=True)

        self._buffer: List[Dict[str, Any]] = []
        self._file_buffer_count: int = 0
        self._is_running = True
        self._flush_timer: Optional[threading.Timer] = None

        if not self._cm.read_only:
            self._recover_file_buffer()
            if self._auto_flush and self._buffer_mode != 'direct':
                self._start_flush_timer()

    @property
    def buffer_mode(self) -> str:
        """Текущий режим буферизации."""
        return self._buffer_mode

    @property
    def buffer_size(self) -> int:
        """Максимальный размер буфера в количестве записей."""
        return self._buffer_size

    @property
    def max_buffer_bytes(self) -> int:
        """Максимальный лимит памяти буфера в байтах."""
        return self._max_buffer_bytes

    @property
    def current_buffer_bytes(self) -> int:
        """Текущий объем занимаемой памяти буфера в байтах."""
        with self._cm.lock:
            return self._current_buffer_bytes

    @property
    def flush_interval_seconds(self) -> float:
        """Интервал таймера автосброса в секундах."""
        return self._flush_interval_seconds

    @property
    def buffer_file_path(self) -> Path:
        """Путь к файлу аварийного JSONL буфера."""
        return self._buffer_file_path

    def _estimate_size(self, record: Dict[str, Any]) -> int:
        """Оценивает объем памяти записи в байтах."""
        try:
            return len(json.dumps(record, ensure_ascii=False, default=str).encode('utf-8')) + 128
        except Exception:
            return sys.getsizeof(record) + 256

    def set_flush_interval_seconds(self, interval: float) -> None:
        """Динамически изменяет интервал периодического сброса буфера в SQLite."""
        new_interval = max(0.5, float(interval))
        if abs(self._flush_interval_seconds - new_interval) > 0.01:
            with self._cm.lock:
                self._flush_interval_seconds = new_interval
                if self._auto_flush and self._buffer_mode != 'direct' and not self._cm.read_only:
                    self._start_flush_timer()
                logger.info(f"Интервал сброса буфера телеметрии обновлен: {self._flush_interval_seconds}с")

    def set_buffer_mode(self, mode: str) -> None:
        """Переключает режим буферизации."""
        m = mode.lower()
        if m in ('memory', 'file', 'direct'):
            with self._cm.lock:
                self.flush()
                self._buffer_mode = m
                if m == 'direct':
                    self._stop_flush_timer()
                elif self._auto_flush and not self._cm.read_only:
                    self._start_flush_timer()
                logger.info(f'Режим буферизации переключен на: {m}')

    def get_buffered_count(self) -> int:
        """Возвращает число накопленных записей в буфере."""
        with self._cm.lock:
            return len(self._buffer) + self._file_buffer_count

    def _start_flush_timer(self) -> None:
        if self._cm.read_only or not self._is_running or self._buffer_mode == 'direct':
            return
        self._stop_flush_timer()
        self._flush_timer = threading.Timer(self._flush_interval_seconds, self._on_flush_timer)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _stop_flush_timer(self) -> None:
        if self._flush_timer is not None:
            try:
                self._flush_timer.cancel()
            except Exception:
                pass
            self._flush_timer = None

    def _on_flush_timer(self) -> None:
        if not self._is_running or self._cm.read_only:
            return
        try:
            self.flush()
        except Exception as ex:
            logger.debug(f'Ошибка фонового сброса буфера телеметрии: {ex}')
        finally:
            with self._cm.lock:
                if self._is_running and self._auto_flush and self._buffer_mode != 'direct':
                    self._start_flush_timer()

    def _recover_file_buffer(self) -> None:
        if self._cm.read_only:
            return
        if self._buffer_file_path.exists() and self._buffer_file_path.stat().st_size > 0:
            try:
                with open(self._buffer_file_path, 'r', encoding='utf-8') as f:
                    count = sum(1 for line in f if line.strip())
                self._file_buffer_count = count
                if count > 0:
                    logger.info(f'Обнаружено {count} сохраненных записей в {self._buffer_file_path.name}. Сброс в БД...')
                    self.flush()
            except Exception as ex:
                logger.warning(f'Ошибка проверки файла буфера телеметрии: {ex}')

    def enqueue(self, record: Dict[str, Any]) -> None:
        """Добавляет запись в буфер в зависимости от выбранного режима."""
        if self._cm.read_only:
            logger.warning('Попытка добавления записи в буфер в режиме Read-Only')
            return

        rec_size = self._estimate_size(record)
        with self._cm.lock:
            if self._buffer_mode == 'file':
                try:
                    line = json.dumps(record, ensure_ascii=False, default=str)
                    with open(self._buffer_file_path, 'a', encoding='utf-8') as f:
                        f.write(line + '\n')
                        f.flush()
                        os.fsync(f.fileno())
                    self._file_buffer_count += 1
                except Exception as ex:
                    logger.error(f'Ошибка записи в файл буфера телеметрии: {ex}')
                    self._buffer.append(record)
                    self._current_buffer_bytes += rec_size

                if self._file_buffer_count >= self._buffer_size or self._current_buffer_bytes >= self._max_buffer_bytes:
                    self.flush()
            else:
                self._buffer.append(record)
                self._current_buffer_bytes += rec_size
                if len(self._buffer) >= self._buffer_size or self._current_buffer_bytes >= self._max_buffer_bytes:
                    self.flush()

    def flush(self) -> int:
        """Принудительно сбрасывает записи в SQLite."""
        if self._cm.read_only:
            return 0

        with self._cm.lock:
            records_to_save: List[Dict[str, Any]] = []

            if self._buffer_file_path.exists() and self._buffer_file_path.stat().st_size > 0:
                try:
                    with open(self._buffer_file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            s = line.strip()
                            if s:
                                try:
                                    records_to_save.append(json.loads(s))
                                except Exception:
                                    pass
                except Exception as read_err:
                    logger.error(f'Ошибка чтения файла буфера: {read_err}')

            if self._buffer:
                records_to_save.extend(self._buffer)
                self._buffer = []
                self._current_buffer_bytes = 0

            if not records_to_save:
                return 0

            inserted_count = self._writer.batch_insert_records(records_to_save)

            if self._buffer_file_path.exists():
                try:
                    with open(self._buffer_file_path, 'w', encoding='utf-8') as f:
                        f.truncate(0)
                    self._file_buffer_count = 0
                except Exception as trunc_err:
                    logger.warning(f'Ошибка усечения файла буфера: {trunc_err}')

            if inserted_count > 0:
                logger.debug(f'💾 [Хранилище SQLite] Пакетный сброс буфера: {inserted_count} записей зафиксировано в {self._cm.db_path.name}')

            return inserted_count

    def close(self) -> None:
        """Останавливает таймер и выполняет финальный сброс буфера."""
        self._is_running = False
        self._stop_flush_timer()
        if not self._cm.read_only:
            try:
                self.flush()
            except Exception:
                pass
