# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Logger - Logger
# =============================================================================
# Description:
#   Централизованный модульный логгер платформы AI-Breadboard.
#   Поддерживает цветной консольный вывод, JSON-форматирование, компрессию повторяющихся
#   строк, ротацию файлов и автоматическую маршрутизацию логов по независимым
#   подсистемам (windows, telemetry, wikillm, ai, rag, skills, apps, fastapi и др.).
#
# Usage Examples:
#   Python API:
#     from logger import logger, get_subsystem_logger
#
#     logger.info("Общее информационное сообщение")
#     win_log = get_subsystem_logger("windows")
#     win_log.info("Событие подсистемы Windows")
#
# File: logger.py
# Project: ai-breadboard
# Package: logger
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:32:00
# =============================================================================

from __future__ import annotations
"""Централизованный модульный логгер с изолированными файлами подсистем."""

import atexit
from collections import Counter
import copy
import inspect
import json
import logging
import logging.handlers
import os
from pathlib import Path
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

import colorama
import header
from header import __root__

colorama.init(autoreset=False)

TEXT_COLORS: Dict[str, str] = {
    'black': colorama.Fore.BLACK,
    'red': colorama.Fore.RED,
    'green': colorama.Fore.GREEN,
    'yellow': colorama.Fore.YELLOW,
    'blue': colorama.Fore.BLUE,
    'magenta': colorama.Fore.MAGENTA,
    'cyan': colorama.Fore.CYAN,
    'white': colorama.Fore.WHITE,
    'light_gray': colorama.Fore.LIGHTBLACK_EX,
    'light_red': colorama.Fore.LIGHTRED_EX,
    'light_green': colorama.Fore.LIGHTGREEN_EX,
    'light_yellow': colorama.Fore.LIGHTYELLOW_EX,
    'light_blue': colorama.Fore.LIGHTBLUE_EX,
    'light_magenta': colorama.Fore.LIGHTMAGENTA_EX,
    'light_cyan': colorama.Fore.LIGHTCYAN_EX,
}

BG_COLORS: Dict[str, str] = {
    'black': colorama.Back.BLACK,
    'red': colorama.Back.RED,
    'green': colorama.Back.GREEN,
    'yellow': colorama.Back.YELLOW,
    'blue': colorama.Back.BLUE,
    'magenta': colorama.Back.MAGENTA,
    'cyan': colorama.Back.CYAN,
    'white': colorama.Back.WHITE,
    'light_gray': colorama.Back.LIGHTBLACK_EX,
    'light_red': colorama.Back.LIGHTRED_EX,
    'light_green': colorama.Back.LIGHTGREEN_EX,
    'light_yellow': colorama.Back.LIGHTYELLOW_EX,
    'light_blue': colorama.Back.LIGHTBLUE_EX,
    'light_magenta': colorama.Back.LIGHTMAGENTA_EX,
    'light_cyan': colorama.Back.LIGHTCYAN_EX,
}

