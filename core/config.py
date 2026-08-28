## \file core/config.py
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Загрузка и предоставление конфигурации приложения
# =============================================================================
# Описание:
#   Модуль загружает глобальную конфигурацию из файла config.json и
#   предоставляет доступ к основным секциям (сервер, ИИ, TTS, логирование,
#   qBittorrent) в виде объектов SimpleNamespace.
#
# File: core/config.py
# Project: ai-breadboard
# Package: core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
.. module:: core.config
    :platform: Windows, Unix
    :synopsis: Глобальная конфигурация приложения
"""

from pathlib import Path
from types import SimpleNamespace
from core.utils.jjson import j_loads_ns
from header import __root__

CONFIG_FILE = __root__ / "config.json"

# Load global configuration
global_settings = j_loads_ns(CONFIG_FILE)

# Expose main sections for easier import
server_cfg = getattr(global_settings, "server", SimpleNamespace())
ai_cfg = getattr(global_settings, "ai", SimpleNamespace())
tts_cfg = getattr(global_settings, "tts", SimpleNamespace())
logging_cfg = getattr(global_settings, "logging", SimpleNamespace())
qbittorrent_cfg = getattr(global_settings, "qbittorrent", SimpleNamespace())
qbt_cfg = qbittorrent_cfg

