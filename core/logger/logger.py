## \file src/logger/logger.py
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль логгера с поддержкой JSON и цветного вывода
# =============================================================================
# Описание:
#   Модуль предоставляет универсальный логгер с поддержкой цветного консольного вывода,
#   записи в файлы (info, debug, errors), а также JSON-форматирования логов. Реализован
#   паттерн Singleton для единого экземпляра логгера по всему приложению.
#
# File: src/logger/logger.py
# Project: ai-assistant
# Package: src.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

#! .pyenv/bin/python3

"""
.. module:: src.logger.logger
    :platform: Windows, Unix
    :synopsis: Модуль логгера
   
"""


import logging
import colorama
import datetime
import json
import inspect
import threading
from pathlib import Path
from typing import Optional, Tuple
from types import SimpleNamespace

import header
from header import __root__




TEXT_COLORS = {
    "black": colorama.Fore.BLACK,
    "red": colorama.Fore.RED,
    "green": colorama.Fore.GREEN,
    "yellow": colorama.Fore.YELLOW,
    "blue": colorama.Fore.BLUE,
    "magenta": colorama.Fore.MAGENTA,
    "cyan": colorama.Fore.CYAN,
    "white": colorama.Fore.WHITE,
    "light_gray": colorama.Fore.LIGHTBLACK_EX,
    "light_red": colorama.Fore.LIGHTRED_EX,
    "light_green": colorama.Fore.LIGHTGREEN_EX,
    "light_yellow": colorama.Fore.LIGHTYELLOW_EX,
    "light_blue": colorama.Fore.LIGHTBLUE_EX,
    "light_magenta": colorama.Fore.LIGHTMAGENTA_EX,
    "light_cyan": colorama.Fore.LIGHTCYAN_EX,
}

# Словарь для цветов фона
BG_COLORS = {
    "black": colorama.Back.BLACK,
    "red": colorama.Back.RED,
    "green": colorama.Back.GREEN,
    "yellow": colorama.Back.YELLOW,
    "blue": colorama.Back.BLUE,
    "magenta": colorama.Back.MAGENTA,
    "cyan": colorama.Back.CYAN,
    "white": colorama.Back.WHITE,
    "light_gray": colorama.Back.LIGHTBLACK_EX,
    "light_red": colorama.Back.LIGHTRED_EX,
    "light_green": colorama.Back.LIGHTGREEN_EX,
    "light_yellow": colorama.Back.LIGHTYELLOW_EX,
    "light_blue": colorama.Back.LIGHTBLUE_EX,
    "light_magenta": colorama.Back.LIGHTMAGENTA_EX,
    "light_cyan": colorama.Back.LIGHTCYAN_EX,
}


class SingletonMeta(type):
    """ Metaclass for Singleton pattern implementation."""

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class JsonFormatter(logging.Formatter):
    """ Custom formatter for logging in JSON format."""

    def format(self, record):
        """ Format the log record as JSON."""
        log_entry = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "message": record.getMessage().replace('"', "'"),
            "exc_info": self.formatException(record.exc_info)
            if record.exc_info
            else None,
        }
        _json = json.dumps(log_entry, ensure_ascii=False)
        return _json


class CompressingHandler(logging.FileHandler):
    """
    Обработчик файлового лога с компрессией повторяющихся записей.
    Буферизует записи и пишет в файл с форматом [Nx] message.
    """
    
    def __init__(self, filename, encoding='utf-8', flush_interval=10):
        super().__init__(filename, encoding=encoding, delay=True)
        self.buffer: dict[str, int] = {}  # message -> count
        self.flush_interval = flush_interval
        self._dirty = False
    
    def emit(self, record: logging.LogRecord):
        """Добавляет запись в буфер и пишет в файл."""
        msg = self.format(record)
        self.buffer[msg] = self.buffer.get(msg, 0) + 1
        self._dirty = True
        
        # Пишем если буфер переполнен или при большом количестве уникальных записей
        if len(self.buffer) > 100 or self._dirty:
            self.flush()
    
    def flush(self):
        """Сбрасывает буфер в файл в сжатом формате."""
        if not self.buffer or not self._dirty:
            return
        
        # Формируем содержимое файла
        lines = []
        for msg, count in self.buffer.items():
            if count > 1:
                lines.append(f"[{count}x] {msg}")
            else:
                lines.append(msg)
        
        # Открываем файл и перезаписываем
        with open(self.baseFilename, 'a', encoding=self.encoding) as f:
            f.write('\n'.join(lines))
            f.write('\n')
        
        self.buffer.clear()
        self._dirty = False
    
    def close(self):
        """Закрывает обработчик, сбрасывая буфер."""
        self.flush()
        super().close()