# =============================================================================
# Декларативная карта маршрутизации логов по подсистемам
# =============================================================================
SUBSYSTEM_ROUTING_MAP: List[Tuple[Tuple[str, ...], str]] = [
    # 1. Стек Windows (apps/windows)
    (('apps/windows/api', 'apps\\windows\\api', 'router_tc', 'internal_app'), 'windows_api.log'),
    (('apps/windows/telemetry', 'apps\\windows\\telemetry', 'telemetry_research', 'lhm'), 'telemetry.log'),
    (('apps/windows/wikillm', 'apps\\windows\\wikillm'), 'wikillm.log'),
    (('apps/windows', 'apps\\windows', 'src/ai/agents/windows_tools', 'src\\ai\\agents\\windows_tools', 'windows_admin'), 'windows.log'),

    # 2. Изолированные провайдеры ИИ и CLI
    (('src/ai/providers/gemini_cli', 'src\\ai\\providers\\gemini_cli', 'gemini_cli_chat', 'gemini_cli'), 'gemini_cli.log'),
    (('src/ai/providers/gemini', 'src\\ai\\providers\\gemini', 'src/ai/gemini', 'src\\ai\\gemini', 'gemini_chat'), 'gemini.log'),
    (('src/ai/providers/agy_cli', 'src\\ai\\providers\\agy_cli', 'agy_cli'), 'agy_cli.log'),
    (('src/ai/providers/agy', 'src\\ai\\providers\\agy', 'agy_chat'), 'agy.log'),
    (('src/ai/providers/ollama', 'src\\ai\\providers\\ollama', 'ollama_chat', 'ollama'), 'ollama.log'),
    (('src/ai/providers/openai', 'src\\ai\\providers\\openai', 'openai_compat_chat', 'openai'), 'openai.log'),
    (('src/ai/providers/foundry', 'src\\ai\\providers\\foundry', 'foundry_chat', 'foundry'), 'foundry.log'),
    (('src/ai/providers/windows_ai', 'src\\ai\\providers\\windows_ai', 'windows_ai'), 'windows_ai.log'),
    (('src/ai/providers/huggingface', 'src\\ai\\providers\\huggingface', 'hf_chat', 'huggingface'), 'huggingface.log'),
    (('src/ai/providers/onnx', 'src\\ai\\providers\\onnx', 'onnx_chat', 'onnx'), 'onnx.log'),
    (('src/ai/voice', 'src\\ai\\voice', 'voice_pipeline', 'audio_diarization'), 'voice.log'),

    # 3. RAG, Агенты и общая оркестрация ИИ
    (('src/rag', 'src\\rag', 'pixelrag'), 'rag.log'),
    (('src/skills', 'src\\skills', '.agents/skills', '.agents\\skills', 'skill_factory', 'langchain_agent'), 'skills.log'),
    (('src/ai', 'src\\ai', 'unified_chat', 'model_manager'), 'ai.log'),

    # 4. Автономные приложения (apps/*)
    (('apps/trading_terminal', 'apps\\trading_terminal', 'trading'), 'trading.log'),
    (('apps/helpdesk', 'apps\\helpdesk'), 'helpdesk.log'),
    (('apps/enterprise_knowledge', 'apps\\enterprise_knowledge'), 'enterprise_knowledge.log'),
    (('apps/cloudflared_monitor', 'apps\\cloudflared_monitor'), 'cloudflared.log'),
    (('apps/gcloud_monitor', 'apps\\gcloud_monitor'), 'gcloud.log'),
    (('apps/website_monitor', 'apps\\website_monitor'), 'website_monitor.log'),
    (('apps/user_assistant', 'apps\\user_assistant'), 'user_assistant.log'),
    (('apps/google_user_desktop', 'apps\\google_user_desktop'), 'google_user_desktop.log'),
    (('apps/wikipedia_research', 'apps\\wikipedia_research'), 'wikipedia_research.log'),
    (('apps/tshark', 'apps\\tshark', 'network_analyzer'), 'network.log'),
    (('playwright', 'torrent_playwright'), 'playwright.log'),
    (('yt_dlp', 'yt-dlp'), 'yt_dlp.log'),

    # 5. Основной сервер и роутеры
    (('src/api', 'src\\api', 'src/app', 'src\\app', 'main.py', 'fastapi'), 'fastapi.log'),
]

SUBSYSTEM_ALIASES: Dict[str, str] = {
    # Windows
    'windows': 'windows.log',
    'windows_api': 'windows_api.log',
    'tc': 'windows_api.log',
    'telemetry': 'telemetry.log',
    'wikillm': 'wikillm.log',
    # ИИ провайдеры и CLI
    'gemini': 'gemini.log',
    'gemini_cli': 'gemini_cli.log',
    'agy': 'agy.log',
    'agy_cli': 'agy_cli.log',
    'ollama': 'ollama.log',
    'openai': 'openai.log',
    'foundry': 'foundry.log',
    'windows_ai': 'windows_ai.log',
    'huggingface': 'huggingface.log',
    'hf': 'huggingface.log',
    'onnx': 'onnx.log',
    'voice': 'voice.log',
    # RAG и ядро ИИ
    'ai': 'ai.log',
    'rag': 'rag.log',
    'skills': 'skills.log',
    # Автономные приложения
    'trading': 'trading.log',
    'helpdesk': 'helpdesk.log',
    'enterprise_knowledge': 'enterprise_knowledge.log',
    'cloudflared': 'cloudflared.log',
    'gcloud': 'gcloud.log',
    'website_monitor': 'website_monitor.log',
    'user_assistant': 'user_assistant.log',
    'google_user_desktop': 'google_user_desktop.log',
    'wikipedia_research': 'wikipedia_research.log',
    'network': 'network.log',
    'tshark': 'network.log',
    'playwright': 'playwright.log',
    'yt_dlp': 'yt_dlp.log',
    'fastapi': 'fastapi.log',
}


