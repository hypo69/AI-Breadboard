# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеграция с моделями Google Generative AI (Gemini)
# =============================================================================
# Описание:
#   Организация взаимодействия с API Google Generative AI через официальный SDK.
#   Выполнение генерации текста, стриминга, эмбеддингов и поддержка вызова функций.
#
# Примеры:
#   >>> from core.ai.gemini import GoogleGenerativeAI
#   >>> ai = GoogleGenerativeAI()
#   >>> response = await ai.ask("Привет!")
#
# File: generative_ai.py
# Project: ai-assistant
# Package: src.ai.gemini
# Module: Core
# Class: GoogleGenerativeAI
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модуль интеграции с моделями Google Generative AI (Gemini).

Реализует управление пулом API-ключей, ротацию моделей при сбоях,
потоковую генерацию ответов, поддержку инструментов и обработку медиа-файлов.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from io import IOBase
from pathlib import Path
from typing import Any, AsyncGenerator

from google import genai
from google.genai import types
import numpy as np
import requests

from core.ai.model_manager import (
    add_unsupported_model as _mgr_add_unsupported_model,
    get_available_models as _mgr_get_available_models,
    load_unsupported_models as _mgr_load_unsupported_models,
)
from core.config import server_cfg
from core.logger.logger import logger
from core.secrets.api_key_state import (
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    update_last_run,
)
from core.utils.image import get_image_bytes
from core.utils.jjson import j_loads


# Загрузка локальной конфигурации модуля Gemini
_config_path: Path = Path(__file__).parent / 'config.json'
_gemini_config: dict = j_loads(_config_path) if _config_path.exists() else {}
_DEFAULT_MODEL: str = (
    _gemini_config.get('model', 'gemini-flash-latest')
    if isinstance(_gemini_config, dict)
    else 'gemini-flash-latest'
)
_DEFAULT_SAVE_HISTORY: bool = (
    _gemini_config.get('save_history_chat', False)
    if isinstance(_gemini_config, dict)
    else False
)


def normalize_text(text: str) -> str:
    """Нормализация текстового ответа модели.

    Замена экранированных последовательностей перевода строки на реальные символы.

    Args:
        text (str): Входной текст для нормализации.

    Returns:
        str: Нормализованный текст.

    Examples:
        >>> normalize_text("Line 1\\\\nLine 2")
        'Line 1\\nLine 2'
    """
    if not text:
        return ''
    return re.sub(r'\\n', '\n', text)


def remove_html_blocks(text: str) -> str:
    """Удаление блоков разметки HTML из ответа модели.

    Args:
        text (str): Входной текст с возможными HTML-блоками.

    Returns:
        str: Текст с вырезанными блоками ```html ... ```.

    Examples:
        >>> remove_html_blocks("```html<div>Test</div>```Hello")
        'Hello'
    """
    if not text:
        return ''
    return re.sub(r'```html.*?```', '', text, flags=re.DOTALL)


def load_unsupported_models() -> set[str]:
    """Загрузка списка неподдерживаемых и устаревших моделей Gemini.

    Returns:
        set[str]: Множество наименований неподдерживаемых моделей.

    Examples:
        >>> unsupported = load_unsupported_models()
        >>> isinstance(unsupported, set)
        True
    """
    return _mgr_load_unsupported_models('gemini')


def add_unsupported_model(model_name: str, reason: str = '') -> bool:
    """Добавление модели в список неподдерживаемых с сохранением в конфигурации.

    Args:
        model_name (str): Наименование блокируемой модели.
        reason (str): Причина исключения модели. Значение по умолчанию: ''.

    Returns:
        bool: True при успешном сохранении, False при ошибке.

    Examples:
        >>> add_unsupported_model('gemini-legacy', reason='404 Not Found')
        True
    """
    if not model_name:
        return False
    return _mgr_add_unsupported_model('gemini', model_name, reason)


