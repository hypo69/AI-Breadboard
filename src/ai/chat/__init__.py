"""Пакет chat агрегирует все чат‑модули провайдеров.
Экспортирует основные классы для удобного импорта:
    from src.ai.chat import AgyChatBase, GeminiChatBase, ...
"""
from .agy import *
from .foundry import *
from .gemini import *
from .gemini_cli import *
from .hf import *
from .ollama import *
from .onnx import *
from .openai_compat import *
from .unified import *