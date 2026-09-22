# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Sensors JSON Telemetry Logger
# =============================================================================
# Description:
#   Логгер телеметрии в JSON формате с инкрементальными записями и ротацией файлов.
#
# File: json_logger.py
# Project: ai-sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Логгер телеметрии в JSON формате с инкрементальными записями и ротацией файлов."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger


class TelemetryJsonLogger:
    """Логгер телеметрии в JSON формате с ротацией файлов."""

    def __init__(
        self,
        log_dir: str,
        filename: str = "ai_sensors_polls.json",
        max_file_size_mb: float = 100.0,
    ) -> None:
        """Инициализирует логгер телеметрии.

        Args:
            log_dir: Директория для хранения логов.
            filename: Имя файла лога.
            max_file_size_mb: Максимальный размер файла в МБ перед ротацией.
        """
        self.log_dir = Path(log_dir)
        self.filename = filename
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)

        self._lock = threading.Lock()
        self._current_file_size = 0
        self._last_measurement: Optional[Dict[str, Any]] = None

        # Создаем директорию если она не существует
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> Path:
        """Возвращает путь к текущему лог-файлу.

        Returns:
            Path: Путь к лог-файлу.
        """
        return self.log_dir / self.filename

    def _rotate_file(self) -> None:
        """Ротирует текущий лог-файл."""
        current_path = self._get_log_file_path()
        if not current_path.exists():
            return

        # Генерируем имя ротированного файла с timestamps
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rotated_name = f"{self.filename.rsplit('.', 1)[0]}_{timestamp}.json"
        rotated_path = self.log_dir / rotated_name

        try:
            current_path.rename(rotated_path)
            logger.info(f"Лог-файл ротирован: {rotated_path}")
            self._current_file_size = 0
        except Exception as e:
            logger.error(f"Ошибка ротации файла: {e}")

    def _check_and_rotate(self) -> None:
        """Проверяет размер файла и ротирует если нужно."""
        current_path = self._get_log_file_path()
        if current_path.exists():
            try:
                self._current_file_size = current_path.stat().st_size
            except OSError:
                self._current_file_size = 0

        if self._current_file_size >= self.max_file_size_bytes:
            self._rotate_file()

    def _write_json_line(self, data: Dict[str, Any]) -> None:
        """Записывает JSON строку в файл.

        Args:
            data: Данные для записи.
        """
        with self._lock:
            self._check_and_rotate()

            current_path = self._get_log_file_path()

            try:
                line = json.dumps(data, ensure_ascii=False, indent=None, default=str) + "\n"

                with open(current_path, "a", encoding="utf-8") as f:
                    f.write(line)

                self._current_file_size += len(line.encode("utf-8"))
                self._last_measurement = data

            except Exception as e:
                logger.error(f"Ошибка записи в лог-файл: {e}")

    def log(self, data: Dict[str, Any]) -> bool:
        """Записывает данные телеметрии в JSON файл.

        Args:
            data: Данные телеметрии для записи.

        Returns:
            bool: True если запись успешна.
        """
        try:
            self._write_json_line(data)
            return True
        except Exception as e:
            logger.error(f"Ошибка логгирования: {e}")
            return False

    def log_batch(self, measurements: List[Dict[str, Any]]) -> int:
        """Записывает пачку измерений в JSON файл.

        Args:
            measurements: Список данных телеметрии.

        Returns:
            int: Количество успешно записанных записей.
        """
        written = 0
        for measurement in measurements:
            if self.log(measurement):
                written += 1
        return written

    def get_last_measurement(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнюю записанную телеметрию.

        Returns:
            Optional[Dict[str, Any]]: Последняя телеметрия или None.
        """
        return self._last_measurement

    def get_log_file_size(self) -> int:
        """Возвращает текущий размер лог-файла в байтах.

        Returns:
            int: Размер файла в байтах.
        """
        current_path = self._get_log_file_path()
        if current_path.exists():
            try:
                return current_path.stat().st_size
            except OSError:
                return 0
        return 0

    def get_log_file_path(self) -> Path:
        """Возвращает путь к текущему лог-файлу.

        Returns:
            Path: Путь к лог-файлу.
        """
        return self._get_log_file_path()
