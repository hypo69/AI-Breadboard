# -*- coding: utf-8 -*-
"""Модуль JSON‑логгера телеметрии Windows.

 Предоставляет класс :class:`TelemetryJsonLogger` для записи событий телеметрии в формате JSON Lines
 с поддержкой ротации файлов при превышении заданного размера.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Optional

import logging

_logger = logging.getLogger(__name__)


class TelemetryJsonLogger:
    """Записывает телеметрические события в JSON‑Lines файл.

    Параметры
    ----------
    log_dir: str
        Путь к директории, где будут храниться лог‑файлы.
    filename: str
        Базовое имя лог‑файла (без расширения).
    max_file_size_mb: float, optional
        Максимальный размер файла в мегабайтах до ротации. По умолчанию 5 МБ.
    """

    def __init__(self, log_dir: str, filename: str, max_file_size_mb: float = 5.0) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.base_filename = filename if filename.endswith('.jsonl') else f"{filename}.jsonl"
        self.max_bytes = int(max_file_size_mb * 1024 * 1024)
        self.current_path = self.log_dir / self.base_filename
        _logger.debug(
            "Инициализирован TelemetryJsonLogger: dir=%s, file=%s, max_bytes=%d",
            self.log_dir,
            self.base_filename,
            self.max_bytes,
        )

    def _rotate_if_needed(self) -> None:
        """Ротирует текущий лог‑файл, если его размер превышает лимит.
        Новый файл получает суффикс с меткой времени.
        """
        if self.current_path.exists() and self.current_path.stat().st_size >= self.max_bytes:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            rotated_name = f"{self.base_filename.rstrip('.jsonl')}_{timestamp}.jsonl"
            rotated_path = self.log_dir / rotated_name
            try:
                self.current_path.rename(rotated_path)
                _logger.info("Файл лога ротирован: %s -> %s", self.current_path.name, rotated_name)
            except OSError as exc:
                _logger.error("Не удалось ротировать лог‑файл: %s", exc)

    def _write_record(self, record: dict) -> None:
        """Записывает одну строку JSON в текущий файл.
        Файл открывается в режиме добавления.
        """
        line = json.dumps(record, ensure_ascii=False)
        with self.current_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        _logger.debug("Записана запись в %s: %s", self.current_path.name, line)

    def log(self, record: dict) -> bool:
        """Записать одну запись.

        Возвращает ``True`` при успешной записи.
        """
        try:
            self._rotate_if_needed()
            self._write_record(record)
            return True
        except Exception as exc:  # pragma: no cover
            _logger.exception("Ошибка записи лога: %s", exc)
            return False

    def log_batch(self, records: List[dict]) -> int:
        """Записать список записей.

        Возвращает количество успешно записанных элементов.
        """
        count = 0
        for rec in records:
            if self.log(rec):
                count += 1
        return count

    def get_last_measurement(self) -> Optional[dict]:
        """Вернуть последнюю запись из текущего лог‑файла, если файл существует.
        """
        if not self.current_path.exists():
            return None
        try:
            with self.current_path.open("rb") as f:
                f.seek(0, os.SEEK_END)
                offset = -1
                while -offset < f.tell():
                    f.seek(offset, os.SEEK_END)
                    if f.read(1) == b"\n" and offset != -1:
                        break
                    offset -= 1
                f.seek(offset + 1, os.SEEK_END)
                last_line = f.readline().decode("utf-8").strip()
                return json.loads(last_line) if last_line else None
        except Exception as exc:  # pragma: no cover
            _logger.exception("Не удалось прочитать последнюю запись: %s", exc)
            return None

    def get_log_file_size(self) -> int:
        """Вернуть размер текущего лог‑файла в байтах.
        """
        return self.current_path.stat().st_size if self.current_path.exists() else 0