@dataclass
class GoogleGenerativeAI:
    """Класс взаимодействия с моделями Google Generative AI (Gemini).

    Attributes:
        api_key (str): Активный API-ключ для запросов.
        model_name (str): Наименование используемой модели Gemini.
        generation_config (dict): Параметры генерации по умолчанию.
        system_instruction (str): Базовая системная инструкция.
        api_key_names (list[str]): Список разрешенных имен ключей.
        save_history_chat (bool): Флаг сохранения контекста истории чата.
        sleep_on_exhausted (bool): Флаг ожидания разблокировки при исчерпании квоты.
    """

    api_key: str = ''
    model_name: str = field(default_factory=lambda: _DEFAULT_MODEL)
    generation_config: dict = field(default_factory=lambda: {'response_mime_type': 'text/plain'})
    system_instruction: str = ''
    api_key_names: list[str] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list, init=False)
    api_key_owners: list[str] = field(default_factory=list, init=False)
    _key_names_active: list[str] = field(default_factory=list, init=False)
    chat_history: list[dict] = field(default_factory=list, init=False)
    _client: Any = field(default=False, init=False)
    _chat: Any = field(default=False, init=False)
    _api_key_index: int = field(default=0, init=False)
    _all_keys_exhausted: bool = field(default=False, init=False)
    _unavailable_attempts: int = field(default=0, init=False)
    save_history_chat: bool = field(default_factory=lambda: _DEFAULT_SAVE_HISTORY)
    sleep_on_exhausted: bool = True

    _last_exception: str = field(default='', init=False)
    _key_errors: dict[str, str] = field(default_factory=dict, init=False)

    MODELS: list[str] = field(default_factory=lambda: GoogleGenerativeAI.get_available_models(), init=False)

    @classmethod
    def get_available_models(cls, api_key: str = '', force_refresh: bool = False) -> list[str]:
        """Получение динамического списка доступных моделей через Google GenAI SDK.

        Args:
            api_key (str): Опциональный API-ключ. Значение по умолчанию: ''.
            force_refresh (bool): Принудительное обновление кэша. Значение по умолчанию: False.

        Returns:
            list[str]: Список доступных моделей.

        Examples:
            >>> models = GoogleGenerativeAI.get_available_models()
            >>> isinstance(models, list)
            True
        """
        return _mgr_get_available_models(provider='gemini', api_key=api_key, force_refresh=force_refresh)

    def __post_init__(self) -> None:
        """Инициализация объекта подключения к Google Generative AI."""
        self._last_exception = ''
        self._key_errors = {}
        self._unavailable_attempts = 0

        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names)
        self.api_key_owners = list(self._key_names_active)

        if not self.api_keys:
            logger.warning('GoogleGenerativeAI: Нет доступных API-ключей Gemini.')
            self._all_keys_exhausted = True
            return

        get_status(self.api_key_names)
        self.api_key = self.api_keys[0]
        logger.info(f'GoogleGenerativeAI: Инициализация с ключом: {self._key_names_active[0]}')
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()

    def _get_exhausted_error_msg(self) -> str:
        """Формирование сообщения об исчерпании всех доступных API-ключей.

        Returns:
            str: Текст сообщения об ошибке с диагностической информацией.
        """
        msg: str = 'Ошибка: Все API ключи исчерпаны.'
        mode: str = getattr(server_cfg, 'mode', 'DEV').upper()
        if mode == 'DEV':
            if self._key_errors:
                msg += '\n[DEV Детали по ключам]:'
                for kname, kerr in self._key_errors.items():
                    msg += f'\n- {kname}: {kerr}'
            elif self._last_exception:
                msg += f'\n[DEV Детали]: {self._last_exception}'
        return msg

    def _record_error(self, ex: Exception | str) -> None:
        """Фиксация последней возникшей ошибки в диагностическом хранилище.

        Args:
            ex (Exception | str): Объект исключения или строка ошибки.
        """
        ex_str: str = str(ex)
        self._last_exception = ex_str
        key_name: str = self._key_names_active[0] if self._key_names_active else '?'
        self._key_errors[key_name] = ex_str

    def _invalidate_api_key(self, key: str) -> None:
        """Исключение невалидного ключа из активного пула.

        Args:
            key (str): Значение недействительного API-ключа.
        """
        idx: int = self.api_keys.index(key) if key in self.api_keys else -1
        key_name: str = self._key_names_active[idx] if 0 <= idx < len(self._key_names_active) else '?'
        logger.warning(f'GoogleGenerativeAI: Недействительный ключ удален: {key_name}')
        self.api_keys = [k for k in self.api_keys if k != key]
        if idx >= 0:
            self._key_names_active = [n for i, n in enumerate(self._key_names_active) if i != idx]
            self.api_key_owners = [o for i, o in enumerate(self.api_key_owners) if i != idx]

    def _mark_key_exhausted(self, key: str) -> None:
        """Маркировка ключа как исчерпавшего суточную квоту.

        Args:
            key (str): Значение исчерпанного API-ключа.
        """
        idx: int = self.api_keys.index(key) if key in self.api_keys else -1
        key_name: str = self._key_names_active[idx] if 0 <= idx < len(self._key_names_active) else key
        mark_exhausted(key_name)
        logger.warning(f'GoogleGenerativeAI: Суточная квота ключа {key_name} исчерпана. Блокировка 24ч.')
        self.api_keys = [k for k in self.api_keys if k != key]
        if idx >= 0:
            self._key_names_active = [n for i, n in enumerate(self._key_names_active) if i != idx]

    def _switch_api_key(self) -> bool:
        """Переключение на следующий доступный API-ключ из пула.

        Returns:
            bool: True при успешном переключении, False при отсутствии доступных ключей.
        """
        if not self.api_keys:
            wait_sec: float = next_available_in()
            if wait_sec > 0 and self.sleep_on_exhausted:
                h: int = int(wait_sec) // 3600
                m: int = (int(wait_sec) % 3600) // 60
                logger.warning(f'GoogleGenerativeAI: Все ключи исчерпаны. Ожидание {h}ч {m}м...')
                time.sleep(wait_sec + 5)
                self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names)
                if not self.api_keys:
                    self._all_keys_exhausted = True
                    return False
                self._all_keys_exhausted = False
            else:
                self._all_keys_exhausted = True
                logger.warning('GoogleGenerativeAI: Все API-ключи исчерпаны.')
                return False

        self._api_key_index = 0
        self.api_key = self.api_keys[0]
        key_name: str = self._key_names_active[0] if self._key_names_active else '?'
        logger.info(f'GoogleGenerativeAI: Переключение на ключ: {key_name}')
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        return True

    def _switch_model(self) -> bool:
        """Переключение на следующую поддерживаемую модель в пуле.

        Returns:
            bool: True при успешном переключении, False если список пуст.
        """
        active_pool: list[str] = self.get_available_models()
        if not active_pool:
            active_pool = [
                'gemini-flash-latest',
                'gemini-flash-lite-latest',
                'gemini-3.6-flash',
                'gemini-3.7-flash',
                'gemini-pro-latest',
            ]
        try:
            idx: int = active_pool.index(self.model_name)
            next_idx: int = (idx + 1) % len(active_pool)
        except ValueError:
            next_idx = 0

        next_model: str = active_pool[next_idx]
        if next_model == self.model_name and len(active_pool) <= 1:
            return False

        logger.info(f'GoogleGenerativeAI: Смена модели {self.model_name} -> {next_model}')
        self.model_name = next_model

        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names)
        if not self.api_keys:
            return False

        self._all_keys_exhausted = False
        self.api_key = self.api_keys[0]
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        return True

    def _switch_model_down(self) -> bool:
        """Переключение на менее ресурсоемкую модель (даунгрейд).

        Returns:
            bool: True при успешном переключении, False если достигнут нижний предел.
        """
        active_pool: list[str] = self.get_available_models()
        if not active_pool:
            active_pool = [
                'gemini-flash-latest',
                'gemini-flash-lite-latest',
                'gemini-3.6-flash',
                'gemini-3.7-flash',
                'gemini-pro-latest',
            ]
        try:
            idx: int = active_pool.index(self.model_name)
        except ValueError:
            idx = 0

        next_idx: int = idx + 1
        if next_idx >= len(active_pool):
            return False

        next_model: str = active_pool[next_idx]
        logger.info(f'GoogleGenerativeAI: Понижение модели {self.model_name} -> {next_model}')
        self.model_name = next_model

        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names)
        if not self.api_keys:
            return False

        self._all_keys_exhausted = False
        self.api_key = self.api_keys[0]
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        return True

    def _build_content_config(
        self,
        instruction: str = '',
        tools: list = (),
        generation_config: dict = {},
    ) -> types.GenerateContentConfig:
        """Построение объекта конфигурации генерации контента для Gemini SDK.

        Args:
            instruction (str): Системная инструкция. Значение по умолчанию: ''.
            tools (list): Набор инструментов (функций) модели.
            generation_config (dict): Дополнительные параметры генерации.

        Returns:
            types.GenerateContentConfig: Сконфигурированный объект генерации.
        """
        cfg_kwargs: dict[str, Any] = {}
        gen_cfg: dict[str, Any] = {}

        if isinstance(self.generation_config, dict):
            gen_cfg.update(self.generation_config)
        if generation_config:
            gen_cfg.update(generation_config)

        response_type: str = gen_cfg.pop('response_type', 'both')
        inst: str = instruction or self.system_instruction or ''

        if inst:
            if response_type == 'chat':
                format_rule: str = (
                    '\n\nCRITICAL: You must format your response for reading on a screen.\n'
                    'Provide a detailed styled markdown response in Russian for the user to read.'
                )
            elif response_type == 'voice':
                format_rule = (
                    '\n\nCRITICAL: You must format your response for a voice narrator (TTS).\n'
                    'Provide a very concise, clear speech-friendly Russian text, using only Russian letters, '
                    'no markdown, no special symbols, write all numbers as words.'
                )
            else:
                format_rule = (
                    '\n\nCRITICAL: You must format your response exactly as follows, with no extra text outside these blocks:\n'
                    '[CHAT]\n<detailed styled markdown response in Russian for the user to read>\n'
                    '[VOICE]\n<very concise, clear speech-friendly Russian text for the narrator, using only Russian letters, '
                    'no markdown, no special symbols, write all numbers as words>'
                )
            inst += format_rule
            cfg_kwargs['system_instruction'] = inst

        all_tools: list = list(tools) if tools else []
        has_search: bool = any(
            hasattr(t, 'google_search') or (isinstance(t, dict) and 'google_search' in t)
            for t in all_tools
        )
        if not has_search:
            all_tools.append(types.Tool(google_search=types.GoogleSearch()))
        cfg_kwargs['tools'] = all_tools

        if gen_cfg:
            for k in ['temperature', 'top_p', 'top_k', 'response_mime_type']:
                val = gen_cfg.get(k)
                if val:
                    cfg_kwargs[k] = val

        return types.GenerateContentConfig(**cfg_kwargs)

    def _start_chat(self, history: list = ()) -> Any:
        """Инициализация сессии чата с поддержкой сохранения истории.

        Args:
            history (list): Начальная история сообщений.

        Returns:
            Any: Экземпляр чата Google GenAI или False если история отключена.
        """
        if not self.save_history_chat:
            return False

        config = self._build_content_config()
        if history:
            return self._client.chats.create(model=self.model_name, config=config, history=list(history))
        return self._client.chats.create(model=self.model_name, config=config)

    def clear_history(self) -> None:
        """Очистка локальной истории диалога в оперативной памяти."""
        self.chat_history = []

    def _restore_chat_from_history(self) -> None:
        """Восстановление состояния сессии чата из накопленной истории сообщений."""
        history_contents: list[types.Content] = []
        for entry in self.chat_history:
            role: str = entry.get('role', 'user')
            if role == 'assistant':
                role = 'model'
            parts: list = entry.get('parts', [])
            parts_objects: list[types.Part] = []
            for p in parts:
                if isinstance(p, str):
                    parts_objects.append(types.Part.from_text(text=p))
                elif isinstance(p, dict) and 'text' in p:
                    parts_objects.append(types.Part.from_text(text=p['text']))
            history_contents.append(types.Content(role=role, parts=parts_objects))

        self._chat = self._start_chat(history=history_contents)

    def _prepare_contents(self, q: str, history: list[dict] = ()) -> list[types.Content]:
        """Подготовка списка объектов Content для передачи в stateless API-запросы.

        Args:
            q (str): Текущий текстовый запрос пользователя.
            history (list[dict]): История предыдущих сообщений.

        Returns:
            list[types.Content]: Список объектов Content.
        """
        contents: list[types.Content] = []
        if history:
            for entry in history:
                role: str = entry.get('role', '')
                if not role:
                    continue
                if role == 'assistant':
                    role = 'model'

                parts = entry.get('parts')
                if not parts:
                    content_str: str = entry.get('content', '')
                    if content_str:
                        parts = [types.Part.from_text(text=content_str)]
                else:
                    new_parts: list = []
                    for p in parts:
                        if isinstance(p, str):
                            new_parts.append(types.Part.from_text(text=p))
                        elif isinstance(p, dict) and 'text' in p:
                            new_parts.append(types.Part.from_text(text=p['text']))
                        else:
                            new_parts.append(p)
                    parts = new_parts

                if parts:
                    contents.append(types.Content(role=role, parts=parts))

        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=q)]))
        return contents

    async def _handle_api_error(
        self,
        ex: Exception,
        active_model: str,
        attempt: int,
        max_attempts: int,
    ) -> bool:
        """Централизованная обработка исключений API и координация повторов.

        Args:
            ex (Exception): Возникшее исключение.
            active_model (str): Наименование используемой модели.
            attempt (int): Порядковый номер текущей попытки.
            max_attempts (int): Максимальное количество попыток.

        Returns:
            bool: True если необходимо повторить запрос, False если ошибка неустранима.
        """
        self._record_error(ex)
        ex_str: str = str(ex)
        logger.error(f'GoogleGenerativeAI: Ошибка API (попытка {attempt + 1}/{max_attempts}): {ex_str}')

        # 1. Ошибка авторизации (невалидный API-ключ)
        if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
            self._invalidate_api_key(self.api_key)
            return self._switch_api_key()

        # 2. Модель не найдена / устарела (404)
        if any(
            k in ex_str
            for k in [
                '404',
                'NOT_FOUND',
                'is no longer available',
                'not found for API version',
                'not supported for generateContent',
            ]
        ):
            add_unsupported_model(active_model, reason=ex_str)
            return self._switch_model()

        # 3. Сервис временно недоступен (503 UNAVAILABLE)
        if '503' in ex_str or 'UNAVAILABLE' in ex_str:
            self._unavailable_attempts += 1
            if self._unavailable_attempts < 6:
                wait: int = 2 ** min(self._unavailable_attempts, 5)
                logger.info(f'GoogleGenerativeAI: 503 UNAVAILABLE. Ожидание {wait}с...')
                await asyncio.sleep(wait)
                return True
            else:
                switched: bool = self._switch_model_down()
                self._unavailable_attempts = 0
                return switched

        # 4. Превышение квоты запросов (429 RESOURCE_EXHAUSTED)
        if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
            is_daily: bool = any(
                k in ex_str.lower()
                for k in ['perday', 'per_day', 'exceeded your current quota', "quota_limit_value': '0'"]
            )
            if is_daily:
                self._mark_key_exhausted(self.api_key)
                if self._switch_api_key():
                    return True
                return self._switch_model()

            m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
            base_wait: int = int(float(m.group(1))) + 2 if m else 5
            wait_time: int = min(base_wait * (2 ** min(attempt, 3)), 60)
            logger.info(f'GoogleGenerativeAI: 429 Rate Limit. Ожидание {wait_time}с перед повтором...')
            await asyncio.sleep(wait_time)
            return True

        # 5. Сетевые ошибки запросов
        if isinstance(ex, requests.exceptions.RequestException):
            if attempt < 5:
                logger.warning('GoogleGenerativeAI: Сетевая ошибка. Ожидание 10с...')
                await asyncio.sleep(10)
                return True
            return False

        # 6. Общие непредвиденные ошибки
        if attempt < max_attempts - 1:
            await asyncio.sleep(2 ** min(attempt, 4))
            return True

        return False

    async def embed(self, text: str, model_name: str = 'text-embedding-004') -> np.ndarray | bool:
        """Генерация векторного представления (эмбеддинга) для переданного текста.

        Args:
            text (str): Исходный текст для векторизации.
            model_name (str): Наименование embedding-модели.

        Returns:
            np.ndarray | bool: Одномерный массив эмбеддинга или False при сбое.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> vec = await ai.embed("Тестовый текст")
        """
        if not text:
            return False
        try:
            response = self._client.models.embed_content(
                model=model_name,
                contents=text,
            )
            if response and response.embeddings:
                return np.array(response.embeddings[0].values)
            return False
        except Exception as ex:
            logger.error('GoogleGenerativeAI: Ошибка генерации эмбеддинга', ex)
            return False

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        generation_config: dict = {},
    ) -> str:
        """Отправка одиночного текстового запроса модели.

        Args:
            q (str): Текст запроса.
            attempts (int): Максимальное количество попыток. Значение по умолчанию: 15.
            generation_config (dict): Дополнительные параметры генерации.

        Returns:
            str: Ответ модели или сообщение об ошибке.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> ans = await ai.ask("Столица Франции?")
        """
        if not q:
            return ''

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                return self._get_exhausted_error_msg()
            self._all_keys_exhausted = False

        for attempt in range(attempts):
            try:
                config = self._build_content_config(generation_config=generation_config)
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=q,
                    config=config,
                )
                if response and response.text:
                    response_text: str = normalize_text(response.text)
                    response_text = remove_html_blocks(response_text)
                    update_last_run(self._key_names_active[0] if self._key_names_active else '')
                    self._unavailable_attempts = 0
                    return response_text

                logger.debug(f'GoogleGenerativeAI: Пустой ответ модели на попытке {attempt + 1}')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return f'Ошибка модели: {self._last_exception or str(ex)}'

        return self._get_exhausted_error_msg()

    async def chat(
        self,
        q: str,
        history: list[dict] = (),
        flag: str = 'save_chat',
        system_instruction: str = '',
        attempts: int = 15,
        model_name: str = '',
        **kwargs,
    ) -> str:
        """Обработка сообщения в контексте чат-диалога.

        Args:
            q (str): Сообщение пользователя.
            history (list[dict]): Внешняя история сообщений для восстановления контекста.
            flag (str): Флаг управления историей ('save_chat', 'clear', 'start_new').
            system_instruction (str): Переопределенная системная инструкция.
            attempts (int): Максимальное число повторных попыток.
            model_name (str): Явное переопределение модели для запроса.
            **kwargs: Дополнительные неиспользуемые параметры.

        Returns:
            str: Ответ модели или диагностическое сообщение об ошибке.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> ans = await ai.chat("Привет!", flag="start_new")
        """
        if not q:
            return ''

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                return self._get_exhausted_error_msg()
            self._all_keys_exhausted = False

        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name

        for attempt in range(attempts):
            try:
                # 1. Режим без сохранения истории (Stateless)
                if not self.save_history_chat:
                    config = self._build_content_config(instruction)
                    response = self._client.models.generate_content(
                        model=active_model,
                        contents=q,
                        config=config,
                    )
                    if response and response.text:
                        response_text: str = normalize_text(response.text)
                        response_text = remove_html_blocks(response_text)
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return response_text

                    await asyncio.sleep(2 ** min(attempt, 4))
                    continue

                # 2. Режим чата с сохранением истории
                if history:
                    self.chat_history = list(history)
                    self._restore_chat_from_history()
                elif flag in ['clear', 'start_new']:
                    self.chat_history = []
                    self._chat = self._start_chat()

                response = self._chat.send_message(q)
                if response and response.text:
                    response_text = normalize_text(response.text)
                    response_text = remove_html_blocks(response_text)
                    self.chat_history.append({'role': 'user', 'parts': [q]})
                    self.chat_history.append({'role': 'model', 'parts': [response_text]})
                    self._unavailable_attempts = 0
                    return response_text

                logger.error('GoogleGenerativeAI: Пустой ответ модели в чате')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, attempt, attempts)
                if not should_retry:
                    return f'Ошибка чата: {self._last_exception or str(ex)}'

        return self._get_exhausted_error_msg()

    async def chat_stream(
        self,
        q: str,
        history: list[dict] = (),
        flag: str = 'save_chat',
        system_instruction: str = '',
        attempts: int = 15,
        model_name: str = '',
        generation_config: dict = {},
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Потоковая генерация ответа модели в виде асинхронного генератора.

        Args:
            q (str): Вопрос пользователя.
            history (list[dict]): История сообщений.
            flag (str): Флаг управления историей.
            system_instruction (str): Системная инструкция.
            attempts (int): Максимальное число попыток.
            model_name (str): Переопределение модели.
            generation_config (dict): Настройки генерации.

        Yields:
            str: Очередной сгенерированный фрагмент текста (чанк).
        """
        if not q:
            return

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                yield self._get_exhausted_error_msg()
                return
            self._all_keys_exhausted = False

        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name

        for attempt in range(attempts):
            try:
                if not self.save_history_chat:
                    config = self._build_content_config(instruction, generation_config=generation_config)
                    contents = self._prepare_contents(q, history)

                    def _collect_stateless(_client=self._client, _m=active_model, _c=contents, _cfg=config):
                        res: list[str] = []
                        for chunk in _client.models.generate_content_stream(model=_m, contents=_c, config=_cfg):
                            if chunk.text:
                                res.append(chunk.text)
                        return res

                    chunks = await asyncio.to_thread(_collect_stateless)
                    if chunks:
                        for chunk_text in chunks:
                            yield chunk_text
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return

                    await asyncio.sleep(2 ** min(attempt, 4))
                    continue

                if history:
                    self.chat_history = list(history)
                    self._restore_chat_from_history()
                elif flag in ['clear', 'start_new']:
                    self.chat_history = []
                    self._chat = self._start_chat()

                _chat_ref = self._chat

                def _collect_chat(_chat=_chat_ref, _query=q):
                    res: list[str] = []
                    for chunk in _chat.send_message_stream(_query):
                        if chunk.text:
                            res.append(chunk.text)
                    return res

                chunks = await asyncio.to_thread(_collect_chat)
                full_text: str = ''.join(chunks)
                if full_text:
                    for chunk_text in chunks:
                        yield chunk_text
                    normalized: str = remove_html_blocks(normalize_text(full_text))
                    self.chat_history.append({'role': 'user', 'parts': [q]})
                    self.chat_history.append({'role': 'model', 'parts': [normalized]})
                    self._unavailable_attempts = 0
                    return

                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, attempt, attempts)
                if not should_retry:
                    yield f'Ошибка стриминга: {self._last_exception or str(ex)}'
                    return

    async def ask_with_tools(
        self,
        q: str,
        tools: list,
        tool_dispatcher: Any,
        system_instruction: str = '',
        model_name: str = '',
    ) -> str:
        """Выполнение запроса с поддержкой вызова внешних функций (Agentic loop).

        Args:
            q (str): Текстовый запрос пользователя.
            tools (list): Список определений инструментов types.Tool.
            tool_dispatcher (Any): Диспетчер вызова функций (name, args) -> str.
            system_instruction (str): Системная инструкция.
            model_name (str): Наименование используемой модели.

        Returns:
            str: Финальный текстовый ответ модели.

        Examples:
            >>> ans = await ai.ask_with_tools("Погода в Париже", tools, dispatcher)
        """
        if not q:
            return ''

        contents: list[types.Content] = [types.Content(role='user', parts=[types.Part.from_text(text=q)])]
        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name
        config = self._build_content_config(instruction, tools)

        for _ in range(10):
            response = self._client.models.generate_content(
                model=active_model,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0] if response and response.candidates else False
            if not candidate:
                break

            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            if not tool_calls:
                return '\n'.join(text_parts)

            contents.append(candidate.content)
            tool_results: list[types.Part] = []
            for part in tool_calls:
                fc = part.function_call
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))

        return ''

    async def ask_with_tools_stream(
        self,
        q: str,
        tools: list,
        tool_dispatcher: Any,
        system_instruction: str = '',
        model_name: str = '',
        history: list[dict] = (),
    ) -> AsyncGenerator[dict[str, str], None]:
        """Выполнение запроса с вызовом функций и потоковой отдачей финального ответа.

        Args:
            q (str): Запрос пользователя.
            tools (list): Список инструментов.
            tool_dispatcher (Any): Диспетчер вызова функций.
            system_instruction (str): Системная инструкция.
            model_name (str): Наименование модели.
            history (list[dict]): История сообщений.

        Yields:
            dict[str, str]: События вида {"text": "chunk"} или {"status": "message"}.
        """
        if not q:
            return

        contents: list[types.Content] = self._prepare_contents(q, history)
        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name
        config = self._build_content_config(instruction, tools)

        for _ in range(10):
            try:
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=active_model,
                    contents=contents,
                    config=config,
                )
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, 0, 3)
                if should_retry:
                    active_model = self.model_name
                    continue
                yield {'status': f'Ошибка generate_content: {str(ex)}'}
                return

            candidate = response.candidates[0] if response and response.candidates else False
            if not candidate:
                break

            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            if not tool_calls:
                try:
                    response_stream = self._client.models.generate_content_stream(
                        model=active_model,
                        contents=contents,
                        config=config,
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            yield {'text': chunk.text}
                except Exception as ex:
                    logger.error(f'GoogleGenerativeAI: Ошибка стриминга ask_with_tools_stream: {ex}')
                    if text_parts:
                        yield {'text': ''.join(text_parts)}
                return

            contents.append(candidate.content)
            tool_results: list[types.Part] = []
            for part in tool_calls:
                fc = part.function_call
                args_json: str = json.dumps(dict(fc.args), ensure_ascii=False)
                yield {'status': f'Вызов функции {fc.name}({args_json})'}
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))

    async def describe_image(
        self,
        image: Path | bytes,
        mime_type: str = 'image/jpeg',
        prompt: str = '',
        attempts: int = 10,
    ) -> str | bool:
        """Формирование текстового описания переданного изображения.

        Args:
            image (Path | bytes): Путь к изображению или его бинарное содержимое.
            mime_type (str): MIME-тип изображения. Значение по умолчанию: 'image/jpeg'.
            prompt (str): Дополнительный текстовый промпт. Значение по умолчанию: ''.
            attempts (int): Максимальное число попыток. Значение по умолчанию: 10.

        Returns:
            str | bool: Текстовое описание или False при сбое.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> desc = await ai.describe_image(Path("poster.jpg"))
        """
        img_bytes: bytes = get_image_bytes(image) if isinstance(image, Path) else image
        if not img_bytes:
            return False

        for attempt in range(attempts):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt or 'Опиши это изображение.'),
                    ],
                )
                if response and response.text:
                    return response.text

                logger.debug(f'GoogleGenerativeAI: Пустой ответ describe_image (попытка {attempt + 1})')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False

        return False

    async def upload_file(
        self,
        file: str | Path | IOBase,
        file_name: str = '',
        attempts: int = 10,
    ) -> bool:
        """Загрузка медиа-файла в хранилище Google GenAI File API.

        Args:
            file (str | Path | IOBase): Путь к файлу или файловый дескриптор.
            file_name (str): Отображаемое имя файла. Значение по умолчанию: ''.
            attempts (int): Максимальное количество попыток. Значение по умолчанию: 10.

        Returns:
            bool: True при успешной загрузке, False при ошибке.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> success = await ai.upload_file(Path("data.pdf"), file_name="data.pdf")
        """
        for attempt in range(attempts):
            try:
                upload_kwargs = (
                    {'config': types.UploadFileConfig(display_name=file_name)}
                    if file_name
                    else {}
                )
                response = self._client.files.upload(path=file, **upload_kwargs)
                if response:
                    logger.debug(f'GoogleGenerativeAI: Файл {file_name} успешно загружен')
                    return True
                return False
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False

        return False
