# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Config Module
# =============================================================================
# Description:
#   Модуль реализации компонента `GoogleGenerativeAIConfigMixin` системы AI-Breadboard.
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.config import GoogleGenerativeAIConfigMixin
#
#     service = GoogleGenerativeAIConfigMixin()
#
# File: config.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:46:40
# =============================================================================


import json
import re
from typing import Any, Optional
from google.genai import types
from logger import logger


def normalize_text(text: str) -> str:
    """Нормализация текста ответа модели.

    Заменяет экранированные последовательности переноса строки на реальные символы новой строки.

    Args:
        text (str): Входной текст для нормализации.

    Returns:
        str: Нормализованный текст с фактическими переносами строк.

    Examples:
        >>> normalize_text("Строка 1\\nСтрока 2")
        'Строка 1\nСтрока 2'
    """
    if not text:
        return ''
    return re.sub(r'\\n', '\n', text)


def remove_html_blocks(text: str) -> str:
    """Удаление блоков разметки HTML из ответа модели.

    Args:
        text (str): Входной текст, потенциально содержащий блоки HTML.

    Returns:
        str: Текст с удалёнными блоками ```html ... ```.

    Examples:
        >>> remove_html_blocks("```html<div>Тест</div>```Привет")
        'Привет'
    """
    if not text:
        return ''
    return re.sub(r'```html.*?```', '', text, flags=re.DOTALL)


