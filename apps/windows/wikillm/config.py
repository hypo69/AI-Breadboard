# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Config
# =============================================================================
# Description:
#   Загрузка и валидация конфигурационных параметров для подсистемы WikiLLM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.config import WikiLLMConfig
#
#     service = WikiLLMConfig()
#
# File: config.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Загрузка и валидация конфигурационных параметров для подсистемы WikiLLM."""

import json
import os
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field


class WikiLLMConfig(BaseModel):
    """Модель конфигурации WikiLLM."""

    database_path: str = Field(
        default="data/windows_wikillm/knowledge.db",
        description="Путь к SQLite базе знаний WikiLLM",
    )
    min_confidence_threshold: float = Field(
        default=0.70,
        description="Минимальный порог уверенности для фиксации фактов",
    )
    max_queue_size: int = Field(
        default=1000,
        description="Максимальный размер асинхронной очереди неизвестных артефактов",
    )
    async_workers: int = Field(
        default=2,
        description="Количество параллельных воркеров разрешения артефактов",
    )
    gemini_model_id: str = Field(
        default="gemini-3.1-flash-lite",
        description="Идентификатор модели Gemini для разрешения неизвестных сущностей",
    )
    enable_code_indexer: bool = Field(
        default=True,
        description="Флаг включения индексатора исходного кода кодовой базы",
    )
    enable_semantic_search: bool = Field(
        default=True,
        description="Флаг включения семантического поиска",
    )
    cache_exact_hits: bool = Field(
        default=True,
        description="Кэшировать ли точные совпадения в оперативной памяти",
    )


def load_config(config_path: Path | str | None = None) -> WikiLLMConfig:
    """Загружает конфигурацию WikiLLM из JSON файла или возвращает значения по умолчанию.

    Args:
        config_path: Путь к файлу конфигурации (опционально).

    Returns:
        Экземпляр WikiLLMConfig.
    """
    default_cfg_path = Path(__file__).parent / "config.json"
    target_path = Path(config_path) if config_path else default_cfg_path

    if target_path.exists() and target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                return WikiLLMConfig(**data)
        except Exception:
            pass

    return WikiLLMConfig()
