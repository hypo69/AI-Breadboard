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
    if _cfg_path.is_absolute() and _cfg_path.exists():
        CONFIG_FILE = _cfg_path
    elif (__root__ / _cfg_env).exists():
        CONFIG_FILE = __root__ / _cfg_env
    elif (__root__ / "start_scenarios_config" / _cfg_path.name).exists():
        CONFIG_FILE = __root__ / "start_scenarios_config" / _cfg_path.name
    elif (__root__ / "config" / _cfg_path.name).exists():
        CONFIG_FILE = __root__ / "config" / _cfg_path.name
    else:
        CONFIG_FILE = __root__ / "config.json"
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
apps_cfg = getattr(global_settings, "apps", SimpleNamespace())


def is_app_enabled(app_name: str) -> bool:
    """Проверяет, активно ли приложение согласно текущей конфигурации.

    Args:
        app_name (str): Идентификатор приложения (например, 'wikipedia_research', 'trading_terminal').

    Returns:
        bool: True, если приложение разрешено и не находится в списке отключенных; иначе False.
    """
    apps_section = getattr(global_settings, "apps", None)
    if not apps_section:
        return True

    enabled = getattr(apps_section, "enabled", None)
    disabled = getattr(apps_section, "disabled", None)

    # Преобразование в список, если представлено иным итерируемым объектом
    if disabled is not None:
        disabled_list = list(disabled) if hasattr(disabled, "__iter__") and not isinstance(disabled, str) else [disabled]
        if app_name in disabled_list:
            return False

    if enabled is not None:
        enabled_list = list(enabled) if hasattr(enabled, "__iter__") and not isinstance(enabled, str) else [enabled]
        if len(enabled_list) > 0:
            return app_name in enabled_list

    return True

from src.utils.ports import load_ports_config, PORTS_FILE
ports_cfg = load_ports_config(PORTS_FILE)

from apps.common.autolog_engine import load_autolog_config
autolog_cfg = load_autolog_config()

