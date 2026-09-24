# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Low-level client and process runner for Google Gemini CLI
# =============================================================================
# Description:
#   Низкоуровневый клиент и провайдер для запуска Gemini CLI из Python.
#   Поддерживает синхронный/асинхронный вызов, парсинг JSON, потоковую передачу
#   stdout и режим работы агента в рабочем каталоге проекта.
#
# File: client.py
# Package: src.ai.providers.gemini_cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, List, Optional, Union

from logger.logger import logger


@dataclass
class GeminiCliResponse:
    """Результат выполнения запроса к Gemini CLI.

    :ivar text: Очищенный текстовый ответ модели.
    :ivar return_code: Код завершения процесса (0 при успехе).
    :ivar stderr: Текст потока ошибок stderr.
    :ivar parsed_json: Распарсенный JSON-объект, если запрос выполнялся в режиме JSON.
    :ivar duration_seconds: Время выполнения процесса в секундах.
    """

    text: str
    return_code: int
    stderr: str
    parsed_json: Optional[Any] = None
    duration_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """Флаг успешного завершения процесса."""
        return self.return_code == 0


class GeminiCliProvider:
    """Провайдер для выполнения запросов к Gemini CLI из Python.

    Предоставляет 4 режима работы:
    1. ``generate()`` / ``generate_async()`` — обычный текстовый запрос.
    2. ``generate_json()`` — получение валидированного JSON.
    3. ``stream()`` / ``stream_async()`` — потоковый вывод токенов/строк.
    4. ``run_agent()`` — выполнение задач CLI в контексте рабочей директории проекта.
    """

    _DEFAULT_MODEL: str = "gemini-3.1-flash-lite"
    _IGNORE_LINE_PREFIXES: tuple[str, ...] = (
        "YOLO mode is enabled",
        "Loaded extension:",
        "Loading extension",
    )

    def __init__(
        self,
        executable: str = "gemini",
        working_directory: Optional[Union[str, Path]] = None,
        timeout: int = 300,
        default_model: str = _DEFAULT_MODEL,
    ) -> None:
        """Инициализация провайдера Gemini CLI.

        :param executable: Имя или полный путь к исполняемому файлу Gemini CLI.
        :param working_directory: Рабочий каталог по умолчанию для запуска процессов CLI.
        :param timeout: Максимальное время выполнения в секундах по умолчанию.
        :param default_model: Идентификатор модели по умолчанию.
        """
        self.executable: str = executable
        self.working_directory: Optional[Path] = (
            Path(working_directory).resolve() if working_directory is not None else None
        )
        self.timeout: int = timeout
        self.default_model: str = default_model

    @classmethod
    def find_executable(cls, custom_name: str = "gemini") -> Optional[str]:
        """Поиск исполняемого файла Gemini CLI в системе и стандартных директориях Windows.

        :param custom_name: Имя файла для поиска.
        :returns: Абсолютный путь к исполняемому файлу или ``None``, если файл не найден.
        """
        # 1. Поиск через системный PATH
        if sys.platform == "win32":
            candidates = [custom_name, f"{custom_name}.cmd", f"{custom_name}.bat", f"{custom_name}.exe"]
        else:
            candidates = [custom_name]

        for cand in candidates:
            resolved = shutil.which(cand)
            if resolved:
                return resolved

        # 2. Поиск в типичных директориях npm global на Windows
        if sys.platform == "win32":
            npm_appdata = os.path.expandvars(r"%APPDATA%\npm\gemini.cmd")
            if os.path.exists(npm_appdata):
                return npm_appdata

            local_npm = os.path.expandvars(r"%LOCALAPPDATA%\Programs\npm\gemini.cmd")
            if os.path.exists(local_npm):
                return local_npm

            user_bin = Path.home() / "AppData" / "Roaming" / "npm" / "gemini.cmd"
            if user_bin.exists():
                return str(user_bin)

        return None

    def resolve_executable(self) -> str:
        """Разрешение пути к исполняемому файлу Gemini CLI с проверкой существования.

        :returns: Проверенный путь к исполняемому файлу.
        :raises RuntimeError: Если исполняемый файл не найден в системе.
        """
        resolved = self.find_executable(self.executable)
        if not resolved:
            raise RuntimeError(
                f"Gemini CLI не найден в системе (executable='{self.executable}'). "
                f"Убедитесь, что 'gemini' установлен и добавлен в системный PATH."
            )
        return resolved

    def is_available(self) -> bool:
        """Проверка наличия Gemini CLI в операционной системе.

        :returns: ``True``, если Gemini CLI доступен для вызова.
        """
        return self.find_executable(self.executable) is not None

    def get_version(self) -> Optional[str]:
        """Диагностика и получение версии установленного Gemini CLI.

        :returns: Строка версии (например, '0.4.1') или ``None`` при ошибке.
        """
        try:
            exe = self.resolve_executable()
            res = subprocess.run(
                [exe, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
            return None
        except Exception as ex:
            logger.debug(f"[GeminiCliProvider] Не удалось получить версию CLI: {ex}")
            return None

    def _clean_output(self, raw_text: str) -> str:
        """Очистка stdout вывода CLI от служебных баннеров и сообщений расширений.

        :param raw_text: Исходный текст из stdout.
        :returns: Очищенный текст ответа модели.
        """
        if not raw_text:
            return ""

        lines = raw_text.splitlines()
        filtered_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(pfx) for pfx in self._IGNORE_LINE_PREFIXES):
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines).strip()

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Безопасное извлечение и парсинг JSON из текстового вывода модели.

        :param text: Текст, содержащий JSON или markdown-блок ```json ... ```.
        :returns: Распарсенный Python-объект (dict, list, etc.).
        :raises ValueError: Если валидный JSON не обнаружен.
        """
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Пустой ответ модели, невозможно распарсить JSON")

        # 1. Попытка прямого парсинга
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 2. Поиск блоков ```json ... ``` или ``` ... ```
        match = re.search(r"```(?:json)?\s*\n(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 3. Поиск подстроки от первой { до последней } или от [ до ]
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            candidate = cleaned[brace_start : brace_end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        bracket_start = cleaned.find("[")
        bracket_end = cleaned.rfind("]")
        if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
            candidate = cleaned[bracket_start : bracket_end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Не удалось распарсить JSON из ответа Gemini CLI: {cleaned[:200]}")

    def _build_command(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        approval_mode: str = "yolo",
        output_format: str = "text",
    ) -> tuple[str, List[str]]:
        """Формирование списка аргументов командной строки для вызова Gemini CLI.

        :param prompt: Текст запроса.
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param approval_mode: Режим подтверждения (по умолчанию 'yolo').
        :param output_format: Формат вывода ('text' или 'json').
        :returns: Кортеж (путь_к_exe, список_аргументов).
        """
        exe = self.resolve_executable()
        effective_model = (model or self.default_model).strip()
        if effective_model.startswith("gemini_cli:"):
            effective_model = effective_model[len("gemini_cli:") :]
        elif effective_model.startswith("models/"):
            effective_model = effective_model[len("models/") :]

        full_prompt = prompt
        if system_instruction and system_instruction.strip():
            full_prompt = f"System Instruction:\n{system_instruction.strip()}\n\nUser Query:\n{prompt}"

        cmd = [
            exe,
            "-p",
            full_prompt,
            "-m",
            effective_model,
            "--approval-mode",
            approval_mode,
            "-o",
            output_format,
        ]
        return exe, cmd

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[Union[str, Path]] = None,
        approval_mode: str = "yolo",
    ) -> GeminiCliResponse:
        """Синхронное выполнение запроса к Gemini CLI (Режим 1).

        :param prompt: Текст запроса.
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param timeout: Время ожидания в секундах (по умолчанию используется self.timeout).
        :param working_directory: Рабочая директория (по умолчанию self.working_directory).
        :param approval_mode: Режим подтверждения ('yolo' по умолчанию).
        :returns: Объект ``GeminiCliResponse``.
        :raises RuntimeError: Если Gemini CLI не найден.
        :raises TimeoutError: Если время выполнения превысило timeout.
        """
        eff_timeout = timeout or self.timeout
        eff_cwd = Path(working_directory).resolve() if working_directory else self.working_directory
        exe, cmd = self._build_command(
            prompt=prompt,
            model=model,
            system_instruction=system_instruction,
            approval_mode=approval_mode,
            output_format="text",
        )

        logger.debug(f"[GeminiCliProvider] Запуск команды: {' '.join(cmd[:3])}... (cwd={eff_cwd})")
        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                cmd,
                cwd=eff_cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=eff_timeout,
                shell=(sys.platform == "win32"),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            logger.error(f"[GeminiCliProvider] Превышен timeout ({eff_timeout} с): {exc}")
            raise TimeoutError(f"Gemini CLI не завершился за {eff_timeout} секунд") from exc
        except Exception as exc:
            logger.error(f"[GeminiCliProvider] Ошибка вызова subprocess: {exc}")
            raise

        duration = time.perf_counter() - start_time
        cleaned_text = self._clean_output(result.stdout)

        if result.returncode != 0:
            logger.warning(
                f"[GeminiCliProvider] Процесс завершился с кодом {result.returncode}. "
                f"Stderr: {result.stderr[:200]}"
            )

        return GeminiCliResponse(
            text=cleaned_text,
            return_code=result.returncode,
            stderr=result.stderr.strip(),
            duration_seconds=round(duration, 3),
        )

    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[Union[str, Path]] = None,
        approval_mode: str = "yolo",
    ) -> GeminiCliResponse:
        """Асинхронное выполнение запроса к Gemini CLI.

        :param prompt: Текст запроса.
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param timeout: Время ожидания в секундах.
        :param working_directory: Рабочая директория.
        :param approval_mode: Режим подтверждения ('yolo').
        :returns: Объект ``GeminiCliResponse``.
        """
        eff_timeout = timeout or self.timeout
        eff_cwd = Path(working_directory).resolve() if working_directory else self.working_directory
        exe, cmd = self._build_command(
            prompt=prompt,
            model=model,
            system_instruction=system_instruction,
            approval_mode=approval_mode,
            output_format="text",
        )

        start_time = time.perf_counter()

        try:
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        *cmd,
                        cwd=eff_cwd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=eff_timeout,
                )
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=eff_timeout,
                )
                stdout_text = stdout_bytes.decode("utf-8", errors="replace")
                stderr_text = stderr_bytes.decode("utf-8", errors="replace")
                returncode = proc.returncode or 0
            except NotImplementedError:
                # Fallback для SelectorEventLoop на Windows
                loop = asyncio.get_running_loop()
                def _run():
                    return subprocess.run(
                        cmd,
                        cwd=eff_cwd,
                        capture_output=True,
                        text=True,
                        shell=(sys.platform == "win32"),
                        encoding="utf-8",
                        errors="replace",
                        timeout=eff_timeout,
                    )
                sub_res = await loop.run_in_executor(None, _run)
                stdout_text = sub_res.stdout
                stderr_text = sub_res.stderr
                returncode = sub_res.returncode
        except (asyncio.TimeoutError, subprocess.TimeoutExpired) as exc:
            logger.error(f"[GeminiCliProvider] Асинхронный вызов превысил таймаут {eff_timeout}с")
            raise TimeoutError(f"Gemini CLI не завершился за {eff_timeout} секунд") from exc

        duration = time.perf_counter() - start_time
        cleaned_text = self._clean_output(stdout_text)

        return GeminiCliResponse(
            text=cleaned_text,
            return_code=returncode,
            stderr=stderr_text.strip(),
            duration_seconds=round(duration, 3),
        )

    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[Union[str, Path]] = None,
        approval_mode: str = "yolo",
    ) -> Any:
        """Синхронное получение структурированного JSON-ответа от Gemini CLI (Режим 2).

        :param prompt: Текст запроса (рекомендуется указать требования к структуре JSON).
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param timeout: Время ожидания в секундах.
        :param working_directory: Рабочая директория.
        :param approval_mode: Режим подтверждения ('yolo').
        :returns: Распарсенный JSON-объект (dict или list).
        :raises ValueError: Если ответ не может быть распарсен как JSON.
        :raises RuntimeError: Если процесс завершился с ошибкой.
        """
        resp = self.generate(
            prompt=prompt,
            model=model,
            system_instruction=system_instruction,
            timeout=timeout,
            working_directory=working_directory,
            approval_mode=approval_mode,
        )

        if not resp.success and not resp.text:
            raise RuntimeError(
                f"Gemini CLI завершился с ошибкой (код {resp.return_code}): {resp.stderr}"
            )

        parsed = self._extract_json(resp.text)
        resp.parsed_json = parsed
        return parsed

    def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[Union[str, Path]] = None,
        approval_mode: str = "yolo",
    ) -> Generator[str, None, None]:
        """Синхронный генератор потокового вывода stdout от Gemini CLI (Режим 3).

        :param prompt: Текст запроса.
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param timeout: Время ожидания в секундах.
        :param working_directory: Рабочая директория.
        :param approval_mode: Режим подтверждения ('yolo').
        :yields: Строки или порции текста из stdout процесса.
        """
        eff_cwd = Path(working_directory).resolve() if working_directory else self.working_directory
        exe, cmd = self._build_command(
            prompt=prompt,
            model=model,
            system_instruction=system_instruction,
            approval_mode=approval_mode,
            output_format="text",
        )

        proc = subprocess.Popen(
            cmd,
            cwd=eff_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=(sys.platform == "win32"),
            encoding="utf-8",
            errors="replace",
        )

        try:
            if proc.stdout:
                for line in proc.stdout:
                    stripped = line.strip()
                    if any(stripped.startswith(pfx) for pfx in self._IGNORE_LINE_PREFIXES):
                        continue
                    yield line

            proc.wait(timeout=timeout or self.timeout)
            if proc.returncode != 0 and proc.stderr:
                err_msg = proc.stderr.read().strip()
                if err_msg:
                    logger.warning(f"[GeminiCliProvider] Потоковый процесс код {proc.returncode}: {err_msg}")
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            raise TimeoutError(f"Gemini CLI превысил timeout во время потоковой передачи") from exc
        finally:
            if proc.poll() is None:
                proc.kill()

    async def stream_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[Union[str, Path]] = None,
        approval_mode: str = "yolo",
    ) -> AsyncGenerator[str, None]:
        """Асинхронный генератор потокового вывода от Gemini CLI (Режим 3 - Async).

        :param prompt: Текст запроса.
        :param model: Идентификатор модели.
        :param system_instruction: Системная инструкция.
        :param timeout: Время ожидания в секундах.
        :param working_directory: Рабочая директория.
        :param approval_mode: Режим подтверждения ('yolo').
        :yields: Фрагменты сгенерированного ответа.
        """
        eff_cwd = Path(working_directory).resolve() if working_directory else self.working_directory
        exe, cmd = self._build_command(
            prompt=prompt,
            model=model,
            system_instruction=system_instruction,
            approval_mode=approval_mode,
            output_format="text",
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=eff_cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            if proc.stdout:
                while True:
                    line_bytes = await proc.stdout.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace")
                    stripped = line.strip()
                    if any(stripped.startswith(pfx) for pfx in self._IGNORE_LINE_PREFIXES):
                        continue
                    yield line

            await proc.wait()
            if proc.returncode != 0 and proc.stderr:
                stderr_bytes = await proc.stderr.read()
                err_text = stderr_bytes.decode("utf-8", errors="replace").strip()
                if err_text:
                    logger.warning(f"[GeminiCliProvider] async stream код {proc.returncode}: {err_text}")

        except NotImplementedError:
            # Fallback для циклов событий без subprocess transport (Windows Selector)
            loop = asyncio.get_running_loop()
            q_lines: queue.Queue[Optional[str]] = queue.Queue()

            def _sync_stream():
                try:
                    p = subprocess.Popen(
                        cmd,
                        cwd=eff_cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=(sys.platform == "win32"),
                        encoding="utf-8",
                        errors="replace",
                    )
                    if p.stdout:
                        for l in p.stdout:
                            q_lines.put(l)
                    p.wait()
                finally:
                    q_lines.put(None)

            t = threading.Thread(target=_sync_stream, daemon=True)
            t.start()

            while True:
                line = await loop.run_in_executor(None, q_lines.get)
                if line is None:
                    break
                stripped = line.strip()
                if any(stripped.startswith(pfx) for pfx in self._IGNORE_LINE_PREFIXES):
                    continue
                yield line

    def run_agent(
        self,
        prompt: str,
        working_directory: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> GeminiCliResponse:
        """Запуск Gemini CLI в режиме автономного агента для проекта (Режим 4).

        Выполняет команду в целевой рабочей директории проекта, обеспечивая
        доступ CLI ко всем проектным файлам, инструментам и контексту репозитория.

        :param prompt: Задача или инструкция для агента.
        :param working_directory: Каталог проекта (по умолчанию self.working_directory).
        :param model: Идентификатор модели.
        :param timeout: Лимит времени выполнения.
        :returns: Объект ``GeminiCliResponse`` с результатом работы агента.
        """
        target_cwd = Path(working_directory).resolve() if working_directory else (self.working_directory or Path.cwd())
        logger.info(f"[GeminiCliProvider] Запуск agent-режима в каталоге: {target_cwd}")

        return self.generate(
            prompt=prompt,
            model=model,
            working_directory=target_cwd,
            timeout=timeout,
            approval_mode="yolo",
        )