class SingletonMeta(type):
    """Метакласс для реализации потокобезопасного паттерна Singleton."""
    _instances: Dict[Any, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class JsonFormatter(logging.Formatter):
    """Кастомный форматтер для сериализации лог-записей в JSON формат."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'levelname': record.levelname,
            'message': record.getMessage().replace('"', "'"),
            'exc_info': self.formatException(record.exc_info) if record.exc_info else None,
        }
        return json.dumps(log_entry, ensure_ascii=False)


class CompressingHandler(logging.handlers.RotatingFileHandler):
    """Обработчик логов с компрессией повторяющихся строк и ротацией файлов."""

    def __init__(self, filename: str, maxBytes: int = 10 * 1024 * 1024, backupCount: int = 5, encoding: str = 'utf-8'):
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=False)
        self.buffer: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._dirty = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            with self._lock:
                self.buffer[msg] = self.buffer.get(msg, 0) + 1
                self._dirty = True
                if len(self.buffer) > 100:
                    self.flush()
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        with self._lock:
            if not self.buffer or not self._dirty:
                return
            try:
                if not self.stream:
                    self.stream = self._open()
                for msg, count in self.buffer.items():
                    if count > 1:
                        self.stream.write(f'[{count}x] {msg}\n')
                    else:
                        self.stream.write(f'{msg}\n')
                self.stream.flush()
                self.buffer.clear()
                self._dirty = False
            except Exception:
                pass

    def close(self) -> None:
        self.flush()
        super().close()


class PrettyConsoleFormatter(logging.Formatter):
    """Консольный форматтер с автоформатированием вложенных структур."""

    def format(self, record: logging.LogRecord) -> str:
        from src.utils.printer import pformat
        try:
            orig_msg = record.getMessage()
            formatted_msg = pformat(orig_msg)
            orig_record_msg = record.msg
            orig_args = record.args
            record.msg = formatted_msg
            record.args = None
            result = super().format(record)
            record.msg = orig_record_msg
            record.args = orig_args
            return result
        except Exception:
            return super().format(record)


class Logger(metaclass=SingletonMeta):
    """Универсальный модульный логгер AI-Breadboard.

    Обеспечивает цветной консольный вывод, JSON-журналирование и автоматическую
    маршрутизацию в отдельные файлы подсистем с ротацией.
    """

    def __init__(
        self,
        info_log_path: Optional[str] = None,
        debug_log_path: Optional[str] = None,
        errors_log_path: Optional[str] = None,
        json_log_path: Optional[str] = None,
    ):
        self._lock = threading.Lock()
        self._module_loggers: Dict[str, logging.Logger] = {}

        env_dir = os.environ.get('AI_BREADBOARD_LOGS_DIR') or os.environ.get('LOG_DIR')
        if env_dir:
            self.log_files_path = Path(env_dir)
        else:
            appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
            base_dir = Path(appdata) if appdata and os.path.exists(appdata) else Path.home() / '.config'
            self.log_files_path = base_dir / 'AI-Breadboard' / 'logs'

        self.info_log_path: Path = self.log_files_path / (info_log_path or 'info.log')
        self.debug_log_path: Path = self.log_files_path / (debug_log_path or 'debug.log')
        self.errors_log_path: Path = self.log_files_path / (errors_log_path or 'errors.log')
        self.json_log_path: Path = self.log_files_path / (json_log_path or 'log.json')

        self.log_files_path.mkdir(parents=True, exist_ok=True)
        for log_path in [self.info_log_path, self.debug_log_path, self.errors_log_path, self.json_log_path]:
            try:
                log_path.touch(exist_ok=True)
            except Exception:
                pass

        if sys.platform == 'win32':
            for stream in (sys.stdout, sys.stderr, getattr(sys, '__stdout__', None), getattr(sys, '__stderr__', None)):
                if stream is not None and hasattr(stream, 'reconfigure'):
                    try:
                        stream.reconfigure(encoding='utf-8', errors='replace')
                    except Exception:
                        pass

        console_formatter = PrettyConsoleFormatter('%(asctime)s - %(levelname)s - %(message)s')
        target_stream = sys.__stdout__ if getattr(sys, '__stdout__', None) is not None else sys.__stderr__
        if target_stream is not None:
            console_handler = logging.StreamHandler(target_stream)
            console_handler.setFormatter(console_formatter)
        else:
            console_handler = logging.NullHandler()

        self.logger_console: logging.Logger = logging.getLogger('logger_console')
        self.logger_console.setLevel(logging.DEBUG)
        self.logger_console.propagate = False
        if not self.logger_console.handlers:
            self.logger_console.addHandler(console_handler)

        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.INFO)
        else:
            for h in root_logger.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.setFormatter(console_formatter)

        for noisy in ['httpx', 'httpcore', 'google', 'google.genai', 'urllib3']:
            logging.getLogger(noisy).setLevel(logging.WARNING)

        self._setup_debug_mode()
        self._setup_file_handlers()
        atexit.register(self._cleanup)

    @property
    def fastapi_log_path(self) -> Path:
        return self.log_files_path / 'fastapi.log'

    @property
    def gemini_log_path(self) -> Path:
        return self.log_files_path / 'ai.log'

    @property
    def playwright_log_path(self) -> Path:
        return self.log_files_path / 'playwright.log'

    @property
    def yt_dlp_log_path(self) -> Path:
        return self.log_files_path / 'yt_dlp.log'

    @property
    def logger_fastapi(self) -> logging.Logger:
        return self._get_or_create_subsystem_logger('fastapi.log')

    @property
    def logger_gemini(self) -> logging.Logger:
        return self._get_or_create_subsystem_logger('ai.log')

    @property
    def logger_playwright(self) -> logging.Logger:
        return self._get_or_create_subsystem_logger('playwright.log')

    @property
    def logger_yt_dlp(self) -> logging.Logger:
        return self._get_or_create_subsystem_logger('yt_dlp.log')

    def _setup_debug_mode(self) -> None:
        """Определяет, находится ли приложение в режиме отладки."""
        try:
            from dotenv import load_dotenv
            load_dotenv(__root__ / '.env')

            config_file = __root__ / 'config.json'
            log_debug = None
            log_level = ''
            mode_val = os.getenv('MODE', 'dev').lower()
            server_debug = os.getenv('DEBUG', 'true').lower() == 'true'

            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        cfg_data = json.load(f)
                    log_cfg = cfg_data.get('logging', {})
                    srv_cfg = cfg_data.get('server', {})
                    log_debug = log_cfg.get('debug')
                    log_level = str(log_cfg.get('level', '')).lower()
                    mode_val = str(srv_cfg.get('mode', mode_val)).lower()
                    server_debug = bool(srv_cfg.get('debug', server_debug))
                except Exception:
                    pass

            if log_debug is not None:
                self.is_debug_mode = bool(log_debug)
            elif log_level:
                self.is_debug_mode = log_level == 'debug'
            else:
                self.is_debug_mode = mode_val in ('dev', 'debug') or server_debug
        except Exception:
            self.is_debug_mode = True

    def _setup_file_handlers(self) -> None:
        """Инициализирует базовые обработчики общих файлов логов."""
        self.logger_file_info: logging.Logger = logging.getLogger('logger_file_info')
        self.logger_file_info.setLevel(logging.INFO)
        self.logger_file_info.propagate = False
        info_handler = logging.FileHandler(self.info_log_path, encoding='utf-8')
        info_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger_file_info.addHandler(info_handler)

        self.logger_file_debug: logging.Logger = logging.getLogger('logger_file_debug')
        self.logger_file_debug.setLevel(logging.DEBUG)
        self.logger_file_debug.propagate = False
        debug_handler = logging.FileHandler(self.debug_log_path, encoding='utf-8')
        debug_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger_file_debug.addHandler(debug_handler)

        self.logger_file_errors: logging.Logger = logging.getLogger('logger_file_errors')
        self.logger_file_errors.setLevel(logging.ERROR)
        self.logger_file_errors.propagate = False
        errors_handler = CompressingHandler(str(self.errors_log_path), encoding='utf-8')
        errors_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger_file_errors.addHandler(errors_handler)

        self.logger_file_json: logging.Logger = logging.getLogger('logger_json')
        self.logger_file_json.setLevel(logging.DEBUG)
        self.logger_file_json.propagate = False
        json_handler = logging.FileHandler(self.json_log_path, encoding='utf-8')
        json_handler.setFormatter(JsonFormatter())
        self.logger_file_json.addHandler(json_handler)

    def _get_or_create_subsystem_logger(self, log_filename: str) -> logging.Logger:
        """Создает или возвращает закешированный логгер для отдельного файла подсистемы.

        Args:
            log_filename (str): Имя файла лога (например, 'windows.log').

        Returns:
            logging.Logger: Настроенный логгер с CompressingHandler.
        """
        with self._lock:
            if log_filename in self._module_loggers:
                return self._module_loggers[log_filename]

            log_path = self.log_files_path / log_filename
            try:
                log_path.touch(exist_ok=True)
            except Exception:
                pass

            logger_name = f'logger_subsystem_{log_filename.replace(".", "_")}'
            sub_logger = logging.getLogger(logger_name)
            sub_logger.setLevel(logging.DEBUG)
            sub_logger.propagate = False

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler = CompressingHandler(str(log_path), encoding='utf-8')
            handler.setFormatter(formatter)
            sub_logger.addHandler(handler)

            self._module_loggers[log_filename] = sub_logger
            return sub_logger

    def get_subsystem_logger(self, subsystem_name: str) -> logging.Logger:
        """Возвращает специализированный логгер подсистемы по имени или файлу.

        Args:
            subsystem_name (str): Имя подсистемы ('windows', 'telemetry', 'rag', 'skills' и др.)
                                  или имя файла ('windows.log').

        Returns:
            logging.Logger: Логгер, направляющий вывод в изолированный файл подсистемы.
        """
        filename = SUBSYSTEM_ALIASES.get(subsystem_name.lower())
        if not filename:
            filename = subsystem_name if subsystem_name.endswith('.log') else f'{subsystem_name}.log'
        return self._get_or_create_subsystem_logger(filename)

    def get_logger(self, name: str) -> logging.Logger:
        """Алиас для get_subsystem_logger для совместимости со стандартным logging.

        Args:
            name (str): Имя подсистемы или логгера.

        Returns:
            logging.Logger: Логгер подсистемы.
        """
        return self.get_subsystem_logger(name)

    def _get_caller_info(self, depth: int = 2) -> Tuple[str, str, int]:
        """Безопасно извлекает имя вызывающего файла, функции и номер строки."""
        try:
            stack = inspect.stack()
            if len(stack) > depth:
                frame_info = stack[depth]
                return (frame_info.filename, frame_info.function, frame_info.lineno)
        except Exception:
            pass
        return ('unknown', 'unknown', 0)

    def _format_message(self, message: Any, ex: Optional[Exception] = None, color: Optional[Tuple[str, str]] = None) -> str:
        """Форматирует сообщение с цветом и информацией об исключении."""
        from src.utils.printer import pformat
        formatted = pformat(message)
        if ex:
            formatted = f'{formatted} {str(ex)}'
        if color:
            text_color, bg_color = color
            t_col = TEXT_COLORS.get(text_color, colorama.Fore.RESET)
            b_col = BG_COLORS.get(bg_color, colorama.Back.RESET)
            return f'{t_col}{b_col}{formatted}{colorama.Style.RESET_ALL}'
        return formatted

    def _route_to_module_logger(self, message: str, level: int, filename: str) -> None:
        """Маршрутизирует запись в файл соответствующей подсистемы."""
        filename_lower = filename.lower().replace('\\', '/')
        for patterns, target_log_file in SUBSYSTEM_ROUTING_MAP:
            if any(p.lower() in filename_lower for p in patterns):
                try:
                    sub_logger = self._get_or_create_subsystem_logger(target_log_file)
                    sub_logger.log(level, message)
                except Exception:
                    pass
                break

    def setLevel(self, level: int | str) -> None:
        """Устанавливает уровень логирования."""
        if isinstance(level, str):
            self.is_debug_mode = level.upper() == 'DEBUG'
        elif isinstance(level, int):
            self.is_debug_mode = level <= logging.DEBUG

    def log(
        self,
        level: int,
        message: Any,
        ex: Optional[Exception] = None,
        exc_info: bool = False,
        color: Optional[Tuple[str, str]] = None,
    ) -> None:
        """Логирует сообщение во все целевые потоки и в изолированный файл подсистемы."""
        if level == logging.DEBUG and (not self.is_debug_mode):
            return

        from src.utils.printer import pformat
        plain_formatted = pformat(message)
        if ex:
            plain_formatted = f'{plain_formatted} {str(ex)}'

        colored_message = self._format_message(message, ex, color)
        if self.logger_console:
            try:
                self.logger_console.log(level, colored_message, exc_info=exc_info)
            except Exception:
                pass

        if self.logger_file_json:
            self.logger_file_json.log(level, plain_formatted, exc_info=exc_info)

        if level == logging.INFO and self.logger_file_info:
            self.logger_file_info.log(level, plain_formatted)
        elif level == logging.DEBUG and self.logger_file_debug:
            self.logger_file_debug.log(level, plain_formatted)
        elif level in (logging.ERROR, logging.CRITICAL) and self.logger_file_errors:
            self.logger_file_errors.log(level, plain_formatted)

        try:
            filename, _, _ = self._get_caller_info(depth=3)
            self._route_to_module_logger(plain_formatted, level, filename)
        except Exception:
            pass

    def _cleanup(self) -> None:
        """Очищает и закрывает все файловые дескрипторы."""
        try:
            for logger_name in ['logger_console', 'logger_file_info', 'logger_file_debug', 'logger_file_errors', 'logger_file_json']:
                logger_obj = getattr(self, logger_name, None)
                if logger_obj:
                    for handler in logger_obj.handlers[:]:
                        handler.flush()
                        handler.close()
                        logger_obj.removeHandler(handler)
            for sub_logger in self._module_loggers.values():
                for handler in sub_logger.handlers[:]:
                    handler.flush()
                    handler.close()
                    sub_logger.removeHandler(handler)
        except Exception:
            pass

    def info(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = False, text_color: str = 'green', bg_color: str = '') -> None:
        color = (text_color, bg_color) if bg_color else (text_color, '')
        self.log(logging.INFO, message, ex, exc_info, color)

    def success(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = False, text_color: str = 'light_green', bg_color: str = '') -> None:
        color = (text_color, bg_color) if bg_color else (text_color, '')
        self.log(logging.INFO, message, ex, exc_info, color)

    def warning(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = False, text_color: str = 'black', bg_color: str = 'yellow') -> None:
        color = (text_color, bg_color)
        self.log(logging.WARNING, message, ex, exc_info, color)

    def debug(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = False, text_color: str = 'cyan', bg_color: str = '') -> None:
        color = (text_color, bg_color) if bg_color else (text_color, '')
        self.log(logging.DEBUG, message, ex, exc_info, color)

    def error(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = True, text_color: str = 'red', bg_color: str = '') -> None:
        color = (text_color, bg_color) if bg_color else (text_color, '')
        self.log(logging.ERROR, message, ex, exc_info, color)

    def critical(self, message: Any, ex: Optional[Exception] = None, exc_info: bool = True, text_color: str = 'white', bg_color: str = 'red') -> None:
        color = (text_color, bg_color)
        self.log(logging.CRITICAL, message, ex, exc_info, color)

    def get_uvicorn_log_config(self, log_filename: str = 'fastapi.log') -> Dict[str, Any]:
        """Возвращает конфигурацию логирования uvicorn с временными метками и записью в файл.

        Args:
            log_filename (str): Имя целевого файла лога (по умолчанию 'fastapi.log').

        Returns:
            Dict[str, Any]: Конфигурация логирования uvicorn.
        """
        return get_uvicorn_log_config(log_filename)


def get_uvicorn_log_config(log_filename: str = 'fastapi.log') -> Dict[str, Any]:
    """Формирует стандартизированную конфигурацию логирования uvicorn с выводом в консоль и в файл.

    Args:
        log_filename (str): Имя целевого файла лога (по умолчанию 'fastapi.log', для TC API 'windows_api.log').

    Returns:
        Dict[str, Any]: Конфигурация логирования uvicorn.
    """
    try:
        import uvicorn.config
        env_dir = os.environ.get('AI_BREADBOARD_LOGS_DIR') or os.environ.get('LOG_DIR')
        if env_dir:
            logs_dir = Path(env_dir)
        else:
            appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
            base_dir = Path(appdata) if appdata and os.path.exists(appdata) else Path.home() / '.config'
            logs_dir = base_dir / 'AI-Breadboard' / 'logs'

        logs_dir.mkdir(parents=True, exist_ok=True)
        target_path = str(logs_dir / log_filename)

        log_config: Dict[str, Any] = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)

        # 1. Форматтеры консоли и файла
        log_config['formatters']['default']['fmt'] = '%(asctime)s %(levelprefix)s %(message)s'
        log_config['formatters']['default']['datefmt'] = '%Y-%m-%d %H:%M:%S'
        log_config['formatters']['access']['fmt'] = (
            '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
        )
        log_config['formatters']['access']['datefmt'] = '%Y-%m-%d %H:%M:%S'

        log_config['formatters']['file_default'] = {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'use_colors': False,
        }
        log_config['formatters']['file_access'] = {
            '()': 'uvicorn.logging.AccessFormatter',
            'fmt': '%(asctime)s [ACCESS] %(client_addr)s - "%(request_line)s" %(status_code)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'use_colors': False,
        }

        # 2. Файловые обработчики с ротацией
        log_config['handlers']['file_default'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file_default',
            'filename': target_path,
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        }
        log_config['handlers']['file_access'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file_access',
            'filename': target_path,
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        }

        # 3. Привязка к логгерам Uvicorn
        if 'uvicorn' in log_config.get('loggers', {}):
            log_config['loggers']['uvicorn']['handlers'] = ['default', 'file_default']
            log_config['loggers']['uvicorn']['propagate'] = False
        if 'uvicorn.error' in log_config.get('loggers', {}):
            log_config['loggers']['uvicorn.error']['handlers'] = ['default', 'file_default']
            log_config['loggers']['uvicorn.error']['propagate'] = False
        if 'uvicorn.access' in log_config.get('loggers', {}):
            log_config['loggers']['uvicorn.access']['handlers'] = ['access', 'file_access']
            log_config['loggers']['uvicorn.access']['propagate'] = False

        log_config['loggers']['fastapi'] = {
            'handlers': ['default', 'file_default'],
            'level': 'INFO',
            'propagate': False,
        }

        return log_config
    except Exception:
        return {}


def get_subsystem_logger(subsystem_name: str) -> logging.Logger:
    """Удобный хелпер для получения логгера конкретной подсистемы.

    Args:
        subsystem_name (str): Имя подсистемы ('windows', 'telemetry', 'wikillm', 'rag', 'ai' и т.д.).

    Returns:
        logging.Logger: Логгер подсистемы.
    """
    return logger.get_subsystem_logger(subsystem_name)


logger: Logger = Logger()
'Глобальный экземпляр логгера для использования во всем приложении.'