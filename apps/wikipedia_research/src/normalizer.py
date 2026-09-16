# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Text Normalizer
# =============================================================================
# Description:
#   Utility module to clean, sanitize, and normalize raw Wikipedia articles,
#   stripping wikitext tags, citations, navigation infoboxes, and references.
#
# File: normalizer.py
# Project: ai-breadboard
# Package: apps.wikipedia_research.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Text normalization and sanitization utilities for Wikipedia content."""

from __future__ import annotations

import re
from typing import List, Tuple


class TextNormalizer:
    """Нормализатор и очиститель текста статей Википедии."""

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Очищает текст от HTML-тегов, сносок, ссылок и избыточных пробелов.

        Args:
            raw_text (str): Исходный необработанный текст.

        Returns:
            str: Очищенный нормализованный текст.
        """
        if not raw_text:
            return ""

        text = raw_text

        # 1. Удаление HTML тегов
        text = re.sub(r"<[^>]+>", " ", text)

        # 2. Удаление сносок вида [1], [12], [источник не указан], [citation needed]
        text = re.sub(r"\[\s*\d+\s*\]", "", text)
        text = re.sub(r"\[\s*[a-zA-Zа-яА-ЯёЁ\s\-\.\,\:\;]+\s*\]", "", text)

        # 3. Удаление фигурных скобок шаблонов {{...}}
        text = re.sub(r"\{\{[^}]*\}\}", "", text)

        # 4. Удаление заголовков разметки wiki == Section ==
        text = re.sub(r"={2,6}\s*(.*?)\s*={2,6}", r"\n### \1\n", text)

        # 5. Удаление URL ссылок
        text = re.sub(r"http[s]?://\S+", "", text)

        # 6. Нормализация пробелов и переносов строк
        lines = [line.strip() for line in text.split("\n")]
        cleaned_lines = []
        for line in lines:
            if line:
                # Сжатие множественных пробелов внутри строки
                cleaned_line = re.sub(r"[ \t]+", " ", line)
                cleaned_lines.append(cleaned_line)

        return "\n\n".join(cleaned_lines)

    @staticmethod
    def extract_lead_and_sections(full_text: str) -> Tuple[str, List[str]]:
        """Извлекает вводный раздел (lead) и список разделов статьи.

        Args:
            full_text (str): Полный очищенный текст.

        Returns:
            Tuple[str, List[str]]: Вводная выжимка и список заголовков разделов.
        """
        if not full_text:
            return "", []

        sections: List[str] = []
        section_matches = re.findall(r"###\s+(.+)", full_text)
        if section_matches:
            sections = [s.strip() for s in section_matches]

        # Извлечение lead section (текст до первого подзаголовка)
        parts = full_text.split("###")
        lead = parts[0].strip() if parts else full_text[:1000]

        return lead, sections

    @staticmethod
    def compute_stats(text: str) -> Tuple[int, int]:
        """Подсчитывает количество слов и символов в тексте.

        Args:
            text (str): Входной текст.

        Returns:
            Tuple[int, int]: (word_count, char_count).
        """
        if not text:
            return 0, 0
        words = text.split()
        return len(words), len(text)
