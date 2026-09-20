# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Apps Common Package Init
# =============================================================================
# Description:
#   Инициализация вспомогательного пакета apps.common.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.common
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Общие утилиты для приложений в apps/."""

from apps.common.discovery import UtilityDiscovery
from apps.common.csv_logger import (
    AppCsvLogger,
    get_apps_log_dir,
    log_custom_csv,
    log_event,
    log_param_change,
    log_poll,
    set_apps_log_dir_override,
    write_csv_row,
)
from apps.common.autolog_engine import (
    AutoLogEngine,
    autolog_engine,
    parse_interval_seconds,
    load_autolog_config,
)

__all__ = [
    "UtilityDiscovery",
    "AppCsvLogger",
    "get_apps_log_dir",
    "set_apps_log_dir_override",
    "write_csv_row",
    "log_event",
    "log_param_change",
    "log_poll",
    "log_custom_csv",
    "AutoLogEngine",
    "autolog_engine",
    "parse_interval_seconds",
    "load_autolog_config",
]

