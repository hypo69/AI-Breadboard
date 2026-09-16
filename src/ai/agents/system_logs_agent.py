# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Logs & OS Diagnostics Agent
# =============================================================================
# Description:
#   Автономный SRE-агент для исследования критических ошибок и инцидентов
#   в журналах операционной системы Windows за указанный период времени.
#
# Examples:
#   >>> agent = SystemLogsAgent()
#   >>> result = await agent.run("Покажи все критические ошибки в ОС за последние 20 дней")
#
# File: system_logs_agent.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль автономного агента анализа системных логов и диагностики ОС."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from src.logger import logger
from src.ai.agents.prompts import SYSTEM_LOGS_AGENT_PROMPT
from src.ai.agents.tools import system_logs_analyzer


class SystemLogsAgent:
    """Автономный агент диагностики системных журналов Windows."""

    # Регулярные выражения и соответствия числительных
    _WORD_NUMBERS = {
        "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, "четыре": 4, "пять": 5,
        "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10,
        "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, "четырнадцать": 14,
        "пятнадцать": 15, "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10, "twenty": 20, "thirty": 30
    }

    def __init__(self, ai_model: Any = None) -> None:
        """Инициализация SystemLogsAgent.

        Args:
            ai_model: Опциональный инстанс модели LLM.
        """
        self.ai_model = ai_model

    def parse_time_window_days(self, user_query: str) -> int:
        """Извлечение запрашиваемого периода в днях из текстового запроса.

        Args:
            user_query: Текст запроса пользователя.

        Returns:
            int: Количество дней для анализа (по умолчанию 20).
        """
        q_lower = user_query.lower()

        # Поиск числовых шаблонов (например, "20 дней", "за 14 дн", "3 недели")
        digit_match = re.search(r'(\d+)\s*(?:дн|day|дней|дня|день)', q_lower)
        if digit_match:
            try:
                days = int(digit_match.group(1))
                return max(1, min(days, 30))
            except ValueError:
                pass

        # Поиск недель
        week_match = re.search(r'(\d+)\s*(?:недел|week)', q_lower)
        if week_match:
            try:
                weeks = int(week_match.group(1))
                return max(1, min(weeks * 7, 30))
            except ValueError:
                pass

        # Поиск текстовых числительных (например, "двадцать дней")
        for word, val in self._WORD_NUMBERS.items():
            if f"{word} дн" in q_lower or f"{word} day" in q_lower or f"{word} недел" in q_lower:
                if "недел" in q_lower or "week" in q_lower:
                    val *= 7
                return max(1, min(val, 30))

        # По умолчанию при общем запросе
        return 20

    async def run(self, user_query: str, active_llm: Any = None) -> str:
        """Выполнение цикла анализа системных логов.

        Args:
            user_query: Запрос пользователя.
            active_llm: Активная языковая модель (опционально).

        Returns:
            str: Сформированный Markdown-отчет.
        """
        days = self.parse_time_window_days(user_query)
        logger.info(f"[SystemLogsAgent] Запуск аудита логов ОС за период: {days} дн.")

        # Вызов системного инструмента
        tool_res_str = await system_logs_analyzer.func(days=days, level="Critical,Error", limit=150)
        
        try:
            log_data = json.loads(tool_res_str)
        except Exception:
            log_data = {"raw": tool_res_str}

        prompt = (
            f"{SYSTEM_LOGS_AGENT_PROMPT}\n\n"
            f"── ВХОДНЫЕ ДАННЫЕ ДИАГНОСТИКИ СИСТЕМЫ ──\n"
            f"Запрос пользователя: {user_query}\n"
            f"Параметры сбора: за последние {days} дней ({days * 24} часов).\n"
            f"Собранные данные и кластеры инцидентов (JSON):\n"
            f"```json\n{json.dumps(log_data, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Сформируйте исчерпывающий, технически грамотный отчет для администратора на русском языке."
        )

        model = active_llm or self.ai_model
        if not model:
            from src.api.router_chat import get_chat_model
            model = get_chat_model("gemini-2.5-flash", system_instruction=SYSTEM_LOGS_AGENT_PROMPT)

        if hasattr(model, 'ask'):
            return await model.ask(prompt)
        elif hasattr(model, 'chat'):
            return await model.chat(prompt)
        elif hasattr(model, 'generate_response'):
            return await model.generate_response(prompt)
        return str(log_data)
