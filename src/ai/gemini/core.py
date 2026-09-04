# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Core Google Generative AI Client
# =============================================================================
# Description:
#   Core client class for Google Generative AI API interaction.
#   Manages API key pool, model rotation, and base configuration.
#
# File: core.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai

from src.ai.orchestration.model_manager import (
    add_unsupported_model as _mgr_add_unsupported_model,
    get_available_models as _mgr_get_available_models,
    load_unsupported_models as _mgr_load_unsupported_models,
)
from src.config import server_cfg
from src.logger.logger import logger
from src.secrets.api_key_state import (
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    update_last_run,
)
from src.utils.jjson import j_loads

# Loading local configuration of Gemini module
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


def load_unsupported_models() -> set[str]:
    """Loading списка неподдерживаемых и устаревших моделей Gemini.

    Returns:
        set[str]: Множество наименований неподдерживаемых моделей.

    Examples:
        >>> unsupported = load_unsupported_models()
        >>> isinstance(unsupported, set)
        True
    """
    return _mgr_load_unsupported_models('gemini')


def add_unsupported_model(model_name: str, reason: str = '') -> bool:
    """Добавление модели в list неподдерживаемых с сохранением в конфигурации.

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
class GoogleGenerativeAICore:
    """Base class взаимодействия с моделями Google Generative AI (Gemini).

    Attributes:
        api_key (str): Активный API-ключ для запросов.
        model_name (str): Наименование используемой модели Gemini.
        generation_config (dict): Parameters генерации по умолчанию.
        system_instruction (str): Базовая системная инструкция.
        api_key_names (list[str]): List разрешенных имен ключей.
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
    _client: Any = field(default=False, init=False)
    _api_key_index: int = field(default=0, init=False)
    _all_keys_exhausted: bool = field(default=False, init=False)
    _unavailable_attempts: int = field(default=0, init=False)
    save_history_chat: bool = field(default_factory=lambda: _DEFAULT_SAVE_HISTORY)
    sleep_on_exhausted: bool = True

    _last_exception: str = field(default='', init=False)
    _key_errors: dict[str, str] = field(default_factory=dict, init=False)

    MODELS: list[str] = field(default_factory=lambda: GoogleGenerativeAICore.get_available_models(), init=False)

    @classmethod
    def get_available_models(cls, api_key: str = '', force_refresh: bool = False) -> list[str]:
        """Получение динамического списка доступных моделей через Google GenAI SDK.

        Args:
            api_key (str): Опциональный API-ключ. Значение по умолчанию: ''.
            force_refresh (bool): Принудительное update кэша. Значение по умолчанию: False.

        Returns:
            list[str]: List доступных моделей.

        Examples:
            >>> models = GoogleGenerativeAICore.get_available_models()
            >>> isinstance(models, list)
            True
        """
        return _mgr_get_available_models(provider='gemini', api_key=api_key, force_refresh=force_refresh)

    def __post_init__(self) -> None:
        """Initialization объекта подключения к Google Generative AI."""
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
        logger.info(f'GoogleGenerativeAI: Initialization с ключом: {self._key_names_active[0]}')
        self._client = genai.Client(api_key=self.api_key)

    def _get_exhausted_error_msg(self) -> str:
        """Formation сообщения об исчерпании всех доступных API-ключей.

        Returns:
            str: Текст сообщения об ошибке с диагностической информацией.
        """
        msg: str = 'Error: Все API ключи исчерпаны.'
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
            ex (Exception | str): Объект исключения или string ошибки.
        """
        ex_str: str = str(ex)
        self._last_exception = ex_str
        key_name: str = self._key_names_active[0] if self._key_names_active else '?'
        self._key_errors[key_name] = ex_str

    def _invalidate_api_key(self, key: str) -> None:
        """Exception невалидного ключа из активного пула.

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
        return True

    def _switch_model(self) -> bool:
        """Переключение на следующую поддерживаемую модель в пуле.

        Returns:
            bool: True при успешном переключении, False если list пуст.
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
        return True
