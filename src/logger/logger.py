# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Application logging system with color output and file rotation
# =============================================================================
# Description:
#   Comprehensive logging module with support for colored console output, JSON formatting,
#   asynchronous logging queue, file rotation, and multi-level filtering for development and production environments.
#
# File: logger.py
# Project: ai-breadboard
# Package: src.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import logging.handlers
import colorama
import datetime
import json
import inspect
import threading
import queue
import atexit
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict
from types import SimpleNamespace
from collections import Counter

import header
from header import __root__

# Initialization colorama для поддержки цветного вывода
colorama.init(autoreset=False)

# Dictionary для цветов текста
TEXT_COLORS: Dict[str, str] = {
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

# Dictionary для цветов фона
BG_COLORS: Dict[str, str] = {
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
    """
    Метакласс для реализации паттерна Singleton.
    Гарантирует, что class имеет только один экземпляр и предоставляет 
    глобальную точку доступа к этому экземпляру.
    
    Потокобезопасен благодаря использованию Lock.
    """

    _instances: Dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """
        Creates или Returns существующий экземпляр класса.
        
        Returns:
            Единственный экземпляр класса.
        """
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

class JsonFormatter(logging.Formatter):
    """
    Кастомный форматтер для логирования в JSON формате.
    
    Преобразует LogRecord в JSON строку с полями:
    - timestamp: временная метка записи
    - level: уровень логирования (INFO, DEBUG и т.д.)
    - message: текст сообщения
    - exc_info: Info об исключении (если присутствует)
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует лог-запись в JSON.
        
        Args:
            record: LogRecord для форматирования.
            
        Returns:
            JSON string с информацией о логе.
        """
        log_entry: Dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage().replace('"', "'"),
            "exc_info": self.formatException(record.exc_info)
            if record.exc_info
            else None,
        }
        return json.dumps(log_entry, ensure_ascii=False)

class CompressingHandler(logging.handlers.RotatingFileHandler):
    """
    Обработчик файловых логов с компрессией повторяющихся записей и ротацией.
    
    Особенности:
    - Буферизирует записи и сжимает их в формате [Nx] message
    - Поддерживает ротацию файлов по размеру
    - Потокобезопасен при многопоточном доступе
    - Гарантирует сохранение логов при падении процесса
    
    Parameters:
        filename: Путь к файлу лога
        maxBytes: Максимальный размер файла перед ротацией (по умолчанию 10MB)
        backupCount: Количество резервных файлов (по умолчанию 5)
    """
    
    def __init__(self, filename: str, maxBytes: int = 10 * 1024 * 1024, 
                 backupCount: int = 5, encoding: str = 'utf-8'):
        """
        Инициализирует обработчик логов с ротацией.
        
        Args:
            filename: Путь к файлу лога.
            maxBytes: Максимальный размер файла в байтах.
            backupCount: Количество сохраняемых резервных файлов.
            encoding: Кодировка файла.
        """
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, 
                        encoding=encoding, delay=False)
        self.buffer: Dict[str, int] = {}  # message -> count
        self._lock = threading.Lock()
        self._dirty = False
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Добавляет запись в буфер с компрессией.
        
        Args:
            record: LogRecord для добавления.
        """
        try:
            msg = self.format(record)
            with self._lock:
                self.buffer[msg] = self.buffer.get(msg, 0) + 1
                self._dirty = True
                
                # Пишем если буфер переполнен или много уникальных записей
                if len(self.buffer) > 100:
                    self.flush()
        except Exception:
            self.handleError(record)
    
    def flush(self) -> None:
        """Сбрасывает буфер в файл с компрессией повторяющихся записей."""
        with self._lock:
            if not self.buffer or not self._dirty:
                return
            
            try:
                # Пишем в файл
                if not self.stream:
                    self.stream = self._open()
                
                for msg, count in self.buffer.items():
                    if count > 1:
                        self.stream.write(f"[{count}x] {msg}\n")
                    else:
                        self.stream.write(f"{msg}\n")
                
                self.stream.flush()
                self.buffer.clear()
                self._dirty = False
            except Exception:
                pass
    
    def close(self) -> None:
        """Закрывает обработчик, предварительно сбрасывая буфер."""
        self.flush()
        super().close()

def compress_lines(lines: list, min_repeat: int = 2) -> list:
    """Сжимает повторяющиеся строки в формат [Nx] text."""
    counter = Counter(lines)
    result = []
    
    for line, count in counter.items():
        stripped = line.strip()
        if not stripped:
            continue
        if count >= min_repeat:
            result.append(f"[{count}x] {stripped}")
        else:
            result.append(stripped)
    
    return result

class Logger(metaclass=SingletonMeta):
    """
    Универсальный логгер с поддержкой цветного вывода, файловых логов и JSON формата.
    
    Реализует паттерн Singleton и гарантирует единственный экземпляр логгера во всем приложении.
    
    Основные возможности:
    - Цветной вывод в консоль с поддержкой цветов текста и фона
    - Splitting логов по типам (info, debug, errors)
    - JSON форматирование для структурированного анализа
    - Ротация файлов логов по размеру
    - Умная маршрутизация логов по модулям (FastAPI, Gemini, Playwright и т.д.)
    - Автоматическое disconnection DEBUG логов в production режиме
    
    Атрибуты:
        log_files_path: Путь к директории с логами
        info_log_path: Путь к файлу информационных логов
        debug_log_path: Путь к файлу отладочных логов
        errors_log_path: Путь к файлу ошибок
        json_log_path: Путь к JSON логам
        is_debug_mode: Флаг режима отладки
    """
    
    def __init__(
        self,
        info_log_path: Optional[str] = None,
        debug_log_path: Optional[str] = None,
        errors_log_path: Optional[str] = None,
        json_log_path: Optional[str] = None,
    ):
        """
        Инициализирует логгер с заданными путями файлов логов.
        
        Args:
            info_log_path: Имя файла для INFO логов.
            debug_log_path: Имя файла для DEBUG логов.
            errors_log_path: Имя файла для ERROR логов.
            json_log_path: Имя файла для JSON логов.
        """
        # Установка путей к файлам логов в системную temp директорию (кроссплатформенно)
        self.log_files_path: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'logs'
        self.info_log_path: Path = self.log_files_path / (info_log_path or "info.log")
        self.debug_log_path: Path = self.log_files_path / (debug_log_path or "debug.log")
        self.errors_log_path: Path = self.log_files_path / (errors_log_path or "errors.log")
        self.json_log_path: Path = self.log_files_path / (json_log_path or "log.json")
        self.fastapi_log_path: Path = self.log_files_path / "fastapi.log"
        self.gemini_log_path: Path = self.log_files_path / "gemini.log"
        self.playwright_log_path: Path = self.log_files_path / "playwright.log"
        self.yt_dlp_log_path: Path = self.log_files_path / "yt_dlp.log"

        # Создание директории с логами
        self.log_files_path.mkdir(parents=True, exist_ok=True)

        # Создание файлов логов
        for log_path in [self.info_log_path, self.debug_log_path, self.errors_log_path,
                        self.json_log_path, self.fastapi_log_path, self.gemini_log_path,
                        self.playwright_log_path, self.yt_dlp_log_path]:
            log_path.touch(exist_ok=True)

        # Консольный логгер
        self.logger_console: logging.Logger = logging.getLogger("logger_console")
        self.logger_console.setLevel(logging.DEBUG)
        self.logger_console.propagate = False

        # Определение режима отладки
        self._setup_debug_mode()
        
        # Установка обработчиков для разных типов логов
        self._setup_file_handlers()
        
        # Установка Module-специфичных логгеров
        self._setup_module_loggers()
        
        # Регистрация очистки при выходе
        atexit.register(self._cleanup)

    def _setup_debug_mode(self) -> None:
        """Определяет, находится ли приложение в режиме отладки."""
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv(__root__ / '.env')
            
            try:
                from src.config import server_cfg
                mode_val = getattr(server_cfg, "mode", "dev").lower()
                is_debug = getattr(server_cfg, "debug", True)
            except ImportError:
                mode_val = os.getenv("MODE", "dev").lower()
                is_debug = os.getenv("DEBUG", "true").lower() == "true"
            
            self.is_debug_mode = (mode_val in ('dev', 'debug') or is_debug)
        except Exception:
            self.is_debug_mode = True  # По умолчанию включаем режим отладки

    def _setup_file_handlers(self) -> None:
        """Sets обработчики для файловых логов."""
        # INFO логгер
        self.logger_file_info: logging.Logger = logging.getLogger("logger_file_info")
        self.logger_file_info.setLevel(logging.INFO)
        self.logger_file_info.propagate = False
        info_handler = logging.FileHandler(self.info_log_path, encoding='utf-8')
        info_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_info.addHandler(info_handler)

        # DEBUG логгер
        self.logger_file_debug: logging.Logger = logging.getLogger("logger_file_debug")
        self.logger_file_debug.setLevel(logging.DEBUG)
        self.logger_file_debug.propagate = False
        debug_handler = logging.FileHandler(self.debug_log_path, encoding='utf-8')
        debug_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_debug.addHandler(debug_handler)

        # ERROR логгер с компрессией
        self.logger_file_errors: logging.Logger = logging.getLogger("logger_file_errors")
        self.logger_file_errors.setLevel(logging.ERROR)
        self.logger_file_errors.propagate = False
        errors_handler = CompressingHandler(str(self.errors_log_path), encoding='utf-8')
        errors_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_errors.addHandler(errors_handler)

        # JSON логгер
        self.logger_file_json: logging.Logger = logging.getLogger("logger_json")
        self.logger_file_json.setLevel(logging.DEBUG)
        self.logger_file_json.propagate = False
        json_handler = logging.FileHandler(self.json_log_path, encoding='utf-8')
        json_handler.setFormatter(JsonFormatter())
        self.logger_file_json.addHandler(json_handler)

    def _setup_module_loggers(self) -> None:
        """Sets логгеры для отдельных модулей."""
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        
        modules_config = [
            ("logger_fastapi", self.fastapi_log_path),
            ("logger_gemini", self.gemini_log_path),
            ("logger_playwright", self.playwright_log_path),
            ("logger_yt_dlp", self.yt_dlp_log_path),
        ]
        
        for logger_name, log_path in modules_config:
            module_logger = logging.getLogger(logger_name)
            module_logger.setLevel(logging.DEBUG)
            module_logger.propagate = False
            handler = CompressingHandler(str(log_path), encoding='utf-8')
            handler.setFormatter(formatter)
            module_logger.addHandler(handler)
            
            # Сохраняем как атрибут класса
            setattr(self, logger_name, module_logger)

    def _get_caller_info(self, depth: int = 2) -> Tuple[str, str, int]:
        """
        Безопасно receives информацию о вызывающей функции.
        
        Args:
            depth: Глубина стека для поиска caller'а.
            
        Returns:
            Tuple (file_name, function_name, line_number).
        """
        try:
            stack = inspect.stack()
            if len(stack) > depth:
                frame_info = stack[depth]
                return (
                    frame_info.filename,
                    frame_info.function,
                    frame_info.lineno
                )
        except Exception:
            pass
        return ("unknown", "unknown", 0)

    def _format_message(self, message: str, ex: Optional[Exception] = None, 
                       color: Optional[Tuple[str, str]] = None) -> str:
        """
        Форматирует сообщение с опциональным цветом и информацией об исключении.
        
        Args:
            message: Текст сообщения.
            ex: Exception для добавления.
            color: Tuple (текст_цвет, фон_цвет).
            
        Returns:
            Отформатированное сообщение.
        """
        if color:
            text_color, bg_color = color
            text_color = TEXT_COLORS.get(text_color, colorama.Fore.RESET)
            bg_color = BG_COLORS.get(bg_color, colorama.Back.RESET)
            ex_str = f" {str(ex)}" if ex else ""
            message = f"{text_color}{bg_color}{message}{ex_str}{colorama.Style.RESET_ALL}"
        elif ex:
            message = f"{message} {str(ex)}"
        return message

    def _route_to_module_logger(self, message: str, level: int, 
                               filename: str) -> None:
        """
        Маршрутизирует лог в Module-специфичный логгер на основе пути файла.
        
        Args:
            message: Текст сообщения.
            level: Уровень логирования.
            filename: Путь к файлу вызывающего кода.
        """
        filename_lower = filename.lower().replace("\\", "/")
        
        routing_map = [
            ("fastapi", self.logger_fastapi),
            ("main.py", self.logger_fastapi),
            ("gemini", self.logger_gemini),
            ("src/ai", self.logger_gemini),
            ("src\\ai", self.logger_gemini),
            ("playwright", self.logger_playwright),
            ("torrent_playwright", self.logger_playwright),
            ("yt_dlp", self.logger_yt_dlp),
            ("yt-dlp", self.logger_yt_dlp),
        ]
        
        for pattern, module_logger in routing_map:
            if pattern.lower() in filename_lower:
                try:
                    module_logger.log(level, message)
                except Exception:
                    pass
                break

    def log(self, level: int, message: str, ex: Optional[Exception] = None, 
            exc_info: bool = False, color: Optional[Tuple[str, str]] = None) -> None:
        """
        Логирует сообщение с заданным уровнем и параметрами.
        
        Args:
            level: Уровень логирования (logging.INFO, logging.ERROR и т.д.).
            message: Текст сообщения.
            ex: Exception для логирования.
            exc_info: Включить полную информацию об исключении.
            color: Tuple (текст_цвет, фон_цвет) для окраски.
        """
        # В production режиме игнорируем DEBUG логи
        if level == logging.DEBUG and not self.is_debug_mode:
            return

        formatted_message = self._format_message(message, ex, color)
        
        # Логирование в консоль
        if self.logger_console:
            self.logger_console.log(level, formatted_message, exc_info=exc_info)

        # Логирование в JSON (без форматирования)
        if self.logger_file_json:
            self.logger_file_json.log(level, message, exc_info=exc_info)

        # Логирование по типам
        if level == logging.INFO and self.logger_file_info:
            self.logger_file_info.log(level, formatted_message)
        elif level == logging.DEBUG and self.logger_file_debug:
            self.logger_file_debug.log(level, formatted_message)
        elif level in [logging.ERROR, logging.CRITICAL] and self.logger_file_errors:
            self.logger_file_errors.log(level, formatted_message)

        # Маршрутизация по модулям
        try:
            filename, func_name, line_no = self._get_caller_info(depth=3)
            clean_msg = str(message)
            if ex:
                clean_msg += f" {str(ex)}"
            self._route_to_module_logger(clean_msg, level, filename)
        except Exception:
            pass

    def _cleanup(self) -> None:
        """Очищает ресурсы при завершении приложения."""
        try:
            for logger_name in ["logger_console", "logger_file_info", "logger_file_debug",
                              "logger_file_errors", "logger_json", "logger_fastapi",
                              "logger_gemini", "logger_playwright", "logger_yt_dlp"]:
                logger_obj = getattr(self, logger_name, None)
                if logger_obj:
                    for handler in logger_obj.handlers[:]:
                        handler.flush()
                        handler.close()
                        logger_obj.removeHandler(handler)
        except Exception:
            pass

    def info(self, message: str, ex: Optional[Exception] = None, exc_info: bool = False,
            text_color: str = "green", bg_color: str = "") -> None:
        """Логирует сообщение уровня INFO с зелёным цветом по умолчанию."""
        color = (text_color, bg_color) if bg_color else (text_color, "")
        self.log(logging.INFO, message, ex, exc_info, color)

    def success(self, message: str, ex: Optional[Exception] = None, exc_info: bool = False,
               text_color: str = "light_green", bg_color: str = "") -> None:
        """Логирует сообщение об успешной операции с жёлтым цветом по умолчанию."""
        color = (text_color, bg_color) if bg_color else (text_color, "")
        self.log(logging.INFO, message, ex, exc_info, color)

    def warning(self, message: str, ex: Optional[Exception] = None, exc_info: bool = False,
               text_color: str = "black", bg_color: str = "yellow") -> None:
        """Логирует сообщение уровня WARNING с чёрным текстом на жёлтом фоне."""
        color = (text_color, bg_color)
        self.log(logging.WARNING, message, ex, exc_info, color)

    def debug(self, message: str, ex: Optional[Exception] = None, exc_info: bool = False,
             text_color: str = "cyan", bg_color: str = "") -> None:
        """Логирует сообщение уровня DEBUG с голубым цветом."""
        color = (text_color, bg_color) if bg_color else (text_color, "")
        self.log(logging.DEBUG, message, ex, exc_info, color)

    def error(self, message: str, ex: Optional[Exception] = None, exc_info: bool = True,
             text_color: str = "red", bg_color: str = "") -> None:
        """Логирует сообщение уровня ERROR с красным цветом и информацией об исключении."""
        color = (text_color, bg_color) if bg_color else (text_color, "")
        self.log(logging.ERROR, message, ex, exc_info, color)

    def critical(self, message: str, ex: Optional[Exception] = None, exc_info: bool = True,
                text_color: str = "white", bg_color: str = "red") -> None:
        """Логирует критическую ошибку с белым текстом на красном фоне."""
        color = (text_color, bg_color)
        self.log(logging.CRITICAL, message, ex, exc_info, color)

# Инициализирация глобального экземпляра логгера (Singleton)
logger: Logger = Logger()
"""Глобальный экземпляр логгера для использования во всем приложении."""
