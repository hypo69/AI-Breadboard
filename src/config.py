# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Application global configuration loading and exposure
# =============================================================================
# Description:
#   Loads global application configuration from config.json file and exposes
#   main configuration sections (server, AI, TTS, logging, qBittorrent) as SimpleNamespace objects
#   for convenient access across the application through centralized config module.
#
# File: config.py
# Project: ai-breadboard
# Package: src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
from types import SimpleNamespace
from src.utils.jjson import j_loads_ns
from header import __root__

CONFIG_FILE = __root__ / "config.json"

# Loading global configuration
global_settings = j_loads_ns(CONFIG_FILE)

# Exposure of main sections for easier import
server_cfg = getattr(global_settings, "server", SimpleNamespace())
ai_cfg = getattr(global_settings, "ai", SimpleNamespace())
tts_cfg = getattr(global_settings, "tts", SimpleNamespace())
logging_cfg = getattr(global_settings, "logging", SimpleNamespace())
qbittorrent_cfg = getattr(global_settings, "qbittorrent", SimpleNamespace())
qbt_cfg = qbittorrent_cfg

