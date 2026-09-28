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
            return ''
        text = raw_text
        text = re.sub('<[^>]+>', ' ', text)
        text = re.sub('\\[\\s*\\d+\\s*\\]', '', text)
        text = re.sub('\\[\\s*[a-zA-Zа-яА-ЯёЁ\\s\\-\\.\\,\\:\\;]+\\s*\\]', '', text)
        text = re.sub('\\{\\{[^}]*\\}\\}', '', text)
        text = re.sub('={2,6}\\s*(.*?)\\s*={2,6}', '\\n### \\1\\n', text)
        text = re.sub('http[s]?://\\S+', '', text)
        lines = [line.strip() for line in text.split('\n')]
        cleaned_lines = []
        for line in lines:
            if line:
                cleaned_line = re.sub('[ \\t]+', ' ', line)
                cleaned_lines.append(cleaned_line)
        return '\n\n'.join(cleaned_lines)

    @staticmethod
    def extract_lead_and_sections(full_text: str) -> Tuple[str, List[str]]:
        """Извлекает вводный раздел (lead) и список разделов статьи.

        Args:
            full_text (str): Полный очищенный текст.

        Returns:
            Tuple[str, List[str]]: Вводная выжимка и список заголовков разделов.
        """
        if not full_text:
            return ('', [])
        sections: List[str] = []
        section_matches = re.findall('###\\s+(.+)', full_text)
        if section_matches:
            sections = [s.strip() for s in section_matches]
        parts = full_text.split('###')
        lead = parts[0].strip() if parts else full_text[:1000]
        return (lead, sections)

    @staticmethod
    def compute_stats(text: str) -> Tuple[int, int]:
        """Подсчитывает количество слов и символов в тексте.

        Args:
            text (str): Входной текст.

        Returns:
            Tuple[int, int]: (word_count, char_count).
        """
        if not text:
            return (0, 0)
        words = text.split()
        return (len(words), len(text))