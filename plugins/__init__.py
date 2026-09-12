# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dynamic Plugin Loader and Registry
# =============================================================================
# Description:
#   Discovers, dynamically imports, initializes, and manages all extension plugins
#   in the AI Breadboard environment with configuration and environment overrides.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Dynamic plugin loader and registry package.

Provides automated discovery and loading of BasePlugin instances from subdirectories
under plugins/, checking configuration toggles and environment variables.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Dict, Optional

from header import __root__
from src.logger import logger
from src.config import global_settings
from plugins.base import BasePlugin

__all__ = ["BasePlugin", "load_plugins"]


def load_plugins(ai_model: Any = None) -> Dict[str, BasePlugin]:
    """Discover, load, and instantiate all available plugins in the plugins directory.

    Scans the plugins/ folder for directories containing __init__.py, imports each
    module, instantiates the plugin using module.plugin(ai_model=ai_model), and checks
    activation state from config.json and DISABLED_PLUGINS environment variable.

    Args:
        ai_model (Any): Optional AI model instance to inject into plugins.

    Returns:
        Dict[str, BasePlugin]: Mapping of plugin names to initialized plugin instances.

    Examples:
        >>> from plugins import load_plugins
        >>> plugins_dict = load_plugins()
        >>> 'telegram_bot' in plugins_dict
        True
    """
    plugins_dir: Path = __root__ / "plugins"
    plugins: Dict[str, BasePlugin] = {}

    if not plugins_dir.exists() or not plugins_dir.is_dir():
        logger.warning(f"Plugins directory not found at {plugins_dir}")
        return plugins

    # Parse disabled plugins from environment variable (comma or space separated)
    disabled_env_raw = os.getenv("DISABLED_PLUGINS", "")
    disabled_env = {
        name.strip().lower()
        for name in disabled_env_raw.replace(",", " ").split()
        if name.strip()
    }

    # Extract plugins section from config.json if available
    plugins_cfg: Dict[str, Any] = getattr(global_settings, "plugins", {})
    if not isinstance(plugins_cfg, dict):
        try:
            plugins_cfg = dict(plugins_cfg.__dict__)
        except Exception:
            plugins_cfg = {}

    for item in plugins_dir.iterdir():
        if not item.is_dir() or item.name.startswith(("_", ".")):
            continue

        init_file = item / "__init__.py"
        if not init_file.exists():
            continue

        plugin_mod_name = f"plugins.{item.name}"
        try:
            module = importlib.import_module(plugin_mod_name)
            if not hasattr(module, "plugin") or not callable(module.plugin):
                logger.debug(f"Module {plugin_mod_name} does not expose a callable 'plugin' factory.")
                continue

            instance: BasePlugin = module.plugin(ai_model=ai_model)
            if not isinstance(instance, BasePlugin):
                logger.warning(
                    f"Factory {plugin_mod_name}.plugin() returned object of type {type(instance)}, expected BasePlugin."
                )
                continue

            # Determine enabled status: config.json > env > default
            is_disabled_env = instance.name.lower() in disabled_env or item.name.lower() in disabled_env
            plugin_specific_cfg = plugins_cfg.get(instance.name, {})
            is_enabled_cfg = True
            if isinstance(plugin_specific_cfg, dict) and "enabled" in plugin_specific_cfg:
                is_enabled_cfg = bool(plugin_specific_cfg["enabled"])

            instance.enabled = (not is_disabled_env) and is_enabled_cfg

            # Merge config from config.json if present
            if isinstance(plugin_specific_cfg, dict) and "config" in plugin_specific_cfg:
                instance.update_config(plugin_specific_cfg["config"])

            plugins[instance.name] = instance
            logger.info(f"Loaded plugin: '{instance.name}' (v{instance.version}, enabled={instance.enabled})")

        except Exception as exc:
            logger.error(f"Failed to load plugin from '{item.name}': {exc}", exc_info=True)

    return plugins
