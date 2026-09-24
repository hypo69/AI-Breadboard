# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Adapter for interacting with Google Gemini CLI
# =============================================================================
# Description:
#   Высокоуровневый адаптер диалога для взаимодействия с Google Gemini CLI.
#   Наследует BaseChatProvider и реализует методы генерации, диалога,
#   потокового вывода и структурированного ответа.
#
# File: chat.py
# Package: src.ai.providers.gemini_cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional, Set, Union

from logger.logger import logger
from src.ai.providers.base import BaseChatProvider
from .client import GeminiCliProvider, GeminiCliResponse


class GeminiCliChatBase(BaseChatProvider):
    """Высокоуровневый адаптер взаимодействия с Google Gemini CLI.

    Реализует стандартный интерфейс чата (ask, chat, chat_stream, stream_chat)
    для выполнения запросов через CLI-утилиту gemini с поддержкой потокового вывода,
    истории сообщений и выбора моделей.

    Attributes:
        model_id (str): Идентификатор модели (например, gemini-3.1-flash-lite).
        system_prompt (str): Системные инструкции для агента.
        history (List[Dict[str, str]]): Локальная история диалога.
        executable_path (str): Путь к исполняемому файлу gemini CLI.
        provider (GeminiCliProvider): Низкоуровневый клиент Gemini CLI.
    """

    _DEFAULT_MODEL: str = "gemini-3.1-flash-lite"

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Получение списка актуальных моделей для Gemini CLI через менеджер моделей.

        :param force_refresh: Флаг принудительного обновления кэша.
        :returns: Список доступных идентификаторов моделей.
        """
        from src.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="gemini_cli", force_refresh=force_refresh)

    @classmethod
    def is_available(cls) -> bool:
        """Проверка доступности Gemini CLI в операционной системе.

        :returns: ``True``, если Gemini CLI найден.
        """
        return GeminiCliProvider().is_available()

    @classmethod
    def get_capabilities(cls) -> Set[str]:
        """Возвращает множество поддерживаемых возможностей.

        :returns: Множество строк с названиями возможностей.
        """
        return {"chat", "stream", "agent", "json"}

    @classmethod
    def normalize_model_id(cls, model_id: str) -> str:
        """Нормализация идентификатора модели для Gemini CLI.

        :param model_id: Входной идентификатор модели.
        :returns: Очищенный нормализованный идентификатор модели.

        Examples:
            >>> GeminiCliChatBase.normalize_model_id('gemini_cli:gemini-3.1-flash-lite')
            'gemini-3.1-flash-lite'
            >>> GeminiCliChatBase.normalize_model_id('')
            'gemini-3.1-flash-lite'
        """
        actual = (model_id or "").strip()
        if actual.startswith("gemini_cli:"):
            actual = actual[len("gemini_cli:") :]
        elif actual.startswith("gemini-cli-"):
            actual = actual[len("gemini-cli-") :]

        if not actual:
            return cls._DEFAULT_MODEL

        if actual.startswith("models/"):
            actual = actual[len("models/") :]

        return actual

    def __init__(
        self,
        model_id: str = "",
        system_prompt: str = "",
        executable_path: str = "",
        working_directory: Optional[Union[str, Path]] = None,
        timeout: int = 300,
    ) -> None:
        """Инициализация клиента Gemini CLI.

        :param model_id: Идентификатор модели.
        :param system_prompt: Системный промпт для диалога.
        :param executable_path: Опциональный путь к исполняемому файлу gemini.
        :param working_directory: Рабочий каталог по умолчанию.
        :param timeout: Таймаут выполнения в секундах.
        """
        self._model_id: str = self.normalize_model_id(model_id)
        self.system_prompt: str = system_prompt or ""
        self._history: List[Dict[str, str]] = []

        # Инициализация низкоуровневого провайдера
        found_exe = executable_path or GeminiCliProvider.find_executable() or "gemini"
        self.executable_path: str = found_exe
        self.provider: GeminiCliProvider = GeminiCliProvider(
            executable=found_exe,
            working_directory=working_directory,
            timeout=timeout,
            default_model=self._model_id,
        )

        logger.info(
            f"[GeminiCliChat] Инициализирован CLI-клиент: модель={self._model_id}, exe={self.executable_path}"
        )

    @property
    def model_id(self) -> str:
        """Получение текущего идентификатора модели."""
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Установка и нормализация идентификатора модели."""
        self._model_id = self.normalize_model_id(val)
        self.provider.default_model = self._model_id

    @property
    def system_instruction(self) -> str:
        """Получение текущей системной инструкции."""
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Установка системной инструкции."""
        self.system_prompt = val or ""

    @property
    def history(self) -> List[Dict[str, str]]:
        """Получение копии локальной истории диалога."""
        return list(self._history)

    @history.setter
    def history(self, val: List[Dict[str, str]]) -> None:
        """Установка локальной истории диалога."""
        self._history = list(val) if val else []

    def clear_history(self) -> None:
        """Очистка локальной истории диалога."""
        self._history = []

    async def close(self) -> None:
        """Освобождение ресурсов."""
        pass

    def _build_full_prompt(
        self,
        q: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = "",
    ) -> str:
        """Формирование полного контекста запроса с историей и системной инструкцией.

        :param q: Текст запроса.
        :param history: История диалога.
        :param system_instruction: Системная инструкция.
        :returns: Объединенная строка контекста.
        """
        sys_inst = system_instruction or self.system_prompt or ""
        parts: List[str] = []

        if sys_inst:
            parts.append(f"System Instructions:\n{sys_inst}\n")

        hist = history if history is not None else self._history
        if hist:
            parts.append("Previous Conversation:")
            for item in hist:
                role = item.get("role", "user")
                content = item.get("content", "")
                if content:
                    parts.append(f"{role.capitalize()}: {content}")
            parts.append("")

        parts.append(f"User Query:\n{q}")
        return "\n".join(parts)

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        **kwargs: Any,
    ) -> Optional[str]:
        """Выполнение одиночного запроса через Gemini CLI.

        :param q: Текстовый запрос пользователя.
        :param attempts: Количество попыток при сбоях.
        :param temperature: Температура генерации (0.0 по умолчанию).
        :param max_tokens: Максимальное количество токенов (0 по умолчанию).
        :param system_instruction: Переопределение системной инструкции.
        :param kwargs: Дополнительные параметры вызова.
        :returns: Ответ модели или пустая строка при ошибке.
        """
        if not q or not q.strip():
            return ""

        full_prompt = self._build_full_prompt(q, history=[], system_instruction=system_instruction)
        return await self._execute_cli(full_prompt)

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> str:
        """Выполнение запроса с учетом контекста истории через Gemini CLI.

        :param q: Текстовый запрос пользователя.
        :param history: История предыдущих сообщений.
        :param system_instruction: Переопределение системной инструкции.
        :param save_history: Сохранять ли запрос и ответ в локальной истории.
        :param temperature: Температура генерации.
        :param max_tokens: Максимальное количество токенов.
        :param kwargs: Дополнительные параметры.
        :returns: Ответ модели или пустая строка при сбое.
        """
        if not q or not q.strip():
            return ""

        effective_history = history if history is not None else self._history
        full_prompt = self._build_full_prompt(
            q, history=effective_history, system_instruction=system_instruction
        )
        response_text = await self._execute_cli(full_prompt)

        if save_history and response_text:
            self._history.append({"role": "user", "content": q})
            self._history.append({"role": "model", "content": response_text})

        return response_text

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Потоковая генерация ответа от Gemini CLI.

        :param q: Текстовый запрос пользователя.
        :param history: История предыдущих сообщений.
        :param system_instruction: Системная инструкция.
        :param save_history: Сохранять ли запрос и ответ в локальной истории.
        :param temperature: Температура генерации.
        :param max_tokens: Максимальное количество токенов.
        :param kwargs: Дополнительные аргументы.
        :yields: Фрагменты сгенерированного текста.
        """
        if not q or not q.strip():
            return

        effective_history = history if history is not None else self._history
        full_prompt = self._build_full_prompt(
            q, history=effective_history, system_instruction=system_instruction
        )

        logger.info(
            f"[GeminiCliChat] chat_stream: запуск {self.executable_path} (модель: {self._model_id})"
        )

        full_response = ""
        try:
            async for chunk in self.provider.stream_async(
                prompt=full_prompt,
                model=self._model_id,
            ):
                full_response += chunk
                yield chunk
        except Exception as ex:
            logger.error(f"[GeminiCliChat] Ошибка потокового выполнения: {ex}")
            yield f"\n[Gemini CLI Error: {str(ex)}]"
        finally:
            if save_history and full_response:
                self._history.append({"role": "user", "content": q})
                self._history.append({"role": "model", "content": full_response.strip()})

    async def stream_chat(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Реализация метода интерфейса BaseChatProvider для потокового чата."""
        async for chunk in self.chat_stream(
            q=q,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def _execute_cli(self, prompt: str) -> str:
        """Асинхронное исполнение CLI процесса и сбор текстового ответа."""
        logger.info(f"[GeminiCliChat] Выполнение команды: model={self._model_id}")

        try:
            resp: GeminiCliResponse = await self.provider.generate_async(
                prompt=prompt,
                model=self._model_id,
            )

            if not resp.success:
                logger.warning(
                    f"[GeminiCliChat] Код возврата {resp.return_code}. Stderr: {resp.stderr[:200]}"
                )
                from src.ai.model_manager import add_unsupported_model
                from src.ai.orchestration.model_error_hub import record_model_error

                err_low = resp.stderr.lower()
                if "model not found" in err_low or "not supported" in err_low:
                    add_unsupported_model("gemini_cli", self._model_id, reason=resp.stderr[:120])

                record_model_error(
                    provider="gemini_cli",
                    model_name=self._model_id,
                    error=resp.stderr.strip() or "CLI execution failed",
                    status_code=resp.return_code if resp.return_code else None,
                    action_taken="failed",
                )

                if not resp.text.strip():
                    return f"[Gemini CLI Error]: {resp.stderr.strip()}"

            return resp.text

        except RuntimeError as ex:
            logger.error(f"[GeminiCliChat] Исполняемый файл '{self.executable_path}' не найден: {ex}")
            from src.ai.orchestration.model_error_hub import record_model_error
            record_model_error(
                provider="gemini_cli",
                model_name=self._model_id,
                error=str(ex),
                action_taken="failed",
            )
            return f"[Gemini CLI Error]: Executable '{self.executable_path}' not found in system PATH."
        except TimeoutError as ex:
            logger.error(f"[GeminiCliChat] Таймаут выполнения: {ex}")
            from src.ai.orchestration.model_error_hub import record_model_error
            record_model_error(
                provider="gemini_cli",
                model_name=self._model_id,
                error=str(ex),
                action_taken="failed",
            )
            return f"[Gemini CLI Error]: Request timed out."
        except Exception as ex:
            logger.error(f"[GeminiCliChat] Непредвиденная ошибка запуска CLI: {ex}")
            from src.ai.orchestration.model_error_hub import record_model_error
            record_model_error(
                provider="gemini_cli",
                model_name=self._model_id,
                error=str(ex),
                action_taken="failed",
            )
            return f"[Gemini CLI Error]: {str(ex)}"