class GoogleGenerativeAIConfigMixin:
    """Миксин для построения конфигурации запросов Google Generative AI.

    Предоставляет методы для генерации объекта GenerateContentConfig,
    нормализации текста и логирования параметров исходящих запросов и входящих ответов.
    """

    def _build_content_config(
        self,
        instruction: str = '',
        tools: list = (),
        generation_config: dict = {},
    ) -> types.GenerateContentConfig:
        """Построение объекта конфигурации генерации контента для Gemini SDK.

        Объединяет базовые параметры генерации экземпляра с переданными переопределениями,
        настраивает форматирование системной инструкции (чат/голос), подключает инструменты
        (Google Search или пользовательские функции) и конфигурирует AFC (Automatic Function Calling).

        Args:
            instruction (str): Системная инструкция (системный промпт). Значение по умолчанию: ''.
            tools (list): Набор инструментов модели (функции или types.Tool). Значение по умолчанию: ().
            generation_config (dict): Дополнительные параметры генерации (temperature, top_p, tools,
                automatic_function_calling, response_type). Значение по умолчанию: {}.

        Returns:
            types.GenerateContentConfig: Сконфигурированный объект генерации контента.

        Examples:
            >>> cfg = self._build_content_config(
            ...     instruction="Ты ассистент",
            ...     generation_config={"temperature": 0.5, "automatic_function_calling": {"disable": False}}
            ... )
        """
        cfg_kwargs: dict[str, Any] = {}
        gen_cfg: dict[str, Any] = {}
        if isinstance(self.generation_config, dict):
            gen_cfg.update(self.generation_config)
        if generation_config:
            gen_cfg.update(generation_config)
        response_type: str = gen_cfg.pop('response_type', 'chat')
        inst: str = instruction or self.system_instruction or ''
        if inst:
            if response_type == 'chat':
                format_rule: str = '\n\nCRITICAL: You must format your response for reading on a screen.\nProvide a detailed styled markdown response for the user to read.'
            elif response_type == 'voice':
                format_rule = '\n\nCRITICAL: You must format your response for a voice narrator (TTS).\nProvide a very concise, clear speech-friendly text, using simple language, no markdown, no special symbols, write all numbers as words.'
            else:
                format_rule = '\n\nCRITICAL: You must format your response exactly as follows, with no extra text outside these blocks:\n[CHAT]\n<detailed styled markdown response for the user to read>\n[VOICE]\n<very concise, clear speech-friendly text for narrator, using simple language, no markdown, no special symbols, write all numbers as words>'
            inst += format_rule
            cfg_kwargs['system_instruction'] = inst
        use_google_search: bool = gen_cfg.pop('use_google_search', getattr(self, 'use_google_search', False))
        extra_tools = gen_cfg.pop('tools', None)
        all_tools: list = list(tools) if tools else []
        if extra_tools:
            if isinstance(extra_tools, (list, tuple)):
                all_tools.extend(extra_tools)
            else:
                all_tools.append(extra_tools)

        if use_google_search:
            has_search: bool = any((hasattr(t, 'google_search') or (isinstance(t, dict) and 'google_search' in t) for t in all_tools))
            if not has_search:
                all_tools.append(types.Tool(google_search=types.GoogleSearch()))
        if all_tools:
            cfg_kwargs['tools'] = all_tools

        afc_cfg = gen_cfg.pop('automatic_function_calling', None)
        if afc_cfg is not None:
            if isinstance(afc_cfg, dict):
                cfg_kwargs['automatic_function_calling'] = types.AutomaticFunctionCallingConfig(**afc_cfg)
            else:
                cfg_kwargs['automatic_function_calling'] = afc_cfg
        elif all_tools:
            cfg_kwargs['automatic_function_calling'] = types.AutomaticFunctionCallingConfig(disable=True)
        if gen_cfg:
            for k in ['temperature', 'top_p', 'top_k', 'response_mime_type']:
                val = gen_cfg.get(k)
                if val:
                    cfg_kwargs[k] = val
        return types.GenerateContentConfig(**cfg_kwargs)

    def _normalize_text(self, text: str) -> str:
        """Нормализация текста ответа модели.

        Args:
            text (str): Входной текст для нормализации.

        Returns:
            str: Нормализованный текст с фактическими переносами строк.

        Examples:
            >>> self._normalize_text("A\\nB")
            'A\nB'
        """
        return normalize_text(text)

    def _remove_html_blocks(self, text: str) -> str:
        """Удаление блоков HTML-разметки из ответа модели.

        Args:
            text (str): Входной текст с возможными блоками HTML.

        Returns:
            str: Текст без блоков ```html ... ```.

        Examples:
            >>> self._remove_html_blocks("```html<b>1</b>```2")
            '2'
        """
        return remove_html_blocks(text)

    def _log_request_details(
        self,
        method: str,
        model: str,
        q: str = '',
        history: Any = None,
        system_instruction: str = '',
        tools: Any = None,
        generation_config: dict = {},
    ) -> None:
        """Логирование структуры, полного промпта, системной инструкции и параметров исходящего запроса.

        Args:
            method (str): Имя вызывающего метода API (например, 'ask', 'chat_stream').
            model (str): Идентификатор модели Gemini.
            q (str): Пользовательский запрос/промпт.
            history (Any): Записи истории диалога при наличии. Значение по умолчанию: None.
            system_instruction (str): Применённая системная инструкция. Значение по умолчанию: ''.
            tools (Any): Список подключенных инструментов при наличии. Значение по умолчанию: None.
            generation_config (dict): Переопределения параметров генерации. Значение по умолчанию: {}.
        """
        try:
            inst: str = system_instruction or getattr(self, 'system_instruction', '') or ''
            tools_list: list = list(tools) if tools else []
            tools_summary: list[str] = []
            for t in tools_list:
                if hasattr(t, 'google_search') or (isinstance(t, dict) and 'google_search' in t):
                    tools_summary.append('google_search')
                elif hasattr(t, 'function_declarations'):
                    tools_summary.append('custom_functions')
                else:
                    tools_summary.append(type(t).__name__)

            history_info = ""
            if history:
                history_count = len(history)
                history_info = f"\nChat History ({history_count} items):\n{json.dumps(history, ensure_ascii=False, indent=2, default=str)}"

            log_msg = (
                f"Gemini Request [{method}] -> Model: \"{model}\"\n"
                f"System Instruction: {inst or '<none>'}\n"
                f"Prompt: {q}\n"
                f"Generation Config: {json.dumps(generation_config or {}, ensure_ascii=False)}\n"
                f"Tools: {tools_summary or 'none'}"
                f"{history_info}"
            )
            logger.info(log_msg)
        except Exception as log_ex:
            logger.debug(f'Gemini: Failed to log request payload details: {log_ex}')

    def _log_response_details(
        self,
        method: str,
        model: str,
        response_text: Any,
        attempt: int = 1,
        extra: Optional[dict] = None,
    ) -> None:
        """Логирование полученного ответа от модели Gemini.

        Args:
            method (str): Имя вызывающего метода API (например, 'ask', 'chat', 'chat_stream').
            model (str): Идентификатор модели Gemini.
            response_text (Any): Полученный текст ответа или структура данных.
            attempt (int): Номер попытки. Значение по умолчанию: 1.
            extra (Optional[dict]): Дополнительные параметры (метаданные, токены и т.д.). Значение по умолчанию: None.
        """
        try:
            extra_str = f" | Extra: {json.dumps(extra, ensure_ascii=False)}" if extra else ""
            formatted_resp = response_text if isinstance(response_text, str) else json.dumps(response_text, ensure_ascii=False, indent=2, default=str)
            logger.info(
                f"Gemini Response [{method}] <- Model: \"{model}\" (attempt {attempt}){extra_str}:\n"
                f"{formatted_resp}"
            )
        except Exception as log_ex:
            logger.debug(f"Gemini: Failed to log response details: {log_ex}")