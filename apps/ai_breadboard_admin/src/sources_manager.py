# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Admin Sources Manager Module
# =============================================================================
# Description:
#   Управление конфигурацией источников данных, чтение, валидация и запись
#   сырого JSON файлов каталогов источников поиска (plugins/movie_search_sources).
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src.sources_manager import SourcesManager
#   >>> manager = SourcesManager()
#   >>> sources = manager.get_sources_raw()
#
# File: sources_manager.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Module: sources_manager
# Class: SourcesManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from header import __root__
from logger import logger


class SourcesManager:
    """Менеджер управления сырыми файлами источников данных.

    Обеспечивает чтение, синтаксическую валидацию и запись файлов источников.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        """Инициализация менеджера источников.

        Args:
            root_dir (Optional[Path]): Корневой каталог проекта. Если не передан,
                используется системный `__root__`.
        """
        self.root_dir: Path = root_dir or __root__
        self.sources_file: Path = self.root_dir / "plugins" / "movie_search_sources" / "sources.json"

    def get_sources_raw(self) -> str:
        """Чтение сырого содержимого файла sources.json.

        Returns:
            str: Содержимое файла или '{}', если файл отсутствует или поврежден.
        """
        if self.sources_file.exists():
            try:
                return self.sources_file.read_text(encoding="utf-8")
            except Exception as ex:
                logger.error(f"Ошибка чтения sources.json из {self.sources_file}", ex)
        return "{}"

    def save_sources_raw(self, content: str) -> bool:
        """Валидация JSON и сохранение сырого содержимого в sources.json.

        Args:
            content (str): Строка в формате JSON.

        Returns:
            bool: True в случае успешной записи.

        Exceptions:
            ValueError: При некорректном синтаксисе JSON.
            IOError: При ошибке записи в файловую систему.
        """
        try:
            json.loads(content)
        except json.JSONDecodeError as ex:
            logger.warning(f"Невалидный JSON при сохранении источников: {ex}")
            raise ValueError(f"Неверный формат JSON: {ex}")

        try:
            self.sources_file.parent.mkdir(parents=True, exist_ok=True)
            self.sources_file.write_text(content, encoding="utf-8")
            logger.info(f"Файл источников успешно обновлен: {self.sources_file}")
            return True
        except Exception as ex:
            logger.error(f"Ошибка записи sources.json в {self.sources_file}", ex)
            raise IOError(f"Не удалось сохранить файл источников: {ex}")


__all__ = ["SourcesManager"]
