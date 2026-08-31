# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Adapter for interacting with Google Gemini CLI
# =============================================================================
# Description:
#   Адаптер для взаимодействия с локальным агентом Google Gemini CLI
#
# File: gemini_cli_chat.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import shutil
import asyncio
from typing import List, Dict, AsyncGenerator

from core.logger.logger import logger

class GeminiCliChatBase:
    """Адаптер взаимодействия с Google Gemini CLI через неинтерактивный режим подпроцесса.

    Реализует стандартный интерфейс чата (ask, chat, chat_stream) для выполнения
    запросов через CLI-утилиту gemini с поддержкой потокового вывода и выборочных моделей.

    Attributes:
        model_id (str): Идентификатор модели (например, gemini-3.1-flash-lite).
        system_prompt (str): Системные инструкции для агента.
        history (List[Dict[str, str]]): Локальная история диалога.
        executable_path (str): Путь к исполняемому файлу gemini CLI.
    """

    _DEFAULT_MODEL: str = "gemini-3.1-flash-lite"

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Получение списка актуальных моделей для Gemini CLI через менеджер моделей.

        Args:
            force_refresh (bool): Флаг принудительного обновления кэша.

        Returns:
            List[str]: List доступных идентификаторов моделей.
        """
        from core.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="gemini_cli", force_refresh=force_refresh)

    @classmethod
    def normalize_model_id(cls, model_id: str) -> str:
        """Нормализация идентификатора модели для Gemini CLI.

        Args:
            model_id (str): Входной идентификатор модели.

        Returns:
            str: Очищенный нормализованный идентификатор модели.

        Examples:
            >>> GeminiCliChatBase.normalize_model_id('gemini_cli:gemini-3.1-flash-lite')
            'gemini-3.1-flash-lite'
            >>> GeminiCliChatBase.normalize_model_id('')
            'gemini-3.1-flash-lite'
        """
        actual = (model_id or "").strip()
        if actual.startswith("gemini_cli:"):
            actual = actual[len("gemini_cli:"):]
        elif actual.startswith("gemini-cli-"):
            actual = actual[len("gemini-cli-"):]

        if not actual:
            return cls._DEFAULT_MODEL

        if actual.startswith("models/"):
            actual = actual[len("models/"):]

        return actual

    @classmethod
    def _find_cli_executable(cls) -> str:
        """Поиск исполняемого файла Gemini CLI в системе."""
        if sys.platform == "win32":
            candidates = ["gemini.cmd", "gemini.bat", "gemini.exe", "gemini"]
        else:
            candidates = ["gemini"]

        for cand in candidates:
            resolved = shutil.which(cand)
            if resolved:
                return resolved

        # Check стандартного пути npm global на Windows
        if sys.platform == "win32":
            npm_appdata = os.path.expandvars(r"%APPDATA%\npm\gemini.cmd")
            if os.path.exists(npm_appdata):
                return npm_appdata

        return "gemini"

    def __init__(self, model_id: str = "", system_prompt: str = "", executable_path: str = "") -> None:
        """Initialization клиента Gemini CLI.

        Args:
            model_id (str): Идентификатор модели.
            system_prompt (str): Системный промпт для диалога.
            executable_path (str): Опциональный путь к исполняемому файлу gemini.
        """
        self._model_id: str = self.normalize_model_id(model_id)
        self.system_prompt: str = system_prompt or ""
        self.history: List[Dict[str, str]] = []
        self.executable_path: str = executable_path or self._find_cli_executable()
        logger.info(f"[GeminiCliChat] Инициализирован CLI-клиент: модель={self._model_id}, exe={self.executable_path}")

    @property
    def model_id(self) -> str:
        """Получение текущего идентификатора модели."""
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Установка и нормализация идентификатора модели."""
        self._model_id = self.normalize_model_id(val)

    @property
    def system_instruction(self) -> str:
        """Получение текущей системной инструкции."""
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Установка системной инструкции."""
        self.system_prompt = val or ""

    def clear_history(self) -> None:
        """Очистка локальной истории диалога."""
        self.history = []

    def _build_full_prompt(self, q: str, history: List[Dict[str, str]] = [], system_instruction: str = "") -> str:
        """Formation полного контекста запроса с историей и системной инструкцией."""
        sys_inst = system_instruction or self.system_prompt or ""
        parts: List[str] = []

        if sys_inst:
            parts.append(f"System Instructions:\n{sys_inst}\n")

        hist = history or self.history
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

    def _clean_cli_output(self, raw_output: str) -> str:
        """Очистка вывода CLI от служебных сообщений."""
        cleaned = raw_output.strip()
        lines = cleaned.splitlines()
        filtered_lines: List[str] = []
        for line in lines:
            # Exception служебных баннеров или предупреждений CLI
            if line.startswith("YOLO mode is enabled") or line.startswith("Loaded extension:"):
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines).strip()

    async def ask(
        self,
        q: str,
        system_instruction: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> str:
        """Выполнение одиночного запроса через Gemini CLI.

        Args:
            q (str): Текстовый запрос пользователя.
            system_instruction (Optional[str]): Переопределение системной инструкции.
            temperature (Optional[float]): Температура генерации (0.0 по умолчанию).
            max_tokens (Optional[int]): Максимальное количество токенов (0 по умолчанию).

        Returns:
            str: Ответ модели или пустая string при ошибке.
        """
        if not q or not q.strip():
            return ""

        full_prompt = self._build_full_prompt(q, history=[], system_instruction=system_instruction)
        return await self._execute_cli(full_prompt)

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, str]]] = [],
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> str:
        """Выполнение запроса с учетом контекста истории через Gemini CLI.

        Args:
            q (str): Текстовый запрос пользователя.
            history (Optional[List[Dict[str, str]]]): История предыдущих сообщений.
            system_instruction (Optional[str]): Переопределение системной инструкции.
            save_history (bool): Сохранять ли запрос и ответ в локальной истории.
            temperature (Optional[float]): Температура генерации (0.0 по умолчанию).
            max_tokens (Optional[int]): Максимальное количество токенов (0 по умолчанию).

        Returns:
            str: Ответ модели или пустая string при сбое.
        """
        if not q or not q.strip():
            return ""

        effective_history = history or self.history
        full_prompt = self._build_full_prompt(q, history=effective_history, system_instruction=system_instruction)
        response_text = await self._execute_cli(full_prompt)

        if save_history and response_text:
            self.history.append({"role": "user", "content": q})
            self.history.append({"role": "model", "content": response_text})

        return response_text

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict[str, str]]] = [],
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Потоковая генерация ответа от Gemini CLI.

        Args:
            q (str): Текстовый запрос пользователя.
            history (Optional[List[Dict[str, str]]]): История предыдущих сообщений.
            system_instruction (Optional[str]): Системная инструкция.
            save_history (bool): Сохранять ли запрос и ответ в локальной истории.
            temperature (Optional[float]): Температура генерации (0.0 по умолчанию).
            max_tokens (Optional[int]): Максимальное количество токенов (0 по умолчанию).

        Yields:
            str: Фрагменты сгенерированного текста.
        """
        if not q or not q.strip():
            return

        effective_history = history or self.history
        full_prompt = self._build_full_prompt(q, history=effective_history, system_instruction=system_instruction)

        cmd = [
            self.executable_path,
            "-p", full_prompt,
            "-m", self._model_id,
            "--approval-mode", "yolo",
            "-o", "text"
        ]

        logger.info(f"[GeminiCliChat] chat_stream: запуск {self.executable_path} (модель: {self._model_id})")

        proc = False
        full_response = ""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace")
                if line.startswith("YOLO mode is enabled") or line.startswith("Loaded extension:"):
                    continue
                full_response += line
                yield line

            await proc.wait()
            if proc.returncode != 0:
                stderr_bytes = await proc.stderr.read()
                err_msg = stderr_bytes.decode("utf-8", errors="replace").strip()
                logger.warning(f"[GeminiCliChat] Процесс завершился с кодом {proc.returncode}: {err_msg}")
        except Exception as ex:
            logger.error(f"[GeminiCliChat] Error потокового выполнения: {ex}")
            yield f"\n[Gemini CLI Error: {str(ex)}]"
        finally:
            if save_history and full_response:
                self.history.append({"role": "user", "content": q})
                self.history.append({"role": "model", "content": full_response.strip()})

    async def _execute_cli(self, prompt: str) -> str:
        """Асинхронное исполнение CLI процесса и сбор текстового ответа."""
        cmd = [
            self.executable_path,
            "-p", prompt,
            "-m", self._model_id,
            "--approval-mode", "yolo",
            "-o", "text"
        ]

        logger.info(f"[GeminiCliChat] Выполнение команды: model={self._model_id}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await proc.communicate()
            stdout_text = stdout_bytes.decode("utf-8", errors="replace")
            stderr_text = stderr_bytes.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                logger.warning(
                    f"[GeminiCliChat] Код возврата {proc.returncode}. Stderr: {stderr_text[:200]}"
                )
                from core.ai.model_manager import add_unsupported_model
                if "model not found" in stderr_text.lower() or "not supported" in stderr_text.lower():
                    add_unsupported_model("gemini_cli", self._model_id, reason=stderr_text[:120])
                if not stdout_text.strip():
                    return f"[Gemini CLI Error]: {stderr_text.strip()}"

            return self._clean_cli_output(stdout_text)

        except FileNotFoundError:
            logger.error(f"[GeminiCliChat] Исполняемый файл '{self.executable_path}' не найден в системе")
            return "[Gemini CLI Error]: Executable 'gemini' not found in system PATH."
        except Exception as ex:
            logger.error(f"[GeminiCliChat] Непредвиденная Error запуска CLI: {ex}")
            return f"[Gemini CLI Error]: {str(ex)}"
