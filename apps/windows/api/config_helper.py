# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Config Helper
# =============================================================================
# Description:
#   Унифицированное чтение и сохранение настроек AI-моделей и провайдеров в config.json.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.config_helper import save_ai_config, resolve_active_config_path
#
#     save_ai_config(provider='gemini', model_name='gemini-3.1-flash-lite')
#
# File: config_helper.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""Унифицированное чтение и сохранение настроек AI-моделей и провайдеров в config.json."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from header import __root__
from logger import logger


def resolve_active_config_path(profile: str = "") -> Path:
    """Находит актуальный путь к конфигурационному файлу apps/windows/config.json."""
    cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    if cfg_env:
        p = Path(cfg_env)
        active_p = p if p.is_absolute() else (__root__ / cfg_env)
        if active_p.exists():
            return active_p

    candidates = [
        __root__ / "apps" / "windows" / "config.json",
        __root__ / "start_scenarios_config" / "tc.json",
        __root__ / "config" / "tc.json",
        __root__ / "config_tc.json",
        __root__ / "tc.json",
        __root__ / "config.json",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    return candidates[0]


def save_ai_config(provider: str, model_name: str, config_path: Optional[Path] = None) -> bool:
    """Сохраняет активный AI-провайдер и модель во все секции конфигурационного файла.

    Обновляет:
      1. ai_providers_and_models_configuration.default_provider
      2. ai_providers_and_models_configuration.default_model
      3. ai_providers_and_models_configuration.providers[prov].enabled = True
      4. ai_providers_and_models_configuration.providers[prov].default_model = model_name
      5. ai_providers_and_models_configuration.providers[prov].model = model_name
      6. ai.provider = prov
      7. ai[prov].model = model_name

    Args:
        provider: Имя провайдера (gemini, agy, foundry, ollama, onnx, hf, openai, gemini_cli).
        model_name: Имя модели.
        config_path: Опциональный путь к файлу конфигурации.

    Returns:
        bool: True если запись успешна.
    """
    target_path = config_path or resolve_active_config_path()
    if not target_path:
        return False

    try:
        data: Dict[str, Any] = {}
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        prov_key = (provider or "").lower().strip()
        model_str = (model_name or "").strip()

        if not prov_key:
            if model_str.startswith("agy-"):
                prov_key = "agy"
            elif model_str.startswith("foundry:"):
                prov_key = "foundry"
            elif model_str.startswith("ollama:"):
                prov_key = "ollama"
            elif model_str.startswith("gemini_cli:"):
                prov_key = "gemini_cli"
            elif model_str.startswith("onnx:") or model_str.startswith("onnx::"):
                prov_key = "onnx"
            elif model_str.startswith("hf:") or model_str.startswith("hf::"):
                prov_key = "hf"
            elif any(model_str.startswith(p) for p in ("openai:", "deepseek:", "groq:", "openrouter:", "lmstudio:")):
                prov_key = "openai"
            else:
                prov_key = "gemini"

        # 1. Обновляем секцию ai_providers_and_models_configuration
        if "ai_providers_and_models_configuration" not in data or not isinstance(data["ai_providers_and_models_configuration"], dict):
            data["ai_providers_and_models_configuration"] = {}

        ai_cfg = data["ai_providers_and_models_configuration"]
        ai_cfg["default_provider"] = prov_key
        ai_cfg["default_model"] = model_str

        if "providers" not in ai_cfg or not isinstance(ai_cfg["providers"], dict):
            ai_cfg["providers"] = {}

        if prov_key not in ai_cfg["providers"] or not isinstance(ai_cfg["providers"][prov_key], dict):
            ai_cfg["providers"][prov_key] = {}

        ai_cfg["providers"][prov_key]["enabled"] = True
        ai_cfg["providers"][prov_key]["default_model"] = model_str
        ai_cfg["providers"][prov_key]["model"] = model_str

        # 2. Обновляем секцию ai
        if "ai" not in data or not isinstance(data["ai"], dict):
            data["ai"] = {}

        data["ai"]["provider"] = prov_key
        if prov_key not in data["ai"] or not isinstance(data["ai"][prov_key], dict):
            data["ai"][prov_key] = {}
        data["ai"][prov_key]["model"] = model_str

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"[ConfigHelper] Конфигурация успешно обновлена: {target_path} -> provider={prov_key}, model={model_str}")
        return True
    except Exception as e:
        logger.error(f"[ConfigHelper] Ошибка сохранения конфигурации в {target_path}: {e}", exc_info=True)
        return False


__all__ = [
    "resolve_active_config_path",
    "save_ai_config",
]