class Logger(metaclass=SingletonMeta):
    """ Logger class implementing Singleton pattern with console, file, and JSON logging."""
    log_files_path: Path
    info_log_path: Path
    debug_log_path: Path
    errors_log_path: Path
    json_log_path: Path
    fastapi_log_path: Path
    gemini_log_path: Path
    playwright_log_path: Path
    yt_dlp_log_path: Path

    def __init__(
        self,
        info_log_path: Optional[str] = None,
        debug_log_path: Optional[str] = None,
        errors_log_path: Optional[str] = None,
        json_log_path: Optional[str] = None,
    ):

        timestamp = datetime.datetime.now().strftime("%d%m%y%H%M")
        self.log_files_path: Path = __root__ / 'tmp' / 'logs'
        self.info_log_path = self.log_files_path / (info_log_path or "info.log")
        self.debug_log_path = self.log_files_path / (debug_log_path or "debug.log")
        self.errors_log_path = self.log_files_path / (errors_log_path or "errors.log")
        self.json_log_path = self.log_files_path / (json_log_path or "log.json")
        self.fastapi_log_path = self.log_files_path / "fastapi.log"
        self.gemini_log_path = self.log_files_path / "gemini.log"
        self.playwright_log_path = self.log_files_path / "playwright.log"
        self.yt_dlp_log_path = self.log_files_path / "yt_dlp.log"

        # Ensure directories exist
        self.log_files_path.mkdir(parents=True, exist_ok=True)

        # Ensure log files exist
        self.info_log_path.touch(exist_ok=True)
        self.debug_log_path.touch(exist_ok=True)
        self.errors_log_path.touch(exist_ok=True)
        self.json_log_path.touch(exist_ok=True)
        self.fastapi_log_path.touch(exist_ok=True)
        self.gemini_log_path.touch(exist_ok=True)
        self.playwright_log_path.touch(exist_ok=True)
        self.yt_dlp_log_path.touch(exist_ok=True)

        # Console logger
        self.logger_console = logging.getLogger(name="logger_console")
        self.logger_console.setLevel(logging.DEBUG)

        import os
        from dotenv import load_dotenv
        load_dotenv(__root__ / '.env')
        try:
            from core.config import server_cfg
            mode_val = getattr(server_cfg, "mode", "dev").lower()
            is_debug = getattr(server_cfg, "debug", True)
        except ImportError:
            mode_val = "dev"
            is_debug = True
        self.is_debug_mode = (mode_val in ('dev', 'debug') or is_debug)

        # Info file logger
        self.logger_file_info = logging.getLogger(name="logger_file_info")
        self.logger_file_info.setLevel(logging.INFO)
        self.logger_file_info.propagate = False
        info_handler = logging.FileHandler(self.info_log_path, encoding='utf-8')
        info_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_info.addHandler(info_handler)

        # Debug file logger
        self.logger_file_debug = logging.getLogger(name="logger_file_debug")
        self.logger_file_debug.setLevel(logging.DEBUG)
        self.logger_file_debug.propagate = False
        debug_handler = logging.FileHandler(self.debug_log_path, encoding='utf-8')
        debug_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_debug.addHandler(debug_handler)

        # Errors file logger (с компрессией повторяющихся ошибок)
        self.logger_file_errors = logging.getLogger(name="logger_file_errors")
        self.logger_file_errors.setLevel(logging.ERROR)
        self.logger_file_errors.propagate = False
        errors_handler = CompressingHandler(self.errors_log_path, encoding='utf-8')
        errors_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_errors.addHandler(errors_handler)

        # Module specific loggers
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        
        self.logger_fastapi = logging.getLogger("logger_fastapi")
        self.logger_fastapi.setLevel(logging.DEBUG)
        self.logger_fastapi.propagate = False
        fastapi_handler = CompressingHandler(self.fastapi_log_path, encoding='utf-8')
        fastapi_handler.setFormatter(formatter)
        self.logger_fastapi.addHandler(fastapi_handler)

        self.logger_gemini = logging.getLogger("logger_gemini")
        self.logger_gemini.setLevel(logging.DEBUG)
        self.logger_gemini.propagate = False
        gemini_handler = CompressingHandler(self.gemini_log_path, encoding='utf-8')
        gemini_handler.setFormatter(formatter)
        self.logger_gemini.addHandler(gemini_handler)

        self.logger_playwright = logging.getLogger("logger_playwright")
        self.logger_playwright.setLevel(logging.DEBUG)
        self.logger_playwright.propagate = False
        playwright_handler = CompressingHandler(self.playwright_log_path, encoding='utf-8')
        playwright_handler.setFormatter(formatter)
        self.logger_playwright.addHandler(playwright_handler)

        self.logger_yt_dlp = logging.getLogger("logger_yt_dlp")
        self.logger_yt_dlp.setLevel(logging.DEBUG)
        self.logger_yt_dlp.propagate = False
        yt_dlp_handler = CompressingHandler(self.yt_dlp_log_path, encoding='utf-8')
        yt_dlp_handler.setFormatter(formatter)
        self.logger_yt_dlp.addHandler(yt_dlp_handler)

        # JSON file logger
        self.logger_file_json = logging.getLogger(name='logger_json')
        self.logger_file_json.setLevel(logging.DEBUG)
        self.logger_file_json.propagate = False
        json_handler = logging.FileHandler(self.json_log_path, encoding='utf-8')
        json_handler.setFormatter(JsonFormatter())  # Используем наш кастомный форматтер
        self.logger_file_json.addHandler(json_handler)


        # Удаляем все обработчики, которые выводят в консоль
        for handler in self.logger_file_json.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.logger_file_json.removeHandler(handler)

    def _format_message(self, message, ex=None, color: Optional[Tuple[str, str]] = None):
        """ Returns formatted message with optional color and exception information."""
        if color:
            text_color, bg_color = color
            text_color = TEXT_COLORS.get(text_color, colorama.Fore.RESET)
            bg_color = BG_COLORS.get(bg_color, colorama.Back.RESET)
            ex_str = ""
            if ex:
                ex_str = f" {ex}"
            message = f"{text_color}{bg_color}{message}{ex_str}{colorama.Style.RESET_ALL}"
        return message

    def _ex_full_info(self, ex):
        """ Returns full exception information along with the previous function, file, and line details."""
        frame_info = inspect.stack()[3]
        file_name = frame_info.filename
        function_name = frame_info.function
        line_number = frame_info.lineno

        ex_str = ""
        if ex:
            ex_str = f"{ex}"
        return f"\nFile: {file_name}, \n |\n  -Function: {function_name}, \n   |\n    --Line: {line_number}\n{ex_str}"

    def log(self, level, message, ex=None, exc_info=False, color: Optional[Tuple[str, str]] = None):
        """
        Логирует сообщение с заданным уровнем, опциональным цветом и информацией об исключении.

        Args:
            level (int): Уровень логирования (например, logging.INFO).
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение для записи.
            exc_info (bool, optional): Включить информацию об исключении в вывод.
            color (tuple, optional): Кортеж (текст, фон) для раскраски сообщения.

        Returns:
            None
        """
        # In PROD mode (not self.is_debug_mode), do not log DEBUG events
        if level == logging.DEBUG and not self.is_debug_mode:
            return

        formatted_message = self._format_message(message, ex, color)
        if exc_info:
            formatted_message += self._ex_full_info(ex)

        if self.logger_console:
            self.logger_console.log(level, formatted_message, exc_info=exc_info)

        if self.logger_file_json:
            self.logger_file_json.log(level, message, exc_info=exc_info)

        if level == logging.INFO and self.logger_file_info:
            self.logger_file_info.log(level, formatted_message)

        if level == logging.DEBUG and self.logger_file_debug:
            self.logger_file_debug.log(level, formatted_message)

        if level in [logging.ERROR, logging.CRITICAL] and self.logger_file_errors:
            self.logger_file_errors.log(level, formatted_message)

        # Перенаправление логов по модулям на основе стека вызовов
        try:
            stack = inspect.stack()
            caller_file = ""
            for frame in stack:
                filename = frame.filename.lower()
                if "logger.py" not in filename:
                    caller_file = filename
                    break

            if caller_file:
                clean_msg = str(message)
                if ex:
                    clean_msg += f" {ex}"
                
                # FastAPI routing
                if "fastapi" in caller_file or "main.py" in caller_file:
                    if self.logger_fastapi:
                        self.logger_fastapi.log(level, clean_msg)
                
                # Gemini / AI routing
                if "gemini" in caller_file or "src/ai" in caller_file or "src\\ai" in caller_file:
                    if self.logger_gemini:
                        self.logger_gemini.log(level, clean_msg)
                
                # Playwright routing
                if "playwright" in caller_file or "torrent_playwright" in caller_file:
                    if self.logger_playwright:
                        self.logger_playwright.log(level, clean_msg)

                # Yt-dlp routing
                if "yt_dlp" in caller_file or "yt-dlp" in caller_file:
                    if self.logger_yt_dlp:
                        self.logger_yt_dlp.log(level, clean_msg)
        except Exception as e:
            pass

    def info(self, message, ex=None, exc_info=False, text_color: str = "green", bg_color: str = ""):
        """
        Логирует сообщение уровня INFO.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.INFO, message, ex, exc_info, color)

    def success(self, message, ex=None, exc_info=False, text_color: str = "yellow", bg_color: str = ""):
        """
        Логирует сообщение об успешной операции.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.INFO, message, ex, exc_info, color)

    def warning(self, message, ex=None, exc_info=False, text_color: str = "black", bg_color: str = "yellow"):
        """
        Логирует сообщение уровня WARNING.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.WARNING, message, ex, exc_info, color)

    def debug(self, message, ex=None, exc_info=True, text_color: str = "cyan", bg_color: str = ""):
        """
        Логирует сообщение уровня DEBUG.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.DEBUG, message, ex, exc_info, color)

    def error(self, message, ex=None, exc_info=True, text_color: str = "red", bg_color: str = ""):
        """
        Логирует сообщение уровня ERROR.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.ERROR, message, ex, exc_info, color)

    def critical(self, message, ex=None, exc_info=True, text_color: str = "red", bg_color: str = "white"):
        """
        Логирует сообщение уровня CRITICAL.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.CRITICAL, message, ex, exc_info, color)

# Initialize logger with file paths
#logger = Logger(info_log_path='info.log', debug_log_path='debug.log', errors_log_path='errors.log', json_log_path='log.json')
logger: Logger = Logger()