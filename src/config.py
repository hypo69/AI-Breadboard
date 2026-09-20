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

import os
from pathlib import Path
from types import SimpleNamespace
from src.utils.jjson import j_loads_ns
from header import __root__

_cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
if _cfg_env:
    _cfg_path = Path(_cfg_env)
    CONFIG_FILE = _cfg_path if _cfg_path.is_absolute() else (__root__ / _cfg_env)
else:
    CONFIG_FILE = __root__ / "config.json"

if not CONFIG_FILE.exists() and (__root__ / "config.json").exists():
    CONFIG_FILE = __root__ / "config.json"


# Load configuration
global_settings = j_loads_ns(CONFIG_FILE)

# Exposure of main sections for easier import
server_cfg = getattr(global_settings, "server", SimpleNamespace())
ai_cfg = getattr(global_settings, "ai", SimpleNamespace())
tts_cfg = getattr(global_settings, "tts", SimpleNamespace())
logging_cfg = getattr(global_settings, "logging", SimpleNamespace())
pprint_cfg = getattr(global_settings, "pprint", getattr(global_settings, "printer", SimpleNamespace()))
printer_cfg = pprint_cfg
qbittorrent_cfg = getattr(global_settings, "qbittorrent", SimpleNamespace())
qbt_cfg = qbittorrent_cfg
storage_cfg = getattr(global_settings, "storage", SimpleNamespace())
plugins_cfg = getattr(global_settings, "plugins", SimpleNamespace())
schedulers_cfg = getattr(global_settings, "schedulers", getattr(global_settings, "scheduler", SimpleNamespace()))

from src.utils.ports import load_ports_config, PORTS_FILE
ports_cfg = load_ports_config(PORTS_FILE)

